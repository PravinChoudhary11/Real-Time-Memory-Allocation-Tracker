#ifndef FIRST_FIT_ALLOCATOR_H
#define FIRST_FIT_ALLOCATOR_H

#include <vector>
#include <iostream>
#include <algorithm>

// Memory block structure
struct MemoryBlock {
    int start;      // Start address of the block
    int size;       // Size of the block
    bool free;      // Whether the block is free or allocated
    
    MemoryBlock(int s, int sz, bool f) : start(s), size(sz), free(f) {}
};

// First Fit Memory Allocator implementation
class FirstFitAllocator {
private:
    int totalMemory;                 // Total memory size
    std::vector<MemoryBlock> blocks; // List of memory blocks

public:
    // Constructor initializes a single free block of the given size
    FirstFitAllocator(int memorySize) : totalMemory(memorySize) {
        blocks.push_back(MemoryBlock(0, memorySize, true));
    }
    
    // Allocate memory using first-fit algorithm
    MemoryBlock* allocate(int size) {
        for (size_t i = 0; i < blocks.size(); i++) {
            MemoryBlock& block = blocks[i];
            if (block.free && block.size >= size) {
                // If the block is exactly the right size or slightly larger
                if (block.size <= size + 16) {  // Small threshold to avoid fragmentation
                    block.free = false;
                    return &blocks[i]; // Important: Use index to get stable reference
                } else {
                    // Split the block - keep the allocation at the start
                    int newStart = block.start + size;
                    int newSize = block.size - size;
                    
                    // Resize the current block
                    block.size = size;
                    block.free = false;
                    
                    // Create a new free block for the remainder
                    blocks.push_back(MemoryBlock(newStart, newSize, true));
                    return &blocks[i]; // Important: Use index to get stable reference
                }
            }
        }
        return nullptr; // No suitable block found
    }
    
    // Deallocate a memory block
    void deallocate(MemoryBlock* block) {
        if (!block) return;
        
        // Find the block in our vector
        for (auto& b : blocks) {
            if (b.start == block->start && b.size == block->size) {
                b.free = true;
                break;
            }
        }
        
        // Merge with adjacent free blocks (coalescing)
        mergeAdjacentFreeBlocks();
    }
    
    // Merge adjacent free blocks to reduce fragmentation
    void mergeAdjacentFreeBlocks() {
        // Sort blocks by start address
        std::sort(blocks.begin(), blocks.end(), 
                 [](const MemoryBlock& a, const MemoryBlock& b) { 
                     return a.start < b.start; 
                 });
        
        for (size_t i = 0; i < blocks.size() - 1; ) {
            if (blocks[i].free && blocks[i+1].free) {
                // Merge blocks i and i+1
                blocks[i].size += blocks[i+1].size;
                blocks.erase(blocks.begin() + i + 1);
                // Don't increment i yet, as we need to check if the next block can also be merged
            } else {
                i++;
            }
        }
    }
    
    // Display the current memory state
    void displayMemoryMap() {
        std::cout << "Memory Map:\n";
        for (const auto& block : blocks) {
            std::cout << "Block at " << block.start << " - " 
                      << (block.start + block.size - 1) << " (" << block.size 
                      << " bytes): " << (block.free ? "Free" : "Allocated") << "\n";
        }
    }
};

#endif // FIRST_FIT_ALLOCATOR_H