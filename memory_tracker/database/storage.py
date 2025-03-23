import sqlite3
import os
import json
import time
from contextlib import contextmanager

class DatabaseManager:
    """
    Manages storage and retrieval of memory tracking data.
    """
    
    def __init__(self, database_path=None):
        """
        Initialize the database manager.
        
        Args:
            database_path (str): Path to the SQLite database file
        """
        if database_path is None:
            # Create database in a temp file
            timestamp = int(time.time())
            database_path = f"memory_tracker_{timestamp}.db"
            
        self.database_path = database_path
        self.conn = None
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        # Create a new connection if needed
        if self.conn is None:
            self.conn = sqlite3.connect(self.database_path)
            self.conn.row_factory = sqlite3.Row
            
        try:
            yield self.conn
        except Exception as e:
            self.conn.rollback()
            raise e
    
    def initialize(self):
        """
        Initialize the database schema.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create snapshots table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    label TEXT,
                    timestamp REAL,
                    elapsed_time REAL,
                    memory_rss INTEGER,
                    memory_vms INTEGER,
                    total_objects INTEGER,
                    summary TEXT,
                    top_stats TEXT
                )
            ''')
            
            # Create object allocations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS object_allocations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    object_id INTEGER,
                    object_type TEXT,
                    size INTEGER,
                    stack_trace TEXT,
                    creation_time REAL
                )
            ''')
            
            # Create object deallocations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS object_deallocations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    object_id INTEGER,
                    object_type TEXT,
                    size INTEGER,
                    lifetime REAL,
                    deletion_time REAL
                )
            ''')
            
            # Create object leaks table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS object_leaks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    object_id INTEGER,
                    object_type TEXT,
                    size INTEGER,
                    stack_trace TEXT,
                    creation_time REAL,
                    tracked_lifetime REAL
                )
            ''')
            
            # Create garbage collection events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gc_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    duration REAL,
                    objects_collected INTEGER,
                    objects_before INTEGER,
                    objects_after INTEGER
                )
            ''')
            
            # Create function tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS function_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    function_name TEXT,
                    module_name TEXT,
                    memory_diff INTEGER,
                    execution_time REAL,
                    snapshot_diff TEXT,
                    timestamp REAL
                )
            ''')
            
            # Create indexes for faster queries
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_object_allocations_id ON object_allocations(object_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_object_deallocations_id ON object_deallocations(object_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_object_type ON object_allocations(object_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshot_timestamp ON snapshots(timestamp)')
            
            conn.commit()
    
    def store_snapshot(self, label, timestamp, elapsed_time, memory_rss, memory_vms, summary, top_stats):
        """
        Store a memory snapshot in the database.
        
        Args:
            label (str): Label for the snapshot
            timestamp (float): Unix timestamp when snapshot was taken
            elapsed_time (float): Time elapsed since tracking started
            memory_rss (int): Resident set size in bytes
            memory_vms (int): Virtual memory size in bytes
            summary (str): JSON string with memory summary
            top_stats (str): JSON string with top memory statistics
            
        Returns:
            int: ID of the newly inserted snapshot
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO snapshots (
                    label, timestamp, elapsed_time, memory_rss,
                    memory_vms, total_objects, summary, top_stats
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                label, timestamp, elapsed_time, memory_rss,
                memory_vms, 0, summary, top_stats
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def store_object_allocation(self, object_id, object_type, size, stack_trace, creation_time):
        """
        Store object allocation information.
        
        Args:
            object_id (int): ID of the allocated object
            object_type (str): Type of the object
            size (int): Size of the object in bytes
            stack_trace (str): Stack trace where the object was created
            creation_time (float): Unix timestamp when the object was created
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO object_allocations (
                    object_id, object_type, size, stack_trace, creation_time
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                object_id, object_type, size, stack_trace, creation_time
            ))
            
            conn.commit()
    
    def store_object_deallocation(self, object_id, object_type, size, lifetime, deletion_time):
        """
        Store object deallocation information.
        
        Args:
            object_id (int): ID of the deallocated object
            object_type (str): Type of the object
            size (int): Size of the object in bytes
            lifetime (float): Lifetime of the object in seconds
            deletion_time (float): Unix timestamp when the object was deleted
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO object_deallocations (
                    object_id, object_type, size, lifetime, deletion_time
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                object_id, object_type, size, lifetime, deletion_time
            ))
            
            conn.commit()
    
    def store_object_leak(self, object_id, object_type, size, stack_trace, creation_time, tracked_lifetime):
        """
        Store information about a potentially leaked object.
        
        Args:
            object_id (int): ID of the object
            object_type (str): Type of the object
            size (int): Size of the object in bytes
            stack_trace (str): Stack trace where the object was created
            creation_time (float): Unix timestamp when the object was created
            tracked_lifetime (float): Time the object was tracked before tracking stopped
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO object_leaks (
                    object_id, object_type, size, stack_trace, creation_time, tracked_lifetime
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                object_id, object_type, size, stack_trace, creation_time, tracked_lifetime
            ))
            
            conn.commit()
    
    def store_gc_event(self, timestamp, duration, objects_collected, objects_before, objects_after):
        """
        Store information about a garbage collection event.
        
        Args:
            timestamp (float): Unix timestamp when the GC occurred
            duration (float): Duration of the GC in seconds
            objects_collected (int): Number of objects collected
            objects_before (int): Number of objects before collection
            objects_after (int): Number of objects after collection
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO gc_events (
                    timestamp, duration, objects_collected, objects_before, objects_after
                ) VALUES (?, ?, ?, ?, ?)
            ''', (
                timestamp, duration, objects_collected, objects_before, objects_after
            ))
            
            conn.commit()
    
    def store_function_tracking(self, function_name, module_name, memory_diff, execution_time, snapshot_diff):
        """
        Store tracking information for a function.
        
        Args:
            function_name (str): Name of the function
            module_name (str): Name of the module containing the function
            memory_diff (int): Memory difference in bytes
            execution_time (float): Execution time in seconds
            snapshot_diff (list): Tracemalloc snapshot difference
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO function_tracking (
                    function_name, module_name, memory_diff, execution_time, snapshot_diff, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                function_name,
                module_name,
                memory_diff,
                execution_time,
                json.dumps([{
                    "filename": stat.traceback[0].filename,
                    "lineno": stat.traceback[0].lineno,
                    "size": stat.size,
                    "count": stat.count
                } for stat in snapshot_diff[:50]]),  # Limit to top 50 stats
                time.time()
            ))
            
            conn.commit()
    
    def get_snapshots(self):
        """
        Get all stored snapshots.
        
        Returns:
            list: List of snapshots
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM snapshots ORDER BY timestamp')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_snapshot(self, snapshot_id):
        """
        Get a specific snapshot by ID.
        
        Args:
            snapshot_id (int): ID of the snapshot
            
        Returns:
            dict: Snapshot data
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM snapshots WHERE id = ?', (snapshot_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_object_allocations(self, limit=1000, object_type=None):
        """
        Get object allocation records.
        
        Args:
            limit (int): Maximum number of records to retrieve
            object_type (str): Filter by object type
            
        Returns:
            list: List of object allocation records
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if object_type:
                cursor.execute(
                    'SELECT * FROM object_allocations WHERE object_type = ? ORDER BY creation_time DESC LIMIT ?', 
                    (object_type, limit)
                )
            else:
                cursor.execute(
                    'SELECT * FROM object_allocations ORDER BY creation_time DESC LIMIT ?', 
                    (limit,)
                )
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_object_deallocations(self, limit=1000, object_type=None):
        """
        Get object deallocation records.
        
        Args:
            limit (int): Maximum number of records to retrieve
            object_type (str): Filter by object type
            
        Returns:
            list: List of object deallocation records
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if object_type:
                cursor.execute(
                    'SELECT * FROM object_deallocations WHERE object_type = ? ORDER BY deletion_time DESC LIMIT ?', 
                    (object_type, limit)
                )
            else:
                cursor.execute(
                    'SELECT * FROM object_deallocations ORDER BY deletion_time DESC LIMIT ?', 
                    (limit,)
                )
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_object_leaks(self, limit=1000, object_type=None):
        """
        Get object leak records.
        
        Args:
            limit (int): Maximum number of records to retrieve
            object_type (str): Filter by object type
            
        Returns:
            list: List of object leak records
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if object_type:
                cursor.execute(
                    'SELECT * FROM object_leaks WHERE object_type = ? ORDER BY size DESC LIMIT ?', 
                    (object_type, limit)
                )
            else:
                cursor.execute(
                    'SELECT * FROM object_leaks ORDER BY size DESC LIMIT ?', 
                    (limit,)
                )
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_gc_events(self, limit=100):
        """
        Get garbage collection event records.
        
        Args:
            limit (int): Maximum number of records to retrieve
            
        Returns:
            list: List of GC event records
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT * FROM gc_events ORDER BY timestamp DESC LIMIT ?', 
                (limit,)
            )
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_function_tracking(self, function_name=None, limit=100):
        """
        Get function tracking records.
        
        Args:
            function_name (str): Filter by function name
            limit (int): Maximum number of records to retrieve
            
        Returns:
            list: List of function tracking records
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if function_name:
                cursor.execute(
                    'SELECT * FROM function_tracking WHERE function_name = ? ORDER BY timestamp DESC LIMIT ?', 
                    (function_name, limit)
                )
            else:
                cursor.execute(
                    'SELECT * FROM function_tracking ORDER BY timestamp DESC LIMIT ?', 
                    (limit,)
                )
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_memory_timeline(self):
        """
        Get memory usage timeline from snapshots.
        
        Returns:
            list: List of (timestamp, memory_rss) tuples
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT timestamp, memory_rss FROM snapshots ORDER BY timestamp')
            return [(row['timestamp'], row['memory_rss']) for row in cursor.fetchall()]
    
    def get_object_type_summary(self):
        """
        Get summary of object allocations by type.
        
        Returns:
            list: List of (object_type, count, total_size) tuples
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT object_type, COUNT(*) as count, SUM(size) as total_size 
                FROM object_allocations 
                GROUP BY object_type 
                ORDER BY total_size DESC
            ''')
            return [(row['object_type'], row['count'], row['total_size']) for row in cursor.fetchall()]
    
    def close(self):
        """
        Close the database connection.
        """
        if self.conn:
            self.conn.close()
            self.conn = None
