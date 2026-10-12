# Milestone 3: Scoring Agent

## Goal
Build the scoring agent that takes a new PCR narrative, retrieves matching rules from vector memory + structured filters, sends them to the LLM for analysis, and returns a risk score with specific flags and suggestions.

## Completion Criteria
- `POST /api/score` with a claim narrative returns a `ClaimScoreResult`
- The demo claim (UHC ALS-1 with missing elements) scores as HIGH risk with 2+ flags
- Each flag references a specific rule and provides an actionable suggestion
- Scoring works ONLY after analysis has been run (rules exist in memory)

---

## Step 1: scoring_agent.py

### 1a: `retrieve_matching_rules(claim_text: str, payer: str, cpt_code: str) -> list[dict]`

This function does a **two-layer retrieval**:

**Layer 1: Vector similarity search**
- Embed the claim narrative text via Gemini with `task_type="retrieval_query"`
- Query `rule_embeddings` collection in Qdrant with the embedding vector
- Request top 5 results
- If payer is provided, add a Qdrant filter:
```python
query_filter = models.Filter(
    should=[
        models.FieldCondition(key="payer_pattern", match=models.MatchValue(value=payer)),
        models.FieldCondition(key="payer_pattern", match=models.MatchValue(value="*")),
    ]
)
```
- If cpt_code is provided, also filter by cpt_pattern (exact match or wildcard `"*"`)
- Qdrant returns results with similarity scores

**Layer 2: SQL cross-reference**
- For each rule_id returned by vector search, also fetch the full rule from SQLite
- This gives us the complete rule with required_elements and recommended_phrases
- Merge the vector distance score with the SQL data

**Return format:**
```python
[
    {
        "rule_id": "R-001",
        "rule_title": "...",
        "payer_pattern": "UnitedHealthcare",
        "cpt_pattern": "A0427",
        "carc_pattern": "CO-16",
        "service_pattern": "ALS-1 Emergency",
        "risk_description": "...",
        "required_elements": ["...", "..."],
        "recommended_phrases": ["...", "..."],
        "confidence": 0.92,
        "severity": "high",
        "source_count": 6,
        "avg_denied_amount": 1847.00,
        "similarity_score": 0.87  # from vector search
    },
    ...
]
```

### 1b: `async score_claim(narrative: str, service_type: str, cpt_code: str, payer: str) -> ClaimScoreResult`

Main scoring function:

```python
async def score_claim(narrative: str, service_type: str, cpt_code: str, payer: str) -> ClaimScoreResult:
    # 1. Check if any rules exist
    status = get_status()
    if status['total_rules'] == 0:
        raise ValueError("No rules in memory. Run analysis first.")
    
    # 2. Retrieve matching rules
    matching_rules = retrieve_matching_rules(narrative, payer, cpt_code)
    
    if not matching_rules:
        # No matching rules found — claim looks clean
        return ClaimScoreResult(
            score_id=generate_score_id(),
            overall_risk="LOW",
            risk_score=5,
            flags=[],
            rules_checked=status['total_rules'],
            rules_matched=0,
            top_recommendation="No matching denial patterns found. Claim appears safe."
        )
    
    # 3. Build scoring prompt
    user_prompt = SCORING_USER_PROMPT_TEMPLATE.format(
        service_type=service_type,
        cpt_code=cpt_code,
        payer=payer,
        claim_narrative=narrative,
        rules_json=json.dumps(matching_rules, indent=2)
    )
    
    # 4. Call LLM
    client = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=LLM_BASE_URL)
    response = await client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SCORING_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
        response_format={"type": "json_object"}
    )
    
    # 5. Parse response
    result_json = json.loads(response.choices[0].message.content)
    
    # 6. Build ClaimScoreResult
    flags = []
    for flag_data in result_json.get("flags", []):
        # Look up the matching rule to get source_count
        rule = next((r for r in matching_rules if r['rule_id'] == flag_data['rule_id']), None)
        flags.append(ClaimFlag(
            rule_id=flag_data['rule_id'],
            rule_title=flag_data['rule_title'],
            risk_level=flag_data['risk_level'],
            missing_element=flag_data['missing_element'],
            suggestion=flag_data['suggestion'],
            estimated_denial_risk=flag_data.get('estimated_denial_risk', 0),
            similar_denial_count=rule['source_count'] if rule else 0
        ))
    
    score_result = ClaimScoreResult(
        score_id=generate_score_id(),
        overall_risk=result_json['overall_risk'],
        risk_score=result_json['risk_score'],
        flags=flags,
        rules_checked=len(matching_rules),
        rules_matched=len(flags),
        top_recommendation=result_json.get('top_recommendation', '')
    )
    
    # 7. Save to DB for audit trail
    insert_score(score_result.model_dump())
    
    return score_result
```

### 1c: `generate_score_id() -> str`
Generate a unique score ID: `f"S-{uuid4().hex[:8]}"`

## Step 2: Add Score Endpoint to main.py

### Request body model:
```python
class ScoreRequest(BaseModel):
    narrative: str          # The PCR narrative text
    service_type: str       # e.g. "ALS-1 Emergency"
    cpt_code: str          # e.g. "A0427"
    payer: str             # e.g. "UnitedHealthcare"
```

### `POST /api/score`
```python
@app.post("/api/score")
async def score_claim_endpoint(request: ScoreRequest):
    try:
        result = await score_claim(
            narrative=request.narrative,
            service_type=request.service_type,
            cpt_code=request.cpt_code,
            payer=request.payer
        )
        return result
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
```

## Step 3: The Demo Claim

This is the pre-filled claim used in Scene 4 of the demo. It must be stored as a constant or returned by an endpoint so the frontend can load it.

### Option A: Hardcode in frontend (simpler)
### Option B: Add endpoint `GET /api/demo-claim` (cleaner)

```python
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
    )
}
```

**What's deliberately missing** (the scoring agent should catch these):
1. **No transport necessity language** — Missing "patient's condition required ALS-level transport because..." → Triggers R-001 (UHC medical necessity rule)
2. **No vital signs** — No BP, HR, SpO2, RR, GCS documented → Triggers level-of-service justification
3. **No ALS interventions documented** — Mentions aspirin PO (a BLS intervention) but no cardiac monitoring, 12-lead, IV access → Could trigger ALS downgrade
4. **No medical necessity justification** — No explanation of why ground ambulance was needed vs. private vehicle

### `GET /api/demo-claim`
```python
@app.get("/api/demo-claim")
def get_demo_claim():
    return DEMO_CLAIM
```

## Step 4: Verification

After building, test in this order (server must be running, analysis must be complete):

```bash
# 1. First run analysis (if not already done)
curl -N -X POST http://localhost:8000/api/analyze

# 2. Verify rules exist
curl http://localhost:8000/api/status
# Should show total_rules: 5

# 3. Get demo claim
curl http://localhost:8000/api/demo-claim

# 4. Score the demo claim
curl -X POST http://localhost:8000/api/score \
  -H "Content-Type: application/json" \
  -d '{
    "service_type": "ALS-1 Emergency",
    "cpt_code": "A0427",
    "payer": "UnitedHealthcare",
    "narrative": "Dispatched to 742 Evergreen Terrace for a 67-year-old male experiencing chest pain. Patient found sitting in recliner, alert and oriented x4, stating my chest hurts. Patient reports pain started approximately 2 hours ago, rates it 7/10, substernal, non-radiating. Administered aspirin 324mg PO. Transported patient to Memorial General Hospital without incident. Patient remained stable during transport. Care transferred to ED staff."
  }'

# Expected response:
# - overall_risk: "HIGH"
# - risk_score: 70-90
# - flags: 2-4 flags
# - At least one flag about "transport necessity language"
# - top_recommendation mentioning what to fix first

# 5. Score a CLEAN claim (should score LOW)
curl -X POST http://localhost:8000/api/score \
  -H "Content-Type: application/json" \
  -d '{
    "service_type": "BLS Emergency",
    "cpt_code": "A0428",
    "payer": "Anthem",
    "narrative": "Dispatched to single vehicle accident on Highway 101. Patient is a 45-year-old female with obvious right femur deformity. Vitals: BP 142/88, HR 110, SpO2 96%, RR 22. Patient immobilized on backboard with cervical collar. IV access established, 500ml NS administered. Pain management with morphine 4mg IV per protocol. Transported Code 3 to Level 1 Trauma Center. Medical necessity: patient required emergency BLS transport due to traumatic injury preventing self-transport, with spinal precautions required."
  }'
# Expected: LOW risk, 0-1 flags
```

All tests should pass. The demo claim should trigger HIGH risk with specific, actionable flags.
