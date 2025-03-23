"""
Example demonstrating memory profiling in a multi-threaded application.
"""

import sys
import os
import time
import threading
import queue

# Add the parent directory to the path so we can import our package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from memory_tracker.utils.helpers import memory_profiler, get_memory_usage


class Worker:
    """Worker class that processes tasks in a separate thread."""
    
    def __init__(self, task_queue):
        self.task_queue = task_queue
        self.results = []
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the worker thread."""
        self.running = True
        self.thread = threading.Thread(target=self._process_tasks)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Stop the worker thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
    
    def _process_tasks(self):
        """Process tasks from the queue."""
        while self.running:
            try:
                task = self.task_queue.get(timeout=0.5)
                # Process the task (in this case, just create a large list)
                result = [i for i in range(task)]
                self.results.append(result)
                self.task_queue.task_done()
            except queue.Empty:
                continue


def main():
    print(f"Initial memory usage: {get_memory_usage():.2f} MB")
    
    # Create a task queue and workers
    task_queue = queue.Queue()
    workers = []
    
    with memory_profiler("Starting workers"):
        # Create and start workers
        for _ in range(4):
            worker = Worker(task_queue)
            worker.start()
            workers.append(worker)
    
    with memory_profiler("Processing tasks"):
        # Add tasks to the queue
        for i in range(10):
            task_queue.put(100000 + i * 50000)
        
        # Wait for tasks to complete
        task_queue.join()
    
    # Memory measurement over time
    print("\nMonitoring memory usage over time:")
    for i in range(5):
        print(f"  Measurement {i+1}: {get_memory_usage():.2f} MB")
        time.sleep(0.5)
    
    with memory_profiler("Stopping workers"):
        # Stop all workers
        for worker in workers:
            worker.stop()
            worker.results.clear()
    
    print(f"Final memory usage: {get_memory_usage():.2f} MB")


if __name__ == "__main__":
    main()
