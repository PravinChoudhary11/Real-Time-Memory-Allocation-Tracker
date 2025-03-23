import json
import time
from collections import defaultdict

class LeakDetector:
    """
    Detects potential memory leaks from tracking data.
    """
    
    def __init__(self, database):
        """
        Initialize the leak detector.
        
        Args:
            database: Database manager instance
        """
        self.database = database
    
    def detect_leaks(self):
        """
        Detect potential memory leaks.
        
        Returns:
            list: List of potential memory leaks
        """
        # Get object allocation and deallocation data
        allocations = self.database.get_object_allocations(limit=100000)  # Large limit to get most data
        deallocations = self.database.get_object_deallocations(limit=100000)
        explicit_leaks = self.database.get_object_leaks(limit=100000)
        
        # Build a map of deallocated objects
        deallocated = {dealloc['object_id']: dealloc for dealloc in deallocations}
        
        # Find objects that were allocated but not deallocated
        potential_leaks = []
        for alloc in allocations:
            if alloc['object_id'] not in deallocated:
                potential_leaks.append({
                    "object_id": alloc['object_id'],
                    "object_type": alloc['object_type'],
                    "size": alloc['size'],
                    "stack_trace": alloc['stack_trace'],
                    "creation_time": alloc['creation_time'],
                    "age": time.time() - alloc['creation_time']
                })
        
        # Add explicit leaks
        for leak in explicit_leaks:
            potential_leaks.append({
                "object_id": leak['object_id'],
                "object_type": leak['object_type'],
                "size": leak['size'],
                "stack_trace": leak['stack_trace'],
                "creation_time": leak['creation_time'],
                "age": leak['tracked_lifetime'],
                "explicit_leak": True
            })
        
        # Sort by size (largest leaks first)
        potential_leaks.sort(key=lambda x: x['size'], reverse=True)
        
        return potential_leaks[:1000]  # Return top 1000 leaks by size
    
    def analyze(self):
        """
        Perform a detailed analysis of memory leaks.
        
        Returns:
            dict: Analysis results
        """
        # Get potential leaks
        leaks = self.detect_leaks()
        
        # Group by object type
        leaks_by_type = defaultdict(list)
        for leak in leaks:
            leaks_by_type[leak['object_type']].append(leak)
        
        # Calculate summary statistics by type
        type_summaries = []
        for obj_type, type_leaks in leaks_by_type.items():
            total_size = sum(leak['size'] for leak in type_leaks)
            avg_size = total_size / len(type_leaks) if type_leaks else 0
            count = len(type_leaks)
            
            type_summaries.append({
                "type": obj_type,
                "count": count,
                "total_size": total_size,
                "avg_size": avg_size,
                "examples": type_leaks[:3]  # First 3 examples
            })
        
        # Sort by total size
        type_summaries.sort(key=lambda x: x['total_size'], reverse=True)
        
        # Group by stack trace pattern
        stack_pattern_to_leaks = defaultdict(list)
        for leak in leaks:
            # Extract first line of stack trace as a pattern
            stack_lines = leak['stack_trace'].split("\n")
            pattern = stack_lines[0] if stack_lines else "unknown"
            stack_pattern_to_leaks[pattern].append(leak)
        
        # Calculate summary statistics by stack trace pattern
        stack_summaries = []
        for pattern, pattern_leaks in stack_pattern_to_leaks.items():
            total_size = sum(leak['size'] for leak in pattern_leaks)
            avg_size = total_size / len(pattern_leaks) if pattern_leaks else 0
            count = len(pattern_leaks)
            
            stack_summaries.append({
                "pattern": pattern,
                "count": count,
                "total_size": total_size,
                "avg_size": avg_size,
                "examples": pattern_leaks[:3]  # First 3 examples
            })
        
        # Sort by total size
        stack_summaries.sort(key=lambda x: x['total_size'], reverse=True)
        
        # Calculate overall statistics
        total_leaked_objects = len(leaks)
        total_leaked_memory = sum(leak['size'] for leak in leaks)
        
        return {
            "total_leaked_objects": total_leaked_objects,
            "total_leaked_memory": total_leaked_memory,
            "leaks_by_type": type_summaries[:20],  # Top 20 types
            "leaks_by_stack": stack_summaries[:20]  # Top 20 stack patterns
        }
