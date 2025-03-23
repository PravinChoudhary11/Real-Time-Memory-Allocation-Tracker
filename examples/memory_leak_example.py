"""
Example demonstrating detection of a typical memory leak scenario.
"""

import sys
import os
import time

# Add the parent directory to the path so we can import our package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from memory_tracker.utils.helpers import memory_profiler, find_leaks, get_memory_usage


# A global cache that might cause memory leaks if not managed properly
_cache = {}


class LeakyClass:
    """A class demonstrating a common memory leak pattern with circular references."""
    
    def __init__(self, name):
        self.name = name
        self.reference = None
        
    def set_reference(self, other):
        """Create a circular reference."""
        self.reference = other
        # Storing in a global cache - common memory leak source
        _cache[self.name] = self


def create_leak():
    """Create objects with circular references that might leak."""
    for i in range(1000):
        obj1 = LeakyClass(f"obj1_{i}")
        obj2 = LeakyClass(f"obj2_{i}")
        
        # Create circular reference
        obj1.set_reference(obj2)
        obj2.set_reference(obj1)


def main():
    print(f"Initial memory usage: {get_memory_usage():.2f} MB")
    
    with memory_profiler("Creating objects with potential leaks"):
        create_leak()
    
    print("\nRunning leak detection...")
    potential_leaks = find_leaks(iterations=5, delay=0.1)
    
    if potential_leaks:
        print("\nPotential memory leaks detected:")
        for obj_type, count in sorted(potential_leaks.items(), key=lambda x: x[1], reverse=True):
            if count > 10:  # Only show significant counts
                print(f"  {obj_type}: {count} instances")
    else:
        print("\nNo significant potential leaks detected.")
    
    print(f"\nFinal memory usage: {get_memory_usage():.2f} MB")
    
    # Clear the cache to prevent actual memory leaks in this example
    print("\nClearing cache and running garbage collection...")
    _cache.clear()
    
    # Check memory after cleanup
    time.sleep(0.5)  # Give GC some time
    print(f"Memory after cleanup: {get_memory_usage():.2f} MB")


if __name__ == "__main__":
    main()
