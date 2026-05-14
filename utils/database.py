import sqlite3
import os
from orchestrator import connection

def get_recent_threads(limit=50):
    """
    Fetch the most recent thread IDs from the LangGraph checkpoints table.
    """
    try:
        cur = connection.cursor()
        cur.execute(
            "SELECT DISTINCT thread_id FROM checkpoints ORDER BY thread_id DESC LIMIT ?", (limit,)
        )
        return [r[0] for r in cur.fetchall()]
    except Exception as e:
        import logging
        logging.warning(f"Could not fetch recent threads: {e}")
        return []

def get_thread_names():
    """
    Fetch saved thread names from the custom thread_names table.
    """
    _ensure_thread_names_table()
    try:
        cur = connection.cursor()
        cur.execute("SELECT thread_id, name FROM thread_names")
        return {r[0]: r[1] for r in cur.fetchall()}
    except Exception as e:
        import logging
        logging.warning(f"Could not fetch thread names: {e}")
        return {}

def save_thread_name(thread_id: str, name: str):
    """
    Save a custom name for a specific thread.
    """
    _ensure_thread_names_table()
    try:
        cur = connection.cursor()
        cur.execute("""
            INSERT INTO thread_names (thread_id, name)
            VALUES (?, ?)
            ON CONFLICT(thread_id) DO UPDATE SET name=excluded.name
        """, (thread_id, name))
        connection.commit()
    except Exception as e:
        import logging
        logging.warning(f"Could not save thread name: {e}")

def _ensure_thread_names_table():
    """
    Ensure the custom table for thread names exists.
    """
    try:
        cur = connection.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS thread_names (
                thread_id TEXT PRIMARY KEY,
                name TEXT NOT NULL
            )
        """)
        connection.commit()
    except Exception as e:
        import logging
        logging.warning(f"Could not create thread_names table: {e}")
