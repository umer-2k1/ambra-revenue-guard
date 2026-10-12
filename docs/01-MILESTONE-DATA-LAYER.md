# Milestone 1: Project Setup + Data Layer

## Goal
Set up the Python project, create SQLite and Qdrant schemas, load seed data, and verify everything works with a simple test script.

## Completion Criteria
- `pip install -r requirements.txt` succeeds
- Running `python backend/database.py` creates SQLite DB with 3 tables, loads 28 denial cases
- Running `python backend/vector_store.py` initializes empty Qdrant collections
- Running `python backend/test_data.py` prints confirmation that all data is correct

---

## Step 1: Project Structure

Create these files:
```
ambra-demo/
├── data/
│   └── seed_denials.json          # Already exists (28 cases)
├── backend/
│   ├── __init__.py
│   ├── config.py                  # Environment variables + paths
│   ├── models.py                  # Pydantic models
│   ├── database.py                # SQLite setup + queries
│   ├── vector_store.py            # Qdrant setup + operations
│   └── test_data.py               # Verification script
├── .env.example
├── .gitignore
└── requirements.txt
```

## Step 2: requirements.txt

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
openai>=1.3.0                   # Used for DeepSeek (OpenAI-compatible API)
qdrant-client>=1.9.0
google-generativeai>=0.8.0      # Gemini embeddings
pydantic>=2.5.0
python-dotenv>=1.0.0
sse-starlette>=1.8.0
```

## Step 3: .env.example

```
DEEPSEEK_API_KEY=sk-your-key-here
GEMINI_API_KEY=your-gemini-key-here
LLM_MODEL=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com
EMBEDDING_MODEL=models/text-embedding-004
DATABASE_PATH=./data/ambra_demo.db
QDRANT_PATH=./data/qdrant_db
```

## Step 4: .gitignore

```
__pycache__/
*.pyc
.env
data/ambra_demo.db
data/qdrant_db/
node_modules/
dist/
.vite/
```

## Step 5: config.py

```python
import os
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "models/text-embedding-004")
DATABASE_PATH = os.getenv("DATABASE_PATH", "./data/ambra_demo.db")
QDRANT_PATH = os.getenv("QDRANT_PATH", "./data/qdrant_db")
SEED_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "seed_denials.json")
```

## Step 6: models.py

Create ALL Pydantic models as defined in the Master Spec section 5.3. Copy them exactly:

- `DenialCase` — maps to `denial_cases` table and seed JSON
- `ExtractedRule` — maps to `prevention_rules` table
- `ClaimFlag` — nested in ClaimScoreResult
- `ClaimScoreResult` — maps to `claim_scores` table
- `AnalysisProgress` — SSE event payload

## Step 7: database.py

This file must do the following:

### 7a: `init_db()` function
- Connect to SQLite at `DATABASE_PATH`
- Create all 3 tables (denial_cases, prevention_rules, claim_scores) using the exact SQL from Master Spec section 5.1
- Use `IF NOT EXISTS` so it's safe to call repeatedly

### 7b: `load_seed_data()` function
- Read `seed_denials.json`
- Check if `denial_cases` table already has data — if yes, skip
- Insert all 28 cases using `INSERT OR IGNORE`
- Map JSON field names to table columns:
  - `denial_reason_text` → `denial_reason`
  - `pcr_narrative_excerpt` → `pcr_excerpt`
  - All other fields map directly

### 7c: Query functions
```python
def get_all_denials() -> list[dict]:
    """Return all 28 denial cases as dicts."""

def get_denials_by_cluster() -> dict[str, list[dict]]:
    """Group denial cases by cluster field. 
    Skip cases where cluster is null or 'scattered'.
    Returns: {'uhc_medical_necessity': [case1, case2, ...], ...}"""

def insert_rule(rule: dict) -> None:
    """Insert an extracted prevention rule."""

def get_all_rules() -> list[dict]:
    """Return all prevention rules."""

def get_rule(rule_id: str) -> dict:
    """Return a single rule by ID."""

def insert_score(score: dict) -> None:
    """Insert a claim score record."""

def get_status() -> dict:
    """Return counts: total_denials, total_rules, total_scores."""

def reset_analysis() -> None:
    """Delete all rows from prevention_rules and claim_scores.
    Do NOT delete denial_cases — those are seed data."""
```

### 7d: Auto-init
At module level, call `init_db()` and `load_seed_data()` when the module is imported for the first time.

## Step 8: vector_store.py

### 8a: Gemini embedding helper
Create a helper function to generate embeddings via Gemini API:
```python
import google.generativeai as genai
from config import GEMINI_API_KEY, EMBEDDING_MODEL

genai.configure(api_key=GEMINI_API_KEY)

def embed_text(text: str, task_type: str = "retrieval_document") -> list[float]:
    """Generate a 768-dim embedding via Gemini text-embedding-004."""
    result = genai.embed_content(
        model=EMBEDDING_MODEL,  # "models/text-embedding-004"
        content=text,
        task_type=task_type  # "retrieval_document" for storing, "retrieval_query" for searching
    )
    return result['embedding']

def embed_texts(texts: list[str], task_type: str = "retrieval_document") -> list[list[float]]:
    """Batch embed multiple texts."""
    result = genai.embed_content(
        model=EMBEDDING_MODEL,
        content=texts,
        task_type=task_type
    )
    return result['embedding']
```

### 8b: `init_vector_store()` function
- Initialize Qdrant client in **local persistent mode**: `QdrantClient(path=QDRANT_PATH)`
- No server needed — data persists to disk at `QDRANT_PATH`
- Create two collections (if they don't exist):
```python
from qdrant_client import QdrantClient, models

client = QdrantClient(path=QDRANT_PATH)

# Create collections with 768-dim vectors (Gemini text-embedding-004)
for collection_name in ["denial_narratives", "rule_embeddings"]:
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=768,
                distance=models.Distance.COSINE
            )
        )
```

### 8c: Operation functions
```python
def add_denial_embedding(denial_case: dict) -> None:
    """Embed and store a denial case narrative.
    text = f"{denial_reason} | {pcr_excerpt} | {missing_element}"
    Generate embedding via Gemini (task_type="retrieval_document")
    Store as a point in 'denial_narratives' collection with payload.
    Use a hash of the denial_id as the point ID (Qdrant needs int or UUID).
    """
    text = f"{denial_case['denial_reason']} | {denial_case['pcr_excerpt']} | {denial_case['missing_element']}"
    vector = embed_text(text, task_type="retrieval_document")
    
    # Convert "D-001" to integer ID: hash or just use the number part
    point_id = int(denial_case['id'].split('-')[1])
    
    client.upsert(
        collection_name="denial_narratives",
        points=[models.PointStruct(
            id=point_id,
            vector=vector,
            payload={
                "denial_id": denial_case['id'],
                "carc_code": denial_case['carc_code'],
                "payer": denial_case['payer'],
                "cpt_code": denial_case['cpt_code'],
                "appeal_outcome": denial_case['appeal_outcome'],
                "cluster": denial_case.get('cluster', ''),
                "text": text
            }
        )]
    )

def add_rule_embedding(rule: dict) -> None:
    """Embed and store a prevention rule.
    text = f"{rule_title} | {risk_description} | {' '.join(required_elements)}"
    Generate embedding via Gemini (task_type="retrieval_document")
    Store in 'rule_embeddings' collection.
    """

def query_similar_rules(claim_text: str, payer: str = None, cpt_code: str = None, n_results: int = 5) -> list[dict]:
    """Find rules similar to a claim narrative.
    1. Embed claim_text via Gemini with task_type="retrieval_query"
    2. Search rule_embeddings collection
    3. Optionally filter by payer_pattern and cpt_pattern using Qdrant's Filter:
    
    query_filter = models.Filter(
        should=[
            models.FieldCondition(key="payer_pattern", match=models.MatchValue(value=payer)),
            models.FieldCondition(key="payer_pattern", match=models.MatchValue(value="*")),
        ]
    )
    
    4. Returns list of {rule_id, score, payload}
    """

def get_collection_counts() -> dict:
    """Return {'denial_narratives': count, 'rule_embeddings': count}"""
    return {
        "denial_narratives": client.count("denial_narratives").count,
        "rule_embeddings": client.count("rule_embeddings").count,
    }

def reset_vectors() -> None:
    """Delete and recreate both collections. Empty state."""
    for name in ["denial_narratives", "rule_embeddings"]:
        client.delete_collection(name)
        client.create_collection(
            collection_name=name,
            vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE)
        )
```

### 8d: Important notes
- Qdrant local mode needs no server process — `QdrantClient(path="...")` reads/writes directly to disk
- Qdrant point IDs must be integers or UUIDs. For denial IDs like "D-001", extract the number: `int("D-001".split('-')[1])` → `1`. For rule IDs like "R-001", same pattern but offset by 1000 to avoid collisions: `1000 + int("R-001".split('-')[1])`
- Gemini embeddings are API calls (not local) — they're fast (~100ms per call) and the free tier allows 1500 requests/minute, more than enough
- For query-time, always use `task_type="retrieval_query"`. For storage, use `task_type="retrieval_document"`. This is important for Gemini embedding quality.
- `reset_vectors()` must delete and recreate collections to truly start fresh

## Step 9: test_data.py

A simple verification script:
```python
"""Run: python backend/test_data.py"""
from database import get_all_denials, get_denials_by_cluster, get_status
from vector_store import init_vector_store, get_collection_counts

# Test 1: Check denial cases loaded
denials = get_all_denials()
assert len(denials) == 28, f"Expected 28 denials, got {len(denials)}"
print(f"✓ {len(denials)} denial cases loaded")

# Test 2: Check clusters
clusters = get_denials_by_cluster()
assert len(clusters) == 5, f"Expected 5 clusters, got {len(clusters)}"
for name, cases in clusters.items():
    print(f"  Cluster '{name}': {len(cases)} cases")
print(f"✓ {len(clusters)} clusters identified")

# Test 3: Check payer distribution
payers = set(d['payer'] for d in denials)
print(f"✓ Payers: {payers}")

# Test 4: Check vector store initialized
counts = get_collection_counts()
assert counts['denial_narratives'] == 0, "Denial narratives should be empty before analysis"
assert counts['rule_embeddings'] == 0, "Rule embeddings should be empty before analysis"
print(f"✓ Vector store initialized (empty)")

# Test 5: Check status
status = get_status()
print(f"✓ Status: {status}")

print("\n=== All Milestone 1 tests passed ===")
```

## Verification
Run `python backend/test_data.py` from the `ambra-demo` directory. All assertions should pass, output should show 28 cases, 5 clusters, empty vector store.
