"""
RubriClean Bridge v1.2 — 组件级拼接：Deep 检测 + Bridge 填充

核心思路：
- Deep 提供最完整的红笔检测覆盖（特别是暗红/深红笔迹）
- Bridge 提供最佳的红黑交叉修复（通道均衡保留黑色笔画）
- 在连通域级别区分"纸上红笔"和"红黑交叉"，分别用 Deep 和 Bridge 处理

比 Bridge v1.1 的改进：
- 暗红/深红笔迹清除能力显著提升（借助 Deep 的激进检测 + 形态学 + 笔画膨胀）
- 红黑交叉修复保持 Bridge 水平（交叉组件使用 Bridge 原始输出）
- 无新增参数，无中间分类逻辑

依赖：red_mask_deep.py, red_mask_bridge.py
"""
import cv2
import numpy as np
from red_mask_deep import process as deep_process
from red_mask_bridge import process as bridge_process


def process(img):
    """
    一站式处理。

    Args:
        img: BGR 图像 (numpy array)

    Returns:
        cleaned: 清除红笔后的 BGR 图像
        mask:    使用的红笔掩码 (Deep 原始掩码)
        info:    调试信息字典
    """
    # ================================================================
    # Step 1: Deep 检测 → 最佳红笔覆盖
    # ================================================================
    r_d = deep_process(img)
    if isinstance(r_d, tuple):
        cleaned_d, mask_d = r_d[0], r_d[1]
    else:
        cleaned_d, mask_d = r_d, None

    # ================================================================
    # Step 2: Bridge 基线 → 最佳交叉修复
    # ================================================================
    cleaned_b, mask_b = bridge_process(img)

    # ================================================================
    # Step 3: 黑墨检测
    # ================================================================
    r = img[:, :, 2].astype(np.int16)
    g = img[:, :, 1].astype(np.int16)
    b = img[:, :, 0].astype(np.int16)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    max_gb = np.maximum(g, b)
    redness = r - max_gb
    ink = (gray < 80) & (redness < 10)

    # ================================================================
    # Step 4: 连通域级交叉判定
    # ================================================================
    n_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        mask_d, connectivity=8)
    crossing_mask = np.zeros(img.shape[:2], dtype=bool)

    for cid in range(1, n_labels):
        comp = (labels == cid)
        if comp.sum() < 10:
            continue
        ink_px = (comp & ink).sum()
        if ink_px >= 20:
            crossing_mask |= comp

    # ================================================================
    # Step 5: 拼接 — Deep 基线 + Bridge 覆盖交叉区
    # ================================================================
    result = cleaned_d.copy()
    result[crossing_mask] = cleaned_b[crossing_mask]

    # ================================================================
    # 调试信息
    # ================================================================
    info = {
        "deep_mask_px": int(cv2.countNonZero(mask_d)),
        "bridge_mask_px": int(cv2.countNonZero(mask_b)),
        "crossing_px": int(crossing_mask.sum()),
    }

    return result, mask_d, info
