"""
RubriClean v3.1 — 红笔痕迹检测
HSV + RGB + 局部红度 + 笔画膨胀 (diff=15)
适用场景: 扫描质量差、红笔偏黑偏暗
"""

import cv2
import numpy as np
import json
import os


def load_config(json_path=None):
    """
    从 JSON 文件加载配置，返回兼容现有代码的字典。
    如文件不存在或未指定，返回内联 CONFIG 作为回退。
    """
    if json_path is None:
        json_path = os.path.join(os.path.dirname(__file__), "config.json")

    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            j = json.load(f)

        inpaint_method_map = {
            "telea": cv2.INPAINT_TELEA,
            "ns": cv2.INPAINT_NS,
        }

        return {
            "hsv_red1_lower": tuple(j["hsv"]["red1_lower"]),
            "hsv_red1_upper": tuple(j["hsv"]["red1_upper"]),
            "hsv_red2_lower": tuple(j["hsv"]["red2_lower"]),
            "hsv_red2_upper": tuple(j["hsv"]["red2_upper"]),
            "rgb_diff_threshold": j["rgb_diff"]["threshold"],
            "rgb_r_min": j["rgb_diff"]["r_min"],
            "local_r_advantage": j["local_contrast"]["r_advantage"],
            "local_r_min": j["local_contrast"]["r_min"],
            "local_proximity": j["local_contrast"]["proximity"],
            "morph_close_kernel": j["morphology"]["close_kernel"],
            "morph_open_kernel": j["morphology"]["open_kernel"],
            "gap_close_kernel": j["morphology"]["gap_close_kernel"],
            "stroke_dilate_iter": j["stroke_expand"]["dilate_iter"],
            "stroke_dilate_kernel": j["stroke_expand"]["dilate_kernel"],
            "safety_gray_tolerance": j["safety"]["gray_tolerance"],
            "inpaint_radius": j["inpainting"]["radius"],
            "inpaint_method": inpaint_method_map.get(
                j["inpainting"]["method"], cv2.INPAINT_TELEA),
            "border_width": j["border_removal"]["border_width"],
            "darkness_threshold": j["border_removal"]["darkness_threshold"],
            # 保留 JSON 原始信息
            "output_suffix": j["output"]["suffix"],
            "output_format": j["output"]["format"],
            "output_quality": j["output"]["quality"],
            "skip_if_no_red": j["output"]["skip_if_no_red"],
        }

    # 回退：内联 CONFIG
    return CONFIG


# ============================================================
# 可调参数（集中管理，方便调优）
# ============================================================
CONFIG = {
    # --- HSV 红色检测 ---
    # 红色在 Hue 环两端，OpenCV H 范围 0-180
    "hsv_red1_lower": (0, 50, 50),
    "hsv_red1_upper": (10, 255, 255),
    "hsv_red2_lower": (170, 50, 50),
    "hsv_red2_upper": (180, 255, 255),

    # --- RGB 差值检测（偏黑红笔）---
    "rgb_diff_threshold": 15,  # v3.1: 8→15, 与Senior对齐, 减少印刷字误检
    "rgb_r_min": 50,           # R 通道最小值，排除纯黑像素

    # --- 局部相对红度检测 ---
    "local_r_advantage": 5,    # R 相对于 G/B 的最小优势值
    "local_r_min": 30,         # 局部检测的最低 R 下限
    "local_proximity": 5,      # 必须靠近已知红色像素的半径

    # --- 笔画膨胀 ---
    "stroke_dilate_iter": 3,
    "stroke_dilate_kernel": 5,
    # 自适应双通道膨胀 (改进C)
    "use_dual_dilate": False,       # 启用双通道膨胀
    "dual_dilate_fine_kernel": 3,   # 细笔画核
    "dual_dilate_fine_iter": 1,     # 细笔画迭代
    "dual_dilate_coarse_kernel": 7, # 粗笔画核
    "dual_dilate_coarse_iter": 2,   # 粗笔画迭代

    # --- 间隙填充 ---
    "gap_close_kernel": 7,     # 最终闭运算核大小

    # --- CLAHE 预处理 (改进A) ---
    "use_clahe": False,
    "clahe_clip": 2.0,
    "clahe_tile": [8, 8],

    # --- 连通域去噪 (改进B) ---
    "use_component_filter": False,  # 是否启用连通域过滤
    "component_min_area": 10,       # 最小连通域面积（小于此值视为噪声）

    # --- 安全阈值 ---
    "safety_gray_tolerance": 5,  # R/G/B 差异小于此值视为纯灰度，绝不删除

    # --- 形态学 ---
    "morph_close_kernel": 5,   # 闭运算核大小
    "morph_open_kernel": 3,    # 开运算核大小

    # --- Inpainting ---
    "inpaint_radius": 5,       # 修复半径
    "inpaint_method": cv2.INPAINT_TELEA,  # Telea 算法
}


def preprocess_clahe(image, config=None):
    """
    CLAHE 自适应对比度增强 — 改进 A。
    在 LAB 色彩空间对亮度通道做局部直方图均衡化，
    让不同扫描亮度的页面统一到相似水平。
    """
    cfg = config or CONFIG
    if not cfg.get("use_clahe", False):
        return image
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(
        clipLimit=cfg.get("clahe_clip", 2.0),
        tileGridSize=tuple(cfg.get("clahe_tile", [8, 8])))
    l = clahe.apply(l)
    lab = cv2.merge([l, a, b])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def detect_red_hsv(image, config=None):
    """
    基于 HSV 色彩空间检测标准红色笔迹。
    """
    cfg = config or CONFIG
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    lower1 = np.array(cfg["hsv_red1_lower"])
    upper1 = np.array(cfg["hsv_red1_upper"])
    lower2 = np.array(cfg["hsv_red2_lower"])
    upper2 = np.array(cfg["hsv_red2_upper"])

    mask1 = cv2.inRange(hsv, lower1, upper1)
    mask2 = cv2.inRange(hsv, lower2, upper2)

    return cv2.bitwise_or(mask1, mask2)


def detect_red_rgb_diff(image, config=None):
    """
    基于 RGB 通道差值检测偏黑/偏暗的红色笔迹。

    原理：红色墨水在 R 通道很强，G/B 通道很弱。
    即使扫描变暗，R 通道仍明显高于 G/B。
    """
    cfg = config or CONFIG

    r = image[:, :, 2].astype(np.int16)
    g = image[:, :, 1].astype(np.int16)
    b = image[:, :, 0].astype(np.int16)

    diff = r - np.maximum(g, b)
    mask = (diff > cfg["rgb_diff_threshold"]) & (r > cfg["rgb_r_min"])

    return mask.astype(np.uint8) * 255


def _is_grayscale_pixel(r, g, b, tolerance=5):
    """
    安全检查：判断像素是否为纯灰度（R≈G≈B）。
    纯灰度像素（黑/白/灰印刷文字）绝不应被标记为红笔。
    """
    return (abs(int(r) - int(g)) <= tolerance and
            abs(int(g) - int(b)) <= tolerance and
            abs(int(r) - int(b)) <= tolerance)


def detect_red_local_contrast(image, seed_mask, config=None):
    """
    局部相对红度检测：找出种子掩码附近、R 通道相对占优的暗像素。

    原理：偏黑红笔的 RGB 绝对值都低（暗），但在局部比较时，
    R 通道仍略微高于 G 和 B。而真正的印刷黑字 R≈G≈B。

    安全机制：
    1. 仅在与 seed_mask 接近的区域内搜索
    2. 绝对排除 R≈G≈B 的纯灰度像素
    3. R 必须同时大于 G 且大于 B
    """
    cfg = config or CONFIG

    r = image[:, :, 2].astype(np.int16)
    g = image[:, :, 1].astype(np.int16)
    b = image[:, :, 0].astype(np.int16)

    # 条件 1: R 同时大于 G 和 B（相对优势）
    r_dominant = (r > g + cfg["local_r_advantage"]) & (r > b + cfg["local_r_advantage"])

    # 条件 2: R 不能太低（排除噪声）
    r_enough = r > cfg["local_r_min"]

    # 条件 3: 排除纯灰度像素
    gray_tol = cfg["safety_gray_tolerance"]
    not_gray = ~((abs(r - g) <= gray_tol) &
                 (abs(g - b) <= gray_tol) &
                 (abs(r - b) <= gray_tol))

    candidate = (r_dominant & r_enough & not_gray).astype(np.uint8) * 255

    # 条件 4: 必须靠近已知红色像素（空间邻近性）
    proximity = cfg["local_proximity"]
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (proximity * 2 + 1, proximity * 2 + 1))
    seed_dilated = cv2.dilate(seed_mask, kernel, iterations=1)

    return cv2.bitwise_and(candidate, seed_dilated)


def expand_along_strokes(mask, image, config=None):
    """
    沿笔画方向膨胀掩码（改进C：双通道模式）。
    默认：单通道固定核膨胀。
    双通道模式：细笔画用小核保守膨胀 + 粗笔画用大核激进膨胀 → 取并集。

    安全机制：只扩展到"偏暗"的像素（笔画区域），不扩展到亮背景。
    """
    cfg = config or CONFIG
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    dark_pixels = (gray < 180).astype(np.uint8) * 255

    # 排除纯灰度像素（黑字保护）
    r = image[:, :, 2].astype(np.int16)
    g = image[:, :, 1].astype(np.int16)
    b = image[:, :, 0].astype(np.int16)
    gray_tol = cfg["safety_gray_tolerance"]
    is_gray = ((abs(r - g) <= gray_tol) &
               (abs(g - b) <= gray_tol) &
               (abs(r - b) <= gray_tol))
    not_gray = (~is_gray).astype(np.uint8) * 255

    if cfg.get("use_dual_dilate", False):
        # 细笔画通道：小核保守
        k_fine = cfg["dual_dilate_fine_kernel"]
        kernel_fine = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_fine, k_fine))
        fine = cv2.dilate(mask, kernel_fine, iterations=cfg["dual_dilate_fine_iter"])

        # 粗笔画通道：大核激进
        k_coarse = cfg["dual_dilate_coarse_kernel"]
        kernel_coarse = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_coarse, k_coarse))
        coarse = cv2.dilate(mask, kernel_coarse, iterations=cfg["dual_dilate_coarse_iter"])

        # 合并两通道
        expanded = cv2.bitwise_or(fine, coarse)
    else:
        k_size = cfg["stroke_dilate_kernel"]
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_size, k_size))
        expanded = cv2.dilate(mask, kernel, iterations=cfg["stroke_dilate_iter"])

    # 安全约束
    expanded = cv2.bitwise_and(expanded, dark_pixels)
    expanded = cv2.bitwise_and(expanded, not_gray)

    new_only = cv2.bitwise_and(expanded, cv2.bitwise_not(mask))
    return cv2.bitwise_or(mask, new_only), new_only


def remove_black_border(image, border_width=20, darkness_threshold=40):
    """
    检测并排除扫描件四周的黑边区域。
    """
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    border_mask = np.zeros((h, w), dtype=np.uint8)

    border_mask[:border_width, :] = 255
    border_mask[h - border_width:, :] = 255
    border_mask[:, :border_width] = 255
    border_mask[:, w - border_width:] = 255

    border_mask = cv2.bitwise_and(border_mask, cv2.threshold(
        gray, darkness_threshold, 255, cv2.THRESH_BINARY_INV)[1])

    return border_mask


def merge_masks(mask_hsv, mask_rgb, mask_local=None, border_mask=None, config=None):
    """
    融合 HSV、RGB 差值和局部红度掩码，排除黑边。
    """
    cfg = config or CONFIG

    merged = cv2.bitwise_or(mask_hsv, mask_rgb)
    if mask_local is not None:
        merged = cv2.bitwise_or(merged, mask_local)

    if border_mask is not None:
        merged = cv2.bitwise_and(merged, cv2.bitwise_not(border_mask))

    # 闭运算：连接断裂笔画
    kernel_close = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (cfg["morph_close_kernel"], cfg["morph_close_kernel"]))
    merged = cv2.morphologyEx(merged, cv2.MORPH_CLOSE, kernel_close)

    # 开运算：去除孤立噪声
    kernel_open = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (cfg["morph_open_kernel"], cfg["morph_open_kernel"]))
    merged = cv2.morphologyEx(merged, cv2.MORPH_OPEN, kernel_open)

    # 间隙填充：大核闭运算
    gap_kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (cfg["gap_close_kernel"], cfg["gap_close_kernel"]))
    merged = cv2.morphologyEx(merged, cv2.MORPH_CLOSE, gap_kernel)

    # 连通域去噪（改进B）：去除微小孤立碎片
    if cfg.get("use_component_filter", False):
        min_area = cfg.get("component_min_area", 10)
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
            merged, connectivity=8)
        clean = np.zeros_like(merged)
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] >= min_area:
                clean[labels == i] = 255
        merged = clean

    return merged


def cleanup_residuals(image, first_mask, first_cleaned, config=None):
    """
    二次清理：检测第一次 Inpaint 后掩码边缘的残留暗像素，
    生成补充掩码，用于第二次 Inpaint。
    """
    cfg = config or CONFIG
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    edge_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask_dilated = cv2.dilate(first_mask, edge_kernel, iterations=3)
    search_ring = cv2.bitwise_and(mask_dilated, cv2.bitwise_not(first_mask))

    r = image[:, :, 2].astype(np.int16)
    g = image[:, :, 1].astype(np.int16)
    b = image[:, :, 0].astype(np.int16)
    gray_tol = cfg["safety_gray_tolerance"]
    not_pure_gray = ~((abs(r - g) <= gray_tol) &
                      (abs(g - b) <= gray_tol) &
                      (abs(r - b) <= gray_tol))
    is_dark = gray < 180

    residual = cv2.bitwise_and(search_ring, (is_dark & not_pure_gray).astype(np.uint8) * 255)

    cleaned_final = cv2.inpaint(
        first_cleaned, residual, cfg["inpaint_radius"], cfg["inpaint_method"])

    return cleaned_final, residual


def detect_red_pen(image, config=None):
    """
    一站式红笔检测：
        HSV + RGB 差值 + 局部相对红度 → 融合 → 笔画膨胀 → 形态学优化
    """
    cfg = config or CONFIG

    # Step 0: CLAHE 预处理（改进A）
    image = preprocess_clahe(image, cfg)

    # Step 1: HSV + RGB 差值检测
    mask_hsv = detect_red_hsv(image, cfg)
    mask_rgb = detect_red_rgb_diff(image, cfg)

    # Step 2: 局部相对红度检测
    seed_mask = cv2.bitwise_or(mask_hsv, mask_rgb)
    mask_local = detect_red_local_contrast(image, seed_mask, cfg)

    # Step 3: 三掩码融合 + 形态学
    border_mask = remove_black_border(image)
    merged = merge_masks(mask_hsv, mask_rgb, mask_local, border_mask, cfg)

    # Step 4: 沿笔画膨胀
    merged, expanded_only = expand_along_strokes(merged, image, cfg)

    # 统计
    debug_info = {
        "mask_hsv": mask_hsv,
        "mask_rgb": mask_rgb,
        "mask_local": mask_local,
        "border_mask": border_mask,
        "expanded_only": expanded_only,
        "final_mask": merged,
        "hsv_pixels": cv2.countNonZero(mask_hsv),
        "rgb_pixels": cv2.countNonZero(mask_rgb),
        "local_pixels": cv2.countNonZero(mask_local),
        "expanded_pixels": cv2.countNonZero(expanded_only),
        "final_pixels": cv2.countNonZero(merged),
    }

    return merged, debug_info


def inpaint_red(image, mask, config=None, two_pass=True):
    """
    使用 Inpainting 清除红笔痕迹（Telea + 二次清理）。
    """
    cfg = config or CONFIG
    first = cv2.inpaint(image, mask, cfg["inpaint_radius"], cfg["inpaint_method"])

    if not two_pass:
        return first, None

    cleaned, residual = cleanup_residuals(image, mask, first, cfg)
    return cleaned, residual


# ============================================================
# 命令行测试入口
# ============================================================
if __name__ == "__main__":
    import sys
    import os

    if len(sys.argv) < 2:
        print("用法: python red_mask.py <image_path>")
        print("示例: python red_mask.py ../samples/page_040.jpg")
        sys.exit(1)

    img_path = sys.argv[1]
    if not os.path.exists(img_path):
        print(f"文件不存在: {img_path}")
        sys.exit(1)

    print(f"处理: {img_path}")
    img = cv2.imread(img_path)
    if img is None:
        print(f"无法读取图片: {img_path}")
        sys.exit(1)

    print(f"  尺寸: {img.shape[1]}x{img.shape[0]}")

    mask, info = detect_red_pen(img)
    cleaned, residual_mask = inpaint_red(img, mask)

    print(f"  HSV 掩码像素:     {info['hsv_pixels']:>8d}")
    print(f"  RGB 掩码像素:     {info['rgb_pixels']:>8d}")
    print(f"  局部红度像素:     {info['local_pixels']:>8d}")
    print(f"  笔画膨胀新增:     {info['expanded_pixels']:>8d}")
    print(f"  最终掩码像素:     {info['final_pixels']:>8d}")
    print(f"  二次清理残留:     {cv2.countNonZero(residual_mask):>8d}")

    base = os.path.splitext(os.path.basename(img_path))[0]
    out_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(out_dir, exist_ok=True)

    cv2.imwrite(os.path.join(out_dir, f"{base}_mask.png"), mask)
    cv2.imwrite(os.path.join(out_dir, f"{base}_clean.jpg"), cleaned)
    cv2.imwrite(os.path.join(out_dir, f"{base}_residual.png"), residual_mask)
    print(f"  结果已保存到: {out_dir}/")
