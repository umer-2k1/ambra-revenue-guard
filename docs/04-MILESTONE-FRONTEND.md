# Milestone 4: Frontend UI

## Goal
Build a React frontend with 4 tab views matching the demo flow. The UI must match Ambra911's design language and feel like a real product extension, not a hackathon prototype.

## Completion Criteria
- `npm run dev` starts the frontend on port 5173
- Tab 1 (Denials) shows 28 cases in a clean table
- Tab 2 (Analyze) shows real-time progress via SSE when "Analyze" is clicked
- Tab 3 (Knowledge Base) shows extracted rules as cards
- Tab 4 (Score Claim) shows demo claim, scores it, displays flags
- All tabs work end-to-end with the backend

---

## Ambra911 Design Theme

Extracted from ambra911.com. The demo must follow this visual language.

### Colors
```css
:root {
  /* Primary */
  --ambra-dark: #5C0A05;        /* Dark brown-red — primary brand, headings, CTA buttons */
  --ambra-orange: #FE4311;      /* Bright orange — accent, highlights, key metrics */
  --ambra-orange-bright: #FF4412; /* Slightly brighter orange variant */
  
  /* Neutrals */
  --ambra-black: #000000;       /* Body text, secondary headings */
  --ambra-text-muted: #999999;  /* Muted/secondary text */
  --ambra-text-body: rgba(0,0,0,0.65); /* Body paragraph text */
  
  /* Backgrounds */
  --ambra-white: #FFFFFF;       /* Main background */
  --ambra-warm-bg: #F8F4F1;     /* Warm off-white — section backgrounds */
  --ambra-card-bg: #EEE7DE;     /* Beige — card backgrounds, panels */
  --ambra-card-border: #DBD0C2; /* Warm tan — borders, dividers */
  
  /* Functional */
  --risk-high: #DC2626;         /* Red for high risk */
  --risk-medium: #F59E0B;       /* Amber for medium risk */
  --risk-low: #10B981;          /* Green for low risk */
  --success: #10B981;           /* Green checkmarks, success states */
}
```

### Typography
```css
/* Ambra uses "Cy Text Bold" — we use Inter as a close match (free, Google Fonts) */
body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

h1 { font-size: 3rem; font-weight: 700; color: var(--ambra-dark); line-height: 1.08; }
h2 { font-size: 2.25rem; font-weight: 600; color: var(--ambra-black); }
h3 { font-size: 1.5rem; font-weight: 600; color: var(--ambra-black); }
body { font-size: 1rem; color: var(--ambra-text-body); }
.small { font-size: 0.875rem; color: var(--ambra-text-muted); }
```

### Component Styles
```css
/* Buttons — Primary CTA */
.btn-primary {
  background: var(--ambra-dark);
  color: white;
  border-radius: 50px;         /* Fully rounded pill shape */
  padding: 12px 32px;
  font-weight: 500;
  border: none;
}

/* Buttons — Secondary */
.btn-secondary {
  background: var(--ambra-black);
  color: white;
  border-radius: 50px;
  padding: 12px 32px;
}

/* Buttons — Outline */
.btn-outline {
  background: transparent;
  color: var(--ambra-dark);
  border: 1px solid var(--ambra-card-border);
  border-radius: 50px;
  padding: 10px 24px;
}

/* Cards */
.card {
  background: var(--ambra-white);
  border: 1px solid var(--ambra-card-border);
  border-radius: 16px;
  padding: 24px;
}

/* Section backgrounds */
.section-warm {
  background: var(--ambra-warm-bg);
  border-radius: 20px;
  padding: 40px;
}

/* Tags/Badges */
.badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  border-radius: 50px;
  font-size: 0.75rem;
  font-weight: 500;
}
.badge-high { background: #FEE2E2; color: #DC2626; }
.badge-medium { background: #FEF3C7; color: #D97706; }
.badge-low { background: #D1FAE5; color: #059669; }
```

### Layout
- Max content width: 1200px, centered
- Page padding: 24px horizontal
- Card gap: 16px
- Section gap: 48px
- Nav height: 64px, sticky

### Key Visual Elements
- **Pill-shaped buttons** — always fully rounded (border-radius: 50px)
- **Warm palette** — beige/cream backgrounds, not cold grays
- **Big bold numbers** — metrics and stats are large and orange
- **Clean cards** — white with subtle warm borders, rounded corners
- **No harsh shadows** — if any shadow, use `box-shadow: 0 1px 3px rgba(0,0,0,0.08)`
- **Orange accents** — for metrics, active states, progress indicators
- **Dark brown CTAs** — primary actions use #5C0A05

---

## Step 1: React Project Setup with shadcn/ui

### 1a: Create the Vite project
```bash
cd ambra-demo
npm create vite@latest frontend -- --template react
cd frontend
npm install
```

### 1b: Install Tailwind CSS v4 + shadcn/ui
shadcn/ui requires Tailwind CSS. Install and configure:
```bash
npm install -D tailwindcss @tailwindcss/vite
npm install lucide-react
```

Add the Tailwind plugin to `vite.config.js`:
```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  },
  resolve: {
    alias: {
      "@": "/src",
    },
  },
})
```

Add to `src/index.css`:
```css
@import "tailwindcss";
```

### 1c: Initialize shadcn/ui
```bash
npx shadcn@latest init
```
When prompted:
- Style: Default
- Base color: Neutral
- CSS variables: Yes

This creates `components.json` and sets up the `src/components/ui/` directory.

### 1d: Install ALL required shadcn/ui components
Install these components heavily used throughout the UI:
```bash
npx shadcn@latest add card table badge button tabs progress textarea select alert separator skeleton scroll-area tooltip
```

This creates individual component files in `src/components/ui/`:
- `card.jsx` — Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter
- `table.jsx` — Table, TableHeader, TableRow, TableHead, TableBody, TableCell
- `badge.jsx` — Badge (with variants)
- `button.jsx` — Button (with variants and sizes)
- `tabs.jsx` — Tabs, TabsList, TabsTrigger, TabsContent
- `progress.jsx` — Progress bar
- `textarea.jsx` — Textarea
- `select.jsx` — Select, SelectTrigger, SelectValue, SelectContent, SelectItem
- `alert.jsx` — Alert, AlertTitle, AlertDescription
- `separator.jsx` — Separator
- `skeleton.jsx` — Skeleton (loading placeholders)
- `scroll-area.jsx` — ScrollArea
- `tooltip.jsx` — Tooltip, TooltipTrigger, TooltipContent, TooltipProvider

### 1e: Customize shadcn/ui theme with Ambra colors
After shadcn/ui init, update the CSS variables in `src/index.css` to use Ambra's warm palette instead of the default cold grays. Map the CSS custom properties that shadcn/ui components use:

```css
@import "tailwindcss";

@layer base {
  :root {
    /* Ambra theme overrides for shadcn/ui */
    --background: 30 33% 97%;        /* #F8F4F1 warm off-white */
    --foreground: 0 0% 0%;           /* #000000 */
    --card: 0 0% 100%;               /* #FFFFFF */
    --card-foreground: 0 0% 0%;
    --popover: 0 0% 100%;
    --popover-foreground: 0 0% 0%;
    --primary: 3 89% 19%;            /* #5C0A05 dark brown-red */
    --primary-foreground: 0 0% 100%;
    --secondary: 30 33% 91%;         /* #EEE7DE card bg */
    --secondary-foreground: 0 0% 0%;
    --muted: 30 33% 91%;             /* #EEE7DE */
    --muted-foreground: 0 0% 60%;    /* #999999 */
    --accent: 14 99% 53%;            /* #FE4311 orange */
    --accent-foreground: 0 0% 100%;
    --destructive: 0 72% 51%;        /* #DC2626 risk-high */
    --destructive-foreground: 0 0% 100%;
    --border: 30 22% 81%;            /* #DBD0C2 warm tan */
    --input: 30 22% 81%;
    --ring: 3 89% 19%;               /* #5C0A05 */
    --radius: 1rem;                  /* 16px rounded cards */

    /* Custom Ambra tokens (used directly in custom styles) */
    --ambra-dark: #5C0A05;
    --ambra-orange: #FE4311;
    --ambra-warm-bg: #F8F4F1;
    --ambra-card-bg: #EEE7DE;
    --ambra-card-border: #DBD0C2;
    --risk-high: #DC2626;
    --risk-medium: #F59E0B;
    --risk-low: #10B981;
  }
}
```

### 1f: Component usage pattern
Throughout the frontend, use shadcn/ui components as the primary building blocks. Example pattern:

```jsx
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert"
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from "@/components/ui/tooltip"
import { Separator } from "@/components/ui/separator"
```

### 1g: Custom Ambra-specific component overrides
Create custom button variants for Ambra's pill-shaped buttons by extending shadcn's Button component in `src/components/ui/button.jsx`:
- Add a `"pill"` variant with `border-radius: 50px` and Ambra dark background
- Add a `"pill-outline"` variant with transparent bg and warm border
- Add a `"pill-accent"` variant with orange background for secondary CTAs

For risk-level badges, extend the shadcn Badge:
- `"high"` variant: red bg/text (#FEE2E2 / #DC2626)
- `"medium"` variant: amber bg/text (#FEF3C7 / #D97706)
- `"low"` variant: green bg/text (#D1FAE5 / #059669)

### Key shadcn/ui usage per screen:
- **DenialsTable (Screen 1)**: `Card` for stat boxes, `Table` for denial list, `Badge` for outcome/payer tags, `Tooltip` for truncated text
- **AnalyzeView (Screen 2)**: `Card` for the main panel, `Button` for analyze CTA, `Progress` for the progress bar, `ScrollArea` for the live feed, `Badge` for severity, `Skeleton` for loading states, `Alert` for completion/error messages
- **KnowledgeBase (Screen 3)**: `Card` for each rule, `Badge` for severity/payer/CPT/CARC tags, `Separator` between sections, `ScrollArea` for long lists
- **ScoreClaim (Screen 4)**: `Card` for the form and results, `Select` for dropdowns, `Textarea` for narrative, `Button` for score CTA, `Badge` for risk level, `Alert` for flags with suggestions, `Skeleton` for loading state, `Separator` between flags

## Step 2: App.jsx — Main Layout

The app has a top nav bar with the Ambra logo (use a simple text logo: "✦ Ambra" with the asterisk in orange) and 4 tab buttons. **Use shadcn/ui `Tabs` component** for the tab navigation.

```
┌──────────────────────────────────────────────────────┐
│  ✦ Ambra   [Denials] [Analyze] [Knowledge] [Score]  │
├──────────────────────────────────────────────────────┤
│                                                      │
│              Active tab content here                 │
│                                                      │
└──────────────────────────────────────────────────────┘
```

```jsx
<Tabs defaultValue="denials" value={activeTab} onValueChange={setActiveTab}>
  <TabsList className="...ambra pill styling...">
    <TabsTrigger value="denials">Denials</TabsTrigger>
    <TabsTrigger value="analyze">Analyze</TabsTrigger>
    <TabsTrigger value="knowledge">Knowledge Base</TabsTrigger>
    <TabsTrigger value="score">Score Claim</TabsTrigger>
  </TabsList>
  <TabsContent value="denials"><DenialsTable /></TabsContent>
  <TabsContent value="analyze"><AnalyzeView /></TabsContent>
  <TabsContent value="knowledge"><KnowledgeBase /></TabsContent>
  <TabsContent value="score"><ScoreClaim /></TabsContent>
</Tabs>
```

- Style `TabsTrigger` with Ambra's pill shape, outline style when inactive, filled dark when active
- Add a small subtitle under the main title: "Denial-to-Prevention Feedback Loop"
- Track system status (rules count) in state — poll `/api/status` on mount
- **Tab flow guidance**: Tabs 3 and 4 should show a gentle `Alert` (shadcn) if analysis hasn't been run yet (no rules exist), directing the user to run analysis first

## Step 3: api.js — API Client

```javascript
const API_BASE = '/api';

export async function getDenials() {
  const res = await fetch(`${API_BASE}/denials`);
  return res.json();
}

export async function getDenialStats() {
  const res = await fetch(`${API_BASE}/denials/stats`);
  return res.json();
}

export async function startAnalysis(onProgress) {
  // Returns an EventSource for SSE
  const eventSource = new EventSource(`${API_BASE}/analyze`, { 
    // Note: EventSource uses GET by default. 
    // We need POST — use fetch with ReadableStream instead.
  });
  // IMPORTANT: EventSource only supports GET. For POST, use fetch:
  const response = await fetch(`${API_BASE}/analyze`, { method: 'POST' });
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  let buffer = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop(); // Keep incomplete line in buffer
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        onProgress(data);
      }
    }
  }
}

export async function getRules() {
  const res = await fetch(`${API_BASE}/rules`);
  return res.json();
}

export async function getStatus() {
  const res = await fetch(`${API_BASE}/status`);
  return res.json();
}

export async function scoreClaim(claimData) {
  const res = await fetch(`${API_BASE}/score`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(claimData),
  });
  return res.json();
}

export async function getDemoClaim() {
  const res = await fetch(`${API_BASE}/demo-claim`);
  return res.json();
}

export async function resetSystem() {
  const res = await fetch(`${API_BASE}/reset`, { method: 'POST' });
  return res.json();
}
```

## Step 4: DenialsTable.jsx — Screen 1

### Layout
```
┌─────────────────────────────────────────────────────────┐
│  Summary Stats Row                                       │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                   │
│  │ 28   │ │$38K  │ │ 5    │ │ 83%  │                   │
│  │Cases │ │Denied│ │Payers│ │Won   │                   │
│  └──────┘ └──────┘ └──────┘ └──────┘                   │
│                                                          │
│  Denial Cases                                            │
│  ┌──────────────────────────────────────────────────────┐│
│  │ ID  │ Payer    │ CPT   │ CARC  │ Amount  │ Outcome  ││
│  │D-001│ UHC     │ A0427 │ CO-16 │ $1,847  │Overturned││
│  │D-002│ UHC     │ A0427 │ CO-16 │ $2,103  │Overturned││
│  │ ... │ ...     │ ...   │ ...   │ ...     │ ...      ││
│  └──────────────────────────────────────────────────────┘│
│                                                          │
│  ⚠ This knowledge is trapped in resolved cases.         │
│    No system learns from these patterns.                 │
└─────────────────────────────────────────────────────────┘
```

### Behavior
- Fetch denials on mount
- Compute summary stats client-side (or use `/api/denials/stats`)
- Stats: use shadcn `Card` components with big orange numbers (#FE4311) for the values
- Table: use shadcn `Table`, `TableHeader`, `TableRow`, `TableHead`, `TableBody`, `TableCell` — style with alternating white/warm-bg rows
- Outcome column: use shadcn `Badge` components (color-coded: green for overturned, red for denied, amber for partial) with custom Ambra risk variants
- Payer column: use shadcn `Badge` with secondary variant
- At the bottom: use shadcn `Alert` component (warm-bg) with the message about trapped knowledge
- Use `Tooltip` for truncated denial reason text
- Clicking a row can expand to show denial_reason and pcr_excerpt (optional nice-to-have)

## Step 5: AnalyzeView.jsx — Screen 2

### Layout — Before Analysis
```
┌─────────────────────────────────────────────────────────┐
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │  🧠  Ready to Analyze                              │  │
│  │                                                     │  │
│  │  28 denial cases • 5 payers • $38K denied          │  │
│  │                                                     │  │
│  │  The system will:                                   │  │
│  │  1. Cluster similar denial patterns                 │  │
│  │  2. Extract prevention rules using AI               │  │
│  │  3. Store rules in vector memory                    │  │
│  │                                                     │  │
│  │          [ Analyze Denials ]                         │  │
│  │                                                     │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Layout — During Analysis (SSE streaming)
```
┌─────────────────────────────────────────────────────────┐
│  ┌──────────────────────────────────────────────────┐    │
│  │  Progress Bar  ████████████░░░░░░░░  60%         │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  Live Feed:                                              │
│  ┌──────────────────────────────────────────────────┐    │
│  │ ✓ Loaded 28 denial cases                         │    │
│  │ ✓ Identified 5 denial patterns                   │    │
│  │ ✓ Cluster 1: uhc_medical_necessity (6 cases)     │    │
│  │   → Rule: "UHC ALS-1 requires transport          │    │
│  │     necessity language"                           │    │
│  │   Confidence: 92% • Severity: HIGH               │    │
│  │ ● Cluster 2: aetna_prior_auth (5 cases)          │    │
│  │   Analyzing...                                    │    │
│  └──────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### Behavior
- On mount: check `/api/status` — if rules already exist, show "Analysis complete" state with option to reset
- **"Analyze Denials" button**: calls `startAnalysis()`, streams SSE events
- Progress bar: updates from `progress` field (0.0 to 1.0)
- Live feed: scrolling list of events. Each event gets appended:
  - `step: "starting"` → "✓ Loaded N denial cases"
  - `step: "clustering"` → "✓ Identified N patterns"
  - `step: "extracting"` → "● Analyzing cluster: {name} ({n} cases)..."
  - `step: "stored"` → "✓ Rule: {title}" with confidence/severity badges
  - `step: "complete"` → "✓ Analysis complete. N rules learned."
- When a rule is extracted (step="stored"), show a mini rule card inline
- On completion: automatically switch to Knowledge Base tab OR show "View Rules →" button
- **Disable the analyze button** during analysis
- If analysis already done: show green "Analysis Complete" banner with rules count and a "Reset & Re-analyze" button

### SSE Integration Notes
- Use `fetch()` with `ReadableStream`, NOT `EventSource` (because POST)
- Parse SSE format: lines starting with `data: ` contain JSON
- Handle connection drops: show error message, allow retry
- The `event: progress` field from SSE maps to different event types via the `step` field

## Step 6: KnowledgeBase.jsx — Screen 3

### Layout
```
┌─────────────────────────────────────────────────────────┐
│  Knowledge Base              5 rules • 24 denials learned│
│                                                          │
│  ┌───────────────────────────────────────────────────┐   │
│  │  R-001  HIGH                                       │   │
│  │  UHC ALS-1 requires transport necessity language   │   │
│  │                                                     │   │
│  │  Payer: UnitedHealthcare  CPT: A0427  CARC: CO-16  │   │
│  │  Based on 6 denials • Confidence: 92%              │   │
│  │  Avg denied: $1,847                                 │   │
│  │                                                     │   │
│  │  Required Elements:                                 │   │
│  │  • Explicit transport necessity statement           │   │
│  │  • Medical condition requiring ALS intervention     │   │
│  │  • Vital signs supporting ALS-level assessment      │   │
│  │                                                     │   │
│  │  Recommended Phrases:                               │   │
│  │  "Patient's condition of [X] required ALS-level     │   │
│  │   transport due to [specific intervention]..."      │   │
│  └───────────────────────────────────────────────────┘   │
│                                                          │
│  ┌───────────────────────────────────────────────────┐   │
│  │  R-002  HIGH                                       │   │
│  │  Aetna BLS Non-Emergency requires prior auth...    │   │
│  │  ...                                                │   │
│  └───────────────────────────────────────────────────┘   │
│                                                          │
│  ... (3 more rule cards)                                 │
└─────────────────────────────────────────────────────────┘
```

### Behavior
- Fetch rules from `/api/rules` on mount
- If no rules exist, show empty state: "No rules learned yet. Run analysis first."
- Each rule is a card with:
  - Rule ID + severity badge (color-coded)
  - Rule title (bold, large)
  - Payer, CPT, CARC as small tag-style badges
  - Source denials count + confidence percentage
  - Average denied amount in orange
  - Required elements as a bulleted list
  - Recommended phrases in a quote-style block (slightly indented, warm bg)
- Cards should be full-width, stacked vertically
- Optional: clicking a rule card expands/collapses the details (show title + badges collapsed, expand for full details)

## Step 7: ScoreClaim.jsx — Screen 4

### Layout — Before Scoring
```
┌─────────────────────────────────────────────────────────┐
│  Score a Claim Before Submission                         │
│                                                          │
│  ┌─────────────────────┐  ┌─────────────────────┐       │
│  │ Service Type         │  │ Payer               │       │
│  │ ALS-1 Emergency     ▼│  │ UnitedHealthcare   ▼│       │
│  └─────────────────────┘  └─────────────────────┘       │
│  ┌─────────────────────┐                                 │
│  │ CPT Code             │                                │
│  │ A0427               ▼│                                │
│  └─────────────────────┘                                 │
│                                                          │
│  PCR Narrative:                                          │
│  ┌──────────────────────────────────────────────────────┐│
│  │ Dispatched to 742 Evergreen Terrace for a 67-year-  ││
│  │ old male experiencing chest pain. Patient found      ││
│  │ sitting in recliner, alert and oriented x4...        ││
│  │                                                      ││
│  │ (pre-filled with demo claim, editable)               ││
│  └──────────────────────────────────────────────────────┘│
│                                                          │
│               [ Score Claim ]                            │
└─────────────────────────────────────────────────────────┘
```

### Layout — After Scoring
```
┌─────────────────────────────────────────────────────────┐
│  Risk Assessment                                         │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │        ┌─────────┐                                │    │
│  │        │  HIGH   │     Risk Score: 82/100         │    │
│  │        │  RISK   │     3 issues found              │    │
│  │        └─────────┘                                │    │
│  │                                                    │    │
│  │  Top Recommendation:                              │    │
│  │  "Add explicit transport necessity statement..."   │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  Flags:                                                  │
│  ┌──────────────────────────────────────────────────┐    │
│  │ ⚠ HIGH  Missing transport necessity language      │    │
│  │ Rule: R-001 • Based on 6 similar denials          │    │
│  │ Est. risk: $1,847                                  │    │
│  │                                                    │    │
│  │ Fix: "Add: Patient's condition of [chest pain]    │    │
│  │ required ALS-level transport due to need for       │    │
│  │ continuous cardiac monitoring..."                  │    │
│  └──────────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────────┐    │
│  │ ⚠ HIGH  No vital signs documented                 │    │
│  │ Rule: R-005 • Based on 4 similar denials          │    │
│  │ ...                                                │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  [ Score Another Claim ]                                 │
└─────────────────────────────────────────────────────────┘
```

### Behavior
- On mount: load demo claim from `/api/demo-claim` and pre-fill the form
- If no rules exist, show message: "Run analysis first to build the knowledge base."
- Service type, CPT code, and payer are dropdown selects (pre-filled)
- Narrative is a textarea (pre-filled, editable)
- **"Score Claim" button**: calls `/api/score` with form data, shows loading spinner
- **Results display**:
  - Big risk badge at top (color-coded: red HIGH, amber MEDIUM, green LOW)
  - Risk score as large number "/100"
  - Top recommendation in a highlighted box
  - Each flag as a card:
    - Risk level badge
    - Missing element (what's wrong)
    - Rule reference + how many similar denials
    - Estimated denial risk in orange ($)
    - Suggestion in a "fix" box (warm bg, slightly different style)
  - "Score Another Claim" button resets the result (not the form)
- Loading state: use shadcn `Skeleton` components to show shimmer on the results area while LLM is thinking

## Step 8: Responsive & Polish

- The demo will be recorded at desktop width (1280px+), but the UI should not break at narrower widths
- Add smooth transitions when switching tabs (fade or slide)
- Progress bar should animate smoothly
- SSE feed should auto-scroll to the latest event
- Use `lucide-react` icons sparingly:
  - `AlertTriangle` for risk flags
  - `CheckCircle` for success/completed steps
  - `Brain` for the knowledge base
  - `Shield` or `ShieldCheck` for the scoring
  - `Loader2` (animated) for loading states
  - `RefreshCw` for reset

## Verification

```bash
# Terminal 1: Backend
cd ambra-demo && uvicorn backend.main:app --reload --port 8000

# Terminal 2: Frontend
cd ambra-demo/frontend && npm run dev

# Open http://localhost:5173
# 1. Denials tab: see 28 cases in table with stats
# 2. Analyze tab: click button, watch real-time progress
# 3. Knowledge Base tab: see 5 rule cards
# 4. Score Claim tab: see pre-filled claim, click Score, see HIGH risk with flags
```
