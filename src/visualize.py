"""
可视化工具 — 生成掩码叠加图和修复前后对比图
"""

import cv2
import numpy as np
import os


def overlay_mask(image, mask, color=(0, 255, 0), alpha=0.4):
    """将掩码叠加到原图上，半透明显示。"""
    overlay = image.copy()
    overlay[mask > 0] = (
        overlay[mask > 0] * (1 - alpha) +
        np.array(color) * alpha
    ).astype(np.uint8)
    return overlay


def make_comparison(original, mask, cleaned, output_path):
    """三栏对比图：原图 | 掩码叠加 | 修复后"""
    h, w = original.shape[:2]
    target_w = 900
    scale = target_w / w
    if scale < 1.0:
        original_s = cv2.resize(original, (target_w, int(h * scale)))
        cleaned_s = cv2.resize(cleaned, (target_w, int(h * scale)))
        mask_s = cv2.resize(mask, (target_w, int(h * scale)))
    else:
        original_s, cleaned_s, mask_s = original, cleaned, mask

    overlaid = overlay_mask(original_s, mask_s)

    def add_label(img, text):
        labeled = img.copy()
        bar_h = 40
        cv2.rectangle(labeled, (0, 0), (labeled.shape[1], bar_h), (0, 0, 0), -1)
        cv2.putText(labeled, text, (10, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        return labeled

    comparison = np.hstack([
        add_label(original_s, "Original"),
        add_label(overlaid, "Red Mask Overlay"),
        add_label(cleaned_s, "Cleaned (Inpainting)"),
    ])
    cv2.imwrite(output_path, comparison)
    print(f"  对比图已保存: {output_path}")


def make_mask_detail(original, info, output_path):
    """掩码细节图（5 栏）：HSV | RGB Diff | Local Contrast | Stroke Expand | Final"""
    h, w = original.shape[:2]
    target_w = 400
    scale = target_w / w
    if scale < 1.0:
        nh, nw = int(h * scale), target_w
        original_s = cv2.resize(original, (nw, nh))
    else:
        original_s, nh, nw = original, h, w

    def make_panel(mask, title, px_count):
        panel = overlay_mask(original_s,
            cv2.resize(mask, (nw, nh)) if mask.shape != original_s.shape[:2] else mask)
        labeled = panel.copy()
        bar_h = 36
        cv2.rectangle(labeled, (0, 0), (nw, bar_h), (0, 0, 0), -1)
        cv2.putText(labeled, title, (6, 16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
        cv2.putText(labeled, f"{px_count} px", (6, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
        return labeled

    panels = [
        make_panel(info["mask_hsv"], "1. HSV", info["hsv_pixels"]),
        make_panel(info["mask_rgb"], "2. RGB Diff", info["rgb_pixels"]),
        make_panel(info["mask_local"], "3. Local Contrast", info["local_pixels"]),
        make_panel(info["expanded_only"], "4. Stroke Expand", info["expanded_pixels"]),
        make_panel(info["final_mask"], "5. Final Mask", info["final_pixels"]),
    ]

    detail = np.hstack(panels)
    cv2.imwrite(output_path, detail)
    print(f"  掩码细节图已保存: {output_path}")


# ============================================================
# 命令行入口
# ============================================================
if __name__ == "__main__":
    import sys
    from red_mask_deep import detect_red_pen, inpaint_red

    if len(sys.argv) < 2:
        print("用法: python visualize.py <image_path> [output_subdir]")
        print("示例: python visualize.py ../samples/page_040.jpg")
        sys.exit(1)

    img_path = sys.argv[1]
    if not os.path.exists(img_path):
        print(f"文件不存在: {img_path}")
        sys.exit(1)

    img = cv2.imread(img_path)
    if img is None:
        print(f"无法读取: {img_path}")
        sys.exit(1)

    subdir = sys.argv[2] if len(sys.argv) > 2 else ""
    out_dir = os.path.join(os.path.dirname(__file__), "..", "output", subdir)
    os.makedirs(out_dir, exist_ok=True)

    print(f"处理: {img_path}")
    mask, info = detect_red_pen(img)
    cleaned, residual = inpaint_red(img, mask)

    for key in ["hsv_pixels", "rgb_pixels", "local_pixels", "expanded_pixels", "final_pixels"]:
        print(f"  {key}: {info[key]}")
    print(f"  residual_pixels: {cv2.countNonZero(residual)}")

    base = os.path.splitext(os.path.basename(img_path))[0]
    make_comparison(img, mask, cleaned, os.path.join(out_dir, f"{base}_comparison.jpg"))
    make_mask_detail(img, info, os.path.join(out_dir, f"{base}_detail.jpg"))
    cv2.imwrite(os.path.join(out_dir, f"{base}_residual.png"), residual)
