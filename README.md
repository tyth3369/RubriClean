# RubriClean

作业扫描件红笔痕迹自动清除工具。从已批改/订正的作业扫描件中检测并清除红色笔迹。

---

## ⚠️ 版本说明

| 版本 | 文件 | 状态 |
|------|------|:--:|
| **Standard** | `src/red_mask_standard.py` | ✅ **日常推荐** |
| **Deep** | `src/red_mask_deep.py` | ✅ 偏黑红笔场景 |

### Standard — 日常通用

`R-G>15 & R-B>15` 判定红色 → Light-gated 晕影吸收 → 白色填充。几乎不误伤印刷文字，适合绝大多数场景。

### Deep — 偏黑红笔

HSV + RGB 差值 + 局部红度 + 笔画膨胀（`diff=15`）→ Light-gated 晕影吸收 → 白色填充。当扫描质量差、红笔明显偏黑，Standard 漏检时使用。

### Light-gated 晕影吸收（v4 新增）

红笔扫描后笔画周围会产生一圈浅色过渡像素（RGB 228-250），这些像素不满足红笔检测阈值，但靠近纯白填充后会形成可见"边框"。通过对 mask 膨胀 13px，但**只吸收浅色像素**（min 通道 > 200），精准捕获晕影的同时保护暗色黑笔不被误伤。

---

## 特性

- **纯颜色检测**：无需 GPU，CPU 即可运行
- **双版本**：Standard 日常使用，v3.1 应对偏黑红笔
- **晕影清除**：Light-gated 膨胀消除红笔边缘残留边框
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
from src.red_mask_standard import process
import cv2
img = cv2.imread('homework.jpg')
cleaned, mask = process(img)
cv2.imwrite('clean.jpg', cleaned)
"

# v3.1（偏黑红笔场景）
python -c "
from src.red_mask_deep import process
import cv2
img = cv2.imread('homework.jpg')
cleaned, mask, info = process(img)
cv2.imwrite('clean.jpg', cleaned)
"
```

## 项目结构

```
RubriClean/
├── src/
│   ├── red_mask_standard.py   # Standard — 日常推荐
│   ├── red_mask_deep.py       # Deep — 偏黑红笔
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
