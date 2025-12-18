## Graph Logic Flow & Routing

The Text-to-SQL agent uses a 20-node LangGraph workflow with conditional routing at key decision points. Below is the complete logic flow with all routing conditions.

### Complete Node Flow

┌─────────┐
│ START │ ── Initialize state, thread_id, retry_count, clarification_attempts
└────┬────┘
│
▼
┌─────────────────┐
│ parse_question │ ── Extract intent, entities, metrics, filters, limit
└────┬────────────┘
│
▼
┌──────────────────┐
│ detect_ambiguity │ ── Check if question needs clarification
└────┬─────────────┘
│
├─────────────────────────────────────────────────────────┐
│ │
│ [ambiguity_router] │
│ │
├─► "clarify" ──► ┌──────────────────────┐ │
│ │clarification_request │ │
│ └──────┬───────────────┘ │
│ │ │
│ │ [clarification_router] │
│ │ │
│ ├─► "fail" ──► [FAIL] ──► END │
│ │ │
│ └─► "parse_question" ───────────┘
│ │
├─► "continue" ──────────────────────────────────────────┤
│ │
└─► "fail" ──► [FAIL] ──► END │
│
┌─────────────────────────────────────────────────────────┘
│
▼
┌──────────────┐
│ load_schema │ ── Load tables, columns, foreign keys, indexes
└──────┬───────┘
│
▼
┌─────────────────┐
│ schema_pruning │ ── Reduce schema to relevant tables/columns (LLM)
└──────┬──────────┘
│
▼
┌──────────────────┐
│ resolve_synonyms │ ── Map user terms → schema terms (LLM)
└──────┬───────────┘
│
▼
┌─────────────────┐
│ query_planning │ ── Create logical plan: select, from, where, order_by, limit
└──────┬──────────┘
│
▼
┌──────────────────────┐
│ sql_safety_validation │ ── Validate logical plan safety (SELECT-only, LIMIT, etc.)
└──────┬───────────────┘
│
├─────────────────────────────────────┐
│ │
│ [safety_router] │
│ │
├─► "continue" ───────────────────────┤
│ │
└─► "fail" ──► [FAIL] ──► END │
│
┌─────────────────────────────────────┘
│
▼
┌──────────────────────┐
│ sql_static_validation │ ── Validate logical plan against schema (tables/columns exist)
└──────┬───────────────┘
│
├─────────────────────────────────────┐
│ │
│ [static_validation_router] │
│ │
├─► "join_resolution" ────────────────┤
│ │
└─► "classify_error" ──► [ERROR PATH] │
│
┌─────────────────────────────────────┘
│
▼
┌─────────────────┐
│ join_resolution │ ── Determine join strategy (LLM)
└──────┬──────────┘
│
▼
┌─────────────────┐
│ sql_generation │ ── Convert logical plan → SQL query (LLM)
└──────┬──────────┘
│
▼
┌─────────────────┐
│ sql_execution │ ── Execute SQL query
└──────┬───────────┘
│
├─────────────────────────────────────┐
│ │
│ [execution_router] │
│ │
├─► "explain" ───────────────────────┤
│ │
└─► "classify_error" ──► [ERROR PATH] │
│
┌─────────────────────────────────────┘
│
▼
┌──────────────────┐
│ explain_reasoning │ ── Generate natural language explanation (LLM)
└──────┬───────────┘
│
▼
┌─────────────────┐
│ build_response │ ── Format final JSON output
└──────┬──────────┘
│
▼
┌─────────────┐
│ log_trace │ ── Log execution trace
└──────┬──────┘
│
▼
END
═══════════════════════════════════════════════════════════════
ERROR PATH (Repair & Recovery):
┌──────────────────┐
│ error_classifier │ ── Classify error type (syntax, missing_column, etc.)
└──────┬───────────┘
│
▼
┌─────────────┐
│ sql_repair │ ── Fix SQL using LLM + error message
└──────┬───────┘
│
▼
┌──────────────────┐
│ repair_decision │ ── Decide: retry or fail
└──────┬───────────┘
│
├─────────────────────────────────────┐
│ │
│ [repair_router] │
│ │
├─► "retry" ──► [BACK TO query_planning]
│ │
└─► "fail" ──► [FAIL] ──► END │