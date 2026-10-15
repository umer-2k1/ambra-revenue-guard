# YouTube thumbnails — Ambra demo

Twelve variants (01–05 original, 06–12 refined from 01), all **1280×720** (16:9), **PNG**, well under YouTube's 2 MB limit.
Every variant is checked programmatically for **text overlap** and canvas overflow — all clear.

| # | File | EMS visual | Hook |
|---|---|---|---|
| 01 | `01-the-loop.png` | — | **Every denial teaches a rule** — the denial → prevention loop |
| 02 | `02-ambulance-loop.png` | Ambulance | **Every denial teaches a rule** + the 4-step loop |
| 03 | `03-ecg-heartbeat.png` | ECG line + ambulance | **One denial = one rule** — "DENIAL HERE / CAUGHT HERE" |
| 04 | `04-star-of-life.png` | Star of Life | **Learn from every denial** + the loop |
| 05 | `05-ambulance-hero.png` | Ambulance (hero) | **Denial → Prevention** — one denial, one rule |

### Refined from 01 (same loop concept, more polish)

| # | File | What's new |
|---|---|---|
| 06 | `06-loop-bold.png` | Huge two-tone headline, glow, LIVE DEMO badge, arrows between steps |
| 07 | `07-loop-flywheel.png` | Circular flywheel diagram beside the headline |
| 08 | `08-denied-to-prevented.png` | DENIED → learns the rule → PREVENTED (risk colors) |
| 09 | `09-loop-warm.png` | Light warm Ambra palette (high contrast alt to dark) |
| 10 | `10-loop-rule-card.png` | Shows an actual learned IF/THEN rule card |
| 11 | `11-flywheel-icons.png` | Flywheel from 07 with icons per step (document, magnifier, database, shield), glow rings |
| 12 | `12-loop-in-out.png` | Centered loop: DENIED flows in, PREVENTED flows out |

`_preview.png` is a contact sheet of all twelve.

## Brand
- Palette: dark `#5C0A05` / `#1A0B09`, orange `#FE4311`, warm `#F8F4F1`.
- Lockup: `✦ Ambra`.
- EMS imagery is drawn in SVG (ambulance side view with light bar, ECG trace, Star of Life) — no stock photos, fully editable.

## Rules followed
- 1280×720 · 16:9 · PNG · ≤ 2 MB ✔
- Big text, few words, readable at phone size ✔
- High contrast, one focal point per thumbnail ✔
- No overlapping text (verified) ✔

## Regenerate / tweak
Edit the `.svg` (source of truth), then re-render with headless Chrome:

```bash
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
for f in docs/thumbnails/*.svg; do
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars \
    --user-data-dir=/tmp/chrome-thumbs --window-size=1280,720 \
    --screenshot="${f%.svg}.png" "file://$PWD/$f"
done
```
