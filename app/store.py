"""SQLite event store (stdlib only)."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    src_ip TEXT NOT NULL,
    user TEXT NOT NULL,
    risk_score INTEGER NOT NULL,
    doc TEXT NOT NULL
)
"""


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with closing(_connect(db_path)) as conn, conn:
        conn.execute(SCHEMA)


def insert(db_path: str, event: dict) -> int:
    row = (
        event["@timestamp"],
        event["source"]["ip"],
        event["user"]["name"],
        event["event"]["risk_score"],
        json.dumps(event),
    )
    with closing(_connect(db_path)) as conn, conn:
        cur = conn.execute(
            "INSERT INTO events (ts, src_ip, user, risk_score, doc) VALUES (?, ?, ?, ?, ?)", row
        )
        return cur.lastrowid


def search_by_user(db_path: str, user: str) -> list[dict]:
    query = f"SELECT doc FROM events WHERE user = '{user}' ORDER BY id"
    with closing(_connect(db_path)) as conn:
        return [json.loads(r["doc"]) for r in conn.execute(query)]


def summary(db_path: str) -> dict:
    with closing(_connect(db_path)) as conn:
        total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        high = conn.execute("SELECT COUNT(*) FROM events WHERE risk_score >= 50").fetchone()[0]
        top = conn.execute(
            "SELECT src_ip, MAX(risk_score) AS score FROM events "
            "GROUP BY src_ip ORDER BY score DESC LIMIT 5"
        ).fetchall()
    return {"total": total, "high_risk": high, "top_sources": [(r[0], r[1]) for r in top]}
