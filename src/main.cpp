#include <iostream>
#include <list>
#include <vector>
#include <queue>
#include <thread>
#include <chrono>
#include <algorithm>

using namespace std;

// Memory block structure.
struct MemoryBlock {
    int start;
    int size;
    bool free;
    MemoryBlock(int s, int sz) : start(s), size(sz), free(true) {}
};

// Abstract memory allocator class.
class MemoryAllocator {
public:
    list<MemoryBlock> blocks;
    int totalSize;
    MemoryAllocator(int total) : totalSize(total) {
        blocks.emplace_back(0, totalSize); // Entire memory is free at start.
    }
    virtual MemoryBlock* allocate(int size) = 0;
    virtual void deallocate(MemoryBlock* block) = 0;
    virtual ~MemoryAllocator() {}
};

// First Fit memory allocation.
class FirstFitAllocator : public MemoryAllocator {
public:
    FirstFitAllocator(int total) : MemoryAllocator(total) {}
    MemoryBlock* allocate(int size) override {
        for (auto it = blocks.begin(); it != blocks.end(); ++it) {
            if (it->free && it->size >= size) {
                int remaining = it->size - size;
                int startAddr = it->start;
                it->free = false;
                it->size = size;
                if (remaining > 0) {
                    blocks.insert(next(it), MemoryBlock(startAddr + size, remaining));
                }
                return &(*it);
            }
        }
        return nullptr; // No suitable block found.
    }
    void deallocate(MemoryBlock* block) override {
        for (auto it = blocks.begin(); it != blocks.end(); ++it) {
            if (&(*it) == block) {
                it->free = true;
                // Merge with previous block if free.
                if (it != blocks.begin()) {
                    auto prevIt = prev(it);
                    if (prevIt->free) {
                        prevIt->size += it->size;
                        it = blocks.erase(it);
                        it = prevIt;
                    }
                }
                // Merge with next block if free.
                auto nextIt = next(it);
                if (nextIt != blocks.end() && nextIt->free) {
                    it->size += nextIt->size;
                    blocks.erase(nextIt);
                }
                break;
            }
        }
    }
};

// Extend RealTimeTask to include priority.
// Tasks with priority == 1 are high priority; others are low priority.
struct RealTimeTask {
    int id;
    int memoryRequired;
    int executionTime; // Execution (burst) time in milliseconds.
    int priority;      // 1 = high priority, others = lower.
    RealTimeTask(int i, int mem, int execTime, int prio)
        : id(i), memoryRequired(mem), executionTime(execTime), priority(prio) {}
};

// Round Robin scheduler for high priority tasks.
class RRScheduler {
private:
    queue<RealTimeTask> tasks;
    int quantum; // Fixed time slice in milliseconds.
public:
    RRScheduler(int q) : quantum(q) {}
    void addTask(const RealTimeTask& task) {
        tasks.push(task);
    }
    void processTasks(FirstFitAllocator& allocator) {
        cout << "Processing High Priority Tasks using Round Robin:" << endl;
        while (!tasks.empty()) {
            RealTimeTask task = tasks.front();
            tasks.pop();
            cout << "Processing Task " << task.id
                 << " requiring " << task.memoryRequired << " bytes with remaining time "
                 << task.executionTime << " ms" << endl;
                 
            MemoryBlock* block = allocator.allocate(task.memoryRequired);
            if (block) {
                cout << "Task " << task.id << " allocated block at address "
                     << block->start << " of size " << block->size << endl;
                // Run for either the quantum or until the task completes.
                int execTime = min(task.executionTime, quantum);
                // this_thread::sleep_for(chrono::milliseconds(execTime));
                int i = 0;
                while(i<execTime){
                    i++;
                }
                task.executionTime -= execTime;
                if (task.executionTime > 0) {
                    cout << "Task " << task.id << " not finished. Remaining time: "
                         << task.executionTime << " ms. Re-queueing task." << endl;
                    tasks.push(task);
                } else {
                    cout << "Task " << task.id << " completed execution." << endl;
                }
                allocator.deallocate(block);
                cout << "Task " << task.id << " deallocated memory" << endl;
            } else {
                cout << "Task " << task.id << " failed to allocate memory!" << endl;
            }
        }
    }
};

// SJF scheduler for low priority tasks.
class SJFScheduler {
private:
    vector<RealTimeTask> tasks;
public:
    void addTask(const RealTimeTask& task) {
        tasks.push_back(task);
    }
    void processTasks(FirstFitAllocator& allocator) {
        cout << "Processing Low Priority Tasks using SJF:" << endl;
        // Sort tasks by execution time (shortest job first).
        sort(tasks.begin(), tasks.end(), [](const RealTimeTask& a, const RealTimeTask& b) {
            return a.executionTime < b.executionTime;
        });
        for (const auto& task : tasks) {
            cout << "Processing Task " << task.id
                 << " requiring " << task.memoryRequired << " bytes with execution time "
                 << task.executionTime << " ms" << endl;
            MemoryBlock* block = allocator.allocate(task.memoryRequired);
            if (block) {
                cout << "Task " << task.id << " allocated block at address "
                     << block->start << " of size " << block->size << endl;
                // this_thread::sleep_for(chrono::milliseconds(task.executionTime));
                int i = 0;
                while(i<500){
                    i++;
                }
                allocator.deallocate(block);
                cout << "Task " << task.id << " completed and deallocated memory" << endl;
            } else {
                cout << "Task " << task.id << " failed to allocate memory!" << endl;
            }
        }
    }
};

int main() {
    // Create a memory allocator with 1000 bytes.
    FirstFitAllocator allocator(1000);
    
    // Create two schedulers:
    // - High priority tasks (priority == 1) will use Round Robin.
    // - Low priority tasks (priority != 1) will use SJF.
    RRScheduler rrScheduler(150); // Quantum set to 150 ms.
    SJFScheduler sjfScheduler;
    
    // Create tasks.
    // High priority tasks.
    rrScheduler.addTask(RealTimeTask(1, 200, 300, 1)); // 300 ms burst time.
    rrScheduler.addTask(RealTimeTask(2, 250, 400, 1)); // 400 ms burst time.
    
    // Low priority tasks.
    sjfScheduler.addTask(RealTimeTask(3, 150, 500, 2)); // 500 ms burst time.
    sjfScheduler.addTask(RealTimeTask(4, 100, 200, 2)); // 200 ms burst time.
    
    // Process high priority tasks first.
    rrScheduler.processTasks(allocator);
    
    // Then process low priority tasks.
    sjfScheduler.processTasks(allocator);
    
    return 0;
}
