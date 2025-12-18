"""
Schema Pruning Node - Reduce schema to relevant subset using LLM.
"""

from typing import Dict, Any
import json
from agents.tools import get_llm, SCHEMA_PRUNING_PROMPT
from db import format_schema_for_llm


def schema_pruning(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reduce schema to relevant subset to prevent prompt overload using LLM.
    
    Responsibility:
    - Reduce schema to relevant subset using LLM
    - Filter tables based on entities mentioned
    - Filter columns based on metrics/filters mentioned
    
    Writes:
    - active_tables: List of relevant table names
    - active_columns: Dict of relevant columns per table
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with pruned schema
    """
    question = state.get('question', '')
    intent = state.get('intent', '')
    entities = state.get('entities', [])
    metrics = state.get('metrics', [])
    all_tables = state.get('tables', [])
    all_columns = state.get('columns', {})
    
    try:
        # Use LLM to select relevant tables
        llm = get_llm()
        
        # Format schema for LLM
        schema_info = format_schema_for_llm(format_style="plain")
        
        prompt = SCHEMA_PRUNING_PROMPT.format(
            question=question,
            intent=intent,
            entities=', '.join(entities) if entities else 'None',
            metrics=', '.join(metrics) if metrics else 'None',
            all_tables=', '.join(all_tables)
        )
        
        response = llm.invoke_structured(
            prompt,
            response_format={"type": "json_object"}
        )
        
        active_tables = response.get('active_tables', [])
        
        # If LLM didn't return tables, use fallback
        if not active_tables:
            # Fallback: match entities to tables
            for entity in entities:
                for table in all_tables:
                    if entity.lower() in table.lower():
                        if table not in active_tables:
                            active_tables.append(table)
        
        # If still no tables, use all tables
        if not active_tables:
            active_tables = all_tables
        
    except Exception as e:
        # Fallback to rule-based pruning
        error_msg = f"LLM schema pruning failed, using fallback: {str(e)}"
        
        active_tables = []
        for entity in entities:
            for table in all_tables:
                if entity.lower() in table.lower():
                    if table not in active_tables:
                        active_tables.append(table)
        
        if not active_tables:
            active_tables = all_tables
    
    # Build active columns for selected tables
    active_columns = {}
    for table in active_tables:
        if table in all_columns:
            # Include all columns for now (can be further pruned)
            active_columns[table] = all_columns[table]
    
    result = {
        'active_tables': active_tables,
        'active_columns': active_columns
    }
    
    # Add error if fallback was used
    if 'error_msg' in locals():
        result['error'] = error_msg
    
    return result

