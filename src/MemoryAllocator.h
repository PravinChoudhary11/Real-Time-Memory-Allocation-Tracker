#ifndef MEMORY_ALLOCATOR_H
#define MEMORY_ALLOCATOR_H

#include <list>

// Structure to represent a memory block
struct MemoryBlock {
    int start;  // Starting address (or index)
    int size;   // Size of the block
    bool free;  // Block status

    MemoryBlock(int s, int sz) : start(s), size(sz), free(true) {}
};

// Abstract base class for memory allocators
class MemoryAllocator {
public:
    std::list<MemoryBlock> blocks;
    int totalSize;

    MemoryAllocator(int total) : totalSize(total) {
        // Initially, the entire memory is a single free block
        blocks.emplace_back(0, totalSize);
    }

    // Pure virtual functions for allocation and deallocation
    virtual MemoryBlock* allocate(int size) = 0;
    virtual void deallocate(MemoryBlock* block) = 0;

    virtual ~MemoryAllocator() {}
};

#endif // MEMORY_ALLOCATOR_H
