# Text-to-SQL Agent

A production-grade Text-to-SQL agent built with LangGraph that converts natural language questions into SQL queries. The agent uses LLMs for language understanding, schema grounding, query planning, and SQL generation, with robust error handling and repair mechanisms.

## Features

- **Natural Language to SQL**: Convert questions like "Show me the top 10 pop songs from 2018" into SQL queries
- **Multi-Dataset Support**: Works with musicoset_popularity, musicoset_metadata, and musicoset_songfeatures datasets
- **Intelligent Schema Understanding**: Automatic schema introspection, foreign key detection, and join graph generation
- **Robust Error Handling**: Automatic SQL repair and retry mechanisms
- **Safety Validation**: Built-in security checks to prevent unsafe queries
- **Clarification Support**: Asks for clarification when queries are ambiguous
- **LangSmith Integration**: Built-in tracing support for observability

## Project Structure

```
sqlagent/
├── agents/              # LangGraph agent implementation
│   ├── nodes/          # Individual graph nodes (20 nodes)
│   ├── conditions.py  # Conditional routing logic
│   ├── graph.py       # Main graph definition
│   ├── state.py       # State schema
│   └── tools/         # LLM clients and prompts
├── db/                 # Database utilities
│   ├── connection.py  # Database connection management
│   ├── load_sqlite.py # CSV to SQLite loader
│   └── schema.py      # Schema introspection utilities
├── dataset/            # CSV data files
│   ├── musicoset_popularity/
│   ├── musicoset_metadata/
│   └── musicoset_songfeatures/
├── data/               # Generated database
│   └── db/
│       └── musicoset_popularity.sqlite
├── main.py            # CLI entry point
├── requirements.txt   # Python dependencies
└── .env               # Environment variables (API keys)
```

## Prerequisites

- Python 3.9 or higher
- pip or conda
- LLM API key (OpenAI or Anthropic)

## Installation

### 1. Clone or Navigate to the Project

```bash
cd /path/to/sqlagent
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- `pandas>=2.0.0` - Data loading
- `openai>=1.0.0` - OpenAI LLM support
- `anthropic>=0.18.0` - Anthropic LLM support
- `langgraph>=0.0.40` - Graph-based agent framework
- `langchain>=0.1.0` - LangChain integration
- `python-dotenv>=1.0.1` - Environment variable management

### 3. Set Up Environment Variables

Create a `.env` file in the `sqlagent/` directory:

```bash
# LLM API Keys (at least one required)
OPENAI_API_KEY=sk-your-openai-key-here
# OR
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# LangSmith Tracing (optional but recommended)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2-your-langsmith-key-here
LANGCHAIN_PROJECT=text-to-sql-agent
```

**Note**: The agent will work with fallback rule-based methods if no LLM API key is provided, but LLM integration provides much better results.

## Loading the Dataset

The project includes three datasets that need to be loaded into SQLite:

1. **musicoset_popularity**: Chart and popularity data (6 tables)
2. **musicoset_metadata**: Album, artist, and song metadata (5 tables)
3. **musicoset_songfeatures**: Acoustic features and lyrics (2 tables)

### Step 1: Verify Dataset Files

Ensure all CSV files are present in the `dataset/` directory:

```bash
# Check dataset structure
ls -R dataset/
```

You should see:
- `dataset/musicoset_popularity/*.csv` (6 files)
- `dataset/musicoset_metadata/*.csv` (5 files)
- `dataset/musicoset_songfeatures/*.csv` (2 files)

### Step 2: Load Data into SQLite

Run the data loader:

```bash
python3 -m db.load_sqlite
```

Or from the project root:

```bash
cd sqlagent
python3 -m db.load_sqlite
```

This will:
- Create the SQLite database at `data/db/musicoset_popularity.sqlite`
- Load all 13 CSV files into tables
- Create indexes on foreign keys and commonly queried columns
- Display progress and row counts for each table

**Expected Output:**
```
============================================================
Loading all dataset data into SQLite
============================================================
Loading album_chart.csv into table 'album_chart'...
  ✓ Loaded 471,706 rows into 'album_chart'
...
✓ Database created successfully at: .../musicoset_popularity.sqlite
============================================================
```

### Step 3: Verify Database

You can verify the database was created:

```bash
sqlite3 data/db/musicoset_popularity.sqlite ".tables"
```

Should show all 13 tables.

## Running the Agent

### Interactive Mode (Recommended)

Start the interactive CLI:

```bash
python3 main.py
```

This will start an interactive session where you can ask questions:

```
============================================================
Text-to-SQL Agent - Interactive Mode
============================================================
Enter your questions (type 'exit', 'quit', or 'q' to stop)
Type 'help' for usage examples

> Show me the top 10 pop songs from 2018
```

