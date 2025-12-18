"""
Clarification Request Node - Ask user for clarification using LLM.
"""

from typing import Dict, Any
from agents.tools import get_llm, CLARIFICATION_REQUEST_PROMPT


def clarification_request(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ask user for clarification using LLM.
    
    In CLI mode, prints clarification question and waits for user input.
    In HTTP mode, this would return the clarification for the API to handle.
    
    Responsibility:
    - Ask user for clarification (CLI/HTTP)
    - Generate natural clarification question using LLM
    - Increment clarification attempt counter
    - Hard stop after max attempts
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with clarification request
    """
    # Increment clarification attempts
    clarification_attempts = state.get('clarification_attempts', 0) + 1
    max_attempts = state.get('max_clarification_attempts', 3)
    
    # Track node visit
    node_visit_count = state.get('node_visit_count', {}).copy()
    node_visit_count['clarification_request'] = node_visit_count.get('clarification_request', 0) + 1
    
    # Hard stop after max attempts
    if clarification_attempts > max_attempts:
        return {
            'clarification_attempts': clarification_attempts,
            'node_visit_count': node_visit_count,
            'error': f'Max clarification attempts ({max_attempts}) exceeded',
            'error_type': 'clarification_limit_exceeded',
            'needs_clarification': False
        }
    
    question = state.get('question', '')
    ambiguity_reason = state.get('ambiguity_reason', 'Additional information needed')
    missing_info = state.get('missing_info', [])
    
    try:
        # Use LLM to generate clarification question
        llm = get_llm()
        
        prompt = CLARIFICATION_REQUEST_PROMPT.format(
            question=question,
            ambiguity_reason=ambiguity_reason,
            missing_info=', '.join(missing_info) if missing_info else 'None'
        )
        
        clarification_text = llm.invoke(prompt)
        
    except Exception as e:
        # Fallback to template-based clarification
        clarification_text = f"Please clarify: {ambiguity_reason}"
    
    # Store clarification request
    clarification = {
        "type": "clarification_request",
        "question": question,
        "ambiguity": ambiguity_reason,
        "request": clarification_text,
    }
    
    # In CLI mode: Print clarification and wait for user input
    print("\n" + "="*60)
    print("❓ Clarification Needed")
    print("="*60)
    print(f"\n{clarification_text}\n")
    
    # Get user's clarification response
    result = {
        'clarification_attempts': clarification_attempts,
        'node_visit_count': node_visit_count,
        'clarification': clarification,
        'needs_clarification': False
    }
    
    try:
        user_response = input("Your answer: ").strip()
        
        if not user_response:
            # If empty response, proceed with best-effort
            print("⚠️  No clarification provided. Proceeding with best-effort parsing...")
            result['clarification_response'] = None
        else:
            # Update question with clarification
            updated_question = f"{question} ({clarification_text} Answer: {user_response})"
            result['question'] = updated_question
            result['clarification_response'] = user_response
            print(f"✓ Clarification received. Updated question: {updated_question}\n")
            
    except (KeyboardInterrupt, EOFError):
        # Handle interruption gracefully
        print("\n⚠️  Clarification interrupted. Proceeding with best-effort parsing...")
        result['clarification_response'] = None
    
    return result