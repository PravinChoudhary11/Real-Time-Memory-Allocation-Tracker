#ifndef TASK_SIMULATOR_H
#define TASK_SIMULATOR_H

#include "FirstFitAllocator.h"
#include <queue>
#include <chrono>
#include <iostream>
#include <thread> // Ensure this is included for std::this_thread
using namespace std;

// Removed invalid namespace usage

// Structure representing a real-time task
struct RealTimeTask {
    int id;
    int memoryRequired;
    int deadline;  // For future scheduling use

    RealTimeTask(int id, int mem, int dl) : id(id), memoryRequired(mem), deadline(dl) {}
};

// Simulator for processing tasks with memory allocation requests
class TaskSimulator {
private:
    FirstFitAllocator& allocator;
    std::queue<RealTimeTask> tasks;

public:
    TaskSimulator(FirstFitAllocator& alloc) : allocator(alloc) {}

    // Add a task to the simulation queue
    void addTask(const RealTimeTask& task) {
        tasks.push(task);
    }

    // Process tasks: allocate memory, simulate task execution, then deallocate memory
    void processTasks() {
        while (!tasks.empty()) {
            RealTimeTask task = tasks.front();
            tasks.pop();
            std::cout << "Processing Task " << task.id 
                      << " requiring " << task.memoryRequired << " bytes\n";
            MemoryBlock* block = allocator.allocate(task.memoryRequired);
            if(block) {
                std::cout << "Task " << task.id << " allocated block at address " 
                          << block->start << " of size " << block->size << "\n";
                // Simulate task execution delay (e.g., 500 milliseconds)
                std::this_thread::sleep_for(std::chrono::milliseconds(500));
                allocator.deallocate(block);
                std::cout << "Task " << task.id << " deallocated memory\n";
            } else {
                std::cout << "Task " << task.id << " failed to allocate memory!\n";
            }
        }
    }
};

#endif // TASK_SIMULATOR_H
