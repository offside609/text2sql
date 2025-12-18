"""
State schema for Text-to-SQL agent.

This module defines the TypedDict for the LangGraph state.
"""

from typing import TypedDict, List, Dict, Any, Optional


class TextToSQLState(TypedDict, total=False):
    """
    State schema for Text-to-SQL LangGraph agent.
    
    All fields are optional to allow incremental state updates.
    """
    
    # ===== Entry & Control =====
    input: str  # Initial user input/question
    question: str  # Normalized question
    thread_id: str  # Unique thread identifier
    retry_count: int  # Current retry attempt
    max_retries: int  # Maximum retry attempts (default: 3)
    
    # ===== Loop Prevention =====
    clarification_attempts: int  # Number of clarification attempts
    max_clarification_attempts: int  # Max clarification attempts (default: 1)
    node_visit_count: Dict[str, int]  # Track visits to each node (for debugging)
    
    # ===== Language Understanding =====
    intent: str  # Query intent: "rank", "count", "filter", "aggregate", "list"
    entities: List[str]  # Entities/tables mentioned (e.g., ["artist", "album"])
    metrics: List[str]  # Metrics/columns mentioned (e.g., ["followers", "popularity"])
    filters: Dict[str, Any]  # Filter conditions (e.g., {"year": 2018, "is_pop": True})
    limit: Optional[int]  # User-specified limit
    grouping: Optional[str]  # Group by field
    
    # ===== Ambiguity Detection =====
    needs_clarification: bool  # Whether clarification is needed
    ambiguity_reason: Optional[str]  # Reason for ambiguity
    missing_info: List[str]  # List of missing information types
    clarification: Optional[Dict[str, Any]]  # Clarification request/response
    
    # ===== Schema Information =====
    tables: List[str]  # All available table names
    columns: Dict[str, List[Dict[str, Any]]]  # Table -> columns mapping
    foreign_keys: Dict[str, List[Dict[str, Any]]]  # Foreign key relationships
    schemas: Dict[str, Dict[str, Any]]  # Full schema information
    
    # ===== Schema Pruning =====
    active_tables: List[str]  # Pruned relevant table names
    active_columns: Dict[str, List[Dict[str, Any]]]  # Pruned relevant columns
    
    # ===== Resolved Terms =====
    resolved_entities: Dict[str, str]  # User term -> schema table mapping
    resolved_metrics: Dict[str, Dict[str, str]]  # User term -> {table, column} mapping
    
    # ===== Query Planning =====
    logical_plan: Dict[str, Any]  # Logical query plan
    # Structure: {
    #   "select": List[str],
    #   "from": List[str],
    #   "where": Dict[str, Any],
    #   "order_by": Optional[str],
    #   "limit": int,
    #   "group_by": Optional[str]
    # }
    
    join_plan: List[Dict[str, Any]]  # Join plan
    # Structure: [
    #   {
    #     "type": str,  # "INNER", "LEFT", etc.
    #     "from_table": str,
    #     "to_table": str,
    #     "from_column": str,
    #     "to_column": str,
    #     "condition": str
    #   }
    # ]
    
    # ===== SQL Generation =====
    sql: Optional[str]  # Generated SQL query
    validated_sql: Optional[str]  # SQL after safety validation
    
    # ===== Execution =====
    result: List[Dict[str, Any]]  # Query results
    execution_stats: Dict[str, Any]  # Execution statistics
    # Structure: {
    #   "time_ms": float,
    #   "rows_returned": int,
    #   "query": str
    # }
    
    # ===== Error Handling =====
    error: Optional[str]  # Error message
    error_type: Optional[str]  # Error type classification
    # Types: "syntax_error", "missing_column", "missing_table", 
    #        "ambiguous_join", "timeout", "unsafe_query", "execution_error"
    
    # ===== Repair =====
    repair_action: Optional[str]  # "retry" or "fail"
    
    # ===== Output =====
    explanation: Optional[str]  # Human-readable explanation
    response: Optional[Dict[str, Any]]  # Final response
    # Structure: {
    #   "question": str,
    #   "sql": str,
    #   "result_preview": List[Dict],
    #   "total_rows": int,
    #   "execution_stats": Dict,
    #   "explanation": str,
    #   "retry_count": int
    # }
    
    # ===== Observability =====
    trace: Optional[Dict[str, Any]]  # Execution trace for logging