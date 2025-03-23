"""
Treemap visualization for memory usage by object type.
"""

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import squarify
from datetime import datetime

from memory_tracker.database.storage import DatabaseManager

from memory_tracker.analysis.leak_detector import LeakDetector


class MemoryTreemap:
    """Class for creating treemap visualizations of memory usage by object type."""
    
    def __init__(self, storage_manager=None, leak_detector=None):
        """
        Initialize a new memory treemap visualization.
        
        Args:
            storage_manager (StorageManager, optional): Storage manager instance
            leak_detector (LeakDetector, optional): Leak detector instance
        """
        self.object_counts = {}
        self.estimated_sizes = {}
        self.cmap = plt.cm.viridis
        self.storage_manager = storage_manager or StorageManager()
        self.leak_detector = leak_detector
    
    def add_object_counts(self, counts, estimated_sizes=None):
        """
        Add object counts data for visualization.
        
        Args:
            counts (dict): Dictionary mapping object types to counts
            estimated_sizes (dict, optional): Dictionary mapping object types to estimated sizes in bytes
        """
        self.object_counts = counts
        self.estimated_sizes = estimated_sizes or {}
        
        # Store in database if storage manager is available
        if self.storage_manager:
            timestamp = datetime.now()
            self.storage_manager.store_object_counts(timestamp, counts, estimated_sizes)
    
    def load_from_storage(self, timestamp=None):
        """
        Load object counts from storage.
        
        Args:
            timestamp (datetime, optional): Specific timestamp to load, or latest if None
            
        Returns:
            bool: True if data was loaded successfully
        """
        if not self.storage_manager:
            print("No storage manager available")
            return False
            
        try:
            result = self.storage_manager.get_object_counts(timestamp)
            if result:
                self.object_counts = result['counts']
                self.estimated_sizes = result.get('sizes', {})
                return True
            return False
        except Exception as e:
            print(f"Error loading from storage: {e}")
            return False
    
    def detect_leaks(self):
        """
        Use the leak detector to find potential memory leaks.
        
        Returns:
            dict: Potential leaks by object type
        """
        if not self.leak_detector or not self.object_counts:
            return {}
            
        try:
            return self.leak_detector.detect_from_counts(self.object_counts)
        except Exception as e:
            print(f"Error detecting leaks: {e}")
            return {}
    
    def _calculate_memory_usage(self):
        """
        Calculate estimated memory usage for each object type.
        
        Returns:
            dict: Estimated memory usage by object type
        """
        memory_usage = {}
        
        for obj_type, count in self.object_counts.items():
            # Use provided size estimate or a default
            size_per_object = self.estimated_sizes.get(obj_type, 64)  # Default: 64 bytes
            memory_usage[obj_type] = count * size_per_object / (1024 * 1024)  # Convert to MB
        
        return memory_usage
    
    def _filter_small_items(self, data, threshold_percent=1.0):
        """
        Filter out items that are too small to visualize effectively.
        
        Args:
            data (dict): Data to filter
            threshold_percent (float): Threshold as percentage of total
            
        Returns:
            dict: Filtered data
        """
        total = sum(data.values())
        threshold = total * threshold_percent / 100
        
        filtered = {k: v for k, v in data.items() if v >= threshold}
        
        # Combine small items into "Other" category
        other_sum = sum(v for k, v in data.items() if v < threshold)
        if other_sum > 0:
            filtered["Other"] = other_sum
            
        return filtered
    
    def visualize(self, output_file=None, title="Memory Usage by Object Type", 
                  max_items=15, threshold_percent=0.5, show=True, highlight_leaks=False):
        """
        Create and display the treemap visualization.
        
        Args:
            output_file (str, optional): Path to save the visualization image
            title (str): Title for the visualization
            max_items (int): Maximum number of items to display individually
            threshold_percent (float): Threshold for "Other" category as percentage
            show (bool): Whether to display the visualization
            highlight_leaks (bool): Whether to highlight potential memory leaks
            
        Returns:
            tuple: Figure and axis objects
        """
        if not self.object_counts:
            print("No data available for treemap visualization")
            return None, None
        
        # Calculate memory usage
        memory_usage = self._calculate_memory_usage()
        
        # Get potential leaks if requested
        potential_leaks = set(self.detect_leaks().keys()) if highlight_leaks and self.leak_detector else set()
        
        # Sort by size and limit to top N items
        sorted_data = dict(sorted(memory_usage.items(), key=lambda x: x[1], reverse=True)[:max_items])
        
        # Filter small items
        filtered_data = self._filter_small_items(sorted_data, threshold_percent)
        
        # Prepare data for treemap
        labels = list(filtered_data.keys())
        sizes = list(filtered_data.values())
        total_mb = sum(sizes)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Generate colors, highlighting potential leaks in red
        norm = mcolors.Normalize(vmin=0, vmax=len(labels))
        colors = []
        for i, label in enumerate(labels):
            if label in potential_leaks:
                colors.append('red')  # Highlight potential leaks
            else:
                colors.append(self.cmap(norm(i)))
        
        # Create treemap
        squarify.plot(
            sizes=sizes,
            label=[f"{l}\n{s:.2f} MB ({s/total_mb*100:.1f}%)" for l, s in zip(labels, sizes)],
            color=colors,
            alpha=0.8,
            text_kwargs={'fontsize': 10},
            ax=ax
        )
        
        # Remove axes
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 100)
        
        # Add title and info
        plt.title(title, fontsize=14)
        plt.figtext(0.5, 0.01, f"Total estimated memory: {total_mb:.2f} MB",
                    horizontalalignment='center', fontsize=12)
        
        # Add leak warning if applicable
        if potential_leaks:
            leak_text = "Potential memory leaks detected (highlighted in red)"
            plt.figtext(0.5, 0.04, leak_text, horizontalalignment='center', 
                        fontsize=12, color='red', weight='bold')
        
        plt.tight_layout(rect=[0, 0.03, 1, 0.97])
        
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"Treemap saved to {output_file}")
        
        if show:
            plt.show()
            
        return fig, ax
    
    def compare_snapshots(self, before_counts, after_counts, output_file=None, 
                          title="Memory Usage Comparison", show=True):
        """
        Compare two memory snapshots.
        
        Args:
            before_counts (dict): Object counts before
            after_counts (dict): Object counts after
            output_file (str, optional): Path to save the visualization image
            title (str): Title for the visualization
            show (bool): Whether to display the visualization
            
        Returns:
            tuple: Figure and axes objects
        """
        # Calculate differences
        diff = {}
        all_types = set(list(before_counts.keys()) + list(after_counts.keys()))
        
        for obj_type in all_types:
            before = before_counts.get(obj_type, 0)
            after = after_counts.get(obj_type, 0)
            diff[obj_type] = after - before
        
        # Filter out unchanged types
        diff = {k: v for k, v in diff.items() if v != 0}
        
        # Sort by absolute difference
        sorted_diff = dict(sorted(diff.items(), key=lambda x: abs(x[1]), reverse=True)[:20])
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 8))
        
        # Prepare data for bar chart
        types = list(sorted_diff.keys())
        values = list(sorted_diff.values())
        
        # Separate increases and decreases
        increases = [v if v > 0 else 0 for v in values]
        decreases = [abs(v) if v < 0 else 0 for v in values]
        
        # Create horizontal bar chart
        y_pos = np.arange(len(types))
        ax1.barh(y_pos, increases, color='red', alpha=0.7, label='Increased')
        ax1.barh(y_pos, [-d for d in decreases], color='green', alpha=0.7, label='Decreased')
        
        # Add labels and title
        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(types)
        ax1.set_xlabel('Object Count Difference')
        ax1.set_title('Object Count Changes')
        ax1.legend()
        
        # Create pie chart for overall change
        total_before = sum(before_counts.values())
        total_after = sum(after_counts.values())
        
        if total_before > 0 and total_after > 0:
            labels = ['Before', 'Added', 'Removed']
            added = sum(v for v in diff.values() if v > 0)
            removed = sum(abs(v) for v in diff.values() if v < 0)
            
            values = [total_before, added, -removed]
            colors = ['gray', 'red', 'green']
            explode = (0, 0.1, 0.1)
            
            ax2.pie(
                [max(0, v) for v in values],
                labels=labels,
                colors=colors,
                explode=explode,
                autopct='%1.1f%%',
                startangle=90
            )
            ax2.axis('equal')
            ax2.set_title('Overall Memory Change')
            
            # Add text
            fig.text(
                0.5, 0.01, 
                f"Total objects before: {total_before:,}\nTotal objects after: {total_after:,}\nNet change: {total_after - total_before:,} ({(total_after - total_before)/total_before*100:.1f}%)",
                ha='center', fontsize=12
            )
        
        plt.tight_layout(rect=[0, 0.05, 1, 0.95])
        plt.suptitle(title, fontsize=16)
        
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"Comparison saved to {output_file}")
        
        if show:
            plt.show()
            
        return fig, (ax1, ax2)
