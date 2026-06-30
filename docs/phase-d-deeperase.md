# Phase D — DeepErase 深度学习方案启动指南

> 在 GPU 机器上阅读本文档即可开始。

---

## 一、项目背景速览

### 目标
从已批改作业扫描件中清除红笔痕迹（教师批改 ✅✗、分数、订正文字），还原学生原始答案，构建大模型训练数据库。

### 当前方案（v3 基线）
- 方法：HSV + RGB 混合颜色检测 + Telea Inpainting
- 优势：CPU 运行、零标注、~18 页/秒
- 瓶颈：扫描后完全变黑的红色像素无法通过颜色检测

### 为什么尝试 DeepErase
DeepErase 用 U-Net 做语义分割。它不只依赖单像素颜色，还能利用：
- **空间上下文**：一个黑像素如果两侧是红色，大概率是同一笔画
- **形状特征**：勾、叉、圈等批改符号的形态规律
- **位置规律**：批改标记通常出现在题目附近，学生答案在答题区

参考论文：[arxiv.org/abs/1910.07070](https://arxiv.org/abs/1910.07070)

**核心优势**：弱监督训练——不需要人工标注数据，通过合成自动生成训练样本。

---

## 二、训练数据合成方案

### 2.1 需要两样东西

| 素材 | 说明 | 来源 |
|------|------|------|
| **红笔笔画库** | 从已批改作业中提取的真实红笔笔迹 | 116 页已批改扫描件 |
| **干净作业模板** | 无批改痕迹的空白作业 | 116 页中无红笔的 14 页干净页 + 同类型空白原件 |

### 2.2 合成流程

```
红笔笔画抠图           干净作业模板
     │                      │
     └────── 随机叠加 ──────┘
              │
     ┌───────┴────────┐
     │                │
  合成训练图       自动标注掩码
  (有红笔痕迹)     (精确知道贴在哪)
```

### 2.3 为什么不需要人工标注

因为红笔是程序**贴上去**的，贴在哪个像素是精确已知的，标注掩码自动生成。唯一成本是提取红笔笔画这一步。

### 2.4 关键：红笔笔画如何提取

方法：用 v3 的 `detect_red_pen()` 生成掩码 → 从掩码区域裁剪笔画片段 → 去重清洗 → 构建笔画库。

提取脚本建议放在新项目的准备工作第一步。

---

## 三、DeepErase 模型概述

### 架构
```
输入: 512×512×3 (作业扫描件)
  │
  ├─ U-Net Encoder (VGG16 backbone，逐步压缩空间、提取特征)
  │
  ├─ Bottleneck (最深层，全局语义)
  │
  ├─ U-Net Decoder (逐步恢复空间分辨率)
  │
  └─ 输出: 512×512×1 (红笔概率图，每个像素 0~1)
```

### 训练配置参考

| 参数 | 建议值 |
|------|--------|
| 输入尺寸 | 512×512 滑动窗口 |
| Batch Size | 8-16（取决于 GPU 显存） |
| 学习率 | 1e-4, Adam |
| Loss | BCE + Dice Loss |
| 训练轮数 | 50-100 epoch |
| 数据量 | 5000-10000 张合成样本 |

### 推理方式
512×512 滑动窗口 + 重叠融合，处理任意尺寸扫描件。

---

## 四、环境安装

### 4.1 基础依赖（与 v3 相同）
```bash
pip install opencv-python numpy Pillow PyMuPDF tqdm
```

### 4.2 GPU 深度学习依赖
```bash
# PyTorch (CUDA 版，根据 CUDA 版本选择)
# CUDA 11.8:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
# CUDA 12.1:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# 其他 DL 工具
pip install albumentations     # 数据增强
pip install segmentation-models-pytorch  # U-Net 等预训练模型
pip install tensorboard         # 训练可视化
pip install scikit-learn        # 评估指标
```

### 4.3 验证 GPU 可用
```python
import torch
print(torch.cuda.is_available())        # 应为 True
print(torch.cuda.get_device_name(0))    # 应显示 GPU 型号
```

---

## 五、开发计划（建议分步）

### Step 1: 环境搭建 + GPU 验证
- 安装 PyTorch CUDA
- 跑验证脚本确认 GPU 可用

### Step 2: 红笔笔画提取
- 用 v3 处理 116 页
- 从掩码区域提取红笔笔画片段
- 构建笔画库（分类：勾、叉、圈、文字、分数）

### Step 3: 训练数据合成
- 选 10-20 页干净作业模板
- 随机叠加红笔笔画
- 生成 5000+ 合成训练样本
- 划分训练集/验证集

### Step 4: 模型训练
- 实现/参考 DeepErase U-Net
- 训练 + TensorBoard 监控
- 在真实样本上验证效果

### Step 5: 对比评估
- v3 vs DeepErase 效果对比
- 重点关注偏黑红笔的改善程度
- 决定是否替换/补充 v3

---

## 六、需要从旧电脑复制的文件

### 必须复制
```
RubriClean/
├── samples/          # 116 页已批改作业扫描件 (74MB)
├── docs/             # 所有项目文档
│   ├── requirements.md
│   ├── technical-spec.md
│   ├── research-reference.md
│   └── phase-d-deeperase.md (本文件)
├── src/
│   ├── red_mask.py           # v3 核心代码（用于笔画提取）
│   ├── visualize.py          # 可视化
│   └── config.json           # v3 参数配置
├── output/wuli_XuFaDaShiYe_8a_stu/  # v3 批量处理结果 (可选，102张)
├── requirements.txt          # 基础依赖
└── README.md
```

### 不需要复制
- `.venv/` — 在新机器上重建
- `output/v*/` — 旧版本迭代输出
- `logs/` — 开发日志（可选）

### 复制方式
- U盘 / 移动硬盘
- 网盘
- scp（如果两台机器在同一网络）
- 重新从 GitHub 克隆：`git clone https://github.com/tyth3369/RubriClean.git`

---

## 七、注意事项

1. **v3 作为笔画提取工具**：DeepErase 的训练数据合成依赖 v3 来提取红笔笔画，v3 效果越好，训练数据质量越高
2. **GPU 显存**：U-Net 训练建议至少 6GB 显存（GTX 1060 及以上）
3. **训练时间**：5000 张合成样本、50 epoch，单块 RTX 3060 约 4-8 小时
4. **推理速度**：CPU 上可达 2-5 秒/页（比 v3 慢，但比不做强）
