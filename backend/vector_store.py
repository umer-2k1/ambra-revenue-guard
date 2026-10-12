"""Qdrant (local mode) vector store.

Two collections, both 768-dim / cosine:

* ``denial_narratives`` - one point per resolved denial case
* ``rule_embeddings``   - one point per learned prevention rule

Qdrant runs embedded (``QdrantClient(path=...)``) so there is no server to run;
data persists to ``QDRANT_PATH`` on disk.
"""
from __future__ import annotations

import config
from embeddings import TASK_DOC, TASK_QUERY, embed_text
from qdrant_client import QdrantClient, models

DENIAL_COLLECTION = "denial_narratives"
RULE_COLLECTION = "rule_embeddings"

_client: QdrantClient | None = None


def get_client() -> QdrantClient:
    """Return the process-wide Qdrant client (created lazily)."""
    global _client
    if _client is None:
        _client = QdrantClient(path=config.QDRANT_PATH)
    return _client


def close_client() -> None:
    """Release the local Qdrant file lock (used by short-lived scripts)."""
    global _client
    if _client is not None:
        try:
            _client.close()
        finally:
            _client = None


def init_vector_store() -> None:
    """Create both collections if they do not exist."""
    client = get_client()
    for name in (DENIAL_COLLECTION, RULE_COLLECTION):
        if not client.collection_exists(name):
            client.create_collection(
                collection_name=name,
                vectors_config=models.VectorParams(
                    size=config.EMBEDDING_DIM,
                    distance=models.Distance.COSINE,
                ),
            )


def _denial_point_id(denial_id: str) -> int:
    """'D-001' -> 1"""
    return int(denial_id.split("-")[1])


def _rule_point_id(rule_id: str) -> int:
    """'R-001' -> 1001 (offset so it never collides with denial ids)."""
    return 1000 + int(rule_id.split("-")[1])


def add_denial_embedding(denial_case: dict) -> None:
    """Embed and store one resolved denial case."""
    text = (
        f"{denial_case['denial_reason']} | "
        f"{denial_case['pcr_excerpt']} | "
        f"{denial_case['missing_element']}"
    )
    vector = embed_text(text, task_type=TASK_DOC)
    get_client().upsert(
        collection_name=DENIAL_COLLECTION,
        points=[
            models.PointStruct(
                id=_denial_point_id(denial_case["id"]),
                vector=vector,
                payload={
                    "denial_id": denial_case["id"],
                    "carc_code": denial_case.get("carc_code"),
                    "payer": denial_case.get("payer"),
                    "cpt_code": denial_case.get("cpt_code"),
                    "appeal_outcome": denial_case.get("appeal_outcome"),
                    "cluster": denial_case.get("cluster") or "",
                    "text": text,
                },
            )
        ],
    )


def add_rule_embedding(rule: dict) -> None:
    """Embed and store one learned prevention rule."""
    text = (
        f"{rule['rule_title']} | "
        f"{rule['risk_description']} | "
        f"{' '.join(rule['required_elements'])}"
    )
    vector = embed_text(text, task_type=TASK_DOC)
    get_client().upsert(
        collection_name=RULE_COLLECTION,
        points=[
            models.PointStruct(
                id=_rule_point_id(rule["rule_id"]),
                vector=vector,
                payload={
                    "rule_id": rule["rule_id"],
                    "payer_pattern": rule.get("payer_pattern"),
                    "cpt_pattern": rule.get("cpt_pattern"),
                    "carc_pattern": rule.get("carc_pattern"),
                    "service_pattern": rule.get("service_pattern"),
                    "confidence": rule.get("confidence"),
                    "severity": rule.get("severity"),
                    "source_count": rule.get("source_count"),
                    "avg_denied_amount": rule.get("avg_denied_amount"),
                    "text": text,
                },
            )
        ],
    )


def query_similar_rules(claim_text: str, n_results: int = 5) -> list[dict]:
    """Semantic search over learned rules.

    Deliberately unfiltered: the scoring agent treats vector hits as *candidates*
    and merges them with exact payer/CPT matches from SQL, so a claim can be
    checked against cross-payer rules that describe the same failure mode.
    """
    vector = embed_text(claim_text, task_type=TASK_QUERY)
    response = get_client().query_points(
        collection_name=RULE_COLLECTION,
        query=vector,
        limit=n_results,
        with_payload=True,
    )
    return [
        {
            "rule_id": point.payload.get("rule_id"),
            "similarity_score": point.score,
            "payload": point.payload,
        }
        for point in response.points
    ]


def get_collection_counts() -> dict:
    """Return the point count in each collection."""
    client = get_client()
    return {
        DENIAL_COLLECTION: client.count(DENIAL_COLLECTION).count,
        RULE_COLLECTION: client.count(RULE_COLLECTION).count,
    }


def reset_vectors() -> None:
    """Delete and recreate both collections (empty state)."""
    client = get_client()
    for name in (DENIAL_COLLECTION, RULE_COLLECTION):
        if client.collection_exists(name):
            client.delete_collection(name)
        client.create_collection(
            collection_name=name,
            vectors_config=models.VectorParams(
                size=config.EMBEDDING_DIM,
                distance=models.Distance.COSINE,
            ),
        )
