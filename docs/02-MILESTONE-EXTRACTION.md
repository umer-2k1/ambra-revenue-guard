# Milestone 2: Extraction Agent + FastAPI Server

## Goal
Build the FastAPI backend with the extraction agent. When the user hits "Analyze Denials," the system clusters cases, sends each cluster to the LLM, extracts prevention rules, stores them in SQLite and Qdrant, and streams progress via Server-Sent Events (SSE).

## Completion Criteria
- `uvicorn backend.main:app --reload` starts the server on port 8000
- `GET /api/denials` returns 28 cases
- `POST /api/analyze` streams SSE events showing real-time progress, creates 5 rules
- `GET /api/rules` returns the 5 extracted rules
- `POST /api/reset` clears rules and embeddings, ready to analyze again

---

## Step 1: prompts.py

Store all LLM prompts as string constants. This keeps them out of logic code.

```python
EXTRACTION_SYSTEM_PROMPT = """You are an EMS billing denial analyst..."""
# Copy the FULL extraction system prompt from Master Spec section 7.1

EXTRACTION_USER_PROMPT_TEMPLATE = """Analyze these {n} related denial cases..."""
# Copy the FULL extraction user prompt from Master Spec section 7.1
# This is a template — {n} and {cases_json} get filled at runtime

SCORING_SYSTEM_PROMPT = """You are an EMS billing quality assurance agent..."""
# Copy from Master Spec section 7.2 — used in Milestone 3

SCORING_USER_PROMPT_TEMPLATE = """Review this PCR narrative..."""
# Copy from Master Spec section 7.2 — used in Milestone 3
```

## Step 2: extraction_agent.py

### 2a: `cluster_denials(denials: list[dict]) -> dict[str, list[dict]]`
- Takes all denial cases
- Groups them by the `cluster` field
- Filters out cases where cluster is `null`, empty, or not in the known 5 clusters
- The scattered cases (D-025 to D-028) have unique cluster values — they should be excluded from analysis because they don't have enough cases to form a meaningful pattern
- Returns dict mapping cluster name to list of cases
- This is essentially the same as `get_denials_by_cluster()` from database.py

### 2b: `extract_rule_from_cluster(cluster_name: str, cases: list[dict], rule_number: int) -> ExtractedRule`
- Takes a cluster name and its list of denial cases
- Calls DeepSeek API (OpenAI-compatible) with:
  - Model: from config `LLM_MODEL` (default: deepseek-chat)
  - System prompt: `EXTRACTION_SYSTEM_PROMPT`
  - User prompt: `EXTRACTION_USER_PROMPT_TEMPLATE` formatted with case count and JSON
- Parses the JSON response into an `ExtractedRule`
- Sets `rule_id = f"R-{rule_number:03d}"` (R-001, R-002, etc.)
- Sets `source_denials` from the case IDs in the cluster
- Sets `source_count` from len(cases)
- **Error handling**: If JSON parsing fails, retry ONCE. If still fails, log warning and return None.

### 2c: `async run_analysis() -> AsyncGenerator[AnalysisProgress, None]`
This is the main function, called by the SSE endpoint. It's an async generator that yields progress events.

```python
async def run_analysis():
    # Step 1: Get all denials
    denials = get_all_denials()
    yield AnalysisProgress(
        step="starting",
        cluster_name="",
        message=f"Loaded {len(denials)} denial cases",
        progress=0.0
    )
    
    # Step 2: Cluster them
    clusters = cluster_denials(denials)
    yield AnalysisProgress(
        step="clustering",
        cluster_name="",
        message=f"Identified {len(clusters)} denial patterns",
        progress=0.1
    )
    
    # Step 3: Process each cluster
    total_clusters = len(clusters)
    for i, (cluster_name, cases) in enumerate(clusters.items()):
        # Yield "extracting" event
        yield AnalysisProgress(
            step="extracting",
            cluster_name=cluster_name,
            message=f"Analyzing cluster {i+1}/{total_clusters}: {cluster_name} ({len(cases)} cases)",
            progress=0.1 + (0.7 * i / total_clusters)
        )
        
        # Call LLM
        rule = await extract_rule_from_cluster(cluster_name, cases, i + 1)
        
        if rule is None:
            yield AnalysisProgress(
                step="error",
                cluster_name=cluster_name,
                message=f"Failed to extract rule from {cluster_name}, skipping",
                progress=0.1 + (0.7 * (i + 1) / total_clusters)
            )
            continue
        
        # Store in SQLite
        insert_rule(rule.model_dump())
        
        # Store denial embeddings for this cluster
        for case in cases:
            add_denial_embedding(case)
        
        # Store rule embedding
        add_rule_embedding(rule.model_dump())
        
        # Yield success event WITH the extracted rule
        yield AnalysisProgress(
            step="stored",
            cluster_name=cluster_name,
            message=f"Extracted rule: {rule.rule_title}",
            progress=0.1 + (0.7 * (i + 1) / total_clusters),
            rule=rule
        )
    
    # Step 4: Done
    status = get_status()
    counts = get_collection_counts()
    yield AnalysisProgress(
        step="complete",
        cluster_name="",
        message=f"Analysis complete. {status['total_rules']} rules learned, {counts['denial_narratives']} denial embeddings, {counts['rule_embeddings']} rule embeddings stored.",
        progress=1.0
    )
```

### Important: Make the LLM call async
Use `openai.AsyncOpenAI` client pointed at DeepSeek's API. DeepSeek uses an OpenAI-compatible API format, so the `openai` SDK works by just changing the `base_url`:
```python
from openai import AsyncOpenAI
from config import DEEPSEEK_API_KEY, LLM_MODEL, LLM_BASE_URL

client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=LLM_BASE_URL   # "https://api.deepseek.com"
)

response = await client.chat.completions.create(
    model=LLM_MODEL,          # "deepseek-chat"
    messages=[
        {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ],
    temperature=0.2,  # Low temp for consistent structured output
    response_format={"type": "json_object"}  # Force JSON response
)
```

## Step 3: main.py — FastAPI Application

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import json

app = FastAPI(title="Ambra Demo - Denial Prevention")

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Endpoints to implement:

#### `GET /api/denials`
- Returns all 28 denial cases from SQLite
- Response: `list[DenialCase]`
- No parameters

#### `GET /api/denials/stats`
- Returns summary statistics computed from denial_cases table:
```json
{
  "total_cases": 28,
  "total_denied_amount": 38245.00,
  "by_payer": {"UnitedHealthcare": 6, "Aetna": 5, ...},
  "by_carc": {"CO-16": 12, "CO-197": 5, ...},
  "by_outcome": {"overturned": 10, "denied": 5, ...},
  "avg_days_to_appeal": 18.5
}
```

#### `POST /api/analyze`
- **This is the key endpoint — returns SSE stream**
- Before starting: check if rules already exist. If yes, return error asking to reset first.
- Uses `EventSourceResponse` from `sse-starlette`
- Each event is a JSON-serialized `AnalysisProgress`
```python
@app.post("/api/analyze")
async def analyze_denials():
    status = get_status()
    if status['total_rules'] > 0:
        return JSONResponse(
            status_code=400, 
            content={"error": "Analysis already complete. Call /api/reset first."}
        )
    
    async def event_generator():
        async for progress in run_analysis():
            yield {
                "event": "progress",
                "data": progress.model_dump_json()
            }
    
    return EventSourceResponse(event_generator())
```

#### `GET /api/rules`
- Returns all prevention rules from SQLite
- Response: `list[ExtractedRule]`
- Parse JSON fields (source_denials, required_elements, recommended_phrases) before returning

#### `GET /api/rules/{rule_id}`
- Returns one rule by ID
- 404 if not found

#### `GET /api/status`
- Returns system status:
```json
{
  "total_denials": 28,
  "total_rules": 0,
  "total_scores": 0,
  "denial_embeddings": 0,
  "rule_embeddings": 0,
  "analysis_complete": false
}
```
- `analysis_complete` is true when `total_rules > 0`

#### `POST /api/reset`
- Calls `reset_analysis()` on database (clears rules + scores)
- Calls `reset_vectors()` on vector store (clears all embeddings)
- Returns `{"status": "reset", "message": "All rules, scores, and embeddings cleared."}`

## Step 4: Verification

After building, test these in order:

```bash
# Terminal 1: Start server
cd ambra-demo
uvicorn backend.main:app --reload --port 8000

# Terminal 2: Test endpoints
# 1. Check denials loaded
curl http://localhost:8000/api/denials | python -m json.tool | head -20

# 2. Check status (should show 0 rules)
curl http://localhost:8000/api/status

# 3. Run analysis (SSE stream)
curl -N http://localhost:8000/api/analyze

# 4. Check rules created
curl http://localhost:8000/api/rules | python -m json.tool

# 5. Check status (should show 5 rules)
curl http://localhost:8000/api/status

# 6. Reset
curl -X POST http://localhost:8000/api/reset

# 7. Verify reset
curl http://localhost:8000/api/status
```

All 7 tests should pass. The SSE stream (test 3) should show 5 clusters being processed with real-time messages.
