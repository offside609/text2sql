"""
Prompt templates for Text-to-SQL agent nodes.
"""

# Parse Question Prompt
PARSE_QUESTION_PROMPT = """You are a natural language understanding system for a Text-to-SQL agent.

Analyze the following user question and extract structured information. Fix any typos or grammatical errors in the question.

User Question: {question}

Extract and return a JSON object with:
- intent: The main intent ("rank", "count", "filter", "aggregate", "list")
- entities: List of entities/tables mentioned (e.g., ["artist", "album", "song"])
- metrics: List of metrics/columns mentioned (e.g., ["followers", "popularity", "score"])
- filters: Dictionary of filters (e.g., {{"year": 2018, "is_pop": true}})
- limit: Number limit if specified (e.g., "top 5" -> 5)
- grouping: Group by field if mentioned (e.g., "by year" -> "year")

Return only valid JSON."""

# Detect Ambiguity Prompt
DETECT_AMBIGUITY_PROMPT = """You are analyzing a user question for a Text-to-SQL system to detect ambiguities.

User Question: {question}
Parsed Components: {parsed_components}
Clarification Attempts: {clarification_attempts}

IMPORTANT: 
- If clarifications have already been provided (check for "(Answer: ...)" in the question), be less strict

- Only flag as ambiguous if truly critical information is missing

Determine if the question needs clarification. Check for:
1. Missing table/entity specification (CRITICAL - must have at least one)
2. Ambiguous metrics or columns (only if intent requires metrics and none found)
3. Missing date/year ranges when time-based queries are implied (only if critical)
4. Multiple possible interpretations (only if truly ambiguous)

Return JSON with:
- needs_clarification: boolean (be conservative - only true if absolutely necessary)
- ambiguity_reason: string explaining what's ambiguous (null if not ambiguous)
- missing_info: list of missing information types

Return only valid JSON."""

# Clarification Request Prompt
CLARIFICATION_REQUEST_PROMPT = """Generate a natural, helpful clarification question for the user.

Original Question: {question}
Ambiguity: {ambiguity_reason}
Missing Info: {missing_info}

Generate a single, clear question that asks for the missing information in a friendly way.
Return only the clarification question text, no JSON."""

# Schema Pruning Prompt
SCHEMA_PRUNING_PROMPT = """You are selecting relevant database tables and columns for a SQL query.

User Question: {question}
Parsed Intent: {intent}
Entities Mentioned: {entities}
Metrics Mentioned: {metrics}

Available Tables: {all_tables}

For each table, determine if it's relevant to the query. Return JSON with:
- active_tables: List of relevant table names
- reasoning: Brief explanation for each selected table

Return only valid JSON."""

# Resolve Synonyms Prompt
RESOLVE_SYNONYMS_PROMPT = """Map user terms to actual database schema terms.

User Question: {question}
User Terms: {user_terms}
Available Schema: {schema_info}

Map each user term to the correct table/column name in the schema.
Return JSON with:
- resolved_entities: {{"user_term": "schema_table"}}
- resolved_metrics: {{"user_term": {{"table": "table_name", "column": "column_name"}}}}

Return only valid JSON."""

# Query Planning Prompt
QUERY_PLANNING_PROMPT = """Create a logical query plan from the user question and schema.

User Question: {question}
Intent: {intent}
Resolved Entities: {resolved_entities}
Resolved Metrics: {resolved_metrics}
Filters: {filters}
Schema: {schema_info}

Create a logical plan (not SQL yet) with:
- select: List of columns to select (fully qualified: table.column)
- from: List of tables to query
- where: Dictionary of WHERE conditions
- order_by: ORDER BY clause if needed (e.g., "column DESC")
- limit: LIMIT value
- group_by: GROUP BY column if needed

Return only valid JSON."""

# Join Resolution Prompt
JOIN_RESOLUTION_PROMPT = """Determine the best join strategy for a multi-table query.

Tables to Join: {tables}
Foreign Keys: {foreign_keys}
Join Graph: {join_graph}

Determine the optimal join path. Return JSON with:
- join_plan: List of joins, each with:
  - type: "INNER", "LEFT", etc.
  - from_table: Source table
  - to_table: Target table
  - condition: Join condition (e.g., "table1.id = table2.foreign_id")

Return only valid JSON."""

# SQL Generation Prompt
SQL_GENERATION_PROMPT = """Generate SQL query from logical plan.

Logical Plan: {logical_plan}
Join Plan: {join_plan}
Schema: {schema_info}

Generate a valid SQLite SELECT query. Rules:
1. Fully qualify all columns (table.column)
2. Include all joins from join_plan
3. Add WHERE conditions from logical_plan
4. Include ORDER BY if specified
5. Include LIMIT (default 100 if not specified)
6. Use proper SQLite syntax

Return only the SQL query, no explanation."""

# SQL Repair Prompt
SQL_REPAIR_PROMPT = """Fix a SQL query that failed execution.

Original SQL: {sql}
Error Message: {error}
Error Type: {error_type}
Schema: {schema_info}
Original Question: {question}

Analyze the error and generate a corrected SQL query.
Return JSON with:
- repaired_sql: The corrected SQL query
- fix_explanation: Brief explanation of what was fixed

Return only valid JSON."""

# Explain Reasoning Prompt
EXPLAIN_REASONING_PROMPT = """Generate a natural language explanation of the SQL query execution.

User Question: {question}
Generated SQL: {sql}
Result Count: {result_count}
Execution Time: {execution_time}ms

Generate a brief, user-friendly explanation (1-2 sentences) of what the query did and what results were returned.
Return only the explanation text, no JSON."""

