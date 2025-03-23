import json
import time
import pandas as pd
import numpy as np
from memory_tracker.analysis.leak_detector import LeakDetector
from memory_tracker.analysis.pattern_analyzer import PatternAnalyzer

class MemoryAnalyzer:
    """
    Analyzes memory usage data to extract insights and detect issues.
    """
    
    def __init__(self, database):
        """
        Initialize the memory analyzer.
        
        Args:
            database: Database manager instance
        """
        self.database = database
        self.leak_detector = LeakDetector(database)
        self.pattern_analyzer = PatternAnalyzer(database)
    
    def analyze(self):
        """
        Perform a comprehensive analysis of memory usage.
        
        Returns:
            dict: Analysis results
        """
        # Start time
        start_time = time.time()
        
        # Get memory timeline
        timeline_data = self.database.get_memory_timeline()
        timestamps, memory_values = zip(*timeline_data) if timeline_data else ([], [])
        
        # Get snapshots
        snapshots = self.database.get_snapshots()
        
        # Detect potential memory leaks
        leaks = self.leak_detector.detect_leaks()
        
        # Analyze allocation patterns
        patterns = self.pattern_analyzer.detect_patterns()
        
        # Calculate basic statistics
        if memory_values:
            memory_stats = {
                "min": min(memory_values),
                "max": max(memory_values),
                "avg": sum(memory_values) / len(memory_values),
                "growth_rate": (memory_values[-1] - memory_values[0]) / (timestamps[-1] - timestamps[0]) if len(timestamps) > 1 else 0,
                "start": memory_values[0],
                "end": memory_values[-1],
                "change": memory_values[-1] - memory_values[0],
                "change_percent": ((memory_values[-1] - memory_values[0]) / memory_values[0]) * 100 if memory_values[0] > 0 else 0
            }
        else:
            memory_stats = {
                "min": 0,
                "max": 0,
                "avg": 0,
                "growth_rate": 0,
                "start": 0,
                "end": 0,
                "change": 0,
                "change_percent": 0
            }
        
        # Get top memory consumers by type
        type_summary = self.database.get_object_type_summary()
        top_types = sorted(type_summary, key=lambda x: x[2], reverse=True)[:20]
        
        # Get GC events
        gc_events = self.database.get_gc_events()
        
        # Get function tracking data
        functions = self.database.get_function_tracking()
        
        # Calculate function memory impact
        function_impacts = {}
        for func in functions:
            name = func['function_name']
            if name not in function_impacts:
                function_impacts[name] = {
                    "count": 0,
                    "total_memory": 0,
                    "total_time": 0,
                    "avg_memory": 0,
                    "avg_time": 0
                }
                
            function_impacts[name]["count"] += 1
            function_impacts[name]["total_memory"] += func['memory_diff']
            function_impacts[name]["total_time"] += func['execution_time']
            
        # Calculate averages
        for name, impact in function_impacts.items():
            if impact["count"] > 0:
                impact["avg_memory"] = impact["total_memory"] / impact["count"]
                impact["avg_time"] = impact["total_time"] / impact["count"]
        
        # Sort functions by memory impact
        top_functions = sorted(
            function_impacts.items(), 
            key=lambda x: x[1]["total_memory"], 
            reverse=True
        )[:20]
        
        # Build results
        results = {
            "memory_stats": memory_stats,
            "leaks": leaks,
            "patterns": patterns,
            "top_types": top_types,
            "gc_events": gc_events,
            "top_functions": top_functions,
            "analysis_time": time.time() - start_time
        }
        
        return results
    
    def analyze_snapshots(self):
        """
        Analyze memory snapshots to identify growth trends.
        
        Returns:
            dict: Snapshot analysis results
        """
        snapshots = self.database.get_snapshots()
        if not snapshots:
            return {"error": "No snapshots available"}
            
        # Extract memory usage over time
        timestamps = []
        memory_values = []
        labels = []
        
        for snapshot in snapshots:
            timestamps.append(snapshot['timestamp'])
            memory_values.append(snapshot['memory_rss'])
            labels.append(snapshot['label'])
        
        # Convert to numpy arrays for analysis
        times = np.array(timestamps)
        memories = np.array(memory_values)
        
        # Calculate basic metrics
        if len(memories) > 1:
            # Calculate overall growth rate
            total_growth = memories[-1] - memories[0]
            total_time = times[-1] - times[0]
            overall_growth_rate = total_growth / total_time if total_time > 0 else 0
            
            # Calculate incremental growth rates
            incremental_rates = []
            for i in range(1, len(memories)):
                growth = memories[i] - memories[i-1]
                time_diff = times[i] - times[i-1]
                rate = growth / time_diff if time_diff > 0 else 0
                incremental_rates.append(rate)
            
            # Find highest growth period
            if incremental_rates:
                max_rate_index = np.argmax(incremental_rates)
                max_growth_period = {
                    "start_label": labels[max_rate_index],
                    "end_label": labels[max_rate_index + 1],
                    "growth_rate": incremental_rates[max_rate_index],
                    "memory_increase": memories[max_rate_index + 1] - memories[max_rate_index]
                }
            else:
                max_growth_period = None
        else:
            total_growth = 0
            overall_growth_rate = 0
            incremental_rates = []
            max_growth_period = None
        
        # Analyze object types in the first and last snapshot
        if len(snapshots) > 1:
            first_summary = json.loads(snapshots[0]['summary'])
            last_summary = json.loads(snapshots[-1]['summary'])
            
            # Convert to dictionaries for easier comparison
            first_types = {item["type"]: {"count": item["count"], "size": item["size"]} for item in first_summary}
            last_types = {item["type"]: {"count": item["count"], "size": item["size"]} for item in last_summary}
            
            # Find types with significant growth
            growing_types = []
            for type_name, last_data in last_types.items():
                if type_name in first_types:
                    first_data = first_types[type_name]
                    growth = last_data["size"] - first_data["size"]
                    count_growth = last_data["count"] - first_data["count"]
                    
                    if growth > 0:
                        growing_types.append({
                            "type": type_name,
                            "size_growth": growth,
                            "count_growth": count_growth,
                            "growth_percent": (growth / first_data["size"]) * 100 if first_data["size"] > 0 else float('inf')
                        })
                else:
                    # New type
                    growing_types.append({
                        "type": type_name,
                        "size_growth": last_data["size"],
                        "count_growth": last_data["count"],
                        "growth_percent": float('inf')
                    })
            
            # Sort by size growth
            growing_types.sort(key=lambda x: x["size_growth"], reverse=True)
            
            # Get top growing types
            top_growing_types = growing_types[:10]
        else:
            top_growing_types = []
        
        results = {
            "overall_growth_rate": overall_growth_rate,
            "memory_start": memories[0] if len(memories) > 0 else 0,
            "memory_end": memories[-1] if len(memories) > 0 else 0,
            "memory_change": total_growth if len(memories) > 1 else 0,
            "max_growth_period": max_growth_period,
            "top_growing_types": top_growing_types
        }
        
        return results
    
    def analyze_leaks(self):
        """
        Perform detailed leak analysis.
        
        Returns:
            dict: Leak analysis results
        """
        return self.leak_detector.analyze()
    
    def analyze_functions(self):
        """
        Analyze function memory usage patterns.
        
        Returns:
            dict: Function analysis results
        """
        # Get function tracking data
        functions = self.database.get_function_tracking()
        
        # Group by function name
        function_data = {}
        for func in functions:
            name = func['function_name']
            if name not in function_data:
                function_data[name] = []
            function_data[name].append(func)
        
        # Analyze each function
        results = []
        for name, calls in function_data.items():
            if len(calls) < 2:
                continue
                
            # Extract memory and time data
            memory_diffs = [call['memory_diff'] for call in calls]
            execution_times = [call['execution_time'] for call in calls]
            
            # Calculate statistics
            avg_memory = sum(memory_diffs) / len(memory_diffs)
            avg_time = sum(execution_times) / len(execution_times)
            max_memory = max(memory_diffs)
            min_memory = min(memory_diffs)
            memory_variance = np.var(memory_diffs) if len(memory_diffs) > 1 else 0
            time_variance = np.var(execution_times) if len(execution_times) > 1 else 0
            
            # Check for consistent growth pattern
            is_growing = all(b >= a for a, b in zip(memory_diffs, memory_diffs[1:]))
            
            # Add to results
            results.append({
                "function_name": name,
                "module_name": calls[0]['module_name'],
                "call_count": len(calls),
                "avg_memory_diff": avg_memory,
                "avg_execution_time": avg_time,
                "max_memory_diff": max_memory,
                "min_memory_diff": min_memory,
                "memory_variance": memory_variance,
                "time_variance": time_variance,
                "is_growing": is_growing,
                "total_memory_impact": sum(memory_diffs)
            })
        
        # Sort by total memory impact
        results.sort(key=lambda x: x["total_memory_impact"], reverse=True)
        
        return results
