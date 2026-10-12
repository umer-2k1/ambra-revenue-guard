"""Data-layer verification. Run: ``python3 backend/test_data.py``

Checks the whole Milestone 1 surface without needing any API keys (no
embeddings are generated, only the empty Qdrant collections are created).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_all_denials, get_denials_by_cluster, get_status
from vector_store import close_client, get_collection_counts, init_vector_store, reset_vectors, store_mode

# Test 1: denial cases loaded
denials = get_all_denials()
assert len(denials) == 28, f"Expected 28 denials, got {len(denials)}"
print(f"✓ {len(denials)} denial cases loaded")

# Test 2: clusters (scattered excluded)
clusters = get_denials_by_cluster()
assert len(clusters) == 5, f"Expected 5 clusters, got {len(clusters)}"
for name, cases in clusters.items():
    print(f"    cluster '{name}': {len(cases)} cases")
print(f"✓ {len(clusters)} clusters identified")

# Test 3: payer distribution
payers = sorted({d["payer"] for d in denials})
print(f"✓ {len(payers)} payers: {', '.join(payers)}")

# Test 4: seed field mapping applied
sample = next(d for d in denials if d["id"] == "D-001")
assert sample["denial_reason"], "denial_reason missing (seed mapping failed)"
assert sample["pcr_excerpt"], "pcr_excerpt missing (seed mapping failed)"
print("✓ seed field mapping (denial_reason_text→denial_reason, pcr_narrative_excerpt→pcr_excerpt)")

# Test 5: vector store initialised and empty
init_vector_store()
reset_vectors()  # guarantee a clean slate regardless of earlier runs
counts = get_collection_counts()
assert counts["denial_narratives"] == 0, "denial_narratives should start empty"
assert counts["rule_embeddings"] == 0, "rule_embeddings should start empty"
print(f"✓ vector store initialised ({store_mode()} mode, empty)")

# Test 6: status
status = get_status()
assert status["total_denials"] == 28
print(f"✓ status: {status}")

close_client()
print("\n=== All Milestone 1 tests passed ===")
