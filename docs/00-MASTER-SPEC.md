# Ambra911 Denial-to-Prevention Feedback Loop — Master Specification

## 1. Project Overview

### What This Is
A demo application that proves the concept of a **Denial-to-Prevention Feedback Loop** for Ambra911, an EMS (Emergency Medical Services) AI billing company. The system turns every resolved insurance denial into a reusable lesson that prevents future claims from being denied.

### Why It Matters to Ambra911
Ambra911 has two products today:
- **Scribe**: AI-powered charting that converts voice → PCR (Patient Care Report) → billing-ready claim
- **Denials**: AI that fights denied claims — writes appeal letters in 38 seconds, navigates payer IVR phone trees

These two products operate as **separate pipelines**. When Denials wins an appeal, that knowledge dies — it doesn't flow back to Scribe to prevent the same denial from happening again. This demo bridges that gap.

### What This Is NOT
- NOT a replacement for anything Ambra already has (appeal letters, IVR agent, NEMSIS validation, claim statusing)
- NOT a deployed production system — it runs locally, gets recorded as a 3–4 minute Loom video, and code goes on GitHub
- NOT static/pre-baked — the analysis, rule extraction, and claim scoring all happen in real-time during the demo

---

## 2. Demo Flow (What the Founder Sees)

The Loom video walks through 4 screens in this exact order:

### Screen 1: Denial Cases (30 seconds)
- A table of 28 resolved denial cases — raw data, no analysis
- The cases represent real EMS denial patterns: medical necessity, prior auth, mileage docs, Medicare PCS, level of service
- Point: "Here are your resolved denials. Right now this knowledge is trapped."

### Screen 2: Analyze — Watch the System Learn (60 seconds)
- User clicks **"Analyze Denials"** button
- The system processes cases in real-time:
  - Groups similar denials into clusters
  - Sends each cluster to an LLM for pattern extraction
  - Stores structured rules in SQLite
  - Stores semantic embeddings in Qdrant
- A live progress feed shows what's happening: "Analyzing cluster 1/5... Extracted rule: UHC ALS-1 requires transport necessity language... Stored 6 embeddings..."
- Point: "The system just learned 5 prevention rules from your historical denials."

### Screen 3: Knowledge Base (30 seconds)
- Shows the extracted prevention rules in a card layout
- Each rule shows: title, payer, CPT code, CARC code, severity, confidence, required elements, recommended phrases, how many denials formed it
- Point: "This is the system's memory. Every resolved denial makes it smarter."

### Screen 4: Score a New Claim (90 seconds — THE MAIN EVENT)
- A pre-filled PCR narrative appears (for a UHC ALS-1 Emergency transport)
- The narrative is deliberately missing elements that would trigger a denial
- User clicks **"Score Claim"**
- The system retrieves matching rules from vector memory + structured filters
- Returns a risk score (0–100), risk level (HIGH/MEDIUM/LOW), and specific flags:
  - "Missing transport necessity language — UHC denied 6 similar claims (avg $1,847)"
  - "No vital signs documented — required for ALS-1 level justification"
- Each flag links to the rule that caught it and shows recommended fixes
- Point: "This claim would have been denied. Now it gets caught before submission."

### Closing (30 seconds)
- Quick visual showing the flywheel: more denials resolved → more rules learned → fewer future denials
- Point: "Every denial makes the system smarter. Connect Scribe and Denials, and denial rates drop over time."

---

## 3. Architecture

```
┌─────────────────────────────────────────────────┐
│                  FRONTEND (React)                │
│                                                   │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐ ┌──────┐│
│  │ Denials  │ │ Analyze  │ │Knowledge│ │Score ││
│  │ Table    │ │ Progress │ │ Base    │ │Claim ││
│  └──────────┘ └──────────┘ └─────────┘ └──────┘│
└───────────────────┬─────────────────────────────┘
                    │ HTTP / SSE (Server-Sent Events)
                    │
┌───────────────────┴─────────────────────────────┐
│               BACKEND (FastAPI)                   │
│                                                   │
│  ┌────────────────┐    ┌────────────────────┐    │
│  │ Extraction     │    │ Scoring            │    │
│  │ Agent          │    │ Agent              │    │
│  │                │    │                    │    │
│  │ - Cluster      │    │ - Retrieve rules   │    │
│  │   denials      │    │   (vector + SQL)   │    │
│  │ - Extract      │    │ - Analyze claim    │    │
│  │   rules (LLM)  │    │   against rules   │    │
│  │ - Store rules  │    │   (LLM)           │    │
│  │ - Store embeds │    │ - Return score +   │    │
│  └────────────────┘    │   flags           │    │
│                        └────────────────────┘    │
│                                                   │
│  ┌────────────────┐    ┌────────────────────┐    │
│  │ SQLite         │    │ Qdrant             │    │
│  │                │    │  (local mode)      │    │
│  │ - denial_cases │    │ - denial_narratives│    │
│  │ - prevention_  │    │ - rule_embeddings  │    │
│  │   rules        │    │                    │    │
│  │ - claim_scores │    │                    │    │
│  └────────────────┘    └────────────────────┘    │
└──────────────────────────────────────────────────┘
```

---

## 4. Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend | Python 3.11+ / FastAPI | Fast, async, great for streaming |
| Database | SQLite | Zero config, single file, perfect for demo |
| Vector DB | Qdrant (local mode) | No server needed, persistent to disk, Python native, fast |
| Embeddings | Google Gemini `text-embedding-004` | High quality, free tier generous (1500 RPM), API-based |
| LLM | DeepSeek `deepseek-chat` | Cheap ($0.14/1M input), fast, excellent at structured extraction. OpenAI-compatible API. User provides `DEEPSEEK_API_KEY` in `.env` |
| Frontend | React (Vite) | Fast dev, component-based, easy to make look good |
| Styling | shadcn/ui + Tailwind CSS | Pre-built accessible components, polished look, heavily used throughout |
| Streaming | Server-Sent Events (SSE) | Real-time progress updates from backend to frontend |

### Why DeepSeek + Gemini?
- **DeepSeek**: Extremely cheap ($0.14/1M input, $0.28/1M output), fast, and uses an OpenAI-compatible API format — so the `openai` Python SDK works directly by changing the `base_url`. Great at structured JSON extraction.
- **Gemini Embeddings**: Google's `text-embedding-004` model is free-tier generous (1500 requests/min), high quality (768 dimensions), and avoids needing to download a local model. Uses the `google-generativeai` Python SDK.
- The prompts are model-agnostic; switching to OpenAI or Claude API later is a one-line config change.

---

## 5. Data Models

### 5.1 SQLite Tables

#### Table: `denial_cases`
Stores the 28 seed denial cases. Pre-loaded at startup from `seed_denials.json`.

```sql
CREATE TABLE denial_cases (
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
    ingested_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Table: `prevention_rules`
Created EMPTY at startup. Populated only when user clicks "Analyze Denials."

```sql
CREATE TABLE prevention_rules (
    rule_id             TEXT PRIMARY KEY,
    source_denials      TEXT NOT NULL,       -- JSON array: ["D-001","D-002"]
    source_count        INTEGER,
    payer_pattern       TEXT,
    cpt_pattern         TEXT,
    carc_pattern        TEXT,
    service_pattern     TEXT,
    rule_title          TEXT NOT NULL,
    risk_description    TEXT,
    required_elements   TEXT NOT NULL,       -- JSON array
    recommended_phrases TEXT,               -- JSON array
    confidence          REAL,
    severity            TEXT,
    avg_denied_amount   REAL,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Table: `claim_scores`
Created EMPTY at startup. Populated when user scores a claim.

```sql
CREATE TABLE claim_scores (
    score_id        TEXT PRIMARY KEY,
    claim_narrative TEXT,
    service_type    TEXT,
    cpt_code        TEXT,
    payer           TEXT,
    overall_risk    TEXT,
    risk_score      REAL,
    flags_found     INTEGER,
    flags_detail    TEXT,                   -- JSON array of flag objects
    rules_matched   TEXT,                   -- JSON array of rule_ids
    scored_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5.2 Qdrant Collections

Both collections are created EMPTY at startup. Populated during "Analyze Denials."
Qdrant runs in **local mode** (no server needed) — `QdrantClient(path="./data/qdrant_db")` persists to disk.
Embeddings are generated via **Gemini text-embedding-004** (768 dimensions).

#### Collection: `denial_narratives`
```python
# Each denial case gets an embedding for semantic similarity
# Text to embed: f"{case.denial_reason} | {case.pcr_excerpt} | {case.missing_element}"
# Vector size: 768 (Gemini text-embedding-004)
# Distance: Cosine
#
# Payload (Qdrant's term for metadata):
{
    "denial_id": "D-001",
    "carc_code": "CO-16",
    "payer": "UnitedHealthcare",
    "cpt_code": "A0427",
    "appeal_outcome": "overturned",
    "cluster": "uhc_medical_necessity",
    "text": "original text that was embedded"
}
```

#### Collection: `rule_embeddings`
```python
# Each extracted rule gets an embedding for matching against new claims
# Text to embed: f"{rule.rule_title} | {rule.risk_description} | {' '.join(rule.required_elements)}"
# Vector size: 768 (Gemini text-embedding-004)
# Distance: Cosine
#
# Payload:
{
    "rule_id": "R-001",
    "payer_pattern": "UnitedHealthcare",
    "cpt_pattern": "A0427",
    "carc_pattern": "CO-16",
    "confidence": 0.92,
    "severity": "high",
    "source_count": 6,
    "text": "original text that was embedded"
}
```

### 5.3 Pydantic Models (Python)

```python
from pydantic import BaseModel
from typing import Optional

class DenialCase(BaseModel):
    id: str
    cluster: str
    payer: str
    payer_id: str
    claim_date: str
    denial_date: str
    resolution_date: Optional[str]
    service_type: str
    cpt_code: str
    billed_amount: float
    denied_amount: float
    paid_after_appeal: Optional[float]
    carc_code: str
    rarc_code: Optional[str]
    denial_reason: str
    pcr_excerpt: str
    missing_element: str
    appeal_strategy: str
    appeal_outcome: str
    days_to_appeal: Optional[int]
    region: str

class ExtractedRule(BaseModel):
    rule_id: str
    source_denials: list[str]
    source_count: int
    payer_pattern: str
    cpt_pattern: str
    carc_pattern: str
    service_pattern: str
    rule_title: str
    risk_description: str
    required_elements: list[str]
    recommended_phrases: list[str]
    confidence: float
    severity: str  # "high", "medium", "low"
    avg_denied_amount: float

class ClaimFlag(BaseModel):
    rule_id: str
    rule_title: str
    risk_level: str  # "high", "medium", "low"
    missing_element: str
    suggestion: str
    estimated_denial_risk: float
    similar_denial_count: int

class ClaimScoreResult(BaseModel):
    score_id: str
    overall_risk: str  # "HIGH", "MEDIUM", "LOW"
    risk_score: int     # 0–100
    flags: list[ClaimFlag]
    rules_checked: int
    rules_matched: int
    top_recommendation: str

class AnalysisProgress(BaseModel):
    """Sent via SSE during analysis"""
    step: str           # "clustering", "extracting", "storing", "embedding"
    cluster_name: str
    message: str        # human-readable progress
    progress: float     # 0.0–1.0
    rule: Optional[ExtractedRule] = None  # included when a rule is extracted
```

---

## 6. API Endpoints

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| GET | `/api/denials` | List all 28 denial cases | `list[DenialCase]` |
| GET | `/api/denials/stats` | Summary stats (total denials, $ denied, by payer, by CARC) | JSON object |
| POST | `/api/analyze` | Trigger real-time analysis. Returns SSE stream. | `text/event-stream` of `AnalysisProgress` |
| GET | `/api/rules` | List all extracted prevention rules | `list[ExtractedRule]` |
| GET | `/api/rules/{rule_id}` | Get one rule with full detail | `ExtractedRule` |
| POST | `/api/score` | Score a claim narrative against learned rules | `ClaimScoreResult` |
| GET | `/api/status` | System status: how many rules, how many embeddings, memory state | JSON object |
| POST | `/api/reset` | Clear all rules, embeddings, scores. Reset to fresh state. | `{"status": "reset"}` |

---

## 7. LLM Prompts

### 7.1 Extraction Prompt
Used in `POST /api/analyze`. The backend clusters denial cases by their `cluster` field, then sends each cluster to the LLM.

```
SYSTEM:
You are an EMS billing denial analyst. You analyze clusters of similar 
insurance denial cases from ambulance services and extract a single, 
reusable prevention rule.

You understand:
- NEMSIS 3.5 data standard
- CMS ambulance billing requirements  
- CARC/RARC denial reason codes
- CPT codes for ambulance: A0425 (BLS Non-Emergency), A0427 (ALS-1 Emergency), 
  A0428 (BLS Emergency), A0429 (ALS-1 Non-Emergency), A0433 (ALS-2), A0434 (SCT)
- Payer-specific documentation requirements (UHC, Aetna, Anthem BCBS, Medicare, Cigna)
- Physician Certification Statement (PCS) requirements
- Condition codes P1–P7

USER:
Analyze these {n} related denial cases. They share a common denial pattern.
Extract ONE prevention rule that would have prevented ALL of these denials.

DENIAL CASES:
{json_array_of_cases}

You MUST respond with ONLY valid JSON in this exact format, no other text:
{
  "rule_title": "One-line summary of the rule, max 80 chars",
  "payer_pattern": "Payer name this applies to, or '*' for all payers",
  "cpt_pattern": "CPT code this applies to, or 'A042*' for wildcard",
  "carc_pattern": "Primary CARC code, e.g. 'CO-16'",
  "service_pattern": "Service type, e.g. 'ALS-1 Emergency'",
  "risk_description": "2-3 sentences explaining WHY this pattern causes denials",
  "required_elements": ["element1", "element2", "..."],
  "recommended_phrases": ["Phrase or sentence template 1", "Phrase 2", "Phrase 3"],
  "confidence": 0.85,
  "severity": "high",
  "avg_denied_amount": 1234.56
}

Rules for extraction:
- required_elements: List EVERY specific documentation element needed. Be precise.
  Bad: "proper documentation"  
  Good: "explicit statement that patient's condition required ALS-level intervention"
- recommended_phrases: Provide actual sentence templates a medic could use.
  Bad: "describe medical necessity"
  Good: "Patient's condition of [diagnosis] required ALS-level transport due to [specific intervention needed] which could not be provided by BLS"
- confidence: 1.0 = every case has identical root cause. 0.5 = cases vary significantly.
- severity: "high" if average denied amount > $800. "medium" if $400-800. "low" if < $400.
```

### 7.2 Scoring Prompt
Used in `POST /api/score`. The backend first retrieves matching rules via vector similarity + SQL filters, then sends the claim + rules to the LLM.

```
SYSTEM:
You are an EMS billing quality assurance agent. You review PCR (Patient Care 
Report) narratives BEFORE they become insurance claims.

Your job: identify documentation gaps that would cause a claim denial, based 
on prevention rules learned from past denials. You are the last line of 
defense before a claim goes to the payer.

USER:
Review this PCR narrative for a {service_type} transport billed as {cpt_code} 
to {payer}.

PCR NARRATIVE:
"{claim_narrative}"

MATCHING PREVENTION RULES FROM MEMORY:
{json_array_of_matching_rules}

Analyze the narrative against each rule. For each rule that identifies a 
problem, create a flag.

You MUST respond with ONLY valid JSON in this exact format, no other text:
{
  "overall_risk": "HIGH" or "MEDIUM" or "LOW",
  "risk_score": 0-100,
  "flags": [
    {
      "rule_id": "R-001",
      "rule_title": "Title of the rule that fired",
      "risk_level": "high" or "medium" or "low",
      "missing_element": "What specific element is missing from the narrative",
      "suggestion": "Exactly what to add or change in the narrative to fix this",
      "estimated_denial_risk": 1847.00
    }
  ],
  "top_recommendation": "Single most important thing to fix before submitting"
}

Scoring rules:
- risk_score: 0 = no issues found, 100 = almost certain denial
- A claim with ANY high-severity flag = overall_risk "HIGH"
- A claim with medium flags but no high = "MEDIUM"  
- A claim with only low flags = "LOW"
- missing_element must quote what's ABSENT, not what's present
- suggestion must be specific and actionable, not generic advice
  Bad: "add more documentation"
  Good: "Add vital signs (BP, HR, SpO2, RR) and GCS score to justify ALS-level assessment"
- If no rules match or no issues found, return risk_score 0 and empty flags array
```

---

## 8. Seed Data

The 28 denial cases are in `data/seed_denials.json`. They are organized into 5 clusters:

| Cluster | Payer | CARC | Service | Cases | Pattern |
|---------|-------|------|---------|-------|---------|
| `uhc_medical_necessity` | UnitedHealthcare | CO-16 | ALS-1 Emergency | D-001 to D-006 | Missing transport necessity language |
| `aetna_prior_auth` | Aetna | CO-197 | BLS Non-Emergency | D-007 to D-011 | Missing prior authorization |
| `anthem_mileage` | Anthem BCBS | CO-16 | BLS Emergency | D-012 to D-015 | Mileage documentation insufficient |
| `medicare_documentation` | Medicare (Novitas) | CO-16/CO-50 | Mixed | D-016 to D-020 | PCS missing/expired, condition codes |
| `cigna_level_of_service` | Cigna | CO-151 | ALS-1 Emergency | D-021 to D-024 | ALS downgrade, insufficient procedure docs |
| (scattered) | Various | Various | Various | D-025 to D-028 | One-offs: timely filing, duplicate, etc. |

The scattered cases (D-025 to D-028) should NOT form a cluster. They exist to test that the system handles noise — the analysis should skip them or group them as "unclustered."

---

## 9. Demo Claim for Scoring (Scene 4)

This claim is pre-filled in the UI. It's a UHC ALS-1 Emergency transport that's deliberately missing key elements.

```json
{
  "service_type": "ALS-1 Emergency",
  "cpt_code": "A0427",
  "payer": "UnitedHealthcare",
  "narrative": "Dispatched to 742 Evergreen Terrace for a 67-year-old male experiencing chest pain. Patient found sitting in recliner, alert and oriented x4, stating 'my chest hurts.' Patient reports pain started approximately 2 hours ago, rates it 7/10, substernal, non-radiating. Administered aspirin 324mg PO. Transported patient to Memorial General Hospital without incident. Patient remained stable during transport. Care transferred to ED staff."
}
```

**What's deliberately missing** (the system should catch these):
1. No explicit transport necessity language ("patient's condition required ALS-level transport because...")
2. No vital signs documented (BP, HR, SpO2, RR, GCS)
3. No specific ALS interventions documented (cardiac monitoring, 12-lead, IV access)
4. No statement about why BLS was insufficient

This should trigger rules R-001 (UHC medical necessity) and potentially R-005 (level of service) depending on how the system learns.

---

## 10. Project Structure

```
ambra-demo/
├── data/
│   └── seed_denials.json           # 28 denial cases
├── backend/
│   ├── main.py                     # FastAPI app, CORS, startup
│   ├── database.py                 # SQLite setup, table creation, queries
│   ├── vector_store.py             # Qdrant setup, embed, query
│   ├── extraction_agent.py         # Cluster denials → extract rules via LLM
│   ├── scoring_agent.py            # Score claim → retrieve rules → LLM analysis
│   ├── models.py                   # Pydantic models
│   ├── prompts.py                  # All LLM prompts as constants
│   └── requirements.txt            # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # Main app, tab navigation
│   │   ├── components/
│   │   │   ├── DenialsTable.jsx    # Screen 1: denial cases table
│   │   │   ├── AnalyzeView.jsx     # Screen 2: analyze button + progress
│   │   │   ├── KnowledgeBase.jsx   # Screen 3: extracted rules
│   │   │   └── ScoreClaim.jsx      # Screen 4: claim scoring
│   │   ├── api.js                  # API client functions
│   │   ├── lib/
│   │   │   └── utils.js            # shadcn/ui utility (cn function)
│   │   └── index.css               # Tailwind + shadcn imports
│   ├── components.json             # shadcn/ui config
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── .env.example                    # DEEPSEEK_API_KEY + GEMINI_API_KEY
├── .gitignore
├── README.md                       # Setup instructions for GitHub
└── start.sh                        # One command to run everything
```

---

## 11. Milestones

| # | Milestone | Description | Spec File |
|---|-----------|-------------|-----------|
| 1 | Project Setup + Data Layer | Python project, SQLite, Qdrant, seed data loader, verify with tests | `01-MILESTONE-DATA-LAYER.md` |
| 2 | Extraction Agent + API | FastAPI server, clustering logic, LLM extraction, SSE streaming, rule storage | `02-MILESTONE-EXTRACTION.md` |
| 3 | Scoring Agent | Vector retrieval, SQL filtering, LLM scoring, flag generation | `03-MILESTONE-SCORING.md` |
| 4 | Frontend UI | React app, all 4 screens, SSE integration, styling | `04-MILESTONE-FRONTEND.md` |
| 5 | Integration + Demo Polish | End-to-end flow, demo claim, reset functionality, README, demo recording script | `05-MILESTONE-INTEGRATION.md` |

Each milestone has its own detailed spec document. Build them in order — each depends on the previous one.

---

## 12. Environment Setup

```bash
# Required
DEEPSEEK_API_KEY=sk-...       # DeepSeek API key from platform.deepseek.com
GEMINI_API_KEY=AIza...        # Google Gemini API key from aistudio.google.com

# Optional (defaults shown)
LLM_MODEL=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com
EMBEDDING_MODEL=models/text-embedding-004
DATABASE_PATH=./data/ambra_demo.db
QDRANT_PATH=./data/qdrant_db
```

### Python Dependencies
```
fastapi>=0.104.0
uvicorn>=0.24.0
openai>=1.3.0                   # Used for DeepSeek (OpenAI-compatible API)
qdrant-client>=1.9.0
google-generativeai>=0.8.0      # Gemini embeddings
pydantic>=2.5.0
python-dotenv>=1.0.0
```

### Frontend Dependencies
```
react ^18
react-dom ^18
vite ^5
tailwindcss ^3
shadcn/ui               # UI component library — use heavily for all components
lucide-react            # icons (included with shadcn/ui)
```

### shadcn/ui Usage
Use shadcn/ui components **heavily** throughout the entire UI. Do not hand-roll components when shadcn has them. Key components to use:
- `Card`, `CardHeader`, `CardContent`, `CardFooter` — for rule cards, flag cards, stat cards
- `Table`, `TableHeader`, `TableRow`, `TableCell` — for the denials table
- `Badge` — for severity badges, outcome badges, CARC/CPT tags
- `Button` — all buttons (customize with Ambra colors)
- `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent` — for the 4 main views
- `Progress` — for the analysis progress bar
- `Textarea` — for the PCR narrative input
- `Select` — for service type, payer, CPT dropdowns
- `Alert`, `AlertTitle`, `AlertDescription` — for risk warnings and flags
- `Separator` — between sections
- `Skeleton` — for loading states while LLM is thinking
- `ScrollArea` — for the SSE live feed
- `Tooltip` — for helpful hints on CARC codes, CPT codes etc.

Initialize shadcn/ui with the Ambra color theme customized in the tailwind config.

---

## 13. Non-Functional Requirements

- **Startup**: The app must start with a single `./start.sh` command
- **First run**: On first run, seed data loads automatically. Vector DB and rules are empty.
- **Reset**: The `/api/reset` endpoint clears everything except seed denial cases, returning to fresh state
- **Speed**: Analysis should complete in < 30 seconds for 28 cases (5 LLM calls)
- **No deployment**: Runs on localhost only. No Docker, no cloud, no auth.
- **Error handling**: If LLM returns malformed JSON, retry once. If still bad, skip that cluster and log a warning.
- **SSE reliability**: Frontend must handle SSE connection drops gracefully and show last known state.
