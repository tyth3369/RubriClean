"""
版面对比工具 — 并排比较不同版本的修复效果
用法: python compare_versions.py <page_number>
"""
import sys
import os
import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from red_mask import detect_red_pen, inpaint_red, CONFIG

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "samples")


def add_label(img, text):
    """在图像顶部添加标签"""
    h, w = img.shape[:2]
    labeled = img.copy()
    bar_h = 40
    cv2.rectangle(labeled, (0, 0), (w, bar_h), (0, 0, 0), -1)
    cv2.putText(labeled, text, (10, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    return labeled


def main():
    if len(sys.argv) < 2:
        print("用法: python compare_versions.py <page_number>")
        print("示例: python compare_versions.py 080")
        sys.exit(1)

    page = sys.argv[1]
    img_path = os.path.join(SAMPLES_DIR, f"page_{page}.jpg")
    if not os.path.exists(img_path):
        print(f"文件不存在: {img_path}")
        sys.exit(1)

    img = cv2.imread(img_path)
    if img is None:
        print(f"无法读取: {img_path}")
        sys.exit(1)

    # 缩小原图用于拼接
    h, w = img.shape[:2]
    scale = 700 / w
    nh, nw = int(h * scale), 700

    # 收集各版本的 cleaned 结果
    results = {}
    for version in ["v3", "v7"]:
        comp_path = os.path.join(OUTPUT_DIR, version, f"page_{page}_comparison.jpg")
        if os.path.exists(comp_path):
            comp = cv2.imread(comp_path)
            # 取对比图的第三栏 (Cleaned 部分)
            # comparison 是三栏并排: original | overlay | cleaned
            pw = comp.shape[1] // 3
            cleaned = comp[:, 2 * pw: 3 * pw]
            results[version] = cv2.resize(cleaned, (nw, nh))
            print(f"  {version}: 已读取")
        else:
            print(f"  {version}: 不存在，跳过")

    if not results:
        print("没有找到任何版本结果")
        sys.exit(1)

    # 并排拼接
    original = add_label(cv2.resize(img, (nw, nh)), "Original Image")
    panels = [original]
    for v in ["v3", "v7"]:
        if v in results:
            panels.append(add_label(results[v], f"{v} Cleaned"))

    comparison = np.hstack(panels)
    out_path = os.path.join(OUTPUT_DIR, f"page_{page}_cross_version_compare.jpg")
    cv2.imwrite(out_path, comparison)
    print(f"版面对比已保存: {out_path}")


if __name__ == "__main__":
    main()
