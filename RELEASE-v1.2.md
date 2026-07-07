# Bridge v1.2 — Component-Level Composition

## Key Improvement

Bridge v1.1 excels at **red-black crossing repair** via channel balance, but its conservative detection threshold (R-G>20) leaves many dark-red pen marks uncleaned.

v1.2 introduces a **component-level composition** architecture:
- **Detection**: Uses Deep's full pipeline (3-layer detection + morphology + stroke expansion) for maximum red pen coverage
- **Fill**: Classifies each connected component as either "paper red" or "crossing"
  - Crossing components (≥20px black ink overlap) → Bridge output (channel balance preserves text)
  - Paper components → Deep white-fill (best dark-red cleanup)

## Improvements over Bridge v1.1

- Significantly better dark-red / near-black red pen removal (via Deep's detection coverage)
- Red-black crossing repair matches Bridge v1.1
- No new parameters; only one new file `red_mask_bridge_v2.py` (~70 lines)

## Known Limitations

- On text-dense handwritten homework pages, some paper-only red areas may be misclassified as crossings → dark-red cleanup slightly below pure Deep
- No per-page adaptive routing (planned for next release)

## Usage

```python
import cv2
from red_mask_bridge_v2 import process

img = cv2.imread("homework.jpg")
cleaned, mask, info = process(img)
cv2.imwrite("cleaned.jpg", cleaned)
```

## Dependencies

- Python 3.9+
- opencv-python, numpy
- `red_mask_deep.py`, `red_mask_bridge.py`, `config.json` (included)
