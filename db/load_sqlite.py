"""
Load CSV files from musicoset_popularity dataset into SQLite database.

This module provides functionality to:
- Load all CSV files into a SQLite database
- Create appropriate table schemas
- Handle data type conversions
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional


# Base directory paths
BASE_DIR = Path(__file__).parent.parent
DATASET_DIR = BASE_DIR / "dataset"
POPULARITY_DIR = DATASET_DIR / "musicoset_popularity"
METADATA_DIR = DATASET_DIR / "musicoset_metadata"
SONGFEATURES_DIR = DATASET_DIR / "musicoset_songfeatures"
DB_DIR = BASE_DIR / "data" / "db"
DB_PATH = DB_DIR / "musicoset_popularity.sqlite"


def create_database(force_recreate: bool = False) -> sqlite3.Connection:
    """
    Create or connect to the SQLite database.
    
    Args:
        force_recreate: If True, drop existing database and create new one.
        
    Returns:
        sqlite3.Connection: Database connection
    """
    # Create db directory if it doesn't exist
    DB_DIR.mkdir(parents=True, exist_ok=True)
    
    # Remove existing database if force_recreate is True
    if force_recreate and DB_PATH.exists():
        DB_PATH.unlink()
    
    # Create connection
    conn = sqlite3.connect(str(DB_PATH))
    return conn


def load_csv_to_table(
    conn: sqlite3.Connection,
    csv_path: Path,
    table_name: str,
    sep: str = '\t',
    if_exists: str = 'replace'
) -> None:
    """
    Load a CSV file into a SQLite table.
    
    Args:
        conn: SQLite connection
        csv_path: Path to CSV file
        table_name: Name of the table to create/update
        sep: CSV separator (default: tab)
        if_exists: What to do if table exists ('replace', 'append', 'fail')
    """
    print(f"Loading {csv_path.name} into table '{table_name}'...")
    
    # Read CSV
    df = pd.read_csv(csv_path, sep=sep)
    
    # Convert boolean columns to int (SQLite doesn't have native boolean)
    for col in df.columns:
        if df[col].dtype == 'bool':
            df[col] = df[col].astype(int)
    
    # Load into SQLite
    df.to_sql(
        table_name,
        conn,
        if_exists=if_exists,
        index=False,
        method='multi',
        chunksize=10000
    )
    
    # Get row count
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = cursor.fetchone()[0]
    print(f"  ✓ Loaded {row_count:,} rows into '{table_name}'")


def create_indexes(conn: sqlite3.Connection) -> None:
    """
    Create indexes on foreign key and commonly queried columns.
    
    Args:
        conn: SQLite connection
    """
    print("\nCreating indexes...")
    
    indexes = [
        # Album chart indexes
        ("album_chart", "album_id"),
        ("album_chart", "date"),
        
        # Album pop indexes
        ("album_pop", "album_id"),
        ("album_pop", "year"),
        ("album_pop", "is_pop"),
        
        # Artist chart indexes
        ("artist_chart", "artist_id"),
        ("artist_chart", "week"),
        
        # Artist pop indexes
        ("artist_pop", "artist_id"),
        ("artist_pop", "year"),
        ("artist_pop", "is_pop"),
        
        # Song chart indexes
        ("song_chart", "song_id"),
        ("song_chart", "week"),
        
        # Song pop indexes
        ("song_pop", "song_id"),
        ("song_pop", "year"),
        ("song_pop", "is_pop"),
        
        # Metadata indexes
        ("albums", "album_id"),
        ("artists", "artist_id"),
        ("songs", "song_id"),
        ("releases", "artist_id"),
        ("releases", "album_id"),
        ("tracks", "song_id"),
        ("tracks", "album_id"),
        
        # Song features indexes
        ("acoustic_features", "song_id"),
        ("lyrics", "song_id"),
    ]
    
    cursor = conn.cursor()
    for table, column in indexes:
        index_name = f"idx_{table}_{column}"
        try:
            cursor.execute(
                f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column})"
            )
            print(f"  ✓ Created index {index_name}")
        except sqlite3.Error as e:
            print(f"  ✗ Failed to create index {index_name}: {e}")


def load_all_data(force_recreate: bool = False) -> str:
    """
    Load all CSV files from all dataset folders into SQLite database.
    
    Args:
        force_recreate: If True, drop existing database and create new one.
        
    Returns:
        str: Path to the created database file
    """
    print("=" * 60)
    print("Loading all dataset data into SQLite")
    print("=" * 60)
    
    # Create database connection
    conn = create_database(force_recreate=force_recreate)
    
    try:
        # Define CSV files and their corresponding table names and directories
        csv_files = [
            # Popularity dataset
            (POPULARITY_DIR, "album_chart.csv", "album_chart"),
            (POPULARITY_DIR, "album_pop.csv", "album_pop"),
            (POPULARITY_DIR, "artist_chart.csv", "artist_chart"),
            (POPULARITY_DIR, "artist_pop.csv", "artist_pop"),
            (POPULARITY_DIR, "song_chart.csv", "song_chart"),
            (POPULARITY_DIR, "song_pop.csv", "song_pop"),
            
            # Metadata dataset
            (METADATA_DIR, "albums.csv", "albums"),
            (METADATA_DIR, "artists.csv", "artists"),
            (METADATA_DIR, "songs.csv", "songs"),
            (METADATA_DIR, "releases.csv", "releases"),
            (METADATA_DIR, "tracks.csv", "tracks"),
            
            # Song features dataset
            (SONGFEATURES_DIR, "acoustic_features.csv", "acoustic_features"),
            (SONGFEATURES_DIR, "lyrics.csv", "lyrics"),
        ]
        
        # Load each CSV file
        for data_dir, csv_file, table_name in csv_files:
            csv_path = data_dir / csv_file
            if not csv_path.exists():
                print(f"Warning: {csv_path} not found, skipping...")
                continue
            
            load_csv_to_table(conn, csv_path, table_name)
        
        # Create indexes
        create_indexes(conn)
        
        # Commit all changes
        conn.commit()
        
        print("\n" + "=" * 60)
        print(f"✓ Database created successfully at: {DB_PATH}")
        print("=" * 60)
        
        return str(DB_PATH)
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ Error loading data: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    # Run the loader
    db_path = load_all_data(force_recreate=True)
    print(f"\nDatabase ready at: {db_path}")

