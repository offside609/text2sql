"""
Build Response Node - Produce final output JSON.
"""

from typing import Dict, Any


def build_response(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produce final output JSON.
    
    Responsibility:
    - Produce final output with:
      {
        "question": "...",
        "sql": "...",
        "result_preview": [...],
        "explanation": "..."
      }
    
    Args:
        state: Current graph state
        
    Returns:
        State with final response formatted
    """
    question = state.get('question', '')
    sql = state.get('validated_sql') or state.get('sql', '')
    result = state.get('result', [])
    explanation = state.get('explanation', 'Query executed successfully.')
    execution_stats = state.get('execution_stats', {})
    
    # Create result preview (first 10 rows)
    result_preview = result[:10] if result else []
    
    # Build final response
    return {
        'response': {
            "question": question,
            "sql": sql,
            "result_preview": result_preview,
            "total_rows": len(result),
            "execution_stats": execution_stats,
            "explanation": explanation,
            "retry_count": state.get('retry_count', 0)
        }
    }

