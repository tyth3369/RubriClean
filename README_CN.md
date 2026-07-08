# RubriClean

作业扫描件红笔痕迹自动清除工具。检测并清除教师批改标记，保留学生原始答案。

本项目全程由 Claude Code 辅助开发。

---

## 版本说明

| 版本 | 文件 | 用途 |
|---------|------|----------|
| **Maestro** | `src/maestro.py` | ✅ **全自动——首选** |
| Standard | `src/red_mask_standard.py` | 日常通用，安全基线 |
| Bridge v1.2 | `src/red_mask_bridge_v2.py` | 交叉密集页面 |
| Bridge v1.1 | `src/red_mask_bridge.py` | 纯亮红笔场景 |
| Deep | `src/red_mask_deep.py` | 偏黑/深红笔迹 |

### Maestro v2.0 — 逐页自适应路由

Maestro 分析每页特征，自动选择最佳策略：
- **交叉密集**（手写密集，红笔叠黑字）→ Bridge v1.2 — 最佳文字保护
- **纸上红笔**（文字稀疏，红笔在纸上）→ Deep — 最佳暗红清除

决策基于笔迹穿透分析：黑墨笔迹是**穿过**红笔区域（真交叉）还是仅**触碰**边缘（伪影）？

零参数。零手动选择。开箱即用。

### Standard — 安全通用

`R-G>15 & R-B>15` 检测 → 晕影吸收 → 通道均衡填充。

平衡暗红清除与交叉修复。适合绝大多数场景。

### Bridge v1.2 — 组件级拼接

Deep 完整检测管线 + Bridge 通道均衡填充。
交叉组件用 Bridge 输出；纸上组件用 Deep 白化。

适合红黑交叉频繁同时存在暗红笔迹的页面。

### Bridge v1.1 — 交叉专家

`R-G>20 & R-B>20` 检测 → 激进通道均衡（dil=7）。

专为**亮红笔叠黑字**设计。保守检测意味着暗红可能漏检。

### Deep — 暗红专家

多层检测（HSV + RGB 差值 + 局部对比度）→ 形态学 → 笔画膨胀 → 白化。

捕获极暗/褪色红笔，但白化会破坏红黑交叉处的黑字——仅用于无交叉页面。

---

## 核心算法

### 通道均衡填充

红笔叠黑字时，简单涂白会切断笔画。通道均衡处理交叉：

1. **检测黑墨**：暗色（`gray < 80`）+ 非红（`redness < 10`）
2. **近墨区膨胀**：扩张黑墨区域覆盖红笔宽度
3. **压 R 通道**：近墨区红笔像素仅压制 R 至 `max(G,B)`——降红度保暗色
4. **其余涂白**：纸上红笔正常白化

### Light-gated 晕影吸收

扫描件红笔周围有浅色过渡像素（RGB 228–250）。mask 膨胀 13px，仅吸收亮像素（`gray > 200`）——捕获晕影同时保护暗色文字。

---

## 快速开始

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

```python
import cv2
from src.maestro import process

img = cv2.imread("homework.jpg")
cleaned, mask, info = process(img)
cv2.imwrite("clean.jpg", cleaned)

print(f"路由至: {info['version']}")
```

---

## 项目结构

```
RubriClean/
├── src/
│   ├── maestro.py              # v2.0 — 自适应路由
│   ├── red_mask_bridge_v2.py   # v1.2 — 组件拼接
│   ├── red_mask_bridge.py      # v1.1 — 交叉专家
│   ├── red_mask_standard.py    # v1.0 — 日常通用
│   ├── red_mask_deep.py        # v1.0 — 暗红专家
│   ├── router.py               # 路由模块（maestro 使用）
│   ├── config.json             # 共享参数
│   ├── visualize.py            # 可视化调试
│   ├── pipeline.py             # 单图 CLI
│   └── batch_processor.py      # PDF 批量处理
├── docs/
├── README.md
└── README_CN.md
```

## 依赖

- Python 3.9+
- OpenCV (`opencv-python`)
- NumPy
- Pillow
- PyMuPDF（PDF 处理用）

## License

MIT
