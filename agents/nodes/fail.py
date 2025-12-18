"""
Fail Node - Graceful termination with error JSON.
"""

from typing import Dict, Any


def fail(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Graceful termination with error JSON.
    
    Responsibility:
    - Graceful termination
    - Return error JSON (not stack traces)
    
    When hit:
    - Unsafe query
    - Retry limit exceeded
    - Unresolvable ambiguity
    
    Args:
        state: Current graph state
        
    Returns:
        State with error response formatted
    """
    error_type = state.get('error_type', 'unknown_error')
    error_message = state.get('error', 'An unknown error occurred')
    question = state.get('question', '')
    
    # Build error response
    return {
        'response': {
            "question": question,
            "sql": state.get('sql'),
            "error": {
                "type": error_type,
                "message": error_message,
                "retry_count": state.get('retry_count', 0)
            },
            "result_preview": [],
            "explanation": f"Query failed: {error_message}"
        }
    }

