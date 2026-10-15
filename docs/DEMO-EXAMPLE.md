# The "combined claim" demo — script + paste text

This is the segment that proves the point: the system is **not** matching exact past
denials — it learned **rules** from *different* cases and can catch a brand-new claim
that quietly combines several of those patterns at once.

Everything here is **verified against the live deployment** (https://ambra.umer2k1.com).

---

## 1. The simple cases to point at (Denials tab)

These are the easy-to-explain ones. They fall into two groups:

| ID | Payer | What happened | Group |
|---|---|---|---|
| **D-027** | Anthem BCBS | Stable, ambulatory, **3 days of back pain** — transported on request. *"Appears to be for patient convenience."* | didn't need an ambulance |
| **D-022** | Cigna | Minor laceration, stable, ambulatory — **no ALS care given** but billed ALS-1. | didn't need an ambulance |
| **D-009** | Aetna | Ambulatory with a walker — ambulance not medically necessary. | didn't need an ambulance |
| **D-012** | Anthem BCBS | Billed **23 miles** but the nearest facility was **8 miles** away — no reason given for the farther hospital. | went too far |
| **D-013** | Anthem BCBS | **17 miles**, no pickup address, no route justification. | went too far |
| **D-015** | Anthem BCBS | Billed **22 miles**; the real distance was **6**. | went too far |

**How to show them:** open **D-027** and **D-012** (click each row → the case-file drawer).

---

## 2. What the system learned from them

On the **Knowledge Base** tab, point at these rules:

- **R-003 — "Every claim must tie billed loaded miles to documented origin/destination and route."**
  Learned from the **distance cases** (D-012–D-015).
- **R-001 — "State ALS necessity and why BLS/other transport was unsafe."**
  Learned from the **UHC medical-necessity** cases.
- **R-005 — "List every ALS procedure in the PCR before billing ALS-1/ALS-2."**
  Learned from the **Cigna level-of-service** cases.

> Key line: *"These are three separate rules, learned from three different sets of cases —
> different payers, different denial codes."*

---

## 3. The new claim to paste (a blend — not a copy of any single case)

**On the Score Claim tab, set:**
- **Service type:** `ALS-1 Emergency`
- **Payer:** `UnitedHealthcare`
- **CPT code:** `A0427`

Then paste this narrative:

> At 10:15 AM we were sent to 88 Birch Lane for a 58-year-old man with low back pain. He told us the pain started about three days ago after he lifted some boxes, and it has not changed since yesterday. He was standing at the door when we arrived and walked to the stretcher by himself. His vital signs were normal - BP 128/78, HR 76, oxygen saturation 98%, breathing rate 16. He rated the pain a 5 out of 10 and said ibuprofen at home had been helping. He asked us to take him to Riverside Medical Center because his back specialist works there. The closest hospital, Springfield General, is about five minutes from his house; Riverside is about 18 miles away. He stayed comfortable the whole ride and walked into the emergency department on his own.

*This is deliberately a **blend**: a non-emergency back-pain transport (like D-027), taken to a
farther hospital (like D-012), billed at ALS (like D-022) — but it is **not** a copy of any of them.*

---

## 4. The verified result

```
HIGH · 92 / 100 · 3 flags of 5 rules checked
```

| Flag | Rule | Severity | The gap |
|---|---|---|---|
| 1 | **R-001** | high | No statement that ALS level was required, or why BLS/other transport was unsafe |
| 2 | **R-005** | high | No itemized list of ALS procedures (with times) |
| 3 | **R-003** | medium | Names the closer vs farther facility, but no full addresses, verified mileage, or reason for the farther destination |

Plus a **"For non-techs"** line, roughly: *"…it never lists a single advanced procedure the
paramedics actually did. That looks like a plain ride, not a paramedic call."*

---

## 5. The spoken script for this segment (~60–75 seconds)

**[Denials tab — open D-027, then D-012]**

> "These are the easy cases. This one — a man with three days of back pain who walked to the
> stretcher. And this one — they billed 23 miles when the nearest hospital was 8 miles away.
> On their own, none of these look like much."

**[Knowledge Base tab — point at R-003]**

> "But watch what it learned. From the distance cases, it pulled out a rule: every claim has to
> justify the miles and the destination. That's R-003. And separately — from other payers' cases —
> it learned rules about proving *why* a paramedic was needed, and listing the procedures."

**[Score Claim tab — set the fields, paste, click Score]**

> "Now here's a brand-new claim. It's not a copy of any of those cases — it's a mix. A back-pain
> patient who walked to the stretcher, taken 18 miles to a farther hospital, billed as advanced
> life support.
>
> **HIGH — 92 out of 100. Three flags.** And look — they come from **three different rules**.
> One says *you haven't proved why a paramedic was needed.* One says *you haven't listed the ALS
> procedures.* And one says *you haven't justified the distance.*
>
> None of these is an exact repeat of a past denial. The system combined what it learned from
> completely different cases and caught the whole thing before it was submitted."

**The line that lands:**

> *"It's not matching old claims — it learned the patterns, and it catches new ones it has never seen."*
