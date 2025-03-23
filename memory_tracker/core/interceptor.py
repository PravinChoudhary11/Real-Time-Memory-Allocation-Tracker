import sys
import gc
import inspect
import random
import time
import threading
import weakref
from functools import wraps
from pympler import asizeof

class MemoryInterceptor:
    """
    Intercepts memory allocations and deallocations to track object lifetimes.
    """
    
    def __init__(self, database, sampling_rate=1.0, track_all_objects=False):
        """
        Initialize the memory interceptor.
        
        Args:
            database: Database manager instance
            sampling_rate (float): Fraction of allocations to track (1.0 = all)
            track_all_objects (bool): Whether to track all objects or just large ones
        """
        self.database = database
        self.sampling_rate = sampling_rate
        self.track_all_objects = track_all_objects
        self.size_threshold = 1024 if not track_all_objects else 0  # 1KB threshold
        
        # Tracking state
        self.is_intercepting = False
        self.tracked_objects = {}  # id: (type, size, stack_trace, creation_time)
        self.original_object_new = None
        self.original_gc_collect = None
        
        # Lock for thread safety
        self.lock = threading.RLock()
    
    def start(self):
        """
        Start intercepting memory operations.
        """
        if self.is_intercepting:
            return
            
        self.tracked_objects.clear()
        
        # Set up object creation tracking
        self._patch_object_creation()
        
        # Set up object deletion tracking
        self._register_finalizer_callback()
        
        # Patch gc.collect to track garbage collection
        self._patch_gc_collect()
        
        self.is_intercepting = True
        
    def stop(self):
        """
        Stop intercepting memory operations.
        """
        if not self.is_intercepting:
            return
            
        # Restore original methods
        if self.original_object_new:
            object.__new__ = self.original_object_new
            self.original_object_new = None
            
        if self.original_gc_collect:
            gc.collect = self.original_gc_collect
            self.original_gc_collect = None
            
        # Store any remaining tracked objects as leaked
        with self.lock:
            for obj_id, (obj_type, size, stack_trace, creation_time) in self.tracked_objects.items():
                self.database.store_object_leak(
                    obj_id, obj_type, size, stack_trace, 
                    creation_time, time.time() - creation_time
                )
            
        self.tracked_objects.clear()
        self.is_intercepting = False
    
    def _patch_object_creation(self):
        """
        Patch the object creation process to track new objects.
        """
        self.original_object_new = object.__new__
        
        @wraps(object.__new__)
        def tracked_new(cls, *args, **kwargs):
            # Create the object
            obj = self.original_object_new(cls, *args, **kwargs)
            
            # Check if we should track this object (based on sampling rate)
            if random.random() > self.sampling_rate:
                return obj
                
            # Get object size
            try:
                size = asizeof.asizeof(obj)
                
                # Only track objects above size threshold
                if size >= self.size_threshold:
                    obj_id = id(obj)
                    obj_type = type(obj).__name__
                    
                    # Get stack trace (skip the first few frames which are our tracking code)
                    stack = inspect.stack()[2:]
                    stack_trace = "\n".join([
                        f"{frame.filename}:{frame.lineno} in {frame.function}"
                        for frame in stack[:10]  # Limit to 10 frames
                    ])
                    
                    # Record the object creation
                    creation_time = time.time()
                    
                    with self.lock:
                        self.tracked_objects[obj_id] = (obj_type, size, stack_trace, creation_time)
                        
                        # Store in database
                        self.database.store_object_allocation(
                            obj_id, obj_type, size, stack_trace, creation_time
                        )
                    
                    # Register finalizer (weak reference callback)
                    weakref.finalize(obj, self._object_deleted, obj_id)
            except:
                # Ignore errors in tracking to avoid affecting program execution
                pass
                
            return obj
            
        # Replace the original method
        object.__new__ = tracked_new
    
    def _object_deleted(self, obj_id):
        """
        Callback when a tracked object is garbage collected.
        
        Args:
            obj_id: ID of the object being deleted
        """
        # Get object information
        with self.lock:
            if obj_id in self.tracked_objects:
                obj_type, size, stack_trace, creation_time = self.tracked_objects[obj_id]
                deletion_time = time.time()
                lifetime = deletion_time - creation_time
                
                # Store deletion in database
                self.database.store_object_deallocation(
                    obj_id, obj_type, size, lifetime, deletion_time
                )
                
                # Remove from tracked objects
                del self.tracked_objects[obj_id]
    
    def _register_finalizer_callback(self):
        """
        Set up callback for object finalization.
        """
        # This is handled by weakref.finalize in _patch_object_creation
        pass
    
    def _patch_gc_collect(self):
        """
        Patch gc.collect to track garbage collection events.
        """
        self.original_gc_collect = gc.collect
        
        @wraps(gc.collect)
        def tracked_collect(*args, **kwargs):
            start_time = time.time()
            before_count = len(gc.get_objects())
            
            # Call original collect
            result = self.original_gc_collect(*args, **kwargs)
            
            # Track GC event
            end_time = time.time()
            after_count = len(gc.get_objects())
            duration = end_time - start_time
            objects_collected = before_count - after_count
            
            # Store GC event
            self.database.store_gc_event(
                start_time, duration, objects_collected, before_count, after_count
            )
            
            return result
            
        # Replace the original method
        gc.collect = tracked_collect
