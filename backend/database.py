"""Database storage: schema, seed loading, and queries.

Works against **either** backend:

* **PostgreSQL** (Neon, or any Postgres) when ``DATABASE_URL`` is set — used in
  the cloud, where there is no persistent local disk.
* **SQLite** (a local file) otherwise — zero-setup local development.

Set ``DATABASE_URL`` to switch; nothing else changes. The three tables are the
same in both:

* ``denial_cases``     - the 28 seed cases (loaded once)
* ``prevention_rules`` - learned rules (empty until "Analyze" runs)
* ``claim_scores``     - audit trail of scored claims

Importing this module initialises the schema and loads the seed data.
"""
from __future__ import annotations

import json
import re
import sqlite3
from typing import Any, Optional

from config import DATABASE_PATH, DATABASE_URL, SEED_DATA_PATH

IS_POSTGRES = bool(DATABASE_URL)
_FLOAT = "DOUBLE PRECISION" if IS_POSTGRES else "REAL"

_SCHEMA_TEMPLATE = """
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
    billed_amount   __FLOAT__,
    denied_amount   __FLOAT__,
    paid_after_appeal __FLOAT__,
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
    plain_title         TEXT,
    plain_summary       TEXT,
    payer_pattern       TEXT,
    cpt_pattern         TEXT,
    carc_pattern        TEXT,
    service_pattern     TEXT,
    rule_title          TEXT NOT NULL,
    risk_description    TEXT,
    required_elements   TEXT NOT NULL,
    recommended_phrases TEXT,
    confidence          __FLOAT__,
    severity            TEXT,
    avg_denied_amount   __FLOAT__,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS claim_scores (
    score_id        TEXT PRIMARY KEY,
    claim_narrative TEXT,
    service_type    TEXT,
    cpt_code        TEXT,
    payer           TEXT,
    overall_risk    TEXT,
    risk_score      __FLOAT__,
    flags_found     INTEGER,
    flags_detail    TEXT,
    rules_matched   TEXT,
    scored_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
SCHEMA = _SCHEMA_TEMPLATE.replace("__FLOAT__", _FLOAT)

# Columns preserved as JSON inside the DB.
_RULE_JSON_FIELDS = ("source_denials", "required_elements", "recommended_phrases")
_SCORE_JSON_FIELDS = ("flags_detail", "rules_matched")
_DENIAL_JSON_FIELDS = ("timeline", "payer_notes")

# Seed JSON key -> denial_cases column.
_SEED_FIELD_MAP = {
    "denial_reason_text": "denial_reason",
    "pcr_narrative_excerpt": "pcr_excerpt",
}


# ── Connection adapter (SQLite or Postgres) ──────────────────────────────────
def _translate(sql: str) -> str:
    """Convert ``:name`` placeholders to psycopg's ``%(name)s`` (Postgres only)."""
    if not IS_POSTGRES:
        return sql
    return re.sub(r":([A-Za-z_]\w*)", r"%(\1)s", sql)


class _Connection:
    """Small adapter so the rest of the module is backend-agnostic."""

    def __init__(self) -> None:
        if IS_POSTGRES:
            import psycopg
            from psycopg.rows import dict_row

            self._raw = psycopg.connect(DATABASE_URL, row_factory=dict_row)
        else:
            self._raw = sqlite3.connect(DATABASE_PATH)
            self._raw.row_factory = sqlite3.Row

    def __enter__(self) -> "_Connection":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is None:
            self._raw.commit()
        else:
            self._raw.rollback()
        self._raw.close()

    def execute(self, sql: str, params: Optional[dict] = None) -> list[dict]:
        cur = self._raw.execute(_translate(sql), params or {})
        if cur.description is None:
            return []
        return [dict(row) for row in cur.fetchall()]

    def executemany(self, sql: str, rows: list[dict]) -> None:
        if IS_POSTGRES:
            with self._raw.cursor() as cur:
                cur.executemany(_translate(sql), rows)
        else:
            self._raw.executemany(_translate(sql), rows)

    def execute_script(self, script: str) -> None:
        for statement in (s.strip() for s in script.split(";")):
            if statement:
                self._raw.execute(_translate(statement))


def _connect() -> _Connection:
    return _Connection()


def _placeholder(col: str) -> str:
    return f":{col}"


def _upsert_sql(table: str, columns: list[str], pk: str) -> str:
    cols = ", ".join(columns)
    values = ", ".join(_placeholder(c) for c in columns)
    if IS_POSTGRES:
        updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in columns if c != pk)
        return (
            f"INSERT INTO {table} ({cols}) VALUES ({values}) "
            f"ON CONFLICT ({pk}) DO UPDATE SET {updates}"
        )
    return f"INSERT OR REPLACE INTO {table} ({cols}) VALUES ({values})"


def _insert_ignore_sql(table: str, columns: list[str], pk: str) -> str:
    cols = ", ".join(columns)
    values = ", ".join(_placeholder(c) for c in columns)
    if IS_POSTGRES:
        return f"INSERT INTO {table} ({cols}) VALUES ({values}) ON CONFLICT ({pk}) DO NOTHING"
    return f"INSERT OR IGNORE INTO {table} ({cols}) VALUES ({values})"


def _dump(value: Any) -> Optional[str]:
    if value is None or isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, default=str)


def _load(value: Any) -> Any:
    if value is None:
        return None
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return value


# ── Setup ────────────────────────────────────────────────────────────────────
def _existing_columns(conn: _Connection, table: str) -> set[str]:
    if IS_POSTGRES:
        rows = conn.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = :t",
            {"t": table},
        )
        return {row["column_name"] for row in rows}
    return {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}


def _ensure_columns(conn: _Connection, table: str, columns: dict[str, str]) -> None:
    """Add any missing columns (lightweight migration for an existing DB)."""
    existing = _existing_columns(conn, table)
    for name, ddl in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")


def init_db() -> None:
    """Create the three tables and apply lightweight migrations (idempotent)."""
    with _connect() as conn:
        conn.execute_script(SCHEMA)
        _ensure_columns(
            conn,
            "denial_cases",
            {"timeline": "TEXT", "appeal_letter": "TEXT", "payer_notes": "TEXT"},
        )
        _ensure_columns(
            conn,
            "prevention_rules",
            {"plain_title": "TEXT", "plain_summary": "TEXT"},
        )


def load_seed_data() -> int:
    """Insert the 28 seed denial cases if the table is empty or un-enriched."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT COUNT(*) AS n, SUM(CASE WHEN timeline IS NULL THEN 1 ELSE 0 END) AS unenriched "
            "FROM denial_cases"
        )
        summary = rows[0] if rows else {"n": 0, "unenriched": 0}
        if summary["n"] and not summary["unenriched"]:
            return 0
        if summary["n"]:  # existing rows predate the case-file fields -> reseed
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

        conn.executemany(_insert_ignore_sql("denial_cases", columns, "id"), rows)
        return len(rows)


# ── Denial queries ───────────────────────────────────────────────────────────
def get_all_denials() -> list[dict]:
    """Return all denial cases (ordered by id) as dicts, JSON fields parsed."""
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM denial_cases ORDER BY id")
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
    skipped. Ordering follows id order, so rule numbering is deterministic.
    """
    clusters: dict[str, list[dict]] = {}
    for case in get_all_denials():
        cluster = (case.get("cluster") or "").strip()
        if not cluster or cluster == "scattered":
            continue
        clusters.setdefault(cluster, []).append(case)
    return clusters


# ── Rule storage ─────────────────────────────────────────────────────────────
_RULE_COLUMNS = [
    "rule_id", "source_denials", "source_count", "plain_title", "plain_summary",
    "payer_pattern", "cpt_pattern", "carc_pattern", "service_pattern", "rule_title",
    "risk_description", "required_elements", "recommended_phrases",
    "confidence", "severity", "avg_denied_amount",
]


def insert_rule(rule: dict) -> None:
    """Insert (or update) an extracted prevention rule."""
    payload = {k: (_dump(v) if k in _RULE_JSON_FIELDS else v) for k, v in rule.items()}
    values = {c: payload.get(c) for c in _RULE_COLUMNS}
    with _connect() as conn:
        conn.execute(_upsert_sql("prevention_rules", _RULE_COLUMNS, "rule_id"), values)


def _row_to_rule(row: dict) -> dict:
    rule = dict(row)
    for field in _RULE_JSON_FIELDS:
        rule[field] = _load(rule.get(field))
    return rule


def get_all_rules() -> list[dict]:
    """Return all prevention rules, JSON fields parsed."""
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM prevention_rules ORDER BY rule_id")
    return [_row_to_rule(r) for r in rows]


def get_rule(rule_id: str) -> Optional[dict]:
    """Return a single rule by id, or ``None``."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM prevention_rules WHERE rule_id = :rule_id",
            {"rule_id": rule_id},
        )
    return _row_to_rule(rows[0]) if rows else None


# ── Score storage ────────────────────────────────────────────────────────────
_SCORE_COLUMNS = [
    "score_id", "claim_narrative", "service_type", "cpt_code", "payer",
    "overall_risk", "risk_score", "flags_found", "flags_detail", "rules_matched",
]


def insert_score(score: dict) -> None:
    """Insert a claim score record (JSON fields serialized)."""
    payload = {k: (_dump(v) if k in _SCORE_JSON_FIELDS else v) for k, v in score.items()}
    values = {c: payload.get(c) for c in _SCORE_COLUMNS}
    with _connect() as conn:
        conn.execute(_upsert_sql("claim_scores", _SCORE_COLUMNS, "score_id"), values)


# ── Status / reset ───────────────────────────────────────────────────────────
def get_status() -> dict:
    """Return row counts for the three tables."""
    with _connect() as conn:
        denials = conn.execute("SELECT COUNT(*) AS n FROM denial_cases")[0]["n"]
        rules = conn.execute("SELECT COUNT(*) AS n FROM prevention_rules")[0]["n"]
        scores = conn.execute("SELECT COUNT(*) AS n FROM claim_scores")[0]["n"]
    return {"total_denials": denials, "total_rules": rules, "total_scores": scores}


def reset_analysis() -> None:
    """Delete every rule and score. Seed denial cases are never touched."""
    with _connect() as conn:
        conn.execute("DELETE FROM prevention_rules")
        conn.execute("DELETE FROM claim_scores")


# Initialise on import so the app always has a usable database.
init_db()
load_seed_data()
