#!/usr/bin/env python3
"""
环境验证脚本 — Phase 1
检查所有依赖库是否正确安装，并验证基础功能可用。
"""

import sys


def check_imports():
    """检查核心库导入"""
    modules = {
        "cv2": "opencv-python",
        "numpy": "numpy",
        "PIL": "Pillow",
        "fitz": "PyMuPDF",
        "tqdm": "tqdm",
    }

    results = []
    for name, package in modules.items():
        try:
            __import__(name)
            results.append((name, package, True, None))
        except ImportError as e:
            results.append((name, package, False, str(e)))

    return results


def check_versions():
    """输出版本信息"""
    import cv2
    import numpy as np
    from PIL import Image

    info = {
        "Python": sys.version,
        "OpenCV": cv2.__version__,
        "NumPy": np.__version__,
        "Pillow": Image.__version__,
    }

    # PyMuPDF 版本获取方式不同
    try:
        import fitz
        info["PyMuPDF"] = fitz.version[0]
    except Exception:
        info["PyMuPDF"] = "unknown"

    return info


def check_opencv_functionality():
    """验证 OpenCV 基础功能"""
    import cv2
    import numpy as np

    # 创建测试图像
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[25:75, 25:75] = [0, 0, 255]  # 红色方块

    # HSV 转换
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Inpainting 可用性
    mask = np.zeros((100, 100), dtype=np.uint8)
    mask[20:80, 20:80] = 255
    restored = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)

    return img.shape == restored.shape


def check_pymupdf_functionality():
    """验证 PyMuPDF 基础功能"""
    try:
        import fitz
        # 尝试创建空文档
        doc = fitz.open()
        doc.close()
        return True
    except Exception:
        return False


def main():
    print("=" * 50)
    print("RubriClean — 环境验证")
    print("=" * 50)

    # 1. 导入检查
    print("\n[1/3] 检查依赖库导入...")
    results = check_imports()
    all_ok = True
    for name, package, ok, error in results:
        status = "✅" if ok else "❌"
        print(f"  {status} {name} ({package})")
        if not ok:
            print(f"      错误: {error}")
            all_ok = False

    if not all_ok:
        print("\n❌ 部分依赖未安装，请运行:")
        print("   pip install opencv-python numpy Pillow PyMuPDF tqdm")
        sys.exit(1)

    # 2. 版本信息
    print("\n[2/3] 版本信息...")
    versions = check_versions()
    for name, ver in versions.items():
        print(f"  {name}: {ver}")

    # 3. 功能验证
    print("\n[3/3] 功能验证...")
    tests = {
        "OpenCV (HSV + Inpainting)": check_opencv_functionality(),
        "PyMuPDF (文档操作)": check_pymupdf_functionality(),
    }
    for name, ok in tests.items():
        status = "✅" if ok else "❌"
        print(f"  {status} {name}")

    if all(tests.values()):
        print("\n" + "=" * 50)
        print("✅ 环境验证全部通过！可以开始 Phase 2 开发。")
        print("=" * 50)
    else:
        print("\n❌ 部分功能验证失败，请检查安装。")
        sys.exit(1)


if __name__ == "__main__":
    main()
