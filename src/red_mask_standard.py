"""
RubriClean Standard — 标准版
R-G>15 & R-B>15 检测 + Light-gated 晕影吸收 + 白色填充
适合绝大多数场景，几乎不误伤印刷字体
"""
import cv2
import numpy as np

CONFIG_STANDARD = {
    "min_diff": 20,              # R 必须同时大于 G 和 B 的最小差值
    # Light-gated 晕影吸收 — 清除红笔周围的浅色扫描过渡带
    "fringe_dilate_px": 13,       # 膨胀半径 (px)
    "fringe_light_thresh": 200,   # min(R,G,B) > 此值才吸收，保护黑笔笔画
    # 通道均衡 — 上下文感知，红黑交叉处保留暗色笔画
    "ink_gray_thresh": 80,        # gray < 此值判定为暗色墨水
    "ink_redness_max": 10,        # redness < 此值才是纯黑墨（非红笔）
    "ink_dilate_px": 3,           # 将黑墨区域膨胀 N px，覆盖红笔叠加区
    "ink_min_area": 15,           # 连通域 < 此面积视为噪点剔除（红笔笔锋暗边）
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


def channel_balance(img, mask, config=None):
    """
    上下文感知通道均衡：替代纯白填充，处理红黑交叉场景。

    不逐像素判断"红在纸上 vs 红在黑上"（分布高度重叠），而是：
    1. 先找出画面中所有黑笔笔画（暗色 + 非红）
    2. 将黑笔区域膨胀 N px，形成"近黑笔区域"
    3. mask 像素在近黑笔区域内 → 压 R，保留暗色
    4. mask 像素在近黑笔区域外 → 涂白

    Args:
        img:    BGR 原图
        mask:   红笔掩码 (0/255)
        config: 配置字典

    Returns:
        BGR 图片
    """
    cfg = config or CONFIG_STANDARD
    ink_gray = cfg.get("ink_gray_thresh", 80)
    ink_redness = cfg.get("ink_redness_max", 10)
    ink_dilate = cfg.get("ink_dilate_px", 3)

    r = img[:, :, 2].astype(np.int16)
    g = img[:, :, 1].astype(np.int16)
    b = img[:, :, 0].astype(np.int16)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    max_gb = np.maximum(g, b)
    redness = r - max_gb

    # 检测黑笔笔画：暗色 + 非红
    ink_strokes = (gray < ink_gray) & (redness < ink_redness)

    # 剔除微小孤立噪点（红笔笔锋暗边会被误检为黑墨，但其连通域很小）
    min_area = cfg.get("ink_min_area", 5)
    if min_area > 0:
        ink_u8 = ink_strokes.astype(np.uint8)
        n_labels, labels, stats, _ = cv2.connectedComponentsWithStats(ink_u8, connectivity=8)
        small_mask = np.zeros(n_labels, dtype=bool)
        for i in range(1, n_labels):
            if stats[i, cv2.CC_STAT_AREA] < min_area:
                small_mask[i] = True
        if small_mask.any():
            ink_strokes[small_mask[labels]] = False

    # 膨胀黑笔区域，覆盖红笔叠加在黑笔上的宽度
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
    """
    一站式处理：检测红笔 → 吸收晕影 → 通道均衡填充

    Args:
        img:    BGR 图片 (numpy array)
        config: 配置字典 (可选)

    Returns:
        cleaned: 清除红笔后的 BGR 图片
        mask:    最终使用的掩码
    """
    mask = detect_red_standard(img, config)
    mask = absorb_fringe(img, mask, config)
    cleaned = channel_balance(img, mask, config)
    return cleaned, mask
