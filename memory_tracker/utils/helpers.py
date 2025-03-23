"""
Helper utilities for memory profiling tasks.
"""

import os
import sys
import time
import psutil
import gc
from contextlib import contextmanager


def get_memory_usage():
    """
    Get the current memory usage of the Python process.
    
    Returns:
        float: Memory usage in MB.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 * 1024)  # Convert to MB


def get_object_count():
    """
    Get counts of all Python objects by type.
    
    Returns:
        dict: Dictionary with object types as keys and counts as values.
    """
    counts = {}
    for obj in gc.get_objects():
        obj_type = type(obj).__name__
        counts[obj_type] = counts.get(obj_type, 0) + 1
    return counts


@contextmanager
def memory_profiler(label="Operation"):
    """
    Context manager to measure memory usage before and after an operation.
    
    Args:
        label (str): Label to identify the operation being profiled.
    
    Yields:
        None
    """
    gc.collect()
    start_mem = get_memory_usage()
    start_time = time.time()
    
    yield
    
    end_time = time.time()
    gc.collect()
    end_mem = get_memory_usage()
    
    print(f"{label}:")
    print(f"  Time elapsed: {end_time - start_time:.2f} seconds")
    print(f"  Memory before: {start_mem:.2f} MB")
    print(f"  Memory after: {end_mem:.2f} MB")
    print(f"  Memory change: {end_mem - start_mem:.2f} MB")


def find_leaks(iterations=3, delay=0.5):
    """
    Run garbage collection and look for objects that aren't being cleaned up.
    
    Args:
        iterations (int): Number of GC cycles to run
        delay (float): Delay between collections in seconds
    
    Returns:
        dict: Counts of objects that persist after multiple collections
    """
    gc.collect()
    initial_counts = get_object_count()
    
    for _ in range(iterations):
        time.sleep(delay)
        gc.collect()
    
    final_counts = get_object_count()
    
    # Find the difference
    potential_leaks = {}
    for obj_type, count in final_counts.items():
        initial = initial_counts.get(obj_type, 0)
        if count > initial:
            potential_leaks[obj_type] = count - initial
    
    return potential_leaks