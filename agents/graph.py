from langgraph.graph import StateGraph, END

from agents.state import TextToSQLState

# Import all nodes
from agents.nodes.start import start
from agents.nodes.fail import fail
from agents.nodes.parse_question import parse_question
from agents.nodes.detect_ambiguity import detect_ambiguity
from agents.nodes.clarification_request import clarification_request
from agents.nodes.load_schema import load_schema
from agents.nodes.schema_pruning import schema_pruning
from agents.nodes.resolve_synonyms import resolve_synonyms
from agents.nodes.query_planning import query_planning
from agents.nodes.join_resolution import join_resolution
from agents.nodes.sql_generation import sql_generation
from agents.nodes.sql_safety_validation import sql_safety_validation
from agents.nodes.sql_static_validation import sql_static_validation
from agents.nodes.sql_execution import sql_execution
from agents.nodes.error_classifier import error_classifier
from agents.nodes.sql_repair import sql_repair
from agents.nodes.repair_decision import repair_decision
from agents.nodes.explain_reasoning import explain_reasoning
from agents.nodes.build_response import build_response
from agents.nodes.log_trace import log_trace

from agents.conditions import (
    ambiguity_router,
    clarification_router,
    safety_router,
    static_validation_router,
    execution_router,
    repair_router,
)


def build_graph():
    g = StateGraph(TextToSQLState)

    # ---- Nodes ----
    g.add_node("start", start)
    g.add_node("fail", fail)
    g.add_node("parse_question", parse_question)
    g.add_node("detect_ambiguity", detect_ambiguity)
    g.add_node("clarification_request", clarification_request)
    g.add_node("load_schema", load_schema)
    g.add_node("schema_pruning", schema_pruning)
    g.add_node("resolve_synonyms", resolve_synonyms)
    g.add_node("query_planning", query_planning)
    g.add_node("join_resolution", join_resolution)
    g.add_node("sql_generation", sql_generation)
    g.add_node("sql_safety_validation", sql_safety_validation)
    g.add_node("sql_static_validation", sql_static_validation)
    g.add_node("sql_execution", sql_execution)
    g.add_node("error_classifier", error_classifier)
    g.add_node("sql_repair", sql_repair)
    g.add_node("repair_decision", repair_decision)
    g.add_node("explain_reasoning", explain_reasoning)
    g.add_node("build_response", build_response)
    g.add_node("log_trace", log_trace)

    # ---- Entry ----
    g.set_entry_point("start")

    # ---- Flow ----
    g.add_edge("start", "parse_question")
    g.add_edge("parse_question", "detect_ambiguity")
    
    g.add_conditional_edges(
        "detect_ambiguity",
        ambiguity_router,
        {
            "clarify": "clarification_request",
            "continue": "load_schema",
            "fail": "fail",  # Terminal path if clarification limit exceeded
        },
    )
    
    # Force clarification to route to fail if max attempts exceeded, otherwise proceed
    g.add_conditional_edges(
        "clarification_request",
        clarification_router,
        {
            "fail": "fail",
            "parse_question": "parse_question",
        },
    )
    g.add_edge("load_schema", "schema_pruning")
    g.add_edge("schema_pruning", "resolve_synonyms")
    g.add_edge("resolve_synonyms", "query_planning")
    
    # Validate logical plan before generating SQL
    g.add_edge("query_planning", "sql_safety_validation")
    
    g.add_conditional_edges(
        "sql_safety_validation",
        safety_router,
        {
            "continue": "sql_static_validation",
            "fail": "fail",
        },
    )
    
    g.add_conditional_edges(
        "sql_static_validation",
        static_validation_router,
        {
            "join_resolution": "join_resolution",  # Continue to join resolution if plan is valid
            "classify_error": "error_classifier",
        },
    )
    
    g.add_edge("join_resolution", "sql_generation")
    g.add_edge("sql_generation", "sql_execution")
    
    g.add_conditional_edges(
        "sql_execution",
        execution_router,
        {
            "explain": "explain_reasoning",
            "classify_error": "error_classifier",
        },
    )
    
    g.add_edge("error_classifier", "sql_repair")
    g.add_edge("sql_repair", "repair_decision")
    
    g.add_conditional_edges(
        "repair_decision",
        repair_router,
        {
            "retry": "query_planning",  # Loop back to query planning to regenerate plan
            "fail": "fail",
        },
    )
    
    g.add_edge("explain_reasoning", "build_response")
    g.add_edge("build_response", "log_trace")
    g.add_edge("log_trace", END)
    g.add_edge("fail", END)

    # Compile the graph (recursion limit set at invocation time)
    return g.compile()