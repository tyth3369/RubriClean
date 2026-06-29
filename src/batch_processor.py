#!/usr/bin/env python3
"""
批量处理器 — Phase 5 初版
处理 PDF 文件：拆分为单页图片 → 逐页检测红笔 → 清除 → 输出

用法: python batch_processor.py <pdf_path> [-o <output_dir>]
"""

import sys
import os
import cv2
import fitz  # PyMuPDF
import numpy as np
import argparse
from datetime import datetime

from red_mask import detect_red_pen, inpaint_red, load_config
from tqdm import tqdm


LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "batch.log")


def log(msg):
    print(msg)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{ts}] {msg}\n")


def process_pdf(pdf_path, output_dir, config=None):
    """处理 PDF：拆分→检测→清除→输出"""
    cfg = config or load_config()
    suffix = cfg.get("output_suffix", "_clean")

    # 打开 PDF
    doc = fitz.open(pdf_path)
    total = doc.page_count
    log(f"PDF: {os.path.basename(pdf_path)} ({total} 页)")

    skipped = 0
    cleaned = 0
    errors = 0

    for i in tqdm(range(total), desc="处理中", unit="页"):
        try:
            # PDF 页 → 图片
            page = doc[i]
            mat = fitz.Matrix(2.0, 2.0)  # 2x 缩放保证分辨率
            pix = page.get_pixmap(matrix=mat)
            img = np.frombuffer(pix.samples, np.uint8).reshape(pix.h, pix.w, pix.n)
            if pix.n == 4:  # RGBA → BGR
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
            elif pix.n == 3:  # RGB → BGR
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

            if img is None:
                log(f"[ERROR] 第 {i+1} 页无法渲染")
                errors += 1
                continue

            # 检测
            mask, info = detect_red_pen(img, cfg)

            if info["final_pixels"] == 0 and cfg.get("skip_if_no_red", True):
                skipped += 1
                continue

            # 修复
            cleaned_img, _ = inpaint_red(img, mask, cfg)

            # 保存
            out_name = f"page_{i+1:03d}{suffix}.jpg"
            out_path = os.path.join(output_dir, out_name)
            cv2.imwrite(out_path, cleaned_img,
                        [cv2.IMWRITE_JPEG_QUALITY, cfg.get("output_quality", 95)])

            cleaned += 1

        except Exception as e:
            log(f"[ERROR] 第 {i+1} 页: {e}")
            errors += 1

    doc.close()

    # 汇总
    log(f"\n{'='*50}")
    log(f"处理完成: {total} 页")
    log(f"  已清除红笔: {cleaned} 页 → {output_dir}/")
    log(f"  无红笔跳过: {skipped} 页")
    log(f"  出错:       {errors} 页")
    log(f"{'='*50}")

    return {"total": total, "cleaned": cleaned, "skipped": skipped, "errors": errors}


def main():
    parser = argparse.ArgumentParser(
        description="RubriClean 批量处理器 — PDF → 清除红笔 → 输出")
    parser.add_argument("pdf", help="PDF 文件路径")
    parser.add_argument("-o", "--output", default=None, help="输出目录（默认: output/<pdf名称>/）")
    parser.add_argument("-c", "--config", default=None, help="配置文件路径")
    args = parser.parse_args()

    if not os.path.exists(args.pdf):
        print(f"文件不存在: {args.pdf}")
        sys.exit(1)

    # 输出目录
    if args.output is None:
        base = os.path.splitext(os.path.basename(args.pdf))[0]
        args.output = os.path.join("..", "output", base)

    os.makedirs(args.output, exist_ok=True)

    # 加载配置
    config = load_config(args.config)

    # 处理
    process_pdf(args.pdf, args.output, config)


if __name__ == "__main__":
    main()
