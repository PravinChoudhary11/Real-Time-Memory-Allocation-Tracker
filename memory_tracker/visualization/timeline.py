"""
Timeline visualization of memory usage over time.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np

from memory_tracker.database.storage import DatabaseManager

from memory_tracker.analysis.analyzer import MemoryAnalyzer


class MemoryTimeline:
    """Class for creating timeline visualizations of memory usage."""
    
    def __init__(self, storage_manager=None, analyzer=None):
        """
        Initialize a new memory timeline visualization.
        
        Args:
            storage_manager (StorageManager, optional): Storage manager instance
            analyzer (MemoryAnalyzer, optional): Memory analyzer instance
        """
        self.snapshots = []
        self.timestamps = []
        self.annotations = []
        self.storage_manager = storage_manager or StorageManager()
        self.analyzer = analyzer
    
    def add_snapshot(self, memory_mb, timestamp=None, annotation=None):
        """
        Add a memory snapshot to the timeline.
        
        Args:
            memory_mb (float): Memory usage in MB
            timestamp (datetime, optional): Timestamp for this snapshot
            annotation (str, optional): Annotation text for this snapshot
        """
        self.snapshots.append(memory_mb)
        self.timestamps.append(timestamp or datetime.now())
        self.annotations.append(annotation)
        
        # Store in database if storage manager is available
        if self.storage_manager:
            # Assuming the storage manager supports storing a dictionary of measurement data
            self.storage_manager.store_snapshot({
                'timestamp': self.timestamps[-1],
                'memory_mb': memory_mb,
                'annotation': annotation
            })
    
    def add_snapshots_from_profile(self, profile_data):
        """
        Add multiple snapshots from profile data.
        
        Args:
            profile_data (list): List of (timestamp, memory_mb, annotation) tuples
        """
        for timestamp, memory_mb, annotation in profile_data:
            self.add_snapshot(memory_mb, timestamp, annotation)
    
    def load_from_storage(self, start_time=None, end_time=None, limit=None):
        """
        Load snapshots from storage.
        
        Args:
            start_time (datetime, optional): Start time for filtering
            end_time (datetime, optional): End time for filtering
            limit (int, optional): Maximum number of snapshots to load
            
        Returns:
            bool: True if data was loaded successfully
        """
        if not self.storage_manager:
            print("No storage manager available")
            return False
        
        try:
            query = {}
            if start_time:
                query['start_time'] = start_time
            if end_time:
                query['end_time'] = end_time
            if limit:
                query['limit'] = limit
                
            snapshots = self.storage_manager.get_snapshots(query)
            
            # Reset current data
            self.snapshots = []
            self.timestamps = []
            self.annotations = []
            
            # Load from retrieved data
            for s in snapshots:
                self.snapshots.append(s['memory_mb'])
                self.timestamps.append(s['timestamp'])
                self.annotations.append(s.get('annotation'))
                
            return True
        except Exception as e:
            print(f"Error loading from storage: {e}")
            return False
    
    def analyze_trends(self):
        """
        Analyze memory trends using the analyzer.
        
        Returns:
            dict: Analysis results
        """
        if not self.analyzer or not self.snapshots:
            return None
            
        try:
            time_points = [(ts - self.timestamps[0]).total_seconds() for ts in self.timestamps]
            return self.analyzer.analyze_trend(time_points, self.snapshots)
        except Exception as e:
            print(f"Error analyzing trends: {e}")
            return None
    
    def visualize(self, output_file=None, title="Memory Usage Timeline", show=True):
        """
        Create and display the timeline visualization.
        
        Args:
            output_file (str, optional): Path to save the visualization image
            title (str): Title for the visualization
            show (bool): Whether to display the visualization
            
        Returns:
            tuple: Figure and axis objects
        """
        if not self.snapshots:
            print("No data available for timeline visualization")
            return None, None
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot the memory timeline
        ax.plot(self.timestamps, self.snapshots, 'b-', linewidth=2)
        ax.plot(self.timestamps, self.snapshots, 'ro', alpha=0.7)
        
        # Add annotations for important points
        for i, (ts, mem, annot) in enumerate(zip(self.timestamps, self.snapshots, self.annotations)):
            if annot:
                ax.annotate(annot, (ts, mem), 
                           xytext=(10, 10 if i % 2 == 0 else -10),
                           textcoords='offset points',
                           arrowprops=dict(arrowstyle="->", connectionstyle="arc3"),
                           bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8))
        
        # Format the x-axis to show time properly
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        
        # Add labels and title
        ax.set_xlabel('Time', fontsize=12)
        ax.set_ylabel('Memory Usage (MB)', fontsize=12)
        ax.set_title(title, fontsize=14)
        
        # Add a grid
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Annotate memory growth trends
        if len(self.snapshots) > 5:
            # Linear regression to show trend
            x = mdates.date2num(self.timestamps)
            z = np.polyfit(range(len(x)), self.snapshots, 1)
            p = np.poly1d(z)
            
            # Calculate growth rate
            total_seconds = (self.timestamps[-1] - self.timestamps[0]).total_seconds()
            if total_seconds > 0:
                rate = (self.snapshots[-1] - self.snapshots[0]) / total_seconds
                growth_text = f"Growth rate: {rate:.2f} MB/second"
                ax.text(0.05, 0.95, growth_text, transform=ax.transAxes, 
                       bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8))
        
        plt.tight_layout()
        fig.autofmt_xdate()  # Rotate date labels
        
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"Timeline saved to {output_file}")
        
        if show:
            plt.show()
            
        return fig, ax
    
    def compare_with(self, other_timeline, labels=None, output_file=None, title="Memory Usage Comparison", show=True):
        """
        Compare this timeline with another timeline.
        
        Args:
            other_timeline (MemoryTimeline): Another timeline to compare with
            labels (list, optional): Labels for the two timelines
            output_file (str, optional): Path to save the comparison image
            title (str): Title for the comparison
            show (bool): Whether to display the visualization
            
        Returns:
            tuple: Figure and axis objects
        """
        if not self.snapshots or not other_timeline.snapshots:
            print("Insufficient data for comparison")
            return None, None
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Normalize timelines to start at the same point
        t1_start = self.timestamps[0]
        t2_start = other_timeline.timestamps[0]
        
        # Convert timestamps to seconds from start
        t1_seconds = [(t - t1_start).total_seconds() for t in self.timestamps]
        t2_seconds = [(t - t2_start).total_seconds() for t in other_timeline.timestamps]
        
        # Plot both timelines
        label1, label2 = labels if labels and len(labels) == 2 else ("Timeline 1", "Timeline 2")
        ax.plot(t1_seconds, self.snapshots, 'b-', linewidth=2, label=label1)
        ax.plot(t2_seconds, other_timeline.snapshots, 'r-', linewidth=2, label=label2)
        
        # Add labels and title
        ax.set_xlabel('Time (seconds)', fontsize=12)
        ax.set_ylabel('Memory Usage (MB)', fontsize=12)
        ax.set_title(title, fontsize=14)
        ax.legend(loc='best')
        
        # Add a grid
        ax.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"Comparison saved to {output_file}")
        
        if show:
            plt.show()
            
        return fig, ax
