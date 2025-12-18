"""
Detect Ambiguity Node - Detect missing information using LLM.
"""

from typing import Dict, Any
import json
from agents.tools import get_llm, DETECT_AMBIGUITY_PROMPT


def detect_ambiguity(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect missing information that needs clarification using LLM.
    
    Responsibility:
    - Detect missing info using LLM:
      - Which table?
      - Which date range?
      - Which metric?
    
    Writes:
    - needs_clarification: bool
    - ambiguity_reason: str (if ambiguous)
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with ambiguity detection results
    """
    question = state.get('question', '')
    
    # Build parsed components summary
    parsed_components = {
        'intent': state.get('intent'),
        'entities': state.get('entities', []),
        'metrics': state.get('metrics', []),
        'filters': state.get('filters', {}),
        'limit': state.get('limit'),
    }
    
    try:
        # Use LLM to detect ambiguity
        llm = get_llm()
        
        prompt = DETECT_AMBIGUITY_PROMPT.format(
            question=question,
            parsed_components=json.dumps(parsed_components, indent=2)
        )
        
        response = llm.invoke_structured(
            prompt,
            response_format={"type": "json_object"}
        )
        
        needs_clarification = response.get('needs_clarification', False)
        ambiguity_reason = response.get('ambiguity_reason')
        missing_info = response.get('missing_info', [])
        
    except Exception as e:
        # Fallback to rule-based detection
        error_msg = f"LLM ambiguity detection failed, using fallback: {str(e)}"
        
        # Simple fallback
        entities = state.get('entities', [])
        metrics = state.get('metrics', [])
        intent = state.get('intent', '')
        
        needs_clarification = False
        ambiguity_reasons = []
        
        if not entities:
            needs_clarification = True
            ambiguity_reasons.append("No table/entity specified")
        
        if intent in ['rank', 'aggregate'] and not metrics:
            needs_clarification = True
            ambiguity_reasons.append("Ranking/aggregation requested but no metric specified")
        
        ambiguity_reason = '; '.join(ambiguity_reasons) if ambiguity_reasons else None
        missing_info = ambiguity_reasons
    
    result = {
        'needs_clarification': needs_clarification,
        'ambiguity_reason': ambiguity_reason,
        'missing_info': missing_info
    }
    
    # Add error if fallback was used
    if 'error_msg' in locals():
        result['error'] = error_msg
    
    return result

