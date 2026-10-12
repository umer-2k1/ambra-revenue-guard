"""SQLite storage: schema, seed loading, and queries.

The database holds three tables:

* ``denial_cases``     - the 28 seed cases (loaded once, never deleted)
* ``prevention_rules`` - learned rules (empty until "Analyze" runs)
* ``claim_scores``     - audit trail of scored claims

Importing this module initialises the schema and loads the seed data.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Any, Optional

from config import DATABASE_PATH, SEED_DATA_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS denial_cases (
    id              TEXT PRIMARY KEY,
    cluster         TEXT,
    payer           TEXT NOT NULL,
    payer_id        TEXT,
    claim_date      TEXT,
    denial_date     TEXT,
    resolution_date TEXT,
    service_type    TEXT,
    cpt_code        TEXT,
    billed_amount   REAL,
    denied_amount   REAL,
    paid_after_appeal REAL,
    carc_code       TEXT,
    rarc_code       TEXT,
    denial_reason   TEXT,
    pcr_excerpt     TEXT,
    missing_element TEXT,
    appeal_strategy TEXT,
    appeal_outcome  TEXT,
    days_to_appeal  INTEGER,
    region          TEXT,
    timeline        TEXT,
    appeal_letter   TEXT,
    payer_notes     TEXT,
    ingested_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS prevention_rules (
    rule_id             TEXT PRIMARY KEY,
    source_denials      TEXT NOT NULL,
    source_count        INTEGER,
    payer_pattern       TEXT,
    cpt_pattern         TEXT,
    carc_pattern        TEXT,
    service_pattern     TEXT,
    rule_title          TEXT NOT NULL,
    risk_description    TEXT,
    required_elements   TEXT NOT NULL,
    recommended_phrases TEXT,
    confidence          REAL,
    severity            TEXT,
    avg_denied_amount   REAL,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS claim_scores (
    score_id        TEXT PRIMARY KEY,
    claim_narrative TEXT,
    service_type    TEXT,
    cpt_code        TEXT,
    payer           TEXT,
    overall_risk    TEXT,
    risk_score      REAL,
    flags_found     INTEGER,
    flags_detail    TEXT,
    rules_matched   TEXT,
    scored_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# Columns preserved as JSON inside the DB.
_RULE_JSON_FIELDS = ("source_denials", "required_elements", "recommended_phrases")
_SCORE_JSON_FIELDS = ("flags_detail", "rules_matched")
_DENIAL_JSON_FIELDS = ("timeline", "payer_notes")

# Seed JSON key -> denial_cases column.
_SEED_FIELD_MAP = {
    "denial_reason_text": "denial_reason",
    "pcr_narrative_excerpt": "pcr_excerpt",
}


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _dump(value: Any) -> Optional[str]:
    if value is None or isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def _load(value: Any) -> Any:
    if value is None:
        return None
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return value


# ── Setup ────────────────────────────────────────────────────────────────────
def _ensure_columns(conn: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
    """Add any missing columns (lightweight migration for an existing DB file)."""
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
    for name, ddl in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")


def init_db() -> None:
    """Create the three tables and apply lightweight migrations (idempotent)."""
    with _connect() as conn:
        conn.executescript(SCHEMA)
        _ensure_columns(
            conn,
            "denial_cases",
            {"timeline": "TEXT", "appeal_letter": "TEXT", "payer_notes": "TEXT"},
        )


def load_seed_data() -> int:
    """Insert the 28 seed denial cases if the table is empty.

    Returns the number of rows inserted. Safe to call repeatedly.
    """
    with _connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n, SUM(CASE WHEN timeline IS NULL THEN 1 ELSE 0 END) AS unenriched "
            "FROM denial_cases"
        ).fetchone()
        if row["n"] and not row["unenriched"]:
            return 0
        if row["n"]:  # existing rows predate the case-file fields -> reseed
            conn.execute("DELETE FROM denial_cases")

        with open(SEED_DATA_PATH, encoding="utf-8") as fh:
            cases = json.load(fh)

        columns = [
            "id", "cluster", "payer", "payer_id", "claim_date", "denial_date",
            "resolution_date", "service_type", "cpt_code", "billed_amount",
            "denied_amount", "paid_after_appeal", "carc_code", "rarc_code",
            "denial_reason", "pcr_excerpt", "missing_element", "appeal_strategy",
            "appeal_outcome", "days_to_appeal", "region",
            "timeline", "appeal_letter", "payer_notes",
        ]

        rows = []
        for case in cases:
            normalized = {_SEED_FIELD_MAP.get(k, k): v for k, v in case.items()}
            row = {col: normalized.get(col) for col in columns}
            for field in _DENIAL_JSON_FIELDS:
                row[field] = _dump(row.get(field))
            rows.append(row)

        placeholders = ", ".join(f":{c}" for c in columns)
        conn.executemany(
            f"INSERT OR IGNORE INTO denial_cases ({', '.join(columns)}) VALUES ({placeholders})",
            rows,
        )
        return len(rows)


# ── Denial queries ───────────────────────────────────────────────────────────
def get_all_denials() -> list[dict]:
    """Return all denial cases (ordered by id) as dicts, JSON fields parsed."""
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM denial_cases ORDER BY id").fetchall()
    cases = []
    for row in rows:
        case = dict(row)
        for field in _DENIAL_JSON_FIELDS:
            case[field] = _load(case.get(field))
        cases.append(case)
    return cases


def get_denials_by_cluster() -> dict[str, list[dict]]:
    """Group denial cases by their ``cluster`` field.

    Cases with a null/empty cluster or the catch-all ``scattered`` cluster are
    skipped, since they do not form a meaningful pattern. Insertion order of
    the returned dict follows id order, so rule numbering is deterministic.
    """
    clusters: dict[str, list[dict]] = {}
    for case in get_all_denials():
        cluster = (case.get("cluster") or "").strip()
        if not cluster or cluster == "scattered":
            continue
        clusters.setdefault(cluster, []).append(case)
    return clusters


# ── Rule storage ─────────────────────────────────────────────────────────────
def insert_rule(rule: dict) -> None:
    """Insert (or replace) an extracted prevention rule."""
    payload = {k: (_dump(v) if k in _RULE_JSON_FIELDS else v) for k, v in rule.items()}
    columns = [
        "rule_id", "source_denials", "source_count", "payer_pattern",
        "cpt_pattern", "carc_pattern", "service_pattern", "rule_title",
        "risk_description", "required_elements", "recommended_phrases",
        "confidence", "severity", "avg_denied_amount",
    ]
    values = {c: payload.get(c) for c in columns}
    placeholders = ", ".join(f":{c}" for c in columns)
    with _connect() as conn:
        conn.execute(
            f"INSERT OR REPLACE INTO prevention_rules ({', '.join(columns)}) VALUES ({placeholders})",
            values,
        )


def _row_to_rule(row: sqlite3.Row) -> dict:
    rule = dict(row)
    for field in _RULE_JSON_FIELDS:
        rule[field] = _load(rule.get(field))
    return rule


def get_all_rules() -> list[dict]:
    """Return all prevention rules, JSON fields parsed."""
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM prevention_rules ORDER BY rule_id").fetchall()
    return [_row_to_rule(r) for r in rows]


def get_rule(rule_id: str) -> Optional[dict]:
    """Return a single rule by id, or ``None``."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM prevention_rules WHERE rule_id = ?", (rule_id,)
        ).fetchone()
    return _row_to_rule(row) if row else None


# ── Score storage ────────────────────────────────────────────────────────────
def insert_score(score: dict) -> None:
    """Insert a claim score record (JSON fields serialized)."""
    payload = {k: (_dump(v) if k in _SCORE_JSON_FIELDS else v) for k, v in score.items()}
    columns = [
        "score_id", "claim_narrative", "service_type", "cpt_code", "payer",
        "overall_risk", "risk_score", "flags_found", "flags_detail", "rules_matched",
    ]
    values = {c: payload.get(c) for c in columns}
    placeholders = ", ".join(f":{c}" for c in columns)
    with _connect() as conn:
        conn.execute(
            f"INSERT OR REPLACE INTO claim_scores ({', '.join(columns)}) VALUES ({placeholders})",
            values,
        )


# ── Status / reset ───────────────────────────────────────────────────────────
def get_status() -> dict:
    """Return row counts for the three tables."""
    with _connect() as conn:
        denials = conn.execute("SELECT COUNT(*) AS n FROM denial_cases").fetchone()["n"]
        rules = conn.execute("SELECT COUNT(*) AS n FROM prevention_rules").fetchone()["n"]
        scores = conn.execute("SELECT COUNT(*) AS n FROM claim_scores").fetchone()["n"]
    return {"total_denials": denials, "total_rules": rules, "total_scores": scores}


def reset_analysis() -> None:
    """Delete every rule and score. Seed denial cases are never touched."""
    with _connect() as conn:
        conn.execute("DELETE FROM prevention_rules")
        conn.execute("DELETE FROM claim_scores")


# Initialise on import so the app always has a usable database.
init_db()
load_seed_data()
