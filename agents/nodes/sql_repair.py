"""
SQL Repair Node - Fix SQL using LLM.
"""

from typing import Dict, Any
import json
import re
from agents.tools import get_llm, SQL_REPAIR_PROMPT
from db import format_schema_for_llm


def sql_repair(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fix SQL using schema, error message, and original intent using LLM.
    
    Responsibility:
    - Fix SQL using LLM:
      - schema information
      - error message
      - original intent
    
    Writes:
    - sql: Repaired SQL
    - retry_count += 1
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with repaired SQL
    """
    error_type = state.get('error_type', 'unknown_error')
    error = state.get('error', '')
    sql = state.get('sql', '')
    question = state.get('question', '')
    
    # Increment retry count
    retry_count = state.get('retry_count', 0) + 1
    
    # Format schema for LLM
    schema_info = format_schema_for_llm(format_style="plain")
    
    try:
        # Use LLM to repair SQL
        llm = get_llm()
        
        prompt = SQL_REPAIR_PROMPT.format(
            sql=sql,
            error=error,
            error_type=error_type,
            schema_info=schema_info,
            question=question
        )
        
        response = llm.invoke_structured(
            prompt,
            response_format={"type": "json_object"}
        )
        
        repaired_sql = response.get('repaired_sql', sql)
        
        # Clean up SQL
        repaired_sql = re.sub(r'```sql\s*', '', repaired_sql, flags=re.IGNORECASE)
        repaired_sql = re.sub(r'```\s*', '', repaired_sql)
        repaired_sql = repaired_sql.strip()
        
    except Exception as e:
        # Fallback to rule-based repair
        error_msg = f"LLM SQL repair failed, using fallback: {str(e)}"
        
        repaired_sql = sql
        columns = state.get('columns', {})
        tables = state.get('tables', [])
        
        # Repair based on error type
        if error_type == 'missing_column':
            col_match = re.search(r"column\s+['\"]?(\w+)['\"]?", error, re.IGNORECASE)
            if col_match:
                missing_col = col_match.group(1)
                for table, table_cols in columns.items():
                    for col in table_cols:
                        if missing_col.lower() in col['name'].lower():
                            repaired_sql = sql.replace(missing_col, f"{table}.{col['name']}")
                            break
                    if repaired_sql != sql:
                        break
        
        elif error_type == 'missing_table':
            table_match = re.search(r"table\s+['\"]?(\w+)['\"]?", error, re.IGNORECASE)
            if table_match:
                missing_table = table_match.group(1)
                for table in tables:
                    if missing_table.lower() in table.lower():
                        repaired_sql = sql.replace(missing_table, table)
                        break
        
        elif error_type == 'syntax_error':
            repaired_sql = re.sub(r',\s*(FROM|WHERE|ORDER BY|GROUP BY|LIMIT)', r' \1', repaired_sql, flags=re.IGNORECASE)
            repaired_sql = repaired_sql.replace('TRUE', '1').replace('FALSE', '0')
    
    # Track node visit
    node_visit_count = state.get('node_visit_count', {}).copy()
    node_visit_count['sql_repair'] = node_visit_count.get('sql_repair', 0) + 1
    
    # Return updated state
    result = {
        'sql': repaired_sql,
        'validated_sql': None,  # Reset validated SQL to re-validate
        'retry_count': retry_count,
        'node_visit_count': node_visit_count,
        # CRITICAL: Clear error state before retrying to prevent infinite loops
        'error': None,
        'error_type': None
    }
    
    # Add error if fallback was used
    if 'error_msg' in locals():
        result['error'] = error_msg
    
    return result

