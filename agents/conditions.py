"""
Conditional edge routers for Text-to-SQL agent graph.

These functions determine the next node based on state conditions.
"""

from typing import Literal
from agents.state import TextToSQLState


def ambiguity_router(state: TextToSQLState) -> Literal["clarify", "continue", "fail"]:
    """
    Route after ambiguity detection.
    
    Routes to:
    - "fail" if clarification attempts exceeded
    - "clarify" if clarification is needed
    - "continue" if no clarification needed
    
    Args:
        state: Current graph state
        
    Returns:
        Next node name
    """
    clarification_attempts = state.get("clarification_attempts", 0)
    max_attempts = state.get("max_clarification_attempts", 3)
    
    # Hard stop if already exceeded
    if clarification_attempts >= max_attempts:
        return "fail"
    
    needs_clarification = state.get("needs_clarification", False)
    
    if needs_clarification:
        return "clarify"
    else:
        return "continue"


def clarification_router(state: TextToSQLState) -> Literal["fail", "load_schema"]:
    """
    Route after clarification request.
    
    Routes to:
    - "fail" if max clarification attempts exceeded
    - "load_schema" to proceed with best-effort parsing
    
    Args:
        state: Current graph state
        
    Returns:
        Next node name
    """
    clarification_attempts = state.get("clarification_attempts", 0)
    max_attempts = state.get("max_clarification_attempts", 3)
    
    # Hard stop if max attempts exceeded
    if clarification_attempts > max_attempts:
        return "fail"
    else:
        return "parse_question"


def safety_router(state: TextToSQLState) -> Literal["continue", "fail"]:
    """
    Route after SQL safety validation.
    
    Routes to:
    - "fail" if unsafe query detected
    - "continue" if safe
    
    Args:
        state: Current graph state
        
    Returns:
        Next node name
    """
    error = state.get("error")
    error_type = state.get("error_type")
    
    # If there's an error and it's an unsafe query, fail
    if error and error_type == "unsafe_query":
        return "fail"
    else:
        return "continue"


def static_validation_router(state: TextToSQLState) -> Literal["join_resolution", "classify_error"]:
    """
    Route after plan static validation.
    
    Routes to:
    - "classify_error" if validation failed
    - "join_resolution" if validation passed (plan is valid, proceed to SQL generation)
    
    Args:
        state: Current graph state
        
    Returns:
        Next node name
    """
    error = state.get("error")
    error_type = state.get("error_type")
    
    # If there's an error, classify it for repair
    if error and error_type:
        return "classify_error"
    else:
        return "join_resolution"


def execution_router(state: TextToSQLState) -> Literal["explain", "classify_error"]:
    """
    Route after SQL execution.
    
    Routes to:
    - "classify_error" if execution failed
    - "explain" if execution succeeded
    
    Args:
        state: Current graph state
        
    Returns:
        Next node name
    """
    error = state.get("error")
    error_type = state.get("error_type")
    result = state.get("result")
    
    # If there's an error, classify it for repair
    if error and error_type:
        return "classify_error"
    # If we have results (even empty list), proceed to explanation
    elif result is not None:
        return "explain"
    else:
        # Default to error classification if unclear
        return "classify_error"


def repair_router(state: TextToSQLState) -> Literal["retry", "fail"]:
    """
    Route after repair decision.
    
    Routes to:
    - "retry" if should retry (loop back to safety validation)
    - "fail" if should fail
    
    Args:
        state: Current graph state
        
    Returns:
        Next node name
    """
    repair_action = state.get("repair_action")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)
    
    # If repair action is explicitly "fail", fail
    if repair_action == "fail":
        return "fail"
    
    # If retry count exceeded, fail
    if retry_count >= max_retries:
        return "fail"
    
    # If repair action is "retry", retry
    if repair_action == "retry":
        return "retry"
    
    # Default: fail if unclear
    return "fail"
