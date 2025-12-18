"""
Load Schema Node - Inspect DB schema and load tables + columns.
"""

from typing import Dict, Any
from db import get_db, get_all_schemas, get_all_foreign_keys


def load_schema(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Inspect DB schema and load tables + columns.
    
    Responsibility:
    - Inspect DB schema
    - Load tables + columns
    - Load foreign keys
    
    Writes:
    - tables: List of table names
    - columns: Dict mapping table -> columns
    - foreign_keys: Dict of FK relationships
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with schema information
    """
    db = get_db()
    
    # Get all table names
    tables = db.get_table_names()
    
    # Get all schemas
    schemas = get_all_schemas(db)
    
    # Extract columns for each table
    columns = {}
    for table_name, schema in schemas.items():
        columns[table_name] = [
            {
                'name': col['name'],
                'type': col['type'],
                'nullable': col['nullable'],
                'primary_key': col['primary_key'],
                'is_unique': col.get('is_unique', False)  # Add unique detection
            }
            for col in schema['columns']
        ]
    
    # Get foreign keys
    foreign_keys = get_all_foreign_keys(db)
    
    # Check for tables without primary keys but with foreign keys
    warnings = []
    for table_name, schema in schemas.items():
        has_pk = bool(schema.get('primary_key'))
        has_fks = bool(foreign_keys.get(table_name))
        
        if not has_pk and has_fks:
            unique_cols = schema.get('unique_columns', [])
            warnings.append(
                f"⚠️  Table '{table_name}' has foreign keys but no primary key. "
                f"Unique columns detected: {unique_cols if unique_cols else 'None'}"
            )
    
    # Print warnings if any
    if warnings:
        print("\n" + "="*60)
        print("SCHEMA WARNINGS")
        print("="*60)
        for warning in warnings:
            print(warning)
        print("="*60 + "\n")
    
    # Return only updated keys
    return {
        'tables': tables,
        'columns': columns,
        'foreign_keys': foreign_keys,
        'schemas': schemas,  # Store full schemas for reference
        'schema_warnings': warnings  # Store warnings in state
    }

