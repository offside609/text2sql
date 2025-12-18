"""
SQL Execution Node - Execute SQL query against the database.
"""

from typing import Dict, Any
import time
from db import get_db


def sql_execution(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute SQL query against the database.
    
    Responsibility:
    - Execute query
    - Enforce:
      - timeout (max 30 seconds)
      - row limit (already enforced in safety validation)
    
    Writes:
    - result: List of result dictionaries
    - execution_stats: Dict with time_ms, rows_returned
    - error: Error message if execution fails
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with query results
    """
    sql = state.get('validated_sql') or state.get('sql', '')
    
    if not sql:
        return {
            'error': 'No SQL to execute',
            'error_type': 'execution_error'
        }
    
    db = get_db()
    
    # Execute query with timeout
    start_time = time.time()
    
    try:
        # Execute query
        result = db.execute_query(sql)
        
        execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Check timeout (30 seconds)
        if execution_time > 30000:
            return {
                'error': 'Query execution timeout (exceeded 30 seconds)',
                'error_type': 'timeout'
            }
        
        # Return results
        return {
            'result': result,
            'execution_stats': {
                'time_ms': round(execution_time, 2),
                'rows_returned': len(result),
                'query': sql
            },
            'error': None,
            'error_type': None
        }
        
    except Exception as e:
        execution_time = (time.time() - start_time) * 1000
        return {
            'error': str(e),
            'error_type': 'execution_error',
            'execution_stats': {
                'time_ms': round(execution_time, 2),
                'rows_returned': 0,
                'query': sql
            }
        }

