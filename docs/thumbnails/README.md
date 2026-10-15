# YouTube thumbnails — Ambra demo

Five variants, all **1280×720** (16:9) and **under 2 MB** (YouTube's limits).

| # | File | Hook | Why it works |
|---|---|---|---|
| 01 | `01-stop-the-denial.png` | **STOP THE DENIAL** | Action + urgency; the claim card shows the payoff (90/100, 3 gaps) |
| 02 | `02-36570-denied.png` | **$36,570 denied** | Money hook; the loop makes it about prevention, not just loss |
| 03 | `03-it-learns-loop.png` | **Every denial teaches a rule** | Explains the product at a glance (4-step loop) |
| 04 | `04-scribe-vs-denials.png` | **SCRIBE ✕ DENIALS** | Uses their own two product names; "the missing link" |
| 05 | `05-high-risk-caught.png` | **This claim looked fine** | Curiosity gap; the flags make it concrete |

`_preview.png` is a contact sheet of all five.

## Brand
- Palette: dark `#5C0A05`, orange `#FE4311`, warm `#F8F4F1`.
- Logo lockup: `✦ Ambra`.
- Numbers come from Ambra's own site (83% overturn, 38s appeal, 100+ agencies) and the demo ($36,570 / 90/100).

## Rules followed (YouTube guidance)
- 1280×720 · JPG/PNG · ≤ 2 MB ✔
- Big text, ≤ ~5 words, readable at phone size ✔
- High contrast (dark ↔ orange ↔ white) ✔
- One clear focal point per thumbnail ✔

Send me your thumbnail guide and I'll adjust (fonts, safe-zone margins, etc.).

## Regenerate / tweak
Edit the `.svg` (the source of truth), then re-render with headless Chrome:

```bash
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
for f in docs/thumbnails/*.svg; do
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars \
    --user-data-dir=/tmp/chrome-thumbs --window-size=1280,720 \
    --screenshot="${f%.svg}.png" "file://$PWD/$f"
done
```
