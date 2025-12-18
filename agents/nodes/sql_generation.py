"""
SQL Generation Node - Convert logical plan → SQL using LLM.
"""

from typing import Dict, Any
import json
import re
from agents.tools import get_llm, SQL_GENERATION_PROMPT
from db import format_schema_for_llm


def sql_generation(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert logical plan → SQL using LLM.
    
    Responsibility:
    - Convert logical plan → SQL using LLM
    - Add default LIMIT
    - Fully qualify columns
    
    Writes:
    - sql: Generated SQL string
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with generated SQL
    """
    # Track node visit
    node_visit_count = state.get('node_visit_count', {}).copy()
    node_visit_count['sql_generation'] = node_visit_count.get('sql_generation', 0) + 1
    
    logical_plan = state.get('logical_plan', {})
    join_plan = state.get('join_plan', [])
    
    # Format schema for LLM
    schema_info = format_schema_for_llm(format_style="plain")
    
    try:
        # Use LLM to generate SQL
        llm = get_llm()
        
        prompt = SQL_GENERATION_PROMPT.format(
            logical_plan=json.dumps(logical_plan, indent=2),
            join_plan=json.dumps(join_plan, indent=2),
            schema_info=schema_info
        )
        
        sql = llm.invoke(prompt).strip()
        
        # Clean up SQL (remove markdown code blocks if present)
        sql = re.sub(r'```sql\s*', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'```\s*', '', sql)
        sql = sql.strip()
        
    except Exception as e:
        # Fallback to template-based SQL generation
        error_msg = f"LLM SQL generation failed, using fallback: {str(e)}"
        
        # Extract plan components
        select_cols = logical_plan.get('select', [])
        from_tables = logical_plan.get('from', [])
        where_filters = logical_plan.get('where', {})
        order_by = logical_plan.get('order_by')
        limit = logical_plan.get('limit', 100)
        group_by = logical_plan.get('group_by')
        
        # Validate plan has required components (no * fallback)
        if not select_cols:
            return {
                'sql': '',
                'node_visit_count': node_visit_count,
                'error': 'Cannot generate SQL: Empty select list in logical plan',
                'error_type': 'invalid_plan'
            }
        
        if not from_tables:
            return {
                'sql': '',
                'node_visit_count': node_visit_count,
                'error': 'Cannot generate SQL: No tables in logical plan',
                'error_type': 'invalid_plan'
            }
        
        select_clause = ', '.join(select_cols)
        from_clause = from_tables[0]
        
        # Build JOIN clauses
        join_clauses = []
        for join in join_plan:
            join_type = join.get('type', 'INNER')
            to_table = join.get('to_table', '')
            condition = join.get('condition', '')
            join_clauses.append(f"{join_type} JOIN {to_table} ON {condition}")
        
        # Build WHERE clause
        where_clauses = []
        for key, value in where_filters.items():
            if isinstance(value, str):
                where_clauses.append(f"{key} = '{value}'")
            elif isinstance(value, bool):
                where_clauses.append(f"{key} = {1 if value else 0}")
            else:
                where_clauses.append(f"{key} = {value}")
        
        where_clause = ' AND '.join(where_clauses) if where_clauses else ''
        
        # Assemble SQL
        sql_parts = [f"SELECT {select_clause}", f"FROM {from_clause}"]
        sql_parts.extend(join_clauses)
        if where_clause:
            sql_parts.append(f"WHERE {where_clause}")
        if group_by:
            sql_parts.append(f"GROUP BY {group_by}")
        if order_by:
            sql_parts.append(f"ORDER BY {order_by}")
        if limit:
            sql_parts.append(f"LIMIT {limit}")
        
        sql = ' '.join(sql_parts)
    
    result = {
        'sql': sql,
        'node_visit_count': node_visit_count
    }
    
    # Add error if fallback was used
    if 'error_msg' in locals():
        result['error'] = error_msg
    
    return result

