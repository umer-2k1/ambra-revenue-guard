# YouTube thumbnails — Ambra demo

Five variants, all **1280×720** (16:9), **PNG**, well under YouTube's 2 MB limit.
Every variant was checked programmatically for **text overlap** and canvas overflow — all clear.

| # | File | Style | Hook |
|---|---|---|---|
| 01 | `01-the-loop.png` | Dark, 4-step flow | **Every denial teaches a rule** — the denial → prevention loop |
| 02 | `02-denied-vs-prevented.png` | Light, split panels | **A denied claim, caught in time** — red vs green |
| 03 | `03-83-percent.png` | Dark, big-number | **83% of appeals get overturned** (Ambra's own figure) |
| 04 | `04-stop-paying-twice.png` | Minimal dark | **Stop paying for the same mistake twice** |
| 05 | `05-catch-the-denial.png` | Warm, product UI | **Catch the denial before you send it** — with a 90/100 risk card |

`_preview.png` is a contact sheet of all five.

## Brand
- Palette: dark `#5C0A05`, orange `#FE4311`, warm `#F8F4F1`.
- Lockup: `✦ Ambra`.
- Numbers are from Ambra's own site (83% overturn) and the demo (90/100).

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

Want a tighter guarantee before shipping? Run a text-overlap check over the SVGs first.
