import time
import threading

class MemoryBlock:
    def __init__(self, size):
        self.size = size
        self.free = True

class RealTimeMemoryAllocator:
    def __init__(self, total_memory):
        self.total_memory = total_memory
        self.memory_blocks = [MemoryBlock(total_memory)]
        self.lock = threading.Lock()

    def allocate_memory(self, size):
        with self.lock:
            for block in self.memory_blocks:
                if block.free and block.size >= size:
                    if block.size > size:
                        new_block = MemoryBlock(block.size - size)
                        self.memory_blocks.insert(self.memory_blocks.index(block) + 1, new_block)
                    block.size = size
                    block.free = False
                    return block
            raise MemoryError("Not enough memory to allocate")

    def free_memory(self, block):
        with self.lock:
            block.free = True
            self.merge_free_blocks()

    def merge_free_blocks(self):
        i = 0
        while i < len(self.memory_blocks) - 1:
            if self.memory_blocks[i].free and self.memory_blocks[i + 1].free:
                self.memory_blocks[i].size += self.memory_blocks[i + 1].size
                del self.memory_blocks[i + 1]
            else:
                i += 1

def simulate_real_time_memory_allocation():
    allocator = RealTimeMemoryAllocator(1024)  # 1KB of memory

    def allocate_and_free(size, duration):
        try:
            block = allocator.allocate_memory(size)
            print(f"Allocated {size} bytes")
            time.sleep(duration)
            allocator.free_memory(block)
            print(f"Freed {size} bytes")
        except MemoryError as e:
            print(e)

    threads = [
        threading.Thread(target=allocate_and_free, args=(100, 2)),
        threading.Thread(target=allocate_and_free, args=(200, 3)),
        threading.Thread(target=allocate_and_free, args=(300, 1)),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    simulate_real_time_memory_allocation()