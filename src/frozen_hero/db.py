"""SQLite data-access layer for frozen-hero.

All queries use parameterised placeholders (?) — no SQL injection possible.
"""

import logging
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from frozen_hero import config

logger = logging.getLogger(__name__)


@contextmanager
def _get_connection() -> Generator[sqlite3.Connection, None, None]:
    """Yield a SQLite connection; commit on success, rollback on error."""
    con = sqlite3.connect(config.DB_PATH)
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def get_all_entries() -> list[dict[str, Any]]:
    """Return all freezer entries ordered by date."""
    with _get_connection() as con:
        cur = con.cursor()
        cur.execute("SELECT id, row_one, row_two, category, date FROM freezer ORDER BY date")
        rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "row_one": row[1],
            "row_two": row[2],
            "category": row[3],
            "date": row[4],
        }
        for row in rows
    ]


def add_entry(row_one: str, row_two: str, category: str, date: str) -> int:
    """Insert a new freezer entry and return the new row id."""
    with _get_connection() as con:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO freezer (row_one, row_two, category, date) VALUES (?, ?, ?, ?)",
            (row_one, row_two, category, date),
        )
        last_id = cur.lastrowid

    if last_id is None:
        raise RuntimeError("INSERT did not return a row id")
    return last_id


def delete_entry(entry_id: int) -> bool:
    """Delete the entry with the given id. Returns True if a row was removed."""
    with _get_connection() as con:
        cur = con.cursor()
        cur.execute("DELETE FROM freezer WHERE id = ?", (entry_id,))
        removed = cur.rowcount > 0

    return removed
