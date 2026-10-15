# Demo Script — Ambra Denial-to-Prevention

**Length:** ~3 min 45 s · **Audience:** the founder (domain expert, short on time) · **Goal:** prove one idea — *a resolved denial can teach a rule that prevents the next denial.*

---

## One-line pitch

> "Every ambulance agency already fights denials. This turns each denial they *win* into a rule that stops the same mistake happening again — before the claim is submitted."

**Three-sentence version** (if asked cold):
> "An ambulance bills an insurer; the insurer denies it; the appeal team wins and moves on — and the lesson dies in that one claim. This system reads all those resolved denials, learns why each one was denied, and checks the next claim before it goes out. So the same documentation gap never costs you money twice."

---

## Before you hit record (5-minute setup)

- [ ] Open **https://ambra.umer2k1.com** in Chrome.
- [ ] Window ~1440px wide. Hide the bookmarks bar, turn off notifications, close personal tabs.
- [ ] On the **Analyze** tab, click **Reset & re-analyze** so rules = **0**. (So the *learning* happens on camera — that's the wow moment.)
- [ ] Start on the **Denials** tab.
- [ ] Have this open in a notes app, ready to read the **narratives** (Section 5 “Optional”).
- [ ] Do a dry run once so you know the timing.

> If **Analyze** feels slow on the day, don't panic — talk over it (the script below has lines for that). If it ever fails, go straight to **Knowledge Base** (rules stay loaded) and say *"we ran this a moment ago — here's what it learned."*

---

## The script

### 0:00 – 0:30 · The problem
**On screen:** Denials tab (28 rows + the four stat cards).

> "Every ambulance company has a pile of cases like this — 28 resolved denials across five payers. **$36,570** denied. Some were overturned on appeal, some weren't.
>
> Here's the thing: when the denial team wins an appeal, they learn something genuinely useful. But that lesson stays inside this one claim. It never reaches the person writing the next patient-care report. So the same documentation mistake causes the same denial, again and again.
>
> That's the gap — charting and denial management are two pipelines that never talk."

**Click one row** (e.g. **D-001**) briefly — the case file opens.

> "Each case has the full story — what the crew charted, why the payer denied it, and how the appeal fixed it." *(Close the drawer.)*

### 0:30 – 1:30 · Watch it learn
**Click:** **Analyze** tab.

> "So we connect them. I'll analyze these denials live."

**Click:** **Analyze Denials.** *(Then literally read the feed as it streams — this is the moment.)*

> "It's clustering similar denials… now it's asking the model to extract a rule from each pattern.
>
> There's the first rule — **UnitedHealthcare denies advanced-life-support claims when the chart never explains why a basic crew wasn't enough.** That's based on six denials.
>
> And it keeps going — Aetna prior-auth… Medicare paperwork… Cigna level-of-service. Five rules, each one learned from a real payer pattern."

*(If it's still running:)* "It's storing each rule as both a database row and a semantic embedding, so it can later match on *meaning*, not keywords."

### 1:30 – 2:00 · The memory
**Click:** **View Knowledge Base** (or the Knowledge Base tab).

> "This is the system's memory. Notice it leads with plain English — *'say why a paramedic was needed, not just that one showed up'* — then exactly what to add to the chart. The billing codes are there but demoted and explained, so a non-expert can read this too.
>
> And each rule shows the denials that taught it — click one and you're back at that case."

### 2:00 – 3:15 · The payoff
**Click:** **Score Claim** tab.

> "Now the payoff. Here's a *new* claim — a 67-year-old with chest pain, transported ALS to UnitedHealthcare. Read it — it looks completely fine. A billing team would send this."

**Click:** **Score Claim.**

> "**HIGH risk — 88 out of 100.** Three flags.
>
> Flag one: the chart never says *why* a paramedic was needed. The system knows UHC denied six similar claims, averaging **$1,850** each — and it tells you the exact sentence to add.
>
> Flag two: no itemized ALS procedures.
>
> And at the top — a plain-English version for anyone who isn't a biller: *'the chart shows chest pain and one aspirin, but never explains why a paramedic-level ambulance was needed instead of a basic crew or a car.'*"

### 3:15 – 3:45 · The vision
**On screen:** the risk result.

> "That claim would have been denied. Now it gets caught before it goes out.
>
> And this is the loop: every denied claim that gets resolved teaches one more rule. More denials resolved, more rules learned, fewer future denials.
>
> Scribe creates the chart. Denials fights the problems. This connects them — and the more data it gets, the smarter it gets."

**Optional close:** *"Live at ambra.umer2k1.com if you want to click around yourself."*

---

## What to INCLUDE
- The problem stated **in money** ($36,570; $1,850 per denial).
- The **live learning** (Analyze) — prove it's real, not pre-baked.
- **One** strong catch (the HIGH-risk chest-pain claim) with a specific dollar estimate and the fix.
- The **plain-English** angle — it's what makes the product usable by non-billers.
- The loop, in one sentence, at the end.

## What to LEAVE OUT
- ❌ Deployment/tech talk (Vercel, LangGraph, Qdrant, Postgres) — the founder cares about the outcome, not the stack.
- ❌ Walking through all 28 cases, the glossary drawer, or every rule.
- ❌ Long silences while Analyze runs — talk over them.
- ❌ Reading the whole flag text aloud — read the numbers and the "fix", then move on.
- ❌ Apologising for anything ("it's just a demo", "sorry it's slow") — narrate confidently.

## Optional extra beats (only if you want a longer cut)

> **Companion: [`docs/DEMO-EXAMPLE.md`](DEMO-EXAMPLE.md)** — a fully scripted "combined claim" segment (a *blend* of the non-emergency cases + the distance/destination cases) with the exact narrative to paste and the **verified** result. That's the strongest proof that the system generalises rather than matching exact old denials.

Run these on **Score Claim** to show the system **grades**, not just shouts:

| Paste this narrative… | Set payer / service / CPT | You get |
|---|---|---|
| Non-emergency back pain, walked to the ambulance, drove past a nearer hospital | Anthem BCBS · BLS Emergency · `A0428` | **MEDIUM 68** |
| A fully documented ALS chest-pain claim (addresses, mileage, procedure times, condition code) | UnitedHealthcare · ALS-1 Emergency · `A0427` | **LOW 15** |

> Line: *"It doesn't just always say HIGH — feed it a complete, well-justified chart and it goes green."*

*(The exact narratives are in the README under “Try these claims yourself”.)*

---

## Delivery tips
- **Move the cursor slowly.** Pause for a beat *after* every click, before you speak the result.
- **One take per screen** if you can — stitch them.
- Zoom in on the **flags** and the **dollar figures**.
- Speak at ~90% of your normal speed; it always sounds faster in the recording.
- Smile in the last 15 seconds — that's the energy people remember.

## Timing cheat-sheet
| Time | Screen | Beat |
|---|---|---|
| 0:00–0:30 | Denials | Problem + trapped knowledge |
| 0:30–1:30 | Analyze | Watch it learn (wow) |
| 1:30–2:00 | Knowledge Base | The memory, in plain English |
| 2:00–3:15 | Score Claim | The catch (payoff) |
| 3:15–3:45 | Score Claim | The loop + close |
