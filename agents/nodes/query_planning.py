"""
Query Planning Node - Create logical plan using LLM.
"""

from typing import Dict, Any
import json
from agents.tools import get_llm, QUERY_PLANNING_PROMPT
from db import format_schema_for_llm


def query_planning(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decide on tables, joins, aggregations, filters, ordering using LLM.
    
    Responsibility:
    - Decide using LLM:
      - tables to query
      - joins needed
      - aggregations
      - filters
      - ordering
    
    Writes:
    - logical_plan: Dict with select, from, where, order_by, limit, group_by
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with logical plan
    """
    question = state.get('question', '')
    intent = state.get('intent', 'filter')
    resolved_entities = state.get('resolved_entities', {})
    resolved_metrics = state.get('resolved_metrics', {})
    filters = state.get('filters', {})
    limit = state.get('limit')
    grouping = state.get('grouping')
    active_tables = state.get('active_tables', [])
    active_columns = state.get('active_columns', {})
    
    # Format schema for LLM
    schema_info = format_schema_for_llm(format_style="plain")
    
    try:
        # Use LLM to create logical plan
        llm = get_llm()
        
        prompt = QUERY_PLANNING_PROMPT.format(
            question=question,
            intent=intent,
            resolved_entities=json.dumps(resolved_entities, indent=2),
            resolved_metrics=json.dumps(resolved_metrics, indent=2),
            filters=json.dumps(filters, indent=2),
            schema_info=schema_info
        )
        
        response = llm.invoke_structured(
            prompt,
            response_format={"type": "json_object"}
        )
        
        logical_plan = {
            'select': response.get('select', []),
            'from': response.get('from', active_tables[:1] if active_tables else []),
            'where': response.get('where', filters),
            'order_by': response.get('order_by'),
            'limit': response.get('limit', limit or 100),
            'group_by': response.get('group_by', grouping)
        }
        
    except Exception as e:
        # Fallback to rule-based planning
        error_msg = f"LLM query planning failed, using fallback: {str(e)}"
        
        logical_plan = {
            'select': [],
            'from': active_tables[:1] if active_tables else [],
            'where': filters,
            'order_by': None,
            'limit': limit or 100,
            'group_by': grouping
        }
        
        # Build select from resolved metrics
        if resolved_metrics:
            for metric_info in resolved_metrics.values():
                table = metric_info.get('table')
                column = metric_info.get('column')
                if table and column:
                    logical_plan['select'].append(f"{table}.{column}")
        
        # Add order by for rank intent
        if intent == 'rank' and logical_plan['select']:
            logical_plan['order_by'] = f"{logical_plan['select'][0]} DESC"
    
    result = {
        'logical_plan': logical_plan
    }
    
    # Add error if fallback was used
    if 'error_msg' in locals():
        result['error'] = error_msg
    
    return result

