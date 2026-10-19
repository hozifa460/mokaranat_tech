"""
SQLite Database Connection and Schema Management.
Clean Architecture - Layer: Repository / Data Access Layer
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator
from core.config import DATABASE_PATH


def get_db_connection(db_path: Path = DATABASE_PATH) -> sqlite3.Connection:
    """Create and configure a SQLite connection with row factory and foreign keys."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


@contextmanager
def db_session(db_path: Path = DATABASE_PATH) -> Generator[sqlite3.Connection, None, None]:
    """Context manager for safe database transactions."""
    conn = get_db_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_schema(db_path: Path = DATABASE_PATH) -> None:
    """Creates tables and indexes if they do not exist."""
    with db_session(db_path) as conn:
        cursor = conn.cursor()

        # Hardware Specifications Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS hardware_specs (
            id TEXT PRIMARY KEY,
            slug TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            brand TEXT NOT NULL,
            release_year INTEGER NOT NULL,
            launch_msrp_usd REAL NOT NULL,
            architecture TEXT NOT NULL,
            process_node_nm REAL NOT NULL,
            tdp_w INTEGER NOT NULL,
            raw_specs_json TEXT NOT NULL,
            benchmark_index REAL NOT NULL,
            gaming_scores_json TEXT NOT NULL,
            ray_tracing_score REAL,
            efficiency_score REAL NOT NULL,
            features_json TEXT NOT NULL,
            pcie_interface TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Migration: Add pcie_interface column if table already exists without it
        cursor.execute("PRAGMA table_info(hardware_specs);")
        columns = {r[1]: r for r in cursor.fetchall()}
        if "pcie_interface" not in columns:
            cursor.execute("ALTER TABLE hardware_specs ADD COLUMN pcie_interface TEXT;")

        # Migration: Make ray_tracing_score nullable if it was created with NOT NULL constraint
        if "ray_tracing_score" in columns and columns["ray_tracing_score"][3] == 1:
            cursor.execute("CREATE TABLE hardware_specs_dg_tmp AS SELECT * FROM hardware_specs;")
            cursor.execute("DROP TABLE hardware_specs;")
            cursor.execute("""
            CREATE TABLE hardware_specs (
                id TEXT PRIMARY KEY,
                slug TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                brand TEXT NOT NULL,
                release_year INTEGER NOT NULL,
                launch_msrp_usd REAL NOT NULL,
                architecture TEXT NOT NULL,
                process_node_nm REAL NOT NULL,
                tdp_w INTEGER NOT NULL,
                raw_specs_json TEXT NOT NULL,
                benchmark_index REAL NOT NULL,
                gaming_scores_json TEXT NOT NULL,
                ray_tracing_score REAL,
                efficiency_score REAL NOT NULL,
                features_json TEXT NOT NULL,
                pcie_interface TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cursor.execute("INSERT INTO hardware_specs SELECT * FROM hardware_specs_dg_tmp;")
            cursor.execute("DROP TABLE hardware_specs_dg_tmp;")

        # Cache Table for Generated Comparisons & Editorial Verdicts
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS comparisons_cache (
            slug TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            item_a_id TEXT NOT NULL,
            item_b_id TEXT NOT NULL,
            data_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_a_id) REFERENCES hardware_specs(id) ON DELETE CASCADE,
            FOREIGN KEY (item_b_id) REFERENCES hardware_specs(id) ON DELETE CASCADE
        );
        """)

        # Indexes for fast querying & pSEO matrix generation
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hardware_category ON hardware_specs(category);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hardware_slug ON hardware_specs(slug);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_hardware_perf ON hardware_specs(benchmark_index);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_comparisons_category ON comparisons_cache(category);")
