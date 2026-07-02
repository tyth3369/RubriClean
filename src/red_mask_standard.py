"""
RubriClean Standard — 标准版
R-G>15 & R-B>15 检测 + Light-gated 晕影吸收 + 白色填充
适合绝大多数场景，几乎不误伤印刷字体
"""
import cv2
import numpy as np

CONFIG_STANDARD = {
    "min_diff": 15,              # R 必须同时大于 G 和 B 的最小差值
    "blue_h_low": 100,           # 蓝色 HSV 范围 (用于蓝笔清除)
    "blue_s_low": 70,
    "blue_v_low": 50,
    "blue_h_high": 130,
    "blue_s_high": 255,
    "blue_v_high": 255,
    # Light-gated 晕影吸收 — 清除红笔周围的浅色扫描过渡带
    "fringe_dilate_px": 13,       # 膨胀半径 (px)
    "fringe_light_thresh": 200,   # min(R,G,B) > 此值才吸收，保护黑笔笔画
}


def detect_red_standard(img, config=None):
    """标准版红笔检测：R-G>min_diff & R-B>min_diff"""
    cfg = config or CONFIG_STANDARD
    r = img[:, :, 2].astype(np.int16)
    g = img[:, :, 1].astype(np.int16)
    b = img[:, :, 0].astype(np.int16)
    diff = cfg["min_diff"]
    mask = (r - g > diff) & (r - b > diff)
    return mask.astype(np.uint8) * 255


def detect_blue_standard(img, config=None):
    """标准版蓝笔检测：HSV 蓝色范围"""
    cfg = config or CONFIG_STANDARD
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower = np.array([cfg["blue_h_low"], cfg["blue_s_low"], cfg["blue_v_low"]])
    upper = np.array([cfg["blue_h_high"], cfg["blue_s_high"], cfg["blue_v_high"]])
    return cv2.inRange(hsv, lower, upper)


def absorb_fringe(img, mask, config=None):
    """
    Light-gated 晕影吸收。

    红笔扫描后在笔画周围会产生一圈浅色过渡像素（RGB 228-250），
    这些像素不是红色（不满足 R-G>15），但靠近纯白填充后会形成可见的"边框"。
    通过对 mask 做膨胀，但只吸收浅色像素（min(R,G,B) > light_thresh），
    捕获晕影的同时保护暗色黑笔不被误吞。

    Args:
        img:   BGR 原图
        mask:  红笔二值掩码 (0/255)
        config: 配置字典

    Returns:
        扩展后的掩码
    """
    cfg = config or CONFIG_STANDARD
    dilate_px = cfg.get("fringe_dilate_px", 13)
    light_thresh = cfg.get("fringe_light_thresh", 200)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ksize = dilate_px * 2 + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))
    expanded = cv2.dilate(mask, kernel, iterations=1)

    # 只吸收浅色像素（晕影），跳过暗色（黑笔笔画）
    light = (gray > light_thresh).astype(np.uint8) * 255
    absorbed = cv2.bitwise_and(expanded, light)

    return cv2.bitwise_or(mask, absorbed)


def white_fill(img, mask):
    """白色填充修复"""
    white = np.ones_like(img) * 255
    return np.where(mask[:, :, np.newaxis] > 0, white, img)


def process(img, config=None):
    """
    一站式处理：检测红笔 → 吸收晕影 → 白色填充

    Args:
        img:    BGR 图片 (numpy array)
        config: 配置字典 (可选)

    Returns:
        cleaned: 清除红笔后的 BGR 图片
        mask:    最终使用的掩码
    """
    mask = detect_red_standard(img, config)
    mask = absorb_fringe(img, mask, config)
    cleaned = white_fill(img, mask)
    return cleaned, mask
