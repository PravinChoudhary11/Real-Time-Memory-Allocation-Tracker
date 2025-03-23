import tracemalloc
import time
import threading
import gc
import os
import sqlite3
import psutil
from functools import wraps
import linecache
import inspect
from collections import defaultdict

from memory_tracker.core.interceptor import MemoryInterceptor
from memory_tracker.core.snapshot import SnapshotManager
from memory_tracker.database.storage import DatabaseManager
from memory_tracker.analysis.analyzer import MemoryAnalyzer
from memory_tracker.visualization.dashboard import MemoryDashboard as Dashboard


class MemoryTracker:
    """
    Main class for tracking memory allocations and deallocations in Python applications.
    """
    
    def __init__(self, 
                 snapshot_interval=5, 
                 trace_lines=True, 
                 database_path=None,
                 sampling_rate=1.0,
                 track_all_objects=False):
        """
        Initialize the memory tracker.
        
        Args:
            snapshot_interval (int): Time interval between memory snapshots in seconds
            trace_lines (bool): Whether to track line-by-line allocations
            database_path (str): Path to SQLite database for storing tracking data
            sampling_rate (float): Fraction of allocations to track (1.0 = all)
            track_all_objects (bool): Whether to track all objects or just large ones
        """
        self.is_tracking = False
        self.snapshot_interval = snapshot_interval
        self.trace_lines = trace_lines
        self.sampling_rate = sampling_rate
        self.track_all_objects = track_all_objects
        
        # Initialize components
        self.database = DatabaseManager(database_path)
        self.interceptor = MemoryInterceptor(self.database, sampling_rate, track_all_objects)
        self.snapshot_manager = SnapshotManager(self.database)
        self.analyzer = MemoryAnalyzer(self.database)
        self.dashboard = Dashboard(self.database, self.analyzer)
        
        # Internal tracking state
        self._snapshot_thread = None
        self._start_time = None
        self._tracemalloc_started = False
        
    def start(self):
        """
        Start tracking memory allocations.
        """
        if self.is_tracking:
            print("Memory tracker is already running.")
            return
            
        # Start tracemalloc
        tracemalloc.start(25)  # Keep 25 frames in traceback
        self._tracemalloc_started = True
        
        # Initialize the database
        self.database.initialize()
        
        # Start the interceptor
        self.interceptor.start()
        
        # Start the snapshot thread
        self._start_snapshot_thread()
        
        # Record start time
        self._start_time = time.time()
        
        # Set tracking flag
        self.is_tracking = True
        
        print(f"Memory tracking started. Snapshot interval: {self.snapshot_interval}s")
        
    def stop(self):
        """
        Stop tracking memory allocations.
        """
        if not self.is_tracking:
            print("Memory tracker is not running.")
            return
            
        # Stop the snapshot thread
        if self._snapshot_thread and self._snapshot_thread.is_alive():
            self._snapshot_thread_running = False
            self._snapshot_thread.join(timeout=2.0)
            
        # Take final snapshot
        self.snapshot_manager.take_snapshot(
            "Final snapshot", 
            time.time() - self._start_time
        )
        
        # Stop the interceptor
        self.interceptor.stop()
        
        # Stop tracemalloc
        if self._tracemalloc_started:
            tracemalloc.stop()
            self._tracemalloc_started = False
            
        # Set tracking flag
        self.is_tracking = False
        
        print("Memory tracking stopped.")
    
    def _start_snapshot_thread(self):
        """
        Start a background thread to take periodic memory snapshots.
        """
        self._snapshot_thread_running = True
        
        def snapshot_worker():
            snapshot_count = 0
            while self._snapshot_thread_running:
                if snapshot_count > 0:  # Skip first run, but take immediate snapshot
                    self.snapshot_manager.take_snapshot(
                        f"Snapshot {snapshot_count}", 
                        time.time() - self._start_time
                    )
                snapshot_count += 1
                
                # Sleep until next snapshot
                for _ in range(int(self.snapshot_interval * 10)):
                    if not self._snapshot_thread_running:
                        break
                    time.sleep(0.1)
        
        self._snapshot_thread = threading.Thread(
            target=snapshot_worker, 
            daemon=True,
            name="MemoryTrackerSnapshotThread"
        )
        self._snapshot_thread.start()
    
    def track_function(self, func):
        """
        Decorator to track memory usage of a specific function.
        
        Usage:
            @tracker.track_function
            def my_function():
                # ...
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Take snapshot before function execution
            if self.is_tracking:
                before_snapshot = tracemalloc.take_snapshot()
                gc.collect()  # Force garbage collection
                before_memory = psutil.Process(os.getpid()).memory_info().rss
                start_time = time.time()
            
            # Call the function
            result = func(*args, **kwargs)
            
            # Take snapshot after function execution
            if self.is_tracking:
                gc.collect()  # Force garbage collection
                after_memory = psutil.Process(os.getpid()).memory_info().rss
                after_snapshot = tracemalloc.take_snapshot()
                execution_time = time.time() - start_time
                
                # Calculate memory difference
                memory_diff = after_memory - before_memory
                
                # Get the function details
                func_name = func.__name__
                module_name = func.__module__
                
                # Get allocation information
                snapshot_diff = after_snapshot.compare_to(before_snapshot, 'lineno')
                
                # Store function tracking data
                self.database.store_function_tracking(
                    func_name,
                    module_name,
                    memory_diff,
                    execution_time,
                    snapshot_diff
                )
                
                print(f"Function {func_name} used {memory_diff / 1024:.2f} KB in {execution_time:.3f} seconds")
            
            return result
        
        return wrapper
    
    def generate_report(self, output_path=None):
        """
        Generate a comprehensive memory usage report.
        
        Args:
            output_path (str): Path to save the report (default: memory_report.html)
        """
        if not output_path:
            output_path = "memory_report"
            
        if not output_path.endswith((".html", ".htm")):
            output_path += ".html"
            
        # Run analysis
        analysis_results = self.analyzer.analyze()
        
        # Generate the report
        self.dashboard.generate_static_report(analysis_results, output_path)
        
        print(f"Memory report generated at: {output_path}")
        return output_path
    
    def launch_dashboard(self, port=8050):
        """
        Launch an interactive dashboard for memory analysis.
        
        Args:
            port (int): Port to run the dashboard on
        """
        self.dashboard.launch(port=port)
    
    def get_current_memory_usage(self):
        """
        Get current memory usage of the application.
        
        Returns:
            dict: Dictionary with memory usage information
        """
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        return {
            "rss": memory_info.rss,  # Resident Set Size
            "vms": memory_info.vms,  # Virtual Memory Size
            "shared": getattr(memory_info, "shared", 0),  # Shared memory
            "text": getattr(memory_info, "text", 0),  # Text (code)
            "lib": getattr(memory_info, "lib", 0),  # Library
            "data": getattr(memory_info, "data", 0),  # Data + stack
            "dirty": getattr(memory_info, "dirty", 0),  # Dirty pages
        }

    def __enter__(self):
        """Support for context manager usage."""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support for context manager usage."""
        self.stop()