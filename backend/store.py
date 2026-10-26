"""Small local SQLite store. Each mutation uses a transaction; no global connection."""
import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("PAPERMIND_DATA_DIR", ROOT / "data")).resolve()

def encode(value):
    return json.dumps(value, ensure_ascii=False)

@contextmanager
def connection(write=False):
    DATA.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DATA / "papermind.db", timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    if write:
        db.execute("BEGIN IMMEDIATE")
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def initialize():
    with connection() as db:
        db.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS messages(id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(id), role TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS patches(id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(id), payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS library(id TEXT PRIMARY KEY, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS memories(id TEXT PRIMARY KEY, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(id), payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS job_events(event_id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT NOT NULL REFERENCES jobs(id), payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS copilot_runs(id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(id), payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS copilot_events(event_id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL REFERENCES copilot_runs(id), payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS model_calls(id TEXT PRIMARY KEY, role TEXT NOT NULL, model TEXT NOT NULL, elapsed REAL NOT NULL, usage TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        """)
        # Fixtures are available only in explicitly isolated test runs.
        if os.environ.get('PAPERMIND_MODE') == 'fixture' and DATA != (ROOT / 'data').resolve():
            from .demo_data import fixture_documents
            for doc in fixture_documents():
                db.execute("INSERT OR IGNORE INTO documents VALUES (?, ?)", (doc["id"], encode(doc)))

def get_document(db, doc_id):
    row = db.execute("SELECT payload FROM documents WHERE id=?", (doc_id,)).fetchone()
    return json.loads(row["payload"]) if row else None

def put_document(db, doc):
    db.execute("INSERT INTO documents VALUES (?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload", (doc["id"], encode(doc)))

def items(db, table):
    if table not in {"library", "memories", "documents"}:
        raise ValueError("Unknown table")
    return [json.loads(row["payload"]) for row in db.execute(f"SELECT payload FROM {table} ORDER BY rowid")]
