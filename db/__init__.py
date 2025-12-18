"""
Database utilities for SQLite operations.

This package provides:
- load_sqlite: CSV to SQLite loading
- connection: Database connection and query execution
- schema: Schema introspection and description
"""

from .connection import DatabaseConnection, get_db
from .schema import (
    get_table_schema,
    get_all_schemas,
    get_schema_description,
    get_table_relationships,
    get_schema_summary,
    get_foreign_keys,
    get_all_foreign_keys,
    get_column_to_table_index,
    find_tables_with_column,
    get_join_graph,
    get_join_paths,
    clear_schema_cache,
    get_cached_schema,
    format_schema_for_llm,
)

__all__ = [
    'DatabaseConnection',
    'get_db',
    'get_table_schema',
    'get_all_schemas',
    'get_schema_description',
    'get_table_relationships',
    'get_schema_summary',
    'get_foreign_keys',
    'get_all_foreign_keys',
    'get_column_to_table_index',
    'find_tables_with_column',
    'get_join_graph',
    'get_join_paths',
    'clear_schema_cache',
    'get_cached_schema',
    'format_schema_for_llm',
]

