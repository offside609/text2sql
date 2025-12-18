"""
Resolve Synonyms Node - Map user terms → schema terms using LLM.
"""

from typing import Dict, Any
import json
from agents.tools import get_llm, RESOLVE_SYNONYMS_PROMPT
from db import format_schema_for_llm


def resolve_synonyms(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map user terms → schema terms using LLM.
    
    Responsibility:
    - Map user terms → schema terms using LLM
    - Examples: "journal" → "venue", "followers" → "follower_count"
    
    Writes:
    - resolved_entities: Dict mapping user term -> schema term
    - resolved_metrics: Dict mapping user term -> schema term
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with resolved terms
    """
    question = state.get('question', '')
    entities = state.get('entities', [])
    metrics = state.get('metrics', [])
    active_tables = state.get('active_tables', [])
    active_columns = state.get('active_columns', {})
    
    # Build user terms
    user_terms = {
        'entities': entities,
        'metrics': metrics
    }
    
    # Format schema for LLM
    schema_info = format_schema_for_llm(format_style="plain")
    
    try:
        # Use LLM to resolve synonyms
        llm = get_llm()
        
        prompt = RESOLVE_SYNONYMS_PROMPT.format(
            question=question,
            user_terms=json.dumps(user_terms, indent=2),
            schema_info=schema_info
        )
        
        response = llm.invoke_structured(
            prompt,
            response_format={"type": "json_object"}
        )
        
        resolved_entities = response.get('resolved_entities', {})
        resolved_metrics = response.get('resolved_metrics', {})
        
    except Exception as e:
        # Fallback to rule-based synonym resolution
        error_msg = f"LLM synonym resolution failed, using fallback: {str(e)}"
        
        # Simple fallback: direct matching
        resolved_entities = {}
        resolved_metrics = {}
        
        # Resolve entities
        for entity in entities:
            entity_lower = entity.lower()
            for table in active_tables:
                if entity_lower in table.lower():
                    resolved_entities[entity] = table
                    break
        
        # Resolve metrics
        for metric in metrics:
            metric_lower = metric.lower()
            for table, cols in active_columns.items():
                for col in cols:
                    if metric_lower in col['name'].lower():
                        resolved_metrics[metric] = {
                            'table': table,
                            'column': col['name']
                        }
                        break
                if metric in resolved_metrics:
                    break
    
    result = {
        'resolved_entities': resolved_entities,
        'resolved_metrics': resolved_metrics
    }
    
    # Add error if fallback was used
    if 'error_msg' in locals():
        result['error'] = error_msg
    
    return result

