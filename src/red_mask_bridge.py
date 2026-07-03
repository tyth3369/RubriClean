"""
RubriClean Bridge — 激进版
专为纯亮红笔场景设计，不考虑偏黑红笔，最大化红黑交叉修复效果。

基于 Standard 的 R-G>15 & R-B>15 检测 + Light-gated 晕影吸收，
使用激进的通道均衡参数：更大的近墨区膨胀，不做噪点过滤。
"""
import cv2
import numpy as np

CONFIG_BRIDGE = {
    "min_diff": 15,              # R 必须同时大于 G 和 B 的最小差值
    # Light-gated 晕影吸收
    "fringe_dilate_px": 13,
    "fringe_light_thresh": 200,
    # 通道均衡 — 激进参数，最大化交叉修复
    "ink_gray_thresh": 80,        # gray < 此值判定为暗色墨水
    "ink_redness_max": 10,        # redness < 此值才是纯黑墨（非红笔）
    "ink_dilate_px": 7,           # 激进膨胀，覆盖更宽的红笔交叉区
    "ink_min_area": 0,            # 不做噪点过滤（无偏黑红笔场景不需要）
}


def detect_red_standard(img, config=None):
    """标准版红笔检测：R-G>min_diff & R-B>min_diff"""
    cfg = config or CONFIG_BRIDGE
    r = img[:, :, 2].astype(np.int16)
    g = img[:, :, 1].astype(np.int16)
    b = img[:, :, 0].astype(np.int16)
    diff = cfg["min_diff"]
    mask = (r - g > diff) & (r - b > diff)
    return mask.astype(np.uint8) * 255


def absorb_fringe(img, mask, config=None):
    """Light-gated 晕影吸收"""
    cfg = config or CONFIG_BRIDGE
    dilate_px = cfg.get("fringe_dilate_px", 13)
    light_thresh = cfg.get("fringe_light_thresh", 200)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ksize = dilate_px * 2 + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
    expanded = cv2.dilate(mask, kernel, iterations=1)

    light = (gray > light_thresh).astype(np.uint8) * 255
    absorbed = cv2.bitwise_and(expanded, light)

    return cv2.bitwise_or(mask, absorbed)


def channel_balance(img, mask, config=None):
    """
    上下文感知通道均衡（激进版）。

    无噪点过滤，更大膨胀半径，假设画面中不存在偏黑红笔。
    """
    cfg = config or CONFIG_BRIDGE
    ink_gray = cfg.get("ink_gray_thresh", 80)
    ink_redness = cfg.get("ink_redness_max", 10)
    ink_dilate = cfg.get("ink_dilate_px", 7)

    r = img[:, :, 2].astype(np.int16)
    g = img[:, :, 1].astype(np.int16)
    b = img[:, :, 0].astype(np.int16)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    max_gb = np.maximum(g, b)
    redness = r - max_gb

    # 检测黑笔笔画：暗色 + 非红
    ink_strokes = (gray < ink_gray) & (redness < ink_redness)

    # 不做微小噪点过滤（假设无偏黑红笔，不会产生笔锋暗斑误检）
    min_area = cfg.get("ink_min_area", 0)
    if min_area > 0:
        ink_u8 = ink_strokes.astype(np.uint8)
        n_labels, labels, stats, _ = cv2.connectedComponentsWithStats(ink_u8, connectivity=8)
        small_mask = np.zeros(n_labels, dtype=bool)
        for i in range(1, n_labels):
            if stats[i, cv2.CC_STAT_AREA] < min_area:
                small_mask[i] = True
        if small_mask.any():
            ink_strokes[small_mask[labels]] = False

    # 激进膨胀，覆盖更宽的红笔交叉区
    ksize = ink_dilate * 2 + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
    near_ink = cv2.dilate(ink_strokes.astype(np.uint8), kernel, iterations=1)

    result = img.copy()

    # mask 像素在近黑笔区域内 + 有红度 → 压 R 保留暗色
    on_ink = (mask > 0) & (near_ink > 0) & (redness > 0)

    # 其余 mask 像素 → 涂白
    on_paper = (mask > 0) & ~on_ink
    result[on_paper] = (255, 255, 255)

    # 仅对近黑笔区域像素压 R 通道
    if on_ink.any():
        r_channel = result[:, :, 2].copy()
        r_channel[on_ink] = np.clip(max_gb[on_ink], 0, 255).astype(np.uint8)
        result[:, :, 2] = r_channel

    return result


def process(img, config=None):
    """一站式处理：检测红笔 → 吸收晕影 → 通道均衡填充"""
    mask = detect_red_standard(img, config)
    mask = absorb_fringe(img, mask, config)
    cleaned = channel_balance(img, mask, config)
    return cleaned, mask
