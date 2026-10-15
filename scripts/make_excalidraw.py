"""Generate editable Excalidraw (.excalidraw) versions of the demo diagrams.

Excalidraw files are just JSON. This script emits a minimal but valid file
(type "excalidraw", version 2) using the hand-drawn font (fontFamily 1) so the
result matches the SVG diagrams and can be opened/edited at excalidraw.com.

Run:  python3 scripts/make_excalidraw.py
"""
from __future__ import annotations

import json
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "diagrams")

DARK = "#5C0A05"
ORANGE = "#FE4311"
INK = "#3a2f2a"
MUTED = "#8a7f78"
BORDER = "#DBD0C2"
WARM = "#FFF3EF"
CARD = "#F8F4F1"
WHITE = "#FFFFFF"
RED = "#c0392b"


def _base(eid, etype, x, y, w, h, stroke, bg="transparent", sw=2, style="solid", roundness=None, roughness=1):
    return {
        "id": eid, "type": etype, "x": x, "y": y, "width": w, "height": h, "angle": 0,
        "strokeColor": stroke, "backgroundColor": bg, "fillStyle": "solid",
        "strokeWidth": sw, "strokeStyle": style, "roughness": roughness, "opacity": 100,
        "groupIds": [], "frameId": None, "roundness": roundness,
        "seed": random.randint(1, 2_000_000_000), "version": 1,
        "versionNonce": random.randint(1, 2_000_000_000),
        "isDeleted": False, "boundElements": None, "updated": 1, "link": None, "locked": False,
    }


def rect(eid, x, y, w, h, stroke=DARK, bg="transparent", sw=2, rounded=True):
    return _base(eid, "rectangle", x, y, w, h, stroke, bg, sw, roundness={"type": 3} if rounded else None)


def text(eid, x, y, s, size=15, color=INK, align="left"):
    lines = s.split("\n")
    width = max((len(line) for line in lines), default=1) * size * 0.60
    height = len(lines) * size * 1.25
    el = _base(eid, "text", x, y, width, height, color)
    el.update({
        "roundness": None, "text": s, "fontSize": size, "fontFamily": 1,
        "textAlign": align, "verticalAlign": "top", "containerId": None,
        "originalText": s, "lineHeight": 1.25, "baseline": int(size * 0.9),
    })
    return el


def line(eid, x, y, dx, dy, color=BORDER, sw=2, style="solid"):
    el = _base(eid, "line", x, y, abs(dx), abs(dy), color, sw=sw, style=style)
    el.update({"points": [[0, 0], [dx, dy]], "lastCommittedPoint": None,
               "startBinding": None, "endBinding": None,
               "startArrowhead": None, "endArrowhead": None})
    return el


def arrow(eid, x, y, dx, dy, color=ORANGE, sw=2):
    el = _base(eid, "arrow", x, y, abs(dx), abs(dy), color, sw=sw)
    el.update({"points": [[0, 0], [dx, dy]], "lastCommittedPoint": None,
               "startBinding": None, "endBinding": None,
               "startArrowhead": None, "endArrowhead": "arrow", "elbowed": False})
    return el


def write(name, elements):
    doc = {
        "type": "excalidraw", "version": 2, "source": "https://excalidraw.com",
        "elements": elements, "files": {},
        "appState": {"gridSize": None, "viewBackgroundColor": "#FFFFFF"},
    }
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2)
    print(f"wrote {name}  ({len(elements)} elements)")


# ── Diagram 10: Scribe / Denials story ───────────────────────────────────────
scribe_denials = [
    text("t-title", 40, 30, "Scribe and Denials - and the piece that is missing", 26, DARK),
    text("t-sub", 40, 74, "Two products. Both good. One gap between them.", 15, MUTED),

    rect("r-scribe", 40, 120, 420, 210, DARK, WHITE, 2),
    text("t-scribe-h", 66, 146, "Scribe", 22, DARK),
    text("t-scribe-sub", 66, 180, "for documentation", 14, ORANGE),
    line("l-scribe", 66, 202, 368, 0),
    text("t-scribe-b", 66, 224, "The medic talks. Scribe writes it down.\nOut comes the patient's chart -\nwhich becomes the claim sent to the insurer.", 15, INK),

    rect("r-denials", 540, 120, 420, 210, DARK, WHITE, 2),
    text("t-denials-h", 566, 146, "Denials", 22, DARK),
    text("t-denials-sub", 566, 180, "for handling rejected claims", 14, ORANGE),
    line("l-denials", 566, 202, 368, 0),
    text("t-denials-b", 566, 224, "The insurer says no. Denials writes the\nappeal, works the phones, and gets the\nclaim overturned.", 15, INK),

    line("l-gap", 460, 220, 80, 0, MUTED, 2, "dashed"),
    text("t-x", 494, 196, "x", 20, RED),

    rect("r-gapbox", 40, 358, 920, 100, ORANGE, WARM, 2),
    text("t-gap1", 66, 380, "Both are great on their own. But right now, they do not talk to each other.", 16, ORANGE),
    text("t-gap2", 66, 408, "So when Denials wins an appeal, that lesson stays inside that one claim. Nobody tells the next person.\nThe same mistake gets denied again - and it costs the same money, again.", 15, "#5b4a3a"),

    arrow("a-down", 500, 466, 0, 40),

    rect("r-built", 40, 512, 920, 280, ORANGE, WHITE, 2),
    text("t-built-h", 66, 538, "What we are building", 22, DARK),
    text("t-built-sub", 66, 572, "We take the resolved denials you already have, and turn them into something that prevents the next one.", 15, INK),

    rect("r-step1", 66, 598, 275, 130, BORDER, CARD, 2),
    text("t-step1", 84, 616, "1. Learn\n\nWe read every resolved denial\nand work out the real reason\nit was denied.", 14, INK),
    rect("r-step2", 362, 598, 275, 130, BORDER, CARD, 2),
    text("t-step2", 380, 616, "2. Remember\n\nWe save each one as a simple\nprevention rule - so the system\ngets smarter with every denial.", 14, INK),
    rect("r-step3", 658, 598, 275, 130, BORDER, CARD, 2),
    text("t-step3", 676, 616, "3. Prevent\n\nBefore a new claim is sent, we\ncheck it against those rules and\npoint out exactly what is missing.", 14, INK),

    arrow("a-s1", 344, 663, 16, 0),
    arrow("a-s2", 640, 663, 16, 0),

    text("t-close1", 66, 748, "The point: every denial you resolve makes the next claim stronger.", 16, DARK),
    text("t-close2", 66, 774, "Denials feeds Scribe. Scribe prevents denials.", 14, MUTED),
]

# ── Diagram 09: Ambra in one slide ───────────────────────────────────────────
one_slide = [
    text("t-title", 40, 30, "Ambra - in one slide", 26, DARK),
    text("t-sub", 40, 70, "Say these five lines, top to bottom.", 14, MUTED),

    rect("r-banner", 40, 100, 920, 70, DARK, DARK, 2),
    text("t-banner", 64, 118, "Ambra911  -  AI billing for US ambulance (EMS) companies.\nTwo products today. They solve two different halves of the same problem.", 15, WHITE),

    rect("r-scribe", 40, 200, 440, 160, BORDER, WHITE, 2),
    text("t-scribe-h", 64, 216, "SCRIBE  -  the charting side", 16, DARK),
    text("t-scribe-b", 64, 250, "Turns the medic's voice into a patient chart,\nthen into a billing-ready claim.\n\n\"Scribe writes the claim.\"", 14, INK),

    rect("r-denials", 520, 200, 440, 160, BORDER, WHITE, 2),
    text("t-denials-h", 544, 216, "DENIALS  -  the fighting side", 16, DARK),
    text("t-denials-b", 544, 250, "When an insurer rejects a claim, it writes the\nappeal and gets it overturned.\n\n\"Denials wins the money back.\"", 14, INK),

    line("l-gap", 480, 280, 40, 0, ORANGE, 3, "dashed"),
    text("t-x", 492, 254, "x", 20, RED),

    rect("r-gapbox", 40, 380, 920, 80, ORANGE, WARM, 2),
    text("t-gap1", 64, 400, "THE GAP: they do not talk to each other.", 16, ORANGE),
    text("t-gap2", 64, 428, "A won appeal teaches nothing to the next chart - so the same mistake is denied again and again.", 14, "#5b4a3a"),

    rect("r-built", 40, 480, 920, 210, DARK, WHITE, 2),
    text("t-built-h", 64, 502, "WHAT WE BUILT: the bridge between them", 16, DARK),
    rect("r-b1", 64, 530, 280, 100, BORDER, CARD, 2),
    text("t-b1", 82, 548, "1. Learn\n\nRead every resolved denial,\nfind why it was denied.", 14, INK),
    rect("r-b2", 364, 530, 280, 100, BORDER, CARD, 2),
    text("t-b2", 382, 548, "2. Remember\n\nTurn it into a prevention\nrule stored in memory.", 14, INK),
    rect("r-b3", 664, 530, 280, 100, BORDER, CARD, 2),
    text("t-b3", 682, 548, "3. Prevent\n\nScore the next claim and catch\nthe gap before sending.", 14, INK),
    arrow("a-b1", 344, 580, 20, 0),
    arrow("a-b2", 644, 580, 20, 0),
    text("t-close", 64, 654, "Denials feeds Scribe. Scribe prevents denials. That is the loop.", 16, DARK),
]

write("10-scribe-denials-story.excalidraw", scribe_denials)
write("09-ambra-in-one-slide.excalidraw", one_slide)
