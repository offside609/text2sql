"""
Error Classifier Node - Classify error type for repair decision.
"""

from typing import Dict, Any


def error_classifier(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify error type for repair decision.
    
    Responsibility:
    - Classify error:
      - syntax
      - missing column
      - ambiguous join
      - unsafe query
      - timeout
    
    Writes:
    - error_type: Classified error type
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with classified error
    """
    error = state.get('error', '')
    error_type = state.get('error_type', 'unknown')
    
    if not error:
        return {}
    
    error_lower = error.lower()
    
    # Classify based on error message patterns
    if 'syntax' in error_lower or 'parse' in error_lower:
        error_type = 'syntax_error'
    elif 'column' in error_lower and ('not exist' in error_lower or 'unknown' in error_lower):
        error_type = 'missing_column'
    elif 'table' in error_lower and ('not exist' in error_lower or 'unknown' in error_lower):
        error_type = 'missing_table'
    elif 'join' in error_lower or 'ambiguous' in error_lower:
        error_type = 'ambiguous_join'
    elif 'timeout' in error_lower:
        error_type = 'timeout'
    elif 'unsafe' in error_lower or 'not allowed' in error_lower:
        error_type = 'unsafe_query'
    elif 'foreign key' in error_lower:
        error_type = 'foreign_key_error'
    else:
        error_type = 'unknown_error'
    
    return {'error_type': error_type}

