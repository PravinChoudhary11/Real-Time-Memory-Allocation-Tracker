import random
import time

class MemoryAllocator:
    """
    A simple memory allocator that simulates allocation and deallocation of memory blocks.
    
    The allocator manages a fixed-size memory space and maintains a free list of available blocks.
    It uses a first-fit algorithm for allocation.
    """
    
    def __init__(self, total_size):
        """
        Initialize the memory allocator.
        
        Args:
            total_size (int): Total size of the memory space (in bytes).
        """
        self.total_size = total_size
        # Initially, all memory is free.
        self.free_list = [(0, total_size)]  # Each tuple is (start_address, block_size)
        self.allocated = {}  # Dictionary mapping block IDs to (start, size)
    
    def allocate(self, block_id, size):
        """
        Allocate a memory block.
        
        Args:
            block_id (str): Unique identifier for the memory block.
            size (int): Size of the memory block to allocate.
        
        Returns:
            bool: True if allocation was successful, False otherwise.
        """
        # First-fit allocation: look for the first free block large enough
        for i, (start, free_size) in enumerate(self.free_list):
            if free_size >= size:
                self.allocated[block_id] = (start, size)
                # Update the free list:
                if free_size == size:
                    # Remove the block entirely if sizes match
                    del self.free_list[i]
                else:
                    # Otherwise, adjust the free block's start and size.
                    self.free_list[i] = (start + size, free_size - size)
                return True
        return False

    def free(self, block_id):
        """
        Free an allocated memory block.
        
        Args:
            block_id (str): Identifier of the block to free.
        
        Returns:
            bool: True if successfully freed, False otherwise.
        """
        if block_id not in self.allocated:
            print(f"Block {block_id} not allocated.")
            return False
        start, size = self.allocated.pop(block_id)
        # Add the freed block back into the free list.
        self.free_list.append((start, size))
        self.free_list.sort(key=lambda x: x[0])
        self._merge_free_blocks()
        return True
    
    def _merge_free_blocks(self):
        """
        Merge adjacent free blocks to reduce fragmentation.
        """
        merged = []
        for start, size in self.free_list:
            if merged and merged[-1][0] + merged[-1][1] == start:
                # Extend the previous block.
                merged[-1] = (merged[-1][0], merged[-1][1] + size)
            else:
                merged.append((start, size))
        self.free_list = merged
    
    def status(self):
        """
        Print the current memory allocation status.
        """
        print("\nAllocated Blocks:")
        for block_id, (start, size) in self.allocated.items():
            print(f"  {block_id}: start = {start}, size = {size}")
        print("Free Memory Blocks:")
        for start, size in self.free_list:
            print(f"  Free block: start = {start}, size = {size}")


if __name__ == "__main__":
    # Create a memory allocator with a total memory of 1024 bytes.
    allocator = MemoryAllocator(total_size=1024)
    print("Initial Memory Status:")
    allocator.status()

    # Simulate allocation of several memory blocks.
    for i in range(5):
        size = random.randint(50, 300)
        block_id = f"block_{i}"
        success = allocator.allocate(block_id, size)
        print(f"\nAllocating {block_id} with size {size} bytes: {'Success' if success else 'Failure'}")
        allocator.status()
        time.sleep(1)  # Pause to simulate time between allocations

    # Simulate freeing one block.
    block_to_free = "block_2"
    print(f"\nFreeing {block_to_free}")
    allocator.free(block_to_free)
    allocator.status()
