"""The demo claim used in Screen 4 (pre-filled, editable in the UI).

A UHC ALS-1 emergency transport that *looks* complete but is deliberately
missing the elements R-001 requires: no explicit transport-necessity
statement, no "why not BLS / private vehicle", no vital signs, and no ALS
interventions beyond a BLS-level aspirin.
"""
from __future__ import annotations

DEMO_CLAIM = {
    "service_type": "ALS-1 Emergency",
    "cpt_code": "A0427",
    "payer": "UnitedHealthcare",
    "narrative": (
        "Dispatched to 742 Evergreen Terrace for a 67-year-old male experiencing "
        "chest pain. Patient found sitting in recliner, alert and oriented x4, "
        "stating 'my chest hurts.' Patient reports pain started approximately 2 "
        "hours ago, rates it 7/10, substernal, non-radiating. Administered aspirin "
        "324mg PO. Transported patient to Memorial General Hospital without incident. "
        "Patient remained stable during transport. Care transferred to ED staff."
    ),
}
