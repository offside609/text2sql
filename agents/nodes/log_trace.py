"""
Log Trace Node - Log execution trace for observability.
"""

from typing import Dict, Any
import json
from datetime import datetime


def log_trace(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Log execution trace for observability.
    
    Responsibility:
    - Log:
      - question
      - sql
      - execution time
      - repair count
      - error (if any)
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state (logging is side effect)
    """
    trace = {
        'timestamp': datetime.now().isoformat(),
        'thread_id': state.get('thread_id'),
        'question': state.get('question', ''),
        'sql': state.get('validated_sql') or state.get('sql', ''),
        'execution_stats': state.get('execution_stats', {}),
        'retry_count': state.get('retry_count', 0),
        'clarification_attempts': state.get('clarification_attempts', 0),
        'node_visit_count': state.get('node_visit_count', {}),
        'error': state.get('error'),
        'error_type': state.get('error_type'),
        'result_count': len(state.get('result', [])),
        'success': state.get('error') is None
    }
    
    # In production, you would:
    # - Write to log file
    # - Send to monitoring system
    # - Store in database
    # - Send to tracing service (e.g., OpenTelemetry)
    
    # Print trace (for development)
    print(f"\n{'='*60}")
    print("EXECUTION TRACE")
    print(f"{'='*60}")
    print(json.dumps(trace, indent=2))
    print(f"{'='*60}\n")
    
    # Return only trace (logging is side effect)
    return {'trace': trace}

