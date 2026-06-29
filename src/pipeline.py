#!/usr/bin/env python3
"""
单图端到端处理管线 — Phase 4
用法: python pipeline.py <input_path> [-o <output_path>] [-c <config_path>]
"""

import sys
import os
import cv2
import argparse

from red_mask import detect_red_pen, inpaint_red, load_config, CONFIG

# 日志文件路径
LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "pipeline.log")


def log(msg):
    """同时输出到终端和日志文件"""
    print(msg)
    log_dir = os.path.dirname(LOG_FILE)
    os.makedirs(log_dir, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        from datetime import datetime
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{ts}] {msg}\n")


def process_image(input_path, output_path=None, config=None, quiet=False):
    """
    处理单张图片：检测红笔 → 修复 → 保存。

    Args:
        input_path: 输入图片路径
        output_path: 输出路径（可选，默认在同目录加 _clean 后缀）
        config: 配置字典（可选，默认从 config.json 加载）
        quiet: 是否静默模式

    Returns:
        dict: {"success": bool, "output": str or None, "red_pixels": int, "skipped": bool}
    """
    cfg = config or load_config()
    suffix = cfg.get("output_suffix", "_clean")

    # 读取图片
    img = cv2.imread(input_path)
    if img is None:
        log(f"[ERROR] 无法读取图片: {input_path}")
        return {"success": False, "output": None, "red_pixels": 0, "skipped": False}

    # 检测红笔
    mask, info = detect_red_pen(img, cfg)

    # 判断是否跳过
    if info["final_pixels"] == 0:
        if cfg.get("skip_if_no_red", True):
            log(f"[SKIP] 未检测到红笔: {input_path}")
            return {"success": True, "output": None, "red_pixels": 0, "skipped": True}
        else:
            if not quiet:
                log(f"[INFO] 未检测到红笔，仍输出副本: {input_path}")
            cleaned = img
    else:
        # 修复
        cleaned, _ = inpaint_red(img, mask, cfg)
        if not quiet:
            log(f"[OK]   红笔 {info['final_pixels']} px → {os.path.basename(input_path)}")

    # 构造输出路径
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        out_format = cfg.get("output_format", "jpg")
        output_path = f"{base}{suffix}.{out_format}"

    # 保存
    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    out_format = cfg.get("output_format", "jpg")
    if out_format == "jpg" or out_format == "jpeg":
        cv2.imwrite(output_path, cleaned, [cv2.IMWRITE_JPEG_QUALITY, cfg.get("output_quality", 95)])
    else:
        cv2.imwrite(output_path, cleaned)

    return {
        "success": True,
        "output": output_path,
        "red_pixels": info["final_pixels"],
        "skipped": False,
    }


def main():
    parser = argparse.ArgumentParser(
        description="RubriClean — 清除作业扫描件红笔痕迹",
        epilog="示例: python pipeline.py hw001.jpg -o hw001_clean.jpg")
    parser.add_argument("input", help="输入图片路径")
    parser.add_argument("-o", "--output", default=None, help="输出路径（默认: 同名_clean）")
    parser.add_argument("-c", "--config", default=None, help="配置文件路径（默认: config.json）")
    parser.add_argument("-q", "--quiet", action="store_true", help="静默模式，仅输出错误")
    parser.add_argument("--force", action="store_true", help="即使无红笔也输出副本")
    args = parser.parse_args()

    # 验证输入
    if not os.path.exists(args.input):
        log(f"[ERROR] 文件不存在: {args.input}")
        sys.exit(1)

    # 加载配置
    config = load_config(args.config)
    if args.force:
        config["skip_if_no_red"] = False

    # 处理
    if not args.quiet:
        print(f"RubriClean v3 — 处理: {args.input}")

    result = process_image(args.input, args.output, config, quiet=args.quiet)

    if not args.quiet:
        if result["skipped"]:
            print(f"  → 跳过 (无红笔)")
        elif result["success"]:
            print(f"  → 已保存: {result['output']}")

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
