# Milestone 5: Integration + Demo Polish

## Goal
Wire everything together end-to-end, add the startup script, write the README for GitHub, and prepare the demo recording script with exact talking points.

## Completion Criteria
- `./start.sh` starts both backend and frontend with one command
- Full flow works: Denials → Analyze → Knowledge Base → Score Claim
- Reset works: clears everything, ready to demo again
- README.md explains setup in under 2 minutes
- Demo script is ready for Loom recording

---

## Step 1: start.sh

```bash
#!/bin/bash
# Start Ambra Demo - Denial-to-Prevention Feedback Loop

echo "🚑 Starting Ambra Demo..."
echo ""

# Check for .env
if [ ! -f .env ]; then
    echo "❌ Missing .env file. Copy .env.example to .env and add your DeepSeek + Gemini API keys."
    echo "   cp .env.example .env"
    exit 1
fi

# Check for API keys
source .env
if [ -z "$DEEPSEEK_API_KEY" ] || [ "$DEEPSEEK_API_KEY" = "sk-your-key-here" ]; then
    echo "❌ Set your DEEPSEEK_API_KEY in .env (get one at platform.deepseek.com)"
    exit 1
fi
if [ -z "$GEMINI_API_KEY" ] || [ "$GEMINI_API_KEY" = "your-gemini-key-here" ]; then
    echo "❌ Set your GEMINI_API_KEY in .env (get one at aistudio.google.com)"
    exit 1
fi

# Install Python dependencies if needed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing Python dependencies..."
    pip install -r backend/requirements.txt --break-system-packages -q
fi

# Install frontend dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

# Start backend
echo "🔧 Starting backend on http://localhost:8000..."
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "   Waiting for backend..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/status > /dev/null 2>&1; then
        echo "   ✓ Backend ready"
        break
    fi
    sleep 1
done

# Start frontend
echo "🎨 Starting frontend on http://localhost:5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "═══════════════════════════════════════════════"
echo "  ✦ Ambra Demo is running!"
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  API docs: http://localhost:8000/docs"
echo "═══════════════════════════════════════════════"
echo ""
echo "Press Ctrl+C to stop both servers."

# Handle shutdown
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait
```

Make it executable: `chmod +x start.sh`

## Step 2: README.md

```markdown
# Ambra911 — Denial-to-Prevention Feedback Loop

A proof-of-concept that turns every resolved EMS insurance denial into a 
reusable prevention rule, catching documentation gaps before claims are submitted.

## The Problem

EMS billing has two separate workflows: **charting** (creating the PCR and claim) 
and **denial management** (appealing denied claims). When a denial is resolved, 
that knowledge dies — it doesn't flow back to prevent the same denial from 
happening again.

## The Solution

This system creates a feedback loop:
1. **Ingest** resolved denial cases
2. **Analyze** patterns using AI — extract reusable prevention rules
3. **Score** new claims against learned rules before submission
4. Every resolved denial makes the system smarter

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/ambra-demo.git
cd ambra-demo

# 2. Set up your API key
cp .env.example .env
# Edit .env and add your DeepSeek + Gemini API keys

# 3. Run
./start.sh
```

Open http://localhost:5173

## Tech Stack

- **Backend**: Python / FastAPI
- **Database**: SQLite (structured rules) + Qdrant (vector embeddings)
- **AI**: DeepSeek `deepseek-chat` (extraction + scoring), Google Gemini `text-embedding-004` (embeddings)
- **Frontend**: React / Vite / shadcn/ui / Tailwind CSS

## How It Works

### 1. Denial Cases
28 realistic EMS denial cases spanning 5 payers and 5 denial patterns 
(medical necessity, prior auth, mileage docs, Medicare PCS, level of service).

### 2. Analyze
AI clusters similar denials and extracts prevention rules in real-time. 
Each rule captures: what went wrong, what documentation is required, and 
recommended language to include.

### 3. Knowledge Base
Browse the extracted rules. Each shows the payer, CPT code, CARC denial code, 
required documentation elements, and recommended phrases.

### 4. Score a Claim
Submit a PCR narrative and get a risk score (0-100) with specific flags 
identifying documentation gaps that would trigger a denial.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/denials | List all denial cases |
| POST | /api/analyze | Analyze denials (SSE stream) |
| GET | /api/rules | List prevention rules |
| POST | /api/score | Score a claim narrative |
| POST | /api/reset | Reset analysis |

Full API docs at http://localhost:8000/docs
```

## Step 3: End-to-End Verification Checklist

Before recording, run through this exact sequence:

### Pre-flight
- [ ] `./start.sh` runs without errors
- [ ] Frontend loads at http://localhost:5173
- [ ] Backend API docs accessible at http://localhost:8000/docs

### Flow Test
- [ ] **Denials tab**: 28 cases visible, stats show correct totals
- [ ] **Analyze tab**: Click "Analyze Denials"
  - [ ] Progress bar moves smoothly
  - [ ] Live feed shows cluster-by-cluster progress
  - [ ] Each extracted rule appears inline with title and severity
  - [ ] Completes with "5 rules learned" message
- [ ] **Knowledge Base tab**: 5 rule cards visible
  - [ ] Each card shows rule title, payer, CPT, CARC, severity
  - [ ] Required elements and recommended phrases are present
- [ ] **Score Claim tab**: Demo claim pre-filled
  - [ ] Click "Score Claim"
  - [ ] Risk score appears: should be HIGH (70-90)
  - [ ] 2+ flags with specific missing elements
  - [ ] Each flag has a concrete suggestion
  - [ ] Dollar amounts shown for estimated risk

### Reset Test
- [ ] Click reset (wherever it's placed)
- [ ] Knowledge Base shows empty state
- [ ] Score Claim shows "run analysis first" message
- [ ] Analyze tab shows "Ready to Analyze" again

## Step 4: Demo Recording Script (Loom, 3-4 minutes)

### Setup Before Recording
1. Run `./start.sh`
2. Open http://localhost:5173 in Chrome
3. Make sure the window is 1280px+ wide
4. Reset the system if any previous analysis exists
5. Start on the Denials tab

### Script

---

**[0:00 – 0:30] The Problem**

*Show: Denials tab with 28 cases*

"Every EMS agency has a pile of resolved denials like this — 28 cases across UnitedHealthcare, Aetna, Anthem, Medicare, and Cigna. Over $38,000 denied. Some were overturned on appeal, some weren't.

Right now, this knowledge is trapped. When your denial team wins an appeal, they learn something valuable — but that lesson doesn't flow back to prevent the next denial. Scribe and Denials operate as separate pipelines."

---

**[0:30 – 1:30] The Analysis (THE WOW MOMENT)**

*Click: Analyze tab → Click "Analyze Denials"*

"Watch what happens when we connect them. I'm going to analyze these resolved denials in real-time."

*As progress streams in:*

"The system is clustering similar denial patterns... now it's extracting prevention rules using AI. Each cluster of similar denials becomes one reusable lesson.

Look — it just learned that UnitedHealthcare denies ALS-1 claims that are missing explicit transport necessity language. That's Rule 1, based on 6 similar denials. 

Now it's processing Aetna prior auth patterns... Medicare PCS requirements... each cluster becomes a rule stored in vector memory."

*Wait for completion*

"Five rules extracted in under 30 seconds. The system just went from zero knowledge to five payer-specific prevention rules."

---

**[1:30 – 2:00] The Knowledge Base**

*Click: Knowledge Base tab*

"Here's what the system learned. Each rule shows the payer, the CPT code, the denial reason, and most importantly — the exact documentation elements required and recommended phrases to include.

This is the system's memory. Every resolved denial makes it smarter. And this memory is searchable — it's stored as semantic embeddings, so it matches on meaning, not just keywords."

---

**[2:00 – 3:30] Scoring a New Claim (THE MAIN EVENT)**

*Click: Score Claim tab*

"Now the payoff. Here's a new PCR narrative — a 67-year-old male, chest pain, transported by ALS-1 Emergency to UnitedHealthcare.

Read this narrative — it looks fine. Dispatched, assessed, treated, transported. A billing team would probably submit this."

*Click "Score Claim"*

"But look at the score — HIGH risk, 82 out of 100. Three flags.

Flag one: missing transport necessity language. The system knows UHC denied 6 similar claims averaging $1,847 each when this phrase was missing. And it tells you exactly what to add.

Flag two: no vital signs documented. Without BP, heart rate, SpO2, the payer can't verify ALS-level care was needed.

This claim would have been denied. Now it gets caught before submission."

---

**[3:30 – 4:00] The Vision**

"This is the denial-to-prevention feedback loop. Every denied claim that gets resolved teaches the system something new. Over time, denial rates drop because the same mistakes stop happening.

Scribe creates the chart. Denials resolves the problems. This system connects them — and the more data it gets, the smarter it becomes.

Thanks for watching."

---

### Recording Tips
- Keep cursor movements slow and deliberate
- Pause briefly after clicking buttons to let results load
- Don't rush through the scoring results — that's the climax
- Zoom in on the flag details if Loom allows
- Use a clean browser window (no bookmarks bar, no extensions showing)
