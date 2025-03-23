"""
A simple example demonstrating basic memory profiling.
"""

import sys
import os

# Add the parent directory to the path so we can import our package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from memory_tracker.utils.helpers import memory_profiler, get_memory_usage


def create_large_list(size=1000000):
    """Create a large list to demonstrate memory usage."""
    return [i for i in range(size)]


def main():
    print(f"Initial memory usage: {get_memory_usage():.2f} MB")
    
    # Profile memory usage when creating a large list
    with memory_profiler("Creating large list"):
        large_list = create_large_list()
    
    # Profile memory usage when deleting the large list
    with memory_profiler("Deleting large list"):
        del large_list
    
    print(f"Final memory usage: {get_memory_usage():.2f} MB")


if __name__ == "__main__":
    main()
