# Maestro v2.0 — Per-Page Adaptive Routing

## What's New

Maestro replaces manual version selection with automatic per-page routing.

Given a scanned homework page, Maestro analyzes page characteristics and picks the best strategy:

- **Crossing-heavy pages** (dense handwriting, red marks overlapping black text) → **Bridge v1.2** — best text preservation via channel balance
- **Paper-red pages** (sparse text, red marks on clean paper) → **Deep** — best dark-red cleanup via white fill

## How It Works

Maestro extracts three signals from each page:

1. **Stroke continuation** — do black-ink strokes pass **through** red regions (genuine crossing), or just **touch** the edges (fringe artifact)?
2. **Ink coverage** — how much of the page is black text?
3. **Stroke ratio** — through / (through + touch) as a tiebreaker

The routing logic:
```
through < 40                     → Deep   (sparse crossings)
ink > 7% AND through < 100       → Deep   (dense text, red separate)
through > 100                    → Bridge v1.2 (genuine crossings)
otherwise, ratio > 55%           → Bridge v1.2
otherwise                        → Deep
```

## Results (5 representative samples)

| Sample | Type | Through | Route | Result |
|--------|------|---------|-------|--------|
| shengwu6 | biology, dense handwriting | 134 | Bridge v1.2 | Crossing repair = Bridge level |
| huaxue118 | chemistry, dense handwriting | 164 | Bridge v1.2 | Crossing repair = Bridge level |
| wuli80 | physics, red marks on paper | 23 | Deep | Dark-red = Deep level |
| wuli92 | physics, red near text | 91 | Deep | Dark-red = Deep level |
| wuli100 | physics, red near text | 94 | Deep | Dark-red = Deep level |

No single version handles all cases. Maestro routes each page to the right one.

## Usage

```python
import cv2
from src.maestro import process

img = cv2.imread("homework.jpg")
cleaned, mask, info = process(img)
cv2.imwrite("clean.jpg", cleaned)

print(f"Routed to: {info['version']}")
```

## New Files

- `src/maestro.py` — per-page auto-router
- `src/router.py` — feature extraction + routing logic
- `README.md` — rewritten (English)
- `README_CN.md` — Chinese reference

## Upgraded Files

- `src/red_mask_bridge_v2.py` — component-level composition (from v1.2)
