"""
Repair Decision Node - Decide whether to retry or fail.
"""

from typing import Dict, Any


def repair_decision(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decide whether to retry or fail.
    
    Responsibility:
    - Decide:
      - retry (if retry_count < max_retries and error is repairable)
      - fail (if retry_count >= max_retries or error is not repairable)
    
    Writes:
    - repair_action: "retry" or "fail"
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with repair decision
    """
    retry_count = state.get('retry_count', 0)
    max_retries = state.get('max_retries', 3)
    error_type = state.get('error_type', 'unknown_error')
    
    # Track node visit
    node_visit_count = state.get('node_visit_count', {}).copy()
    node_visit_count['repair_decision'] = node_visit_count.get('repair_decision', 0) + 1
    
    # Non-repairable errors
    non_repairable = ['unsafe_query', 'timeout', 'clarification_limit_exceeded']
    
    result = {
        'node_visit_count': node_visit_count
    }
    
    if error_type in non_repairable:
        result['repair_action'] = 'fail'
    elif retry_count >= max_retries:
        result['repair_action'] = 'fail'
        result['error'] = f'Max retries ({max_retries}) exceeded'
    else:
        result['repair_action'] = 'retry'
    
    return result

