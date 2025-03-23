import tracemalloc
import psutil
import os
import time
import gc
import json
from pympler import muppy, summary

class SnapshotManager:
    """
    Manages memory snapshots for later analysis.
    """
    
    def __init__(self, database):
        """
        Initialize the snapshot manager.
        
        Args:
            database: Database manager instance
        """
        self.database = database
        self.snapshots = []
    
    def take_snapshot(self, label, elapsed_time):
        """
        Take a snapshot of the current memory state.
        
        Args:
            label (str): Label for the snapshot
            elapsed_time (float): Time elapsed since tracking started
        
        Returns:
            int: Snapshot ID
        """
        # Force garbage collection to get accurate numbers
        gc.collect()
        
        # Get tracemalloc snapshot
        try:
            tracemalloc_snapshot = tracemalloc.take_snapshot()
        except RuntimeError:
            tracemalloc_snapshot = None
        
        # Get process memory info
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        # Get summary of all objects
        all_objects = muppy.get_objects()
        objects_summary = summary.summarize(all_objects)
        
        # Convert summary to storable format
        summary_data = []
        for row in objects_summary:
            summary_data.append({
                "type": str(row[0]),
                "count": row[1],
                "size": row[2]
            })
        
        # Process tracemalloc snapshot for top statistics
        top_stats = []
        if tracemalloc_snapshot:
            # Get top 100 allocations by size
            for stat in tracemalloc_snapshot.statistics('lineno')[:100]:
                frame = stat.traceback[0]
                top_stats.append({
                    "file": frame.filename,
                    "line": frame.lineno,
                    "size": stat.size,
                    "count": stat.count
                })
        
        # Store snapshot data
        snapshot_data = {
            "label": label,
            "timestamp": time.time(),
            "elapsed_time": elapsed_time,
            "memory_rss": memory_info.rss,
            "memory_vms": memory_info.vms,
            "total_objects": len(all_objects),
            "summary": summary_data,
            "top_stats": top_stats
        }
        
        # Save to database
        snapshot_id = self.database.store_snapshot(
            snapshot_data["label"],
            snapshot_data["timestamp"],
            snapshot_data["elapsed_time"],
            snapshot_data["memory_rss"],
            snapshot_data["memory_vms"],
            json.dumps(snapshot_data["summary"]),
            json.dumps(snapshot_data["top_stats"])
        )
        
        return snapshot_id
    
    def get_snapshots(self):
        """
        Get all stored snapshots.
        
        Returns:
            list: List of snapshots
        """
        return self.database.get_snapshots()
    
    def get_snapshot(self, snapshot_id):
        """
        Get a specific snapshot by ID.
        
        Args:
            snapshot_id (int): ID of the snapshot
            
        Returns:
            dict: Snapshot data
        """
        return self.database.get_snapshot(snapshot_id)
    
    def compare_snapshots(self, snapshot_id1, snapshot_id2):
        """
        Compare two snapshots and identify differences.
        
        Args:
            snapshot_id1 (int): ID of the first snapshot
            snapshot_id2 (int): ID of the second snapshot
            
        Returns:
            dict: Differences between snapshots
        """
        # Get snapshots
        snapshot1 = self.database.get_snapshot(snapshot_id1)
        snapshot2 = self.database.get_snapshot(snapshot_id2)
        
        if not snapshot1 or not snapshot2:
            return None
            
        # Extract summary data
        summary1 = json.loads(snapshot1["summary"])
        summary2 = json.loads(snapshot2["summary"])
        
        # Build type maps for comparison
        type_map1 = {item["type"]: {"count": item["count"], "size": item["size"]} for item in summary1}
        type_map2 = {item["type"]: {"count": item["count"], "size": item["size"]} for item in summary2}
        
        # Find all types across both snapshots
        all_types = set(type_map1.keys()) | set(type_map2.keys())
        
        # Calculate differences
        diff = {
            "added_types": [],
            "removed_types": [],
            "changed_types": [],
            "memory_diff": snapshot2["memory_rss"] - snapshot1["memory_rss"],
            "total_objects_diff": snapshot2["total_objects"] - snapshot1["total_objects"],
            "time_between": snapshot2["timestamp"] - snapshot1["timestamp"]
        }
        
        for type_name in all_types:
            if type_name in type_map1 and type_name not in type_map2:
                diff["removed_types"].append({
                    "type": type_name,
                    "count": type_map1[type_name]["count"],
                    "size": type_map1[type_name]["size"]
                })
            elif type_name not in type_map1 and type_name in type_map2:
                diff["added_types"].append({
                    "type": type_name,
                    "count": type_map2[type_name]["count"],
                    "size": type_map2[type_name]["size"]
                })
            else:
                # Type exists in both snapshots, check for differences
                count1 = type_map1[type_name]["count"]
                count2 = type_map2[type_name]["count"]
                size1 = type_map1[type_name]["size"]
                size2 = type_map2[type_name]["size"]
                
                if count1 != count2 or size1 != size2:
                    diff["changed_types"].append({
                        "type": type_name,
                        "count_before": count1,
                        "count_after": count2,
                        "count_diff": count2 - count1,
                        "size_before": size1,
                        "size_after": size2,
                        "size_diff": size2 - size1
                    })
        
        # Sort differences by magnitude
        diff["added_types"] = sorted(diff["added_types"], key=lambda x: x["size"], reverse=True)
        diff["removed_types"] = sorted(diff["removed_types"], key=lambda x: x["size"], reverse=True)
        diff["changed_types"] = sorted(diff["changed_types"], key=lambda x: abs(x["size_diff"]), reverse=True)
        
        return diff
