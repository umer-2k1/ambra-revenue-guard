"""One-off enrichment: turn each seed denial into a full "case file".

Adds three fields to every case in ``data/seed_denials.json``:

* ``timeline``      - claim -> denial -> appeal -> resolution, from the real dates
* ``appeal_letter`` - the appeal we sent (reuses each case's own appeal_strategy text)
* ``payer_notes``   - call / portal / remittance notes

Everything is derived from the case's own authored fields (dates, amounts,
payer, CARC/CPT, appeal_strategy), so the generated history stays consistent
with the data. Idempotent: re-running overwrites the three fields.

Run:  python3 scripts/enrich_seed.py
"""
from __future__ import annotations

import json
import os
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = os.path.join(ROOT, "backend", "data", "seed_denials.json")


def money(n) -> str:
    return f"${n:,.0f}" if n else "$0"


def d(iso: str) -> date:
    return date.fromisoformat(iso)


def plus(iso: str, days: int) -> str:
    return (d(iso) + timedelta(days=days)).isoformat()


def clean_strategy(s: str) -> str:
    s = (s or "").strip()
    low = s.lower()
    if low.startswith("added language:"):
        s = s[len("added language:"):].strip()
        s = s.strip().strip('"').strip("'")
    return s


RESOLUTION_LABEL = {
    "overturned": "Overturned on appeal",
    "partially_overturned": "Partially overturned on appeal",
    "denied": "Appeal upheld — denial stands",
    "corrected_resubmitted": "Corrected and resubmitted",
    "downgraded_resubmitted": "Downgraded and resubmitted",
    "accepted_downgrade": "Accepted downgrade and rebilled",
    "no_appeal_needed": "Closed — no appeal needed",
}


def build_timeline(c: dict) -> list[dict]:
    reason = c.get("denial_reason_text") or c.get("denial_reason")
    events = []

    events.append(
        {
            "date": c["claim_date"],
            "kind": "claim",
            "title": "Claim submitted",
            "detail": f"{c['service_type']} transport ({c['cpt_code']}) billed to {c['payer']} for {money(c['billed_amount'])}.",
        }
    )
    events.append(
        {
            "date": c["denial_date"],
            "kind": "denial",
            "title": f"Denial received — {c['carc_code']}",
            "detail": reason,
        }
    )

    if c.get("days_to_appeal"):
        events.append(
            {
                "date": plus(c["denial_date"], c["days_to_appeal"]),
                "kind": "appeal",
                "title": "Appeal filed",
                "detail": f"First-level appeal submitted {c['days_to_appeal']} days after the denial, with the PCR and supporting documentation attached.",
            }
        )

    events.append(
        {
            "date": c["resolution_date"],
            "kind": "resolution",
            "title": RESOLUTION_LABEL.get(c["appeal_outcome"], c["appeal_outcome"].replace("_", " ").title()),
            "detail": (
                f"{money(c['paid_after_appeal'])} recovered of {money(c['denied_amount'])} denied."
                if c.get("paid_after_appeal")
                else f"{money(c['denied_amount'])} written off."
            ),
        }
    )
    return events


def build_letter(c: dict) -> str | None:
    outcome = c["appeal_outcome"]
    if outcome in {"corrected_resubmitted", "downgraded_resubmitted", "accepted_downgrade", "no_appeal_needed"}:
        return None  # resolved internally, not by appeal

    appeal_date = plus(c["denial_date"], c.get("days_to_appeal") or 3)
    body = clean_strategy(c["appeal_strategy"])
    reason = c.get("denial_reason_text") or c.get("denial_reason")

    return (
        f"Date: {appeal_date}\n"
        f"To: {c['payer']} — Appeals Department\n"
        f"Re: Denial of {c['service_type']} transport · CPT {c['cpt_code']} · DOS {c['claim_date']} · {c['carc_code']}\n\n"
        f"To whom it may concern,\n\n"
        f"We are formally appealing the denial of the above claim, denied with the reason: "
        f"\"{reason}\"\n\n"
        f"The transport was medically necessary and properly documented. {body}\n\n"
        f"We respectfully request reprocessing and payment of {money(c['denied_amount'])}. "
        f"The patient care report, physician documentation, and applicable medical-necessity criteria are attached.\n\n"
        f"Sincerely,\nAmbra Revenue Recovery — Appeals Team"
    )


def build_notes(c: dict) -> list[dict]:
    outcome = c["appeal_outcome"]
    notes = [
        {
            "date": plus(c["denial_date"], 1),
            "channel": "call",
            "text": (
                f"Called {c['payer']} provider services. Representative confirmed the denial ({c['carc_code']}) "
                f"is documentation-based and directed us to file a first-level appeal with the PCR attached."
            ),
        }
    ]

    if c.get("days_to_appeal"):
        appeal_date = plus(c["denial_date"], c["days_to_appeal"])
        notes.append(
            {
                "date": appeal_date,
                "channel": "portal",
                "text": f"First-level appeal uploaded to the {c['payer']} provider portal with the PCR and medical-necessity statement.",
            }
        )

    if outcome in {"corrected_resubmitted", "downgraded_resubmitted", "accepted_downgrade"}:
        notes.append(
            {
                "date": c["resolution_date"],
                "channel": "note",
                "text": clean_strategy(c["appeal_strategy"]),
            }
        )
    elif outcome == "no_appeal_needed":
        notes.append(
            {
                "date": c["resolution_date"],
                "channel": "note",
                "text": clean_strategy(c["appeal_strategy"]),
            }
        )
    else:
        notes.append(
            {
                "date": c["resolution_date"],
                "channel": "remit",
                "text": (
                    f"Payer response received: {RESOLUTION_LABEL.get(outcome, outcome)}"
                    + (f", {money(c['paid_after_appeal'])} recovered." if c.get("paid_after_appeal") else ".")
                ),
            }
        )
    return notes


def main() -> None:
    with open(SEED, encoding="utf-8") as fh:
        cases = json.load(fh)

    for c in cases:
        c["timeline"] = build_timeline(c)
        c["appeal_letter"] = build_letter(c)
        c["payer_notes"] = build_notes(c)

    with open(SEED, "w", encoding="utf-8") as fh:
        json.dump(cases, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print(f"enriched {len(cases)} cases with timeline / appeal_letter / payer_notes")


if __name__ == "__main__":
    main()
