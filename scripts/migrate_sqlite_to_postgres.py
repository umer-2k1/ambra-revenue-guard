"""One-off: copy ``prevention_rules`` + ``claim_scores`` from the local SQLite
file into Postgres (Neon).

Denial cases are *not* copied — the app seeds those from
``data/seed_denials.json`` on startup. Run this **after** ``DATABASE_URL`` is
set. Idempotent (upserts by primary key).

    python3 scripts/migrate_sqlite_to_postgres.py
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "backend"))

import config  # noqa: E402
from database import IS_POSTGRES, get_status, insert_rule, insert_score  # noqa: E402

SQLITE_PATH = os.path.join(ROOT, "backend", "data", "ambra_demo.db")
RULE_JSON = ("source_denials", "required_elements", "recommended_phrases")
SCORE_JSON = ("flags_detail", "rules_matched")


def _load(value):
    if value is None:
        return None
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return value


def main() -> None:
    if not IS_POSTGRES:
        print("DATABASE_URL is not set — set it in .env first.")
        return
    if not os.path.exists(SQLITE_PATH):
        print(f"No local SQLite file at {SQLITE_PATH}; nothing to migrate.")
        return

    con = sqlite3.connect(SQLITE_PATH)
    con.row_factory = sqlite3.Row
    rules = [dict(r) for r in con.execute("SELECT * FROM prevention_rules")]
    scores = [dict(r) for r in con.execute("SELECT * FROM claim_scores")]
    con.close()

    for rule in rules:
        for field in RULE_JSON:
            rule[field] = _load(rule.get(field))
        insert_rule(rule)

    for score in scores:
        for field in SCORE_JSON:
            score[field] = _load(score.get(field))
        insert_score(score)

    print(f"migrated {len(rules)} rules + {len(scores)} scores -> postgres")
    print("postgres status:", get_status())


if __name__ == "__main__":
    main()
