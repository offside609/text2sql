"""
Schema introspection utilities for the database.

This module provides functions to:
- Get table schemas
- Get column information
- Generate schema descriptions for LLMs
- List available tables and their relationships
- Introspect foreign key constraints
- Build column-to-table reverse indexes
- Generate join graphs from foreign keys
- Cache schema information in memory
- Format schemas in LLM-safe formats
"""

from typing import List, Dict, Any, Optional
from .connection import get_db, DatabaseConnection


def get_table_schema(table_name: str, db: Optional[DatabaseConnection] = None) -> Dict[str, Any]:
    """
    Get detailed schema information for a table.
    
    Args:
        table_name: Name of the table
        db: Optional database connection. If None, uses global instance.
        
    Returns:
        Dictionary containing schema information:
        - name: Table name
        - columns: List of column dictionaries with name, type, nullable, default
        - primary_key: Primary key column(s)
        - indexes: List of indexes
    """
    if db is None:
        db = get_db()
    
    # Get column information
    query = f"PRAGMA table_info({table_name})"
    columns_info = db.execute_query(query)
    
    # Get primary key
    primary_key = [
        col['name'] for col in columns_info 
        if col['pk'] == 1
    ]
    
    # Get indexes and detect unique columns
    query = f"PRAGMA index_list({table_name})"
    indexes_info = db.execute_query(query)
    
    # Track which columns are unique (from UNIQUE indexes)
    unique_columns = set()
    indexes = []
    
    for idx in indexes_info:
        idx_name = idx['name']
        is_unique = idx.get('unique', 0) == 1
        
        # Get columns in index
        idx_cols_query = f"PRAGMA index_info({idx_name})"
        idx_cols = db.execute_query(idx_cols_query)
        idx_column_names = [col['name'] for col in idx_cols]
        
        indexes.append({
            'name': idx_name,
            'columns': idx_column_names,
            'unique': is_unique
        })
        
        # If it's a unique index with a single column, mark that column as unique
        if is_unique and len(idx_column_names) == 1:
            unique_columns.add(idx_column_names[0])
    
    # Also detect common identifier patterns (id, _id, etc.)
    common_id_patterns = ['id', '_id', 'uuid', 'key', 'pk']
    
    return {
        'name': table_name,
        'columns': [
            {
                'name': col['name'],
                'type': col['type'],
                'nullable': col['notnull'] == 0,
                'default': col['dflt_value'],
                'primary_key': col['pk'] == 1,
                'is_unique': (
                    col['pk'] == 1 or  # Primary key is always unique
                    col['name'].lower() in unique_columns or  # Has unique index
                    any(col['name'].lower().endswith(pattern) for pattern in common_id_patterns)  # Common ID pattern
                )
            }
            for col in columns_info
        ],
        'primary_key': primary_key,
        'indexes': indexes,
        'unique_columns': list(unique_columns)  # Columns with unique indexes
    }


def get_all_schemas(db: Optional[DatabaseConnection] = None) -> Dict[str, Dict[str, Any]]:
    """
    Get schema information for all tables.
    
    Args:
        db: Optional database connection. If None, uses global instance.
        
    Returns:
        Dictionary mapping table names to their schema information
    """
    if db is None:
        db = get_db()
    
    table_names = db.get_table_names()
    return {
        table_name: get_table_schema(table_name, db)
        for table_name in table_names
    }


def get_schema_description(
    table_name: Optional[str] = None,
    db: Optional[DatabaseConnection] = None,
    include_sample: bool = False,
    sample_size: int = 3
) -> str:
    """
    Generate a human-readable schema description for LLM context.
    
    Args:
        table_name: Specific table name. If None, describes all tables.
        db: Optional database connection. If None, uses global instance.
        include_sample: Whether to include sample data
        sample_size: Number of sample rows to include
        
    Returns:
        Formatted string describing the schema
    """
    if db is None:
        db = get_db()
    
    if table_name:
        schemas = {table_name: get_table_schema(table_name, db)}
    else:
        schemas = get_all_schemas(db)
    
    description_parts = []
    
    for table_name, schema in schemas.items():
        desc = f"Table: {table_name}\n"
        desc += "Columns:\n"
        
        for col in schema['columns']:
            col_desc = f"  - {col['name']} ({col['type']})"
            
            # Highlight primary keys
            if col['primary_key']:
                col_desc += " [PRIMARY KEY]"
            
            # Highlight unique columns (even without explicit PK)
            elif col.get('is_unique', False):
                col_desc += " [UNIQUE]"
            
            # Highlight common identifier patterns
            common_id_patterns = ['id', '_id', 'uuid', 'key']
            if any(col['name'].lower().endswith(p) for p in common_id_patterns):
                if not col['primary_key'] and not col.get('is_unique', False):
                    col_desc += " [IDENTIFIER PATTERN]"
            
            if not col['nullable']:
                col_desc += " [NOT NULL]"
            if col['default'] is not None:
                col_desc += f" [DEFAULT: {col['default']}]"
            desc += col_desc + "\n"
        
        if schema['indexes']:
            desc += "Indexes:\n"
            for idx in schema['indexes']:
                desc += f"  - {idx['name']} on ({', '.join(idx['columns'])})\n"
        
        # Add sample data if requested
        if include_sample:
            try:
                sample_query = f"SELECT * FROM {table_name} LIMIT {sample_size}"
                samples = db.execute_query(sample_query)
                if samples:
                    desc += "\nSample data:\n"
                    for i, row in enumerate(samples, 1):
                        desc += f"  Row {i}: {dict(row)}\n"
            except Exception as e:
                desc += f"\nCould not fetch sample data: {e}\n"
        
        description_parts.append(desc)
    
    return "\n" + "="*60 + "\n".join(description_parts) + "="*60 + "\n"


def get_table_relationships(db: Optional[DatabaseConnection] = None) -> Dict[str, List[str]]:
    """
    Infer table relationships based on common ID patterns.
    
    Args:
        db: Optional database connection. If None, uses global instance.
        
    Returns:
        Dictionary mapping table names to lists of related table names
    """
    if db is None:
        db = get_db()
    
    schemas = get_all_schemas(db)
    relationships = {}
    
    # Common ID patterns
    id_patterns = {
        'album_id': ['album_chart', 'album_pop'],
        'artist_id': ['artist_chart', 'artist_pop'],
        'song_id': ['song_chart', 'song_pop'],
    }
    
    for table_name, schema in schemas.items():
        related = []
        for col in schema['columns']:
            col_name = col['name']
            if col_name in id_patterns:
                # Find tables that might share this ID
                for related_table in id_patterns[col_name]:
                    if related_table != table_name and related_table in schemas:
                        related.append(related_table)
        
        if related:
            relationships[table_name] = list(set(related))
    
    return relationships


def get_schema_summary(db: Optional[DatabaseConnection] = None) -> str:
    """
    Get a concise summary of all tables and their purposes.
    
    Args:
        db: Optional database connection. If None, uses global instance.
        
    Returns:
        String summary of the database schema
    """
    if db is None:
        db = get_db()
    
    table_names = db.get_table_names()
    
    summary = "Database Schema Summary:\n"
    summary += f"Total tables: {len(table_names)}\n\n"
    
    # Table descriptions based on naming patterns
    descriptions = {
        'album_chart': 'Album chart rankings from Billboard 200',
        'album_pop': 'Album popularity classification',
        'artist_chart': 'Artist chart rankings from Billboard',
        'artist_pop': 'Artist popularity classification',
        'song_chart': 'Song chart rankings from Hot 100',
        'song_pop': 'Song popularity classification',
    }
    
    for table_name in sorted(table_names):
        desc = descriptions.get(table_name, 'No description available')
        schema = get_table_schema(table_name, db)
        col_count = len(schema['columns'])
        summary += f"  - {table_name}: {desc} ({col_count} columns)\n"
    
    return summary


# ============================================================================
# Foreign Key Introspection
# ============================================================================

def get_foreign_keys(
    table_name: str,
    db: Optional[DatabaseConnection] = None
) -> List[Dict[str, Any]]:
    """
    Get foreign key constraints for a table using PRAGMA foreign_key_list.
    
    Args:
        table_name: Name of the table
        db: Optional database connection. If None, uses global instance.
        
    Returns:
        List of foreign key dictionaries with:
        - id: Sequential number of the foreign key
        - seq: Column sequence number
        - table: Referenced table name
        - from: Column name in the current table
        - to: Column name in the referenced table
        - on_update: Action on update (NO ACTION, RESTRICT, SET NULL, etc.)
        - on_delete: Action on delete
        - match: Match clause
    """
    if db is None:
        db = get_db()
    
    # Enable foreign key constraints for PRAGMA to work
    db.execute_query("PRAGMA foreign_keys = ON")
    
    query = f"PRAGMA foreign_key_list({table_name})"
    fk_info = db.execute_query(query)
    
    return fk_info


def get_all_foreign_keys(
    db: Optional[DatabaseConnection] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all foreign key constraints for all tables.
    
    Args:
        db: Optional database connection. If None, uses global instance.
        
    Returns:
        Dictionary mapping table names to their foreign key lists
    """
    if db is None:
        db = get_db()
    
    table_names = db.get_table_names()
    all_fks = {}
    
    for table_name in table_names:
        fks = get_foreign_keys(table_name, db)
        if fks:
            all_fks[table_name] = fks
    
    return all_fks


# ============================================================================
# Column-to-Table Reverse Index
# ============================================================================

def get_column_to_table_index(
    db: Optional[DatabaseConnection] = None
) -> Dict[str, List[Dict[str, str]]]:
    """
    Create a reverse index mapping column names to tables that contain them.
    
    Args:
        db: Optional database connection. If None, uses global instance.
        
    Returns:
        Dictionary mapping column names to lists of dictionaries with:
        - table: Table name containing the column
        - type: Column data type
        - is_primary_key: Whether column is a primary key
        - is_unique: Whether column is unique (via unique index or ID pattern)
        - is_foreign_key: Whether column is a foreign key (if FK info available)
    """
    if db is None:
        db = get_db()
    
    schemas = get_all_schemas(db)
    all_fks = get_all_foreign_keys(db)
    
    # Build FK lookup: table -> column -> referenced table
    fk_lookup = {}
    for table_name, fks in all_fks.items():
        fk_lookup[table_name] = {}
        for fk in fks:
            from_col = fk.get('from', fk.get('from_column'))
            fk_lookup[table_name][from_col] = fk
    
    column_index = {}
    
    for table_name, schema in schemas.items():
        table_fks = fk_lookup.get(table_name, {})
        
        for col in schema['columns']:
            col_name = col['name']
            if col_name not in column_index:
                column_index[col_name] = []
            
            # Check if this column is a foreign key
            is_fk = col_name in table_fks
            fk_info = table_fks.get(col_name, {})
            
            column_index[col_name].append({
                'table': table_name,
                'type': col['type'],
                'is_primary_key': col['primary_key'],
                'is_unique': col.get('is_unique', False),
                'is_foreign_key': is_fk,
                'references_table': fk_info.get('table') if is_fk else None,
                'references_column': fk_info.get('to', fk_info.get('to_column')) if is_fk else None,
            })
    
    return column_index


def find_tables_with_column(
    column_name: str,
    db: Optional[DatabaseConnection] = None
) -> List[Dict[str, str]]:
    """
    Find all tables that contain a specific column name.
    
    Args:
        column_name: Name of the column to search for
        db: Optional database connection. If None, uses global instance.
        
    Returns:
        List of dictionaries with table and column information
    """
    column_index = get_column_to_table_index(db)
    return column_index.get(column_name, [])


# ============================================================================
# Join Graph
# ============================================================================

def get_join_graph(
    db: Optional[DatabaseConnection] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Build a lightweight join graph from foreign key relationships.
    
    Args:
        db: Optional database connection. If None, uses global instance.
        
    Returns:
        Dictionary mapping table names to lists of joinable tables with:
        - target_table: Table that can be joined
        - join_type: Type of join ('FK' for foreign key, 'REVERSE_FK' for reverse)
        - local_column: Column in source table
        - foreign_column: Column in target table
        - relationship: Relationship description
    """
    if db is None:
        db = get_db()
    
    all_fks = get_all_foreign_keys(db)
    schemas = get_all_schemas(db)
    join_graph = {}
    
    # Build forward joins (this table -> other tables via FKs)
    for table_name in schemas.keys():
        join_graph[table_name] = []
        
        # Forward foreign keys
        fks = all_fks.get(table_name, [])
        for fk in fks:
            from_col = fk.get('from', fk.get('from_column'))
            to_col = fk.get('to', fk.get('to_column'))
            ref_table = fk.get('table')
            
            if ref_table and ref_table in schemas:
                join_graph[table_name].append({
                    'target_table': ref_table,
                    'join_type': 'FK',
                    'local_column': from_col,
                    'foreign_column': to_col,
                    'relationship': f"{table_name}.{from_col} -> {ref_table}.{to_col}",
                })
        
        # Reverse foreign keys (other tables -> this table)
        for other_table, other_fks in all_fks.items():
            if other_table == table_name:
                continue
            
            for fk in other_fks:
                ref_table = fk.get('table')
                if ref_table == table_name:
                    from_col = fk.get('from', fk.get('from_column'))
                    to_col = fk.get('to', fk.get('to_column'))
                    
                    join_graph[table_name].append({
                        'target_table': other_table,
                        'join_type': 'REVERSE_FK',
                        'local_column': to_col,
                        'foreign_column': from_col,
                        'relationship': f"{other_table}.{from_col} -> {table_name}.{to_col}",
                    })
    
    return join_graph


def get_join_paths(
    from_table: str,
    to_table: str,
    db: Optional[DatabaseConnection] = None,
    max_depth: int = 3
) -> List[List[Dict[str, Any]]]:
    """
    Find all possible join paths between two tables.
    
    Args:
        from_table: Source table name
        to_table: Target table name
        db: Optional database connection. If None, uses global instance.
        max_depth: Maximum depth to search for paths
        
    Returns:
        List of join paths, where each path is a list of join dictionaries
    """
    if db is None:
        db = get_db()
    
    join_graph = get_join_graph(db)
    
    if from_table not in join_graph or to_table not in join_graph:
        return []
    
    def dfs(current: str, target: str, path: List[Dict], visited: set, depth: int) -> List[List[Dict]]:
        if depth > max_depth:
            return []
        
        if current == target:
            return [path]
        
        paths = []
        for join_info in join_graph.get(current, []):
            next_table = join_info['target_table']
            if next_table not in visited:
                new_path = path + [join_info]
                new_visited = visited | {next_table}
                found_paths = dfs(next_table, target, new_path, new_visited, depth + 1)
                paths.extend(found_paths)
        
        return paths
    
    return dfs(from_table, to_table, [], {from_table}, 0)


# ============================================================================
# Schema Caching
# ============================================================================

# In-memory cache for schemas
_schema_cache: Dict[str, Dict[str, Any]] = {}
_cache_timestamp: Optional[float] = None


def clear_schema_cache() -> None:
    """Clear the in-memory schema cache."""
    global _schema_cache, _cache_timestamp
    _schema_cache = {}
    _cache_timestamp = None


def get_cached_schema(
    table_name: Optional[str] = None,
    db: Optional[DatabaseConnection] = None,
    cache_ttl: Optional[float] = None
) -> Dict[str, Any]:
    """
    Get schema information with in-memory caching.
    
    Args:
        table_name: Specific table name. If None, returns all schemas.
        db: Optional database connection. If None, uses global instance.
        cache_ttl: Time-to-live for cache in seconds. If None, cache never expires.
        
    Returns:
        Cached schema information
    """
    import time
    
    global _schema_cache, _cache_timestamp
    
    # Check if cache is valid
    if cache_ttl is not None and _cache_timestamp is not None:
        if time.time() - _cache_timestamp > cache_ttl:
            clear_schema_cache()
    
    cache_key = table_name or '__all__'
    
    # Return cached if available
    if cache_key in _schema_cache:
        return _schema_cache[cache_key]
    
    # Fetch and cache
    if table_name:
        schema = get_table_schema(table_name, db)
        _schema_cache[cache_key] = schema
    else:
        schema = get_all_schemas(db)
        _schema_cache[cache_key] = schema
    
    _cache_timestamp = time.time()
    return schema


# ============================================================================
# LLM-Safe Schema Formatter
# ============================================================================

def format_schema_for_llm(
    table_name: Optional[str] = None,
    db: Optional[DatabaseConnection] = None,
    include_foreign_keys: bool = True,
    include_indexes: bool = False,
    include_sample: bool = False,
    sample_size: int = 2,
    format_style: str = "markdown"
) -> str:
    """
    Format schema information in an LLM-safe, structured format.
    
    Args:
        table_name: Specific table name. If None, formats all tables.
        db: Optional database connection. If None, uses global instance.
        include_foreign_keys: Whether to include foreign key relationships
        include_indexes: Whether to include index information
        include_sample: Whether to include sample data
        sample_size: Number of sample rows to include
        format_style: Output format ('markdown', 'json', 'plain')
        
    Returns:
        Formatted schema string safe for LLM consumption
    """
    if db is None:
        db = get_db()
    
    if table_name:
        schemas = {table_name: get_table_schema(table_name, db)}
        all_fks = {table_name: get_foreign_keys(table_name, db)} if include_foreign_keys else {}
    else:
        schemas = get_all_schemas(db)
        all_fks = get_all_foreign_keys(db) if include_foreign_keys else {}
    
    if format_style == "json":
        import json
        result = {
            'tables': []
        }
        for tbl_name, schema in schemas.items():
            table_info = {
                'name': tbl_name,
                'columns': [
                    {
                        'name': col['name'],
                        'type': col['type'],
                        'nullable': col['nullable'],
                        'primary_key': col['primary_key'],
                        'is_unique': col.get('is_unique', False)
                    }
                    for col in schema['columns']
                ]
            }
            if include_foreign_keys and tbl_name in all_fks:
                table_info['foreign_keys'] = all_fks[tbl_name]
            if include_indexes:
                table_info['indexes'] = schema['indexes']
            result['tables'].append(table_info)
        return json.dumps(result, indent=2)
    
    elif format_style == "markdown":
        lines = []
        lines.append("# Database Schema\n")
        
        for tbl_name, schema in schemas.items():
            lines.append(f"## Table: `{tbl_name}`\n")
            lines.append("### Columns\n")
            lines.append("| Column | Type | Nullable | Primary Key | Unique |")
            lines.append("|--------|------|----------|-------------|--------|")
            
            for col in schema['columns']:
                # Build flags column
                flags = []
                if col['primary_key']:
                    flags.append("PK")
                if col.get('is_unique', False) and not col['primary_key']:
                    flags.append("UNIQUE")
                common_id_patterns = ['id', '_id', 'uuid', 'key']
                if any(col['name'].lower().endswith(p) for p in common_id_patterns):
                    if not col['primary_key'] and not col.get('is_unique', False):
                        flags.append("ID")
                flags_str = ", ".join(flags) if flags else "-"
                
                lines.append(
                    f"| `{col['name']}` | {col['type']} | "
                    f"{'Yes' if col['nullable'] else 'No'} | "
                    f"{'Yes' if col['primary_key'] else 'No'} | "
                    f"{flags_str} |"
                )
            
            if include_foreign_keys and tbl_name in all_fks:
                fks = all_fks[tbl_name]
                if fks:
                    lines.append("\n### Foreign Keys\n")
                    for fk in fks:
                        from_col = fk.get('from', fk.get('from_column', ''))
                        to_table = fk.get('table', '')
                        to_col = fk.get('to', fk.get('to_column', ''))
                        lines.append(f"- `{from_col}` → `{to_table}.{to_col}`")
            
            if include_indexes and schema['indexes']:
                lines.append("\n### Indexes\n")
                for idx in schema['indexes']:
                    lines.append(f"- `{idx['name']}` on ({', '.join(idx['columns'])})")
            
            if include_sample:
                try:
                    sample_query = f"SELECT * FROM {tbl_name} LIMIT {sample_size}"
                    samples = db.execute_query(sample_query)
                    if samples:
                        lines.append("\n### Sample Data\n")
                        for i, sample in enumerate(samples, 1):
                            lines.append(f"**Row {i}:**")
                            for key, value in sample.items():
                                # Truncate long values for LLM safety
                                val_str = str(value)
                                if len(val_str) > 100:
                                    val_str = val_str[:97] + "..."
                                lines.append(f"  - `{key}`: {val_str}")
                except Exception:
                    pass
            
            lines.append("")  # Empty line between tables
        
        return "\n".join(lines)
    
    else:  # plain format
        lines = []
        for tbl_name, schema in schemas.items():
            lines.append(f"Table: {tbl_name}")
            lines.append("-" * 60)
            for col in schema['columns']:
                col_str = f"  {col['name']} ({col['type']})"
                
                # Highlight primary keys
                if col['primary_key']:
                    col_str += " [PK]"
                
                # Highlight unique columns (even without explicit PK)
                elif col.get('is_unique', False):
                    col_str += " [UNIQUE]"
                
                # Highlight common identifier patterns
                common_id_patterns = ['id', '_id', 'uuid', 'key']
                if any(col['name'].lower().endswith(p) for p in common_id_patterns):
                    if not col['primary_key'] and not col.get('is_unique', False):
                        col_str += " [ID PATTERN]"
                
                if not col['nullable']:
                    col_str += " [NOT NULL]"
                lines.append(col_str)
            
            if include_foreign_keys and tbl_name in all_fks:
                fks = all_fks[tbl_name]
                if fks:
                    lines.append("\nForeign Keys:")
                    for fk in fks:
                        from_col = fk.get('from', fk.get('from_column', ''))
                        to_table = fk.get('table', '')
                        to_col = fk.get('to', fk.get('to_column', ''))
                        lines.append(f"  {from_col} -> {to_table}.{to_col}")
            
            lines.append("")
        
        return "\n".join(lines)
