### Single Query Mode

Run a single query:

```bash
python3 main.py "Show me the top 10 pop songs from 2018"
```

### With Custom Retries

```bash
python3 main.py "Count albums by year" --max-retries 5
```

## Usage Examples

### Example 1: Simple Query

```bash
python3 main.py "List 10 songs"
```

**Output:**
```json
{
  "question": "List 10 songs",
  "sql": "SELECT * FROM songs LIMIT 10",
  "result_preview": [...],
  "explanation": "Retrieved 10 songs from the database."
}
```

### Example 2: Filtered Query

```bash
python3 main.py "Show me pop songs from 2018"
```

### Example 3: Aggregation

```bash
python3 main.py "Count albums by year"
```

### Example 4: Ranking

```bash
python3 main.py "What are the top 5 most popular artists?"
```

## How It Works

The agent uses a LangGraph workflow with 20 specialized nodes:

### 1. **Entry & Control**
- `start`: Initialize state
- `fail`: Graceful error handling

### 2. **Language Understanding**
- `parse_question`: Extract intent, entities, metrics, filters
- `detect_ambiguity`: Identify missing information
- `clarification_request`: Ask user for clarification

### 3. **Schema & Grounding**
- `load_schema`: Introspect database schema
- `schema_pruning`: Select relevant tables/columns
- `resolve_synonyms`: Map user terms to schema terms

### 4. **Planning**
- `query_planning`: Create logical query plan
- `join_resolution`: Determine join strategy

### 5. **SQL Generation & Safety**
- `sql_generation`: Convert plan to SQL
- `sql_safety_validation`: Security checks (SELECT-only, no DDL/DML)
- `sql_static_validation`: Validate against schema

### 6. **Execution**
- `sql_execution`: Execute query with timeout

### 7. **Repair & Recovery**
- `error_classifier`: Classify error types
- `sql_repair`: Fix SQL using LLM
- `repair_decision`: Decide retry or fail

### 8. **Output**
- `explain_reasoning`: Generate natural language explanation
- `build_response`: Format final JSON output
- `log_trace`: Log execution trace

## Configuration

### Max Retries

Control how many times the agent retries failed queries:

```python
# In main.py or your code
run_agent(question, max_retries=5)
```

### Max Clarification Attempts

Control how many clarification questions to ask:

```python
initial_state = {
    "question": question,
    "max_clarification_attempts": 2  # Default is 1
}
```

### Recursion Limit

The graph has a recursion limit to prevent infinite loops:

```python
graph.invoke(state, config={"recursion_limit": 50})
```

## Troubleshooting

### Database Not Found

**Error**: `Database not found at ...`

**Solution**: Run the data loader first:
```bash
python3 -m db.load_sqlite
```

### No LLM API Key

**Warning**: `⚠️ Warning: No LLM API key found...`

**Solution**: Add your API key to `.env`:
```bash
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...
```

### Module Not Found

**Error**: `ModuleNotFoundError: No module named 'pandas'`

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

### Recursion Limit Exceeded

**Error**: `Recursion limit of 50 reached`

**Solution**: This usually indicates a loop in the graph. Check:
- Clarification attempts aren't exceeding max
- Error states are being cleared in repair nodes
- All conditional routers have terminal paths

### Query Fails After Clarification

**Issue**: Agent asks for clarification but query still fails

**Solution**: The prompts may need adjustment. Check:
- `PARSE_QUESTION_PROMPT` handles clarified questions
- `DETECT_AMBIGUITY_PROMPT` is less strict after clarifications
- Schema information is available to the LLM

## Advanced Usage

### Using LangSmith Tracing

1. Sign up at [smith.langchain.com](https://smith.langchain.com)
2. Get your API key
3. Add to `.env`:
   ```
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY=lsv2-...
   LANGCHAIN_PROJECT=text-to-sql-agent
   ```
4. Run queries - traces will appear in LangSmith dashboard

### Programmatic Usage

```python
from agents.graph import build_graph
from agents.state import TextToSQLState

# Build graph
graph = build_graph()

# Initialize state
state: TextToSQLState = {
    "input": "Show me top 10 songs",
    "question": "Show me top 10 songs",
    "max_retries": 3,
}

# Run graph
result = graph.invoke(
    state,
    config={"recursion_limit": 50}
)

# Get response
response = result.get("response", {})
print(response["sql"])
print(response["result_preview"])
```

### Custom LLM Configuration

Edit `agents/tools/llm_client.py` to customize:
- Model selection (GPT-4, Claude, etc.)
- Temperature
- Max tokens
- Other LLM parameters

## Dataset Information

### musicoset_popularity (6 tables)
- `album_chart`: Album chart rankings
- `album_pop`: Album popularity metrics
- `artist_chart`: Artist chart rankings
- `artist_pop`: Artist popularity metrics
- `song_chart`: Song chart rankings
- `song_pop`: Song popularity metrics

### musicoset_metadata (5 tables)
- `albums`: Album information
- `artists`: Artist information
- `songs`: Song information
- `releases`: Release information
- `tracks`: Track information

### musicoset_songfeatures (2 tables)
- `acoustic_features`: Audio features (tempo, energy, etc.)
- `lyrics`: Song lyrics

## Contributing

When adding new features:
1. Follow the existing node structure
2. Return partial state updates (not full state)
3. Add appropriate error handling
4. Update this README if needed

## License

[Add your license here]

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review LangGraph documentation
3. Check LangSmith traces for debugging

---

**Happy Querying! 🎵**

