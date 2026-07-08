"""
RubriClean Maestro v2.0 — Per-Page Adaptive Routing

Maestro analyzes each page and automatically selects the optimal strategy:
- Crossing-heavy pages → Bridge v1.2 (best text preservation)
- Paper-red pages    → Deep         (best dark-red cleanup)

Three signals drive the routing:
  1. Stroke continuation — do ink strokes pass THROUGH red regions?
  2. Ink coverage        — how much of the page is black text?
  3. Stroke ratio        — through / (through + touch) for edge cases

No unified algorithm. No parameter tuning. Just smart per-page routing.
"""
import cv2
import numpy as np
from red_mask_deep import process as deep_process
from red_mask_bridge_v2 import process as bridge_v2_process
from red_mask_bridge import process as bridge_process


def _extract_features(img):
    """
    Extract page-level features for routing decision.

    Returns dict with:
        stroke_through_ratio: 穿过型笔迹 / (穿过 + 触碰)
        bridge_on_ink_density: Bridge on_ink px / Bridge mask px
        ink_coverage: ink_base px / total image px
    """
    h, w = img.shape[:2]
    total_px = h * w
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    r = img[:, :, 2].astype(np.int16)
    g = img[:, :, 1].astype(np.int16)
    b = img[:, :, 0].astype(np.int16)
    max_gb = np.maximum(g, b)
    redness = r - max_gb

    # --- Ink detection ---
    ink = (gray < 80) & (redness < 10)
    ink_coverage = ink.sum() / total_px

    # --- Bridge on_ink density ---
    cleaned_b, mask_b = bridge_process(img)
    bridge_on_ink = (mask_b > 0) & (cleaned_b[:, :, 2] < 250)
    bridge_mask_px = cv2.countNonZero(mask_b)
    bridge_on_ink_density = bridge_on_ink.sum() / max(bridge_mask_px, 1)

    # --- Deep mask for stroke analysis ---
    r_d = deep_process(img)
    mask_d = r_d[0] if isinstance(r_d, (list, tuple)) else None
    if isinstance(r_d, tuple):
        mask_d = r_d[1] if len(r_d) >= 2 else None
        cleaned_d = r_d[0]
    else:
        mask_d = None

    if mask_d is None:
        return {
            "stroke_through_ratio": 0,
            "bridge_on_ink_density": bridge_on_ink_density,
            "ink_coverage": ink_coverage,
        }

    # --- Stroke continuation analysis ---
    ink_n, ink_labels, ink_stats, _ = cv2.connectedComponentsWithStats(
        ink.astype(np.uint8), 8)
    d_n, d_labels, d_stats, _ = cv2.connectedComponentsWithStats(mask_d, 8)

    through = 0
    touch = 0

    for cid in range(1, d_n):
        comp = (d_labels == cid)
        comp_sz = d_stats[cid, cv2.CC_STAT_AREA]
        if comp_sz < 100:
            continue

        touching_ink = np.unique(ink_labels[comp & ink])
        touching_ink = touching_ink[touching_ink > 0]

        for ilid in touching_ink:
            ink_total = ink_stats[ilid, cv2.CC_STAT_AREA]
            if ink_total < 5:
                continue
            ink_inside = (comp & (ink_labels == ilid)).sum()
            ink_outside = ink_total - ink_inside
            if ink_outside / ink_total > 0.30:
                through += 1
            else:
                touch += 1

    total_strokes = through + touch
    stroke_through_ratio = through / max(total_strokes, 1)

    return {
        "stroke_through_ratio": stroke_through_ratio,
        "bridge_on_ink_density": bridge_on_ink_density,
        "ink_coverage": ink_coverage,
        "through_strokes": through,
        "touch_strokes": touch,
    }


def route(img):
    """
    Analyze page and return the recommended processing version.

    Returns:
        "deep"       → Use pure Deep (best dark-red cleanup)
        "bridge_v2"  → Use Bridge v1.2 (best crossing repair with Deep coverage)

    Decision logic uses three signals:
        through      — absolute count of ink strokes passing THROUGH red components
        ink_coverage — ink_base pixels / total image pixels (text density)
        ratio        — through / (through + touch) for edge cases
    """
    f = _extract_features(img)
    through = f.get("through_strokes", 0)
    ink_cov = f["ink_coverage"]

    # Sparse crossings → paper-red → Deep
    if through < 40:
        return "deep"

    # Dense text + moderate crossings → likely fringe, not real crossing → Deep
    if ink_cov > 0.07 and through < 100:
        return "deep"

    # Many genuine crossings → Bridge v1.2
    if through > 100:
        return "bridge_v2"

    # Edge cases: use ratio as tiebreaker
    if f["stroke_through_ratio"] > 0.55:
        return "bridge_v2"
    else:
        return "deep"


def process(img):
    """
    Auto-route and process. Returns same format as other process() functions.

    Returns:
        cleaned: BGR image
        mask:    red pen mask
        info:    dict with routing decision + features
    """
    f = _extract_features(img)
    version = route(img)

    if version == "deep":
        r = deep_process(img)
        cleaned = r[0] if isinstance(r, tuple) else r
        mask = r[1] if isinstance(r, tuple) and len(r) >= 2 else None
    else:
        cleaned, mask, info_v2 = bridge_v2_process(img)

    info = {
        "version": version,
        "features": f,
    }
    return cleaned, mask, info
