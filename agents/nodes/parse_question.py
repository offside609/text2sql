"""
Parse Question Node - Extract intent and constraints using LLM.
"""

from typing import Dict, Any
import json
from agents.tools import get_llm, PARSE_QUESTION_PROMPT


def parse_question(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize question and extract intent + constraints using LLM.
    
    Responsibility:
    - Normalize question
    - Extract intent + constraints using LLM
    - Parse metrics, filters, limit, grouping
    
    Writes:
    - intent (e.g., "rank", "count", "filter", "aggregate")
    - entities (e.g., ["artist", "album"])
    - metrics (e.g., ["followers", "popularity"])
    - filters (e.g., {"year": 2018, "is_pop": True})
    - limit (user-specified limit)
    - grouping (group by field)
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with parsed question components
    """
    question = state.get('question', '').strip()
    
    if not question:
        # Fallback to defaults
        return {
            'intent': 'filter',
            'entities': [],
            'metrics': [],
            'filters': {},
            'limit': None,
            'grouping': None
        }
    
    try:
        # Use LLM to parse question
        llm = get_llm()
        
        prompt = PARSE_QUESTION_PROMPT.format(question=question)
        
        # Get structured response
        response = llm.invoke_structured(
            prompt,
            response_format={"type": "json_object"}
        )
        
        intent = response.get('intent', 'filter')
        entities = response.get('entities', [])
        metrics = response.get('metrics', [])
        filters = response.get('filters', {})
        limit = response.get('limit')
        grouping = response.get('grouping')
        
    except Exception as e:
        # Fallback to rule-based parsing if LLM fails
        error_msg = f"LLM parsing failed, using fallback: {str(e)}"
        
        # Simple fallback
        question_lower = question.lower()
        
        # Detect intent
        if any(word in question_lower for word in ['top', 'best', 'highest', 'most', 'rank']):
            intent = 'rank'
        elif any(word in question_lower for word in ['count', 'how many']):
            intent = 'count'
        elif any(word in question_lower for word in ['average', 'avg', 'mean', 'sum']):
            intent = 'aggregate'
        else:
            intent = 'filter'
        
        entities = []
        metrics = []
        filters = {}
        limit = None
        grouping = None
    
    # Early ambiguity detection: If no entities found, mark as ambiguous
    needs_clarification = False
    ambiguity_reason = None
    if not entities and not metrics:
        needs_clarification = True
        ambiguity_reason = "No specific table or metric identified in question"
    
    result = {
        'intent': intent,
        'entities': entities,
        'metrics': metrics,
        'filters': filters,
        'limit': limit,
        'grouping': grouping,
        'needs_clarification': needs_clarification,
        'ambiguity_reason': ambiguity_reason
    }
    
    # Add error if fallback was used
    if 'error_msg' in locals():
        result['error'] = error_msg
    
    return result

