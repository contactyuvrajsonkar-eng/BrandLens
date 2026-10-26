import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from backend.rules_engine import DEFAULT_APPROVED_FACTS, DEFAULT_BANNED_TERMS


def _database_path() -> Path:
    configured_path = os.environ.get("BRANDLENS_DB_PATH")
    if configured_path:
        return Path(configured_path)
    return Path(__file__).resolve().parent / "brandlens.db"


@contextmanager
def _connection():
    path = _database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def initialize_database() -> None:
    with _connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS rules (
                rule_id TEXT PRIMARY KEY,
                term TEXT NOT NULL UNIQUE COLLATE NOCASE,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS facts (
                fact_id TEXT PRIMARY KEY,
                text TEXT NOT NULL UNIQUE COLLATE NOCASE,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'needs_review',
                reviewer_note TEXT NOT NULL DEFAULT '',
                findings TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                review_id INTEGER NOT NULL REFERENCES reviews(id),
                action TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            """
        )
        created_at = _now()
        for index, term in enumerate(DEFAULT_BANNED_TERMS, start=1):
            connection.execute(
                "INSERT OR IGNORE INTO rules (rule_id, term, created_at) VALUES (?, ?, ?)",
                (f"G-{index:03d}", term, created_at),
            )
        for index, fact in enumerate(DEFAULT_APPROVED_FACTS, start=1):
            connection.execute(
                "INSERT OR IGNORE INTO facts (fact_id, text, created_at) VALUES (?, ?, ?)",
                (f"F-{index:03d}", fact, created_at),
            )


def get_policy() -> dict[str, list[dict[str, str]]]:
    with _connection() as connection:
        rules = connection.execute(
            "SELECT rule_id, term, created_at FROM rules ORDER BY rule_id"
        ).fetchall()
        facts = connection.execute(
            "SELECT fact_id, text, created_at FROM facts ORDER BY fact_id"
        ).fetchall()
    return {
        "rules": [dict(row) for row in rules],
        "facts": [dict(row) for row in facts],
    }


def add_rule(term: str) -> dict[str, str]:
    rule = {"rule_id": f"G-{uuid4().hex[:8].upper()}", "term": term.strip(), "created_at": _now()}
    with _connection() as connection:
        connection.execute(
            "INSERT INTO rules (rule_id, term, created_at) VALUES (?, ?, ?)",
            (rule["rule_id"], rule["term"], rule["created_at"]),
        )
    return rule


def add_fact(text: str) -> dict[str, str]:
    fact = {"fact_id": f"F-{uuid4().hex[:8].upper()}", "text": text.strip(), "created_at": _now()}
    with _connection() as connection:
        connection.execute(
            "INSERT INTO facts (fact_id, text, created_at) VALUES (?, ?, ?)",
            (fact["fact_id"], fact["text"], fact["created_at"]),
        )
    return fact


def create_review(title: str, content: str, findings: list[dict[str, Any]]) -> dict[str, Any]:
    created_at = _now()
    with _connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO reviews (title, content, status, findings, created_at, updated_at)
            VALUES (?, ?, 'needs_review', ?, ?, ?)
            """,
            (title.strip() or "Untitled draft", content, json.dumps(findings), created_at, created_at),
        )
        review_id = cursor.lastrowid
        connection.execute(
            "INSERT INTO audit_events (review_id, action, created_at) VALUES (?, ?, ?)",
            (review_id, "Review completed", created_at),
        )
    return get_review(int(review_id))


def list_reviews(limit: int = 30) -> list[dict[str, Any]]:
    with _connection() as connection:
        rows = connection.execute(
            """
            SELECT id, title, status, reviewer_note, findings, created_at, updated_at
            FROM reviews ORDER BY id DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [_review_record(row, include_content=False) for row in rows]


def get_review(review_id: int) -> dict[str, Any] | None:
    with _connection() as connection:
        row = connection.execute(
            "SELECT * FROM reviews WHERE id = ?", (review_id,)
        ).fetchone()
        if row is None:
            return None
        events = connection.execute(
            """
            SELECT action, note, created_at FROM audit_events
            WHERE review_id = ? ORDER BY id ASC
            """,
            (review_id,),
        ).fetchall()
    review = _review_record(row, include_content=True)
    review["audit_log"] = [dict(event) for event in events]
    return review


def decide_review(review_id: int, decision: str, note: str) -> dict[str, Any] | None:
    updated_at = _now()
    action = "Approved by reviewer" if decision == "approved" else "Changes requested"
    with _connection() as connection:
        cursor = connection.execute(
            """
            UPDATE reviews SET status = ?, reviewer_note = ?, updated_at = ?
            WHERE id = ?
            """,
            (decision, note.strip(), updated_at, review_id),
        )
        if cursor.rowcount == 0:
            return None
        connection.execute(
            """
            INSERT INTO audit_events (review_id, action, note, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (review_id, action, note.strip(), updated_at),
        )
    return get_review(review_id)


def _review_record(row: sqlite3.Row, include_content: bool) -> dict[str, Any]:
    findings = json.loads(row["findings"])
    record: dict[str, Any] = {
        "id": row["id"],
        "title": row["title"],
        "status": row["status"],
        "reviewer_note": row["reviewer_note"],
        "findings": findings,
        "total_issues": len(findings),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
    if include_content:
        record["content"] = row["content"]
    return record
