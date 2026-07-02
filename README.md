# RubriClean

作业扫描件红笔痕迹自动清除工具。从已批改/订正的作业扫描件中检测并清除红色/蓝色笔迹。

---

## ⚠️ 版本说明

| 版本 | 文件 | 状态 |
|------|------|:--:|
| **Standard** | `src/red_mask_standard.py` | ✅ **当前推荐** |
| **v3.1** | `src/red_mask.py` | ✅ 特殊场景 |
| ~~v3~~ | — | ❌ **已淘汰** |

### Standard — 日常通用

`R-G>15 & R-B>15` 判定红色，白色填充修复。几乎不误伤印刷文字，适合绝大多数场景。

### v3.1 — 偏黑红笔

HSV + RGB 差值 + 局部红度 + 笔画膨胀（`diff=15`），白色填充修复。当扫描质量差、红笔明显偏黑时使用。

### v3（已淘汰）

~~HSV + RGB + 局部红度（`diff=8`）+ Inpainting。误检率偏高，修复有涂抹感。~~

---

## 特性

- **纯颜色检测**：无需 GPU，CPU 即可运行
- **双版本**：Standard 日常使用，v3.1 应对偏黑红笔
- **红蓝清除**：支持答案框内蓝笔清除（需 JSON 标注）
- **批量处理**：支持 PDF 拆分 + 逐页检测
- **零标注**：不需要训练数据，开箱即用

## 依赖

- Python 3.9+
- OpenCV (`opencv-python`)
- NumPy
- Pillow
- PyMuPDF（PDF 处理）

## 快速开始

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Standard（推荐日常使用）
python -c "
from src.red_mask_standard import detect_red_standard, white_fill
import cv2
img = cv2.imread('homework.jpg')
mask = detect_red_standard(img)
cv2.imwrite('clean.jpg', white_fill(img, mask))
"

# v3.1（偏黑红笔场景）
python src/pipeline.py homework.jpg -o clean.jpg
```

## 项目结构

```
RubriClean/
├── src/
│   ├── red_mask_standard.py   # Standard — 日常推荐
│   ├── red_mask.py            # v3.1 — 偏黑红笔
│   ├── visualize.py           # 可视化工具
│   ├── pipeline.py            # 单图 CLI
│   └── batch_processor.py     # PDF 批量处理
├── docs/
│   ├── requirements.md
│   ├── technical-spec.md
│   └── research-reference.md
└── README.md
```

## License

MIT
