"""
Join Resolution Node - Resolve ambiguous joins using LLM.
"""

from typing import Dict, Any
import json
from agents.tools import get_llm, JOIN_RESOLUTION_PROMPT
from db import get_join_graph, get_join_paths, get_db


def join_resolution(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolve ambiguous joins and decide join paths explicitly using LLM.
    
    Responsibility:
    - Resolve ambiguous joins using LLM
    - Decide join paths explicitly
    - Use foreign key relationships
    
    Writes:
    - join_plan: List of join dictionaries with table, on, type
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with explicit join plan
    """
    logical_plan = state.get('logical_plan', {})
    from_tables = logical_plan.get('from', [])
    foreign_keys = state.get('foreign_keys', {})
    
    # If only one table, no joins needed
    if len(from_tables) <= 1:
        return {'join_plan': []}
    
    db = get_db()
    join_graph = get_join_graph(db)
    
    try:
        # Use LLM to determine join strategy
        llm = get_llm()
        
        prompt = JOIN_RESOLUTION_PROMPT.format(
            tables=', '.join(from_tables),
            foreign_keys=json.dumps(foreign_keys, indent=2),
            join_graph=json.dumps(join_graph, indent=2)
        )
        
        response = llm.invoke_structured(
            prompt,
            response_format={"type": "json_object"}
        )
        
        join_plan = response.get('join_plan', [])
        
    except Exception as e:
        # Fallback to rule-based join resolution
        error_msg = f"LLM join resolution failed, using fallback: {str(e)}"
        
        join_plan = []
        
        # Find direct joins
        for i in range(len(from_tables) - 1):
            from_table = from_tables[i]
            to_table = from_tables[i + 1]
            
            # Find direct join if exists
            from_joins = join_graph.get(from_table, [])
            direct_join = None
            for join_info in from_joins:
                if join_info['target_table'] == to_table:
                    direct_join = join_info
                    break
            
            if direct_join:
                join_plan.append({
                    'type': 'INNER',
                    'from_table': from_table,
                    'to_table': to_table,
                    'from_column': direct_join['local_column'],
                    'to_column': direct_join['foreign_column'],
                    'condition': f"{from_table}.{direct_join['local_column']} = {to_table}.{direct_join['foreign_column']}"
                })
            else:
                # Try to find join path
                paths = get_join_paths(from_table, to_table, db, max_depth=2)
                if paths and len(paths[0]) > 0:
                    path = paths[0]
                    for join_info in path:
                        join_plan.append({
                            'type': 'INNER',
                            'from_table': join_info.get('target_table', from_table),
                            'to_table': to_table,
                            'from_column': join_info.get('local_column'),
                            'to_column': join_info.get('foreign_column'),
                            'condition': join_info.get('relationship', '')
                        })
    
    result = {'join_plan': join_plan}
    
    # Add error if fallback was used
    if 'error_msg' in locals():
        result['error'] = error_msg
    
    return result

