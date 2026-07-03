# RubriClean

作业扫描件红笔痕迹自动清除工具。从已批改/订正的作业扫描件中检测并清除红色笔迹。
本项目全程由Claude Code辅助开发完成。

---

## 版本说明

| 版本 | 文件 | 状态 |
|------|------|:--:|
| **Standard** | `src/red_mask_standard.py` | ✅ **日常推荐** |
| **Bridge** | `src/red_mask_bridge.py` | ✅ 红黑交叉密集场景 |
| **Deep** | `src/red_mask_deep.py` | ✅ 偏黑红笔场景 |

### Standard — 日常通用

`R-G>15 & R-B>15` 判定红色 → Light-gated 晕影吸收 → 通道均衡填充。

保守的参数配置，兼顾**偏黑红笔的笔锋不会被误留暗斑**和**红黑交叉处保留黑笔笔画**。适合绝大多数场景，是日常使用的首选。

### Bridge — 红黑交叉密集

`R-G>15 & R-B>15` 判定红色 → Light-gated 晕影吸收 → **激进**通道均衡填充。

专为**纯亮红笔 + 红黑笔迹频繁交叉**的场景设计。使用更大的近墨区膨胀（7 px）、不做连通域噪点过滤，最大化红黑交叉处的修复效果。

> ⚠️ **前提假设**：你的红笔是标准亮红色（教师批改常用笔），不存在偏黑/深红笔迹。
> 如果画面中有偏黑红笔（笔锋呈暗红色、扫描后红度偏低），Bridge 的激进策略会将笔锋暗斑误判为黑墨而留下黑色残留。
> **如果你不确定红笔类型，请先用 Standard。**

| 对比 | Standard | Bridge |
|------|----------|--------|
| 红黑交叉修复 | ✅ 良好 | ✅✅ 最佳 |
| 偏黑红笔兼容 | ✅ 笔锋暗斑过滤 | ❌ 可能残留暗斑 |
| 近墨区膨胀 | 3 px | 7 px |
| 噪点过滤 | min_area ≥ 15 | 无过滤 |
| 适用场景 | 通用，不确定红笔类型时使用 | 明确为纯亮红笔，追求极致交叉修复 |

### Deep — 偏黑红笔

HSV + RGB 差值 + 局部红度 + 笔画膨胀（`diff=15`）→ Light-gated 晕影吸收 → 白色填充。

当扫描质量差、红笔明显偏黑，Standard 漏检时使用。

---

## 核心算法

### 通道均衡填充（Channel Balance）

当红笔批改记号与黑色印刷字体重叠时，简单涂白会切断黑笔笔画。通道均衡通过**上下文感知**解决红黑交叉问题：

1. **检测黑墨笔画**：暗色（gray < 80）+ 非红（redness < 10）→ 识别画面中的真实黑墨
2. **近墨区膨胀**：将黑墨区域膨胀 N px，覆盖红笔叠加在黑笔上的宽度
3. **压 R 保暗**：近墨区内的红笔像素仅压制 R 通道至 max(G,B)，保留底层暗色笔画
4. **其余涂白**：纯纸面上的红笔正常涂白
5. （Standard 额外）**连通域过滤**：剔除 < 15 px 的孤立噪点，防止笔锋暗斑误膨胀

### Light-gated 晕影吸收

红笔扫描后笔画周围会产生一圈浅色过渡像素（RGB 228-250），这些像素不满足红笔检测阈值，但靠近纯白填充后会形成可见"边框"。通过对 mask 膨胀 13px，但**只吸收浅色像素**（min 通道 > 200），精准捕获晕影的同时保护暗色黑笔不被误伤。

---

## 特性

- **纯颜色检测**：无需 GPU，CPU 即可运行
- **通道均衡**：上下文感知，红黑交叉处保留黑笔笔画不切断
- **双策略**：Standard 保守通用，Bridge 激进修复
- **晕影清除**：Light-gated 膨胀消除红笔边缘残留边框
- **偏黑红笔支持**：Deep 版本处理扫描质量差的深色红笔
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

# Standard — 日常推荐，绝大多数场景
python -c "
from src.red_mask_standard import process
import cv2
img = cv2.imread('homework.jpg')
cleaned, mask = process(img)
cv2.imwrite('clean.jpg', cleaned)
"

# Bridge — 纯亮红笔 + 红黑交叉密集场景
python -c "
from src.red_mask_bridge import process
import cv2
img = cv2.imread('homework.jpg')
cleaned, mask = process(img)
cv2.imwrite('clean.jpg', cleaned)
"

# Deep — 偏黑红笔场景
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
│   ├── red_mask_bridge.py     # Bridge — 红黑交叉密集
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
