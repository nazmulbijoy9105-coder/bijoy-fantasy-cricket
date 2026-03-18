"""
database.py — SQLite connection helper.
WAL mode for concurrent reads. Row factory returns dicts.
"""
import sqlite3
import yaml
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
with open(BASE_DIR / "config.yaml") as f:
    _cfg = yaml.safe_load(f)

DB_PATH = BASE_DIR / _cfg["database"]["path"]


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def query_db(query: str, params: tuple = ()) -> list[dict]:
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def execute_db(query: str, params: tuple = ()) -> int:
    """Returns lastrowid."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def executemany_db(query: str, params_list: list[tuple]) -> None:
    conn = get_conn()
    try:
        conn.executemany(query, params_list)
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Initialise schema on startup."""
    schema = (BASE_DIR / "database" / "bpl_schema.sql").read_text()
    conn = get_conn()
    try:
        conn.executescript(schema)
        conn.commit()
    finally:
        conn.close()
