# RubriClean

作业扫描件红笔痕迹自动清除工具。从已批改/订正的作业扫描件中检测并清除红色笔迹（教师批改、标注、订正），还原学生原始答案。

## 适用场景

- 构建批改作业大模型训练数据库时，需要学生原始错误答案（而非已被教师订正后的正确答案）
- 批量清洗扫描件中的红色批改标记

## 特性

- **纯颜色检测**：HSV + RGB 混合算法，无需 GPU，CPU 即可运行
- **偏黑红笔覆盖**：专门解决扫描后红色墨水偏暗/偏黑导致的漏检
- **黑字保护**：三重安全检查机制，确保不误删黑色印刷文字和学生手写答案
- **批量处理**：支持 PDF 拆分 + 逐页检测，处理速度 ~18 页/秒
- **零标注**：不需要训练数据，开箱即用

## 依赖

- Python 3.9+
- OpenCV (`opencv-python`)
- NumPy
- Pillow
- PyMuPDF（PDF 处理）

## 快速开始

```bash
# 1. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 单张图片处理
python src/pipeline.py samples/page_040.jpg

# 4. PDF 批量处理
python src/batch_processor.py 作业扫描件.pdf -o output/clean/
```

## 项目结构

```
RubriClean/
├── src/
│   ├── config.json          # 参数配置
│   ├── red_mask.py          # 红笔检测与修复核心
│   ├── visualize.py         # 可视化工具
│   ├── pipeline.py          # 单图 CLI 工具
│   └── batch_processor.py   # PDF 批量处理器
├── docs/
│   ├── requirements.md      # 需求规格说明
│   ├── technical-spec.md    # 技术方案
│   └── research-reference.md # 研究资料
├── samples/                 # 测试样例
├── requirements.txt
└── README.md
```

## 技术方案

采用方案 C：HSV + RGB 混合检测 + Telea Inpainting 修复。

详细见 [docs/technical-spec.md](docs/technical-spec.md)。

## 参数调优

编辑 `src/config.json` 即可调整所有检测阈值，无需修改代码。

## License

MIT
