# RubriClean

Automated red-pen removal from scanned homework assignments. Detects and erases teacher grading marks and student correction while preserving the student's original answers.

Built entirely with Claude Code.

---

## Versions

| Version | File | Use Case |
|---------|------|----------|
| **Maestro** | `src/maestro.py` | ✅ **Auto — start here** |
| Standard v1.1 | `src/red_mask_standard.py` | General-purpose, safe baseline |
| Bridge v1.2 | `src/red_mask_bridge_v2.py` | Crossing-heavy pages |
| Bridge v1.1 | `src/red_mask_bridge.py` | Pure bright-red pen |
| Deep | `src/red_mask_deep.py` | Dark-red / faded pen |

### Maestro — Per-page auto-routing

Maestro analyzes each page and automatically picks the best strategy:
- **Crossing-heavy** (dense handwriting, red over black ink) → Bridge v1.2 — best text preservation
- **Paper-red** (sparse text, red marks on paper) → Deep — best dark-red cleanup

Decision is driven by stroke-continuation analysis: do black-ink strokes pass **through** red regions (real crossing) or just **touch** the edges (fringe artifact)?

No parameters. No manual version selection. Just drop in and go.

### Standard v1.1 — Safe general-purpose

`R-G>15 & R-B>15` detection → fringe absorption → channel balance fill.

Balances dark-red cleanup with crossing repair. Works for most scenarios.

### Bridge v1.2 — Component-level composition

Deep's full detection pipeline + Bridge's channel balance fill.
Crossing components use Bridge output; paper components use Deep white-fill.

Best for pages with frequent red-black crossings but also dark-red marks.

### Bridge v1.1 — Crossing specialist

`R-G>20 & R-B>20` detection → aggressive channel balance (dil=7).

Designed for **bright-red pen crossing black text**. Conservative detection means dark-red marks may be missed.

### Deep — Dark-red specialist

Multi-layer detection (HSV + RGB diff + local contrast) → morphology → stroke expansion → white fill.

Catches very dark / faded red ink that other versions miss. White fill means black text at crossings is destroyed — use only on pages with no red-black overlap.

---

## Core Algorithm

### Channel Balance Fill

When red marks overlap black text, simple white fill cuts through the text. Channel balance handles crossings:

1. **Detect black ink**: dark pixels (`gray < 80`) with no red tint (`redness < 10`)
2. **Dilate near-ink zone**: expand black ink region to cover the red stroke width
3. **Clamp R channel**: for red pixels near ink, clamp R to `max(G,B)` — suppresses red while preserving the dark text underneath
4. **White fill elsewhere**: red pixels on clean paper become white

### Light-gated Fringe Absorption

Scanned red pen marks have a pale halo (RGB 228–250) around the stroke. These pixels don't satisfy red-detection thresholds but would form visible borders after white fill. The mask is dilated 13px, but only light pixels (gray > 200) are absorbed — capturing the halo while protecting dark text.

---

## Quick Start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

```python
import cv2
from src.maestro import process

img = cv2.imread("homework.jpg")
cleaned, mask, info = process(img)
cv2.imwrite("clean.jpg", cleaned)

print(f"Routed to: {info['version']}")
```

---

## Project Structure

```
RubriClean/
├── src/
│   ├── maestro.py              # v2.0 — Auto-routing
│   ├── red_mask_bridge_v2.py   # v1.2 — Component composition
│   ├── red_mask_bridge.py      # v1.1 — Crossing specialist
│   ├── red_mask_standard.py    # v1.0 — General purpose
│   ├── red_mask_deep.py        # v1.0 — Dark-red specialist
│   ├── router.py               # Router module (used by maestro)
│   ├── config.json             # Shared parameters
│   ├── visualize.py            # Debug visualization
│   ├── pipeline.py             # Single-image CLI
│   └── batch_processor.py      # PDF batch processing
├── docs/
└── README.md
```

## Dependencies

- Python 3.9+
- OpenCV (`opencv-python`)
- NumPy
- Pillow
- PyMuPDF (for PDF processing)

## License

MIT
