"""
Dashboard for visualizing memory usage in applications.
"""

import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import os

# Import from the project structure
from memory_tracker.database.storage import DatabaseManager



class MemoryDashboard:
    """Dashboard to visualize memory usage metrics."""
    
    def __init__(self, title="Memory Usage Dashboard", storage_manager=None):
        """
        Initialize a new memory dashboard.
        
        Args:
            title (str): The title of the dashboard
            storage_manager (StorageManager, optional): Storage manager instance
        """
        self.title = title
        self.memory_data = []
        self.timestamps = []
        self.labels = []
        self.events = []
        self.storage_manager = storage_manager or StorageManager()
    
    def add_measurement(self, memory_mb, label=None, event=None):
        """
        Add a memory measurement to the dashboard.
        
        Args:
            memory_mb (float): Memory usage in MB
            label (str, optional): Label for this measurement
            event (str, optional): Event associated with this measurement
        """
        self.memory_data.append(memory_mb)
        self.timestamps.append(datetime.now())
        self.labels.append(label or f"Measurement {len(self.memory_data)}")
        
        if event:
            self.events.append((len(self.memory_data) - 1, event))
            
        # Store in database if storage manager is available
        if self.storage_manager:
            self.storage_manager.store_measurement({
                'timestamp': self.timestamps[-1],
                'memory_mb': memory_mb,
                'label': self.labels[-1],
                'event': event
            })
    
    def load_from_storage(self, query=None):
        """
        Load measurements from storage.
        
        Args:
            query (dict, optional): Query parameters for filtering data
            
        Returns:
            bool: True if data was loaded successfully
        """
        if not self.storage_manager:
            print("No storage manager available")
            return False
            
        try:
            measurements = self.storage_manager.get_measurements(query)
            
            # Reset current data
            self.memory_data = []
            self.timestamps = []
            self.labels = []
            self.events = []
            
            # Load from retrieved data
            for m in measurements:
                self.memory_data.append(m['memory_mb'])
                self.timestamps.append(m['timestamp'])
                self.labels.append(m['label'])
                
                if m.get('event'):
                    self.events.append((len(self.memory_data) - 1, m['event']))
                    
            return True
        except Exception as e:
            print(f"Error loading from storage: {e}")
            return False
    
    def generate_dashboard(self, output_file=None, show=True):
        """
        Generate and display the memory dashboard.
        
        Args:
            output_file (str, optional): Path to save the dashboard image
            show (bool): Whether to display the dashboard
            
        Returns:
            tuple: Figure and axes objects
        """
        if not self.memory_data:
            print("No data available for visualization")
            return None, None
        
        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1]})
        
        # Time series plot
        ax1.plot(range(len(self.memory_data)), self.memory_data, 'b-', linewidth=2)
        ax1.set_title(f"{self.title} - Time Series", fontsize=14)
        ax1.set_xlabel("Measurements", fontsize=12)
        ax1.set_ylabel("Memory Usage (MB)", fontsize=12)
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        # Add event markers
        for idx, event in self.events:
            ax1.axvline(x=idx, color='r', linestyle='--', alpha=0.5)
            ax1.text(idx, max(self.memory_data) * 0.95, event, rotation=90, 
                     verticalalignment='top', fontsize=10)
        
        # Plot memory growth
        memory_growth = [self.memory_data[i] - self.memory_data[i-1] if i > 0 else 0 
                         for i in range(len(self.memory_data))]
        
        ax2.bar(range(len(memory_growth)), memory_growth, color=['g' if x <= 0 else 'r' for x in memory_growth])
        ax2.set_title("Memory Growth Between Measurements", fontsize=14)
        ax2.set_xlabel("Measurements", fontsize=12)
        ax2.set_ylabel("Memory Change (MB)", fontsize=12)
        ax2.grid(True, linestyle='--', alpha=0.7, axis='y')
        
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"Dashboard saved to {output_file}")
        
        if show:
            plt.show()
            
        return fig, (ax1, ax2)
    
    def generate_summary(self):
        """
        Generate a text summary of memory statistics.
        
        Returns:
            str: Summary text
        """
        if not self.memory_data:
            return "No data available for summary"
        
        summary = [
            f"=== Memory Dashboard Summary: {self.title} ===",
            f"Total measurements: {len(self.memory_data)}",
            f"Initial memory: {self.memory_data[0]:.2f} MB",
            f"Final memory: {self.memory_data[-1]:.2f} MB",
            f"Peak memory: {max(self.memory_data):.2f} MB",
            f"Minimum memory: {min(self.memory_data):.2f} MB",
            f"Average memory: {np.mean(self.memory_data):.2f} MB",
            f"Net memory change: {self.memory_data[-1] - self.memory_data[0]:.2f} MB",
            "",
            "Significant events:"
        ]
        
        for idx, event in self.events:
            summary.append(f"  - {event} (at measurement {idx+1}, memory: {self.memory_data[idx]:.2f} MB)")
        
        return "\n".join(summary)
    
    def save_data(self, filename):
        """
        Save the dashboard data to a CSV file.
        
        Args:
            filename (str): Output filename
            
        Returns:
            bool: True if successful
        """
        try:
            with open(filename, 'w') as f:
                f.write("Timestamp,Label,Memory (MB)\n")
                for i, (ts, label, mem) in enumerate(zip(self.timestamps, self.labels, self.memory_data)):
                    f.write(f"{ts},{label},{mem:.2f}\n")
            
            print(f"Data saved to {filename}")
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False