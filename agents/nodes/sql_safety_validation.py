"""
Plan Safety Validation Node - Validate logical plan for safety.

This node validates the logical plan (not SQL) to ensure:
- Valid SELECT-only intent
- Required components (tables, select columns) are present
- LIMIT constraints are enforced
- Join count is within limits

Validates BEFORE SQL generation to prevent invalid queries.
"""

from typing import Dict, Any


def sql_safety_validation(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate logical plan for safety before SQL generation.
    
    Responsibility:
    - Validate logical plan structure
    - Ensure plan has valid intent (SELECT-only)
    - Check for required components (tables, select columns)
    - Enforce LIMIT constraints
    - Validate join count
    
    🚨 Security boundary node - validates logical plan, not SQL
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with validation result
    """
    logical_plan = state.get('logical_plan', {})
    intent = state.get('intent', 'filter')
    join_plan = state.get('join_plan', [])
    
    # Check if logical plan exists
    if not logical_plan:
        return {
            'error': 'No logical plan to validate',
            'error_type': 'invalid_plan'
        }
    
    # Validate intent is safe (SELECT-only operations)
    safe_intents = ['filter', 'list', 'rank', 'count', 'aggregate']
    if intent not in safe_intents:
        return {
            'error': f'Unsafe or invalid intent: "{intent}". Only SELECT queries are allowed.',
            'error_type': 'unsafe_query'
        }
    
    # Check for required components
    from_tables = logical_plan.get('from', [])
    select_cols = logical_plan.get('select', [])
    
    if not from_tables:
        return {
            'error': 'Invalid plan: No tables specified in FROM clause',
            'error_type': 'invalid_plan'
        }
    
    if not select_cols:
        return {
            'error': 'Invalid plan: No columns specified in SELECT clause',
            'error_type': 'invalid_plan'
        }
    
    # Validate LIMIT (max 10000 rows)
    limit = logical_plan.get('limit', 100)
    if limit and limit > 10000:
        return {
            'error': f'LIMIT too large: {limit} (max 10000)',
            'error_type': 'unsafe_query'
        }
    
    # Validate join count (prevent cartesian products)
    if len(join_plan) > 5:
        return {
            'error': f'Too many joins: {len(join_plan)} (max 5)',
            'error_type': 'unsafe_query'
        }
    
    # Plan passed safety checks
    return {
        'error': None,
        'error_type': None
    }

