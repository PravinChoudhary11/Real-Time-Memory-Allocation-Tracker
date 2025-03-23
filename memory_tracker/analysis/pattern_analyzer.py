import numpy as np
from collections import defaultdict

class PatternAnalyzer:
    """
    Analyzes memory allocation patterns.
    """
    
    def __init__(self, database):
        """
        Initialize the pattern analyzer.
        
        Args:
            database: Database manager instance
        """
        self.database = database
    
    def detect_patterns(self):
        """
        Detect memory allocation patterns.
        
        Returns:
            list: Detected memory patterns
        """
        # Get memory timeline from snapshots
        timeline = self.database.get_memory_timeline()
        if not timeline or len(timeline) < 3:
            return []
            
        # Extract timestamps and memory values
        timestamps, memory_values = zip(*timeline)
        
        # Look for periodic patterns
        periodic_patterns = self._detect_periodic_patterns(timestamps, memory_values)
        
        # Look for growth patterns
        growth_patterns = self._detect_growth_patterns(timestamps, memory_values)
        
        # Look for allocation bursts
        burst_patterns = self._detect_burst_patterns(timestamps, memory_values)
        
        # Combine results
        all_patterns = periodic_patterns + growth_patterns + burst_patterns
        
        return all_patterns
    
    def _detect_periodic_patterns(self, timestamps, memory_values):
        """
        Detect periodic memory usage patterns.
        
        Args:
            timestamps (list): List of timestamps
            memory_values (list): List of memory values
            
        Returns:
            list: Detected periodic patterns
        """
        if len(timestamps) < 10:
            return []
            
        # Calculate memory changes
        memory_changes = np.diff(memory_values)
        
        # Look for alternating increases and decreases
        signs = np.sign(memory_changes)
        
        # Check for sign changes (alternating pattern)
        sign_changes = np.diff(signs) != 0
        
        # If over 60% of consecutive values have opposite signs, that's a potential oscillation
        if np.mean(sign_changes) > 0.6:
            # Calculate average period using zero crossings
            zero_crossings = np.where(np.diff(np.signbit(memory_changes)))[0]
            if len(zero_crossings) > 1:
                periods = [timestamps[i+1] - timestamps[i] for i in zero_crossings]
                avg_period = np.mean(periods)
            else:
                avg_period = None
            return [{
                "pattern": "periodic oscillation",
                "avg_period": avg_period,
                "description": "Detected alternating increases and decreases in memory usage."
            }]
        else:
            return []
    
    def _detect_growth_patterns(self, timestamps, memory_values):
        """
        Detect steady growth in memory usage.
        
        Args:
            timestamps (list): List of timestamps
            memory_values (list): List of memory values
            
        Returns:
            list: Detected growth patterns
        """
        total_growth = memory_values[-1] - memory_values[0]
        total_time = timestamps[-1] - timestamps[0]
        growth_rate = total_growth / total_time if total_time > 0 else 0
        
        # Heuristic: if overall growth is positive and exceeds a minimal threshold, report it.
        if growth_rate > 0:
            return [{
                "pattern": "steady growth",
                "growth_rate": growth_rate,
                "total_growth": total_growth,
                "description": "Detected a steady increase in memory usage over time."
            }]
        else:
            return []
    
    def _detect_burst_patterns(self, timestamps, memory_values):
        """
        Detect sudden bursts in memory allocation.
        
        Args:
            timestamps (list): List of timestamps
            memory_values (list): List of memory values
            
        Returns:
            list: Detected burst patterns
        """
        memory_changes = np.diff(memory_values)
        avg_change = np.mean(memory_changes)
        std_change = np.std(memory_changes)
        
        burst_patterns = []
        # Identify bursts where change is significantly higher than average (e.g., > avg + 2*std)
        burst_indices = np.where(memory_changes > avg_change + 2 * std_change)[0]
        for idx in burst_indices:
            burst_patterns.append({
                "pattern": "burst",
                "timestamp": timestamps[idx + 1],
                "memory_increase": memory_changes[idx],
                "description": "Detected a sudden burst in memory allocation."
            })
        return burst_patterns
