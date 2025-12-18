"""
Plan Static Validation Node - Validate logical plan against schema.

This node validates the logical plan (not SQL) against the database schema:
- Tables exist in schema
- Columns exist in schema
- Join tables exist

Validates BEFORE SQL generation to prevent invalid queries.
"""

from typing import Dict, Any


def sql_static_validation(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate logical plan against database schema.
    
    Responsibility:
    - Validate tables exist in schema
    - Validate columns exist in schema
    - Validate join tables exist
    
    🚨 Validates logical plan, not SQL
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with validation result
    """
    logical_plan = state.get('logical_plan', {})
    tables = state.get('tables', [])
    columns = state.get('columns', {})
    join_plan = state.get('join_plan', [])
    
    # Track node visit
    node_visit_count = state.get('node_visit_count', {}).copy()
    node_visit_count['sql_static_validation'] = node_visit_count.get('sql_static_validation', 0) + 1
    
    if not logical_plan:
        return {
            'node_visit_count': node_visit_count,
            'error': 'No logical plan to validate',
            'error_type': 'validation_error'
        }
    
    # Validate tables exist
    from_tables = logical_plan.get('from', [])
    for table in from_tables:
        if table not in tables:
            return {
                'node_visit_count': node_visit_count,
                'error': f'Table does not exist: {table}',
                'error_type': 'missing_table'
            }
    
    # Validate columns exist
    select_cols = logical_plan.get('select', [])
    for col in select_cols:
        # Handle fully qualified columns (table.column)
        if '.' in col:
            table_name, col_name = col.split('.', 1)
            if table_name in columns:
                table_cols = [c['name'] for c in columns[table_name]]
                if col_name not in table_cols:
                    return {
                        'node_visit_count': node_visit_count,
                        'error': f'Column does not exist: {col}',
                        'error_type': 'missing_column'
                    }
        else:
            # Unqualified column - check if it exists in any of the from_tables
            found = False
            for table in from_tables:
                if table in columns:
                    table_cols = [c['name'] for c in columns[table]]
                    if col in table_cols:
                        found = True
                        break
            if not found:
                return {
                    'node_visit_count': node_visit_count,
                    'error': f'Column does not exist in any table: {col}',
                    'error_type': 'missing_column'
                }
    
    # Validate join tables exist
    for join in join_plan:
        to_table = join.get('to_table', '')
        from_table = join.get('from_table', '')
        if to_table and to_table not in tables:
            return {
                'node_visit_count': node_visit_count,
                'error': f'Join table does not exist: {to_table}',
                'error_type': 'missing_table'
            }
        if from_table and from_table not in tables:
            return {
                'node_visit_count': node_visit_count,
                'error': f'Join table does not exist: {from_table}',
                'error_type': 'missing_table'
            }
    
    # Validation passed
    return {
        'node_visit_count': node_visit_count,
        'error': None,
        'error_type': None
    }

