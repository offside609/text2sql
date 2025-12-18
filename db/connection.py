"""
Database connection and query execution utilities.

This module provides:
- Database connection management
- Query execution with error handling
- Result formatting
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager


# Database path
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "data" / "db" / "musicoset_popularity.sqlite"


class DatabaseConnection:
    """Manages SQLite database connections and query execution."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database. If None, uses default path.
        """
        self.db_path = db_path or DB_PATH
        
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Database not found at {self.db_path}. "
                f"Run db/load_sqlite.py first to create the database."
            )
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        
        Yields:
            sqlite3.Connection: Database connection
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()
    
    def execute_query(
        self,
        query: str,
        parameters: Optional[Tuple] = None,
        fetch_all: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results.
        
        Args:
            query: SQL query string
            parameters: Optional query parameters for parameterized queries
            fetch_all: If True, fetch all results; if False, fetch one
            
        Returns:
            List of dictionaries representing rows
            
        Raises:
            sqlite3.Error: If query execution fails
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                if parameters:
                    cursor.execute(query, parameters)
                else:
                    cursor.execute(query)
                
                if fetch_all:
                    rows = cursor.fetchall()
                    # Convert Row objects to dictionaries
                    return [dict(row) for row in rows]
                else:
                    row = cursor.fetchone()
                    return [dict(row)] if row else []
                    
            except sqlite3.Error as e:
                raise sqlite3.Error(f"Query execution failed: {e}\nQuery: {query}")
    
    def execute_write(
        self,
        query: str,
        parameters: Optional[Tuple] = None,
        commit: bool = True
    ) -> int:
        """
        Execute a write query (INSERT, UPDATE, DELETE).
        
        Args:
            query: SQL query string
            parameters: Optional query parameters
            commit: Whether to commit the transaction
            
        Returns:
            Number of rows affected
            
        Raises:
            sqlite3.Error: If query execution fails
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                if parameters:
                    cursor.execute(query, parameters)
                else:
                    cursor.execute(query)
                
                if commit:
                    conn.commit()
                
                return cursor.rowcount
                
            except sqlite3.Error as e:
                conn.rollback()
                raise sqlite3.Error(f"Write query failed: {e}\nQuery: {query}")
    
    def execute_script(self, script: str) -> None:
        """
        Execute multiple SQL statements from a script.
        
        Args:
            script: SQL script containing multiple statements
            
        Raises:
            sqlite3.Error: If script execution fails
        """
        with self.get_connection() as conn:
            try:
                conn.executescript(script)
                conn.commit()
            except sqlite3.Error as e:
                conn.rollback()
                raise sqlite3.Error(f"Script execution failed: {e}")
    
    def get_table_names(self) -> List[str]:
        """
        Get list of all table names in the database.
        
        Returns:
            List of table names
        """
        query = """
            SELECT name 
            FROM sqlite_master 
            WHERE type='table' 
            AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """
        results = self.execute_query(query)
        return [row['name'] for row in results]
    
    def validate_query(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a SQL query without executing it.
        
        Args:
            query: SQL query string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(f"EXPLAIN QUERY PLAN {query}")
                return True, None
            except sqlite3.Error as e:
                return False, str(e)


# Global instance for convenience
_db_instance: Optional[DatabaseConnection] = None


def get_db() -> DatabaseConnection:
    """
    Get or create a global database connection instance.
    
    Returns:
        DatabaseConnection instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseConnection()
    return _db_instance


def reset_db_instance():
    """Reset the global database instance (useful for testing)."""
    global _db_instance
    _db_instance = None

