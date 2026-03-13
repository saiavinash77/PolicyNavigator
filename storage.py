import os
import sqlite3
from typing import List, Dict, Any
from config import settings

DB_PATH = os.path.join(settings.storage_dir, "metadata.db")


def init_db() -> None:
    os.makedirs(settings.storage_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            doc_id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    conn.commit()
    conn.close()


def insert_document(doc_id: str, filename: str, created_at: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO documents (doc_id, filename, created_at) VALUES (?, ?, ?)",
        (doc_id, filename, created_at),
    )
    conn.commit()
    conn.close()
