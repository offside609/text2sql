"""
Start Node - Initialize state and attach thread_id.
"""

from typing import Dict, Any
import uuid


def start(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Initialize state and attach thread_id.
    
    Responsibility:
    - Initialize state
    - Attach thread_id
    - Store raw question
    - Set retry_count = 0
    
    Writes:
    - state.question
    - state.retry_count = 0
    - state.thread_id (if not present)
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with initialized fields
    """
    updates = {}
    
    # Initialize retry count if not present
    if 'retry_count' not in state:
        updates['retry_count'] = 0
    
    # Ensure question is stored
    if 'question' not in state:
        updates['question'] = state.get('input', '')
    
    # Initialize thread_id if not present
    if 'thread_id' not in state:
        updates['thread_id'] = str(uuid.uuid4())
    
    # Initialize error tracking
    if 'error' not in state:
        updates['error'] = None
    
    # Initialize max_retries if not present
    if 'max_retries' not in state:
        updates['max_retries'] = 3
    
    # Initialize loop prevention counters
    if 'clarification_attempts' not in state:
        updates['clarification_attempts'] = 0
    if 'max_clarification_attempts' not in state:
        updates['max_clarification_attempts'] = 3
    if 'node_visit_count' not in state:
        updates['node_visit_count'] = {}
    
    return updates

