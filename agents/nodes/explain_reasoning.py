"""
Explain Reasoning Node - Produce short explanation using LLM.
"""

from typing import Dict, Any
from agents.tools import get_llm, EXPLAIN_REASONING_PROMPT


def explain_reasoning(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produce short explanation of the query using LLM.
    
    Responsibility:
    - Produce short explanation using LLM
    - No chain-of-thought leakage
    - Human-readable summary
    
    Writes:
    - explanation: Human-readable explanation string
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with explanation
    """
    question = state.get('question', '')
    sql = state.get('validated_sql') or state.get('sql', '')
    result = state.get('result', [])
    execution_stats = state.get('execution_stats', {})
    
    result_count = len(result)
    execution_time = execution_stats.get('time_ms', 0)
    
    try:
        # Use LLM to generate explanation
        llm = get_llm()
        
        prompt = EXPLAIN_REASONING_PROMPT.format(
            question=question,
            sql=sql,
            result_count=result_count,
            execution_time=execution_time
        )
        
        explanation = llm.invoke(prompt).strip()
        
    except Exception as e:
        # Fallback to template-based explanation
        error_msg = f"LLM explanation failed, using fallback: {str(e)}"
        
        intent = state.get('intent', 'filter')
        entities = state.get('entities', [])
        
        explanation_parts = []
        
        if intent == 'rank':
            explanation_parts.append(f"Ranked {', '.join(entities) if entities else 'items'}")
        elif intent == 'count':
            explanation_parts.append(f"Counted {', '.join(entities) if entities else 'items'}")
        else:
            explanation_parts.append(f"Retrieved data for {', '.join(entities) if entities else 'items'}")
        
        if result:
            explanation_parts.append(f"Returned {result_count} result{'s' if result_count != 1 else ''}")
        else:
            explanation_parts.append("No results found")
        
        if execution_time > 0:
            explanation_parts.append(f"Executed in {execution_time:.2f}ms")
        
        explanation = '. '.join(explanation_parts) + '.'
    
    result = {'explanation': explanation}
    
    # Add error if fallback was used
    if 'error_msg' in locals():
        result['error'] = error_msg
    
    return result

