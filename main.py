"""
Main entry point for Text-to-SQL agent.

CLI interface that takes natural language questions and outputs JSON.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# Find .env file in the same directory as this script
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from agents.graph import build_graph
from agents.state import TextToSQLState


def run_agent(question: str, max_retries: int = 3) -> dict:
    """
    Run the Text-to-SQL agent with a question.
    
    Args:
        question: User's natural language question
        max_retries: Maximum number of retry attempts
        
    Returns:
        JSON response with question, sql, result_preview, explanation
    """
    # Build the graph
    graph = build_graph()
    
    # Initialize state
    initial_state: TextToSQLState = {
        "input": question,
        "question": question,
        "max_retries": max_retries,
    }
    
    # Run the graph with recursion limit
    try:
        final_state = graph.invoke(
            initial_state,
            config={"recursion_limit": 50}
        )
        
        # Extract response from state
        response = final_state.get("response", {})
        
        # Format output to match exact specification
        output = {
            "question": response.get("question", question),
            "sql": response.get("sql", ""),
            "result_preview": response.get("result_preview", []),
            "explanation": response.get("explanation", "Query executed successfully.")
        }
        
        # If there's an error, include it in explanation
        if "error" in response:
            error_info = response["error"]
            if isinstance(error_info, dict):
                error_msg = error_info.get("message", str(error_info))
            else:
                error_msg = str(error_info)
            output["explanation"] = f"Query failed: {error_msg}"
            output["sql"] = response.get("sql", "")
        
        return output
        
    except Exception as e:
        # Return error response
        return {
            "question": question,
            "sql": "",
            "result_preview": [],
            "explanation": f"Agent execution failed: {str(e)}"
        }


def run_interactive():
    """Run the agent in interactive CLI mode."""
    print("=" * 60)
    print("Text-to-SQL Agent - Interactive Mode")
    print("=" * 60)
    print("Enter your questions (type 'exit', 'quit', or 'q' to stop)")
    print("Type 'help' for usage examples")
    print()
    
    # Check for required environment variables (optional warning)
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  Warning: No LLM API key found.", file=sys.stderr)
        print("   Add OPENAI_API_KEY or ANTHROPIC_API_KEY to your .env file.", file=sys.stderr)
        print("   Example: OPENAI_API_KEY=sk-...", file=sys.stderr)
        print("   The agent will use fallback rule-based methods.", file=sys.stderr)
        print()
    
    # Build graph once (reuse for all queries)
    try:
        graph = build_graph()
    except Exception as e:
        print(f"❌ Failed to build graph: {str(e)}", file=sys.stderr)
        sys.exit(1)
    
    while True:
        try:
            # Get user input
            question = input("\n> ").strip()
            
            # Handle commands
            if question.lower() in ['exit', 'quit', 'q']:
                print("\nGoodbye!")
                break
            
            if question.lower() == 'help':
                print("\nUsage examples:")
                print("  Show me the top 5 most popular songs in 2018")
                print("  Count albums by year")
                print("  List all artists")
                print("  What are the most popular songs?")
                continue
            
            if not question:
                continue
            
            print("\nProcessing...")
            
            # Initialize state
            initial_state: TextToSQLState = {
                "input": question,
                "question": question,
                "max_retries": 3,
            }
            
            # Run the graph with recursion limit
            try:
                final_state = graph.invoke(
                    initial_state,
                    config={"recursion_limit": 50}
                )
                
                # Extract response
                response = final_state.get("response", {})
                
                # Format output
                output = {
                    "question": response.get("question", question),
                    "sql": response.get("sql", ""),
                    "result_preview": response.get("result_preview", []),
                    "explanation": response.get("explanation", "Query executed successfully.")
                }
                
                # Handle errors
                if "error" in response:
                    error_info = response["error"]
                    if isinstance(error_info, dict):
                        error_msg = error_info.get("message", str(error_info))
                    else:
                        error_msg = str(error_info)
                    output["explanation"] = f"Query failed: {error_msg}"
                    output["sql"] = response.get("sql", "")
                
                # Output JSON
                print("\n" + json.dumps(output, indent=2))
                
            except Exception as e:
                error_output = {
                    "question": question,
                    "sql": "",
                    "result_preview": [],
                    "explanation": f"Agent execution failed: {str(e)}"
                }
                print("\n" + json.dumps(error_output, indent=2))
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except EOFError:
            print("\n\nGoodbye!")
            break


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Text-to-SQL Agent - Convert natural language to SQL queries",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (default)
  python main.py
  
  # Single question mode
  python main.py "Show me the top 5 most popular songs in 2018"
  
  # With custom retries
  python main.py "Count albums by year" --max-retries 5
        """
    )
    
    parser.add_argument(
        "question",
        nargs="?",
        help="Natural language question to convert to SQL (optional, defaults to interactive mode)"
    )
    
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum number of retry attempts (default: 3)"
    )
    
    args = parser.parse_args()
    
    # If question provided, run single query mode
    if args.question:
        try:
            output = run_agent(args.question, args.max_retries)
            print(json.dumps(output, indent=2))
            
            # Exit with error code if query failed
            if "failed" in output.get("explanation", "").lower():
                sys.exit(1)
        except KeyboardInterrupt:
            print("\nInterrupted.", file=sys.stderr)
            sys.exit(130)
        except Exception as e:
            error_output = {
                "question": args.question,
                "sql": "",
                "result_preview": [],
                "explanation": f"Error: {str(e)}"
            }
            print(json.dumps(error_output, indent=2))
            sys.exit(1)
    else:
        # Default to interactive mode
        run_interactive()


if __name__ == "__main__":
    main()