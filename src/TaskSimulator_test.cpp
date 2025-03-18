#include "TaskSimulator.h"
#include <iostream>

int main() {
    std::cout << "Starting TaskSimulator test program...\n";
    
    try {
        // Create a memory allocator with 1000 bytes
        std::cout << "Creating allocator with 1000 bytes...\n";
        FirstFitAllocator allocator(1000);
        
        // Show initial memory map
        std::cout << "Initial memory state:\n";
        allocator.displayMemoryMap();
        
        // Create a simulator
        std::cout << "Creating simulator...\n";
        TaskSimulator simulator(allocator);
        
        // Add some tasks
        std::cout << "Adding tasks...\n";
        simulator.addTask(RealTimeTask(1, 200, 100));
        simulator.addTask(RealTimeTask(2, 300, 200));
        
        // Process the tasks
        std::cout << "Processing tasks...\n";
        simulator.processTasks();
        
        // Show final memory map
        std::cout << "Final memory state:\n";
        allocator.displayMemoryMap();
        
        std::cout << "All tasks processed successfully.\n";
    } catch (const std::exception& e) {
        std::cout << "Exception caught: " << e.what() << std::endl;
    } catch (...) {
        std::cout << "Unknown exception caught!" << std::endl;
    }
    
    std::cout << "Program finished. Press Enter to exit...\n";
    std::cin.get(); // Wait for Enter key
    return 0;
}