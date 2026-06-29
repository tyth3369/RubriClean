# 执行计划

## 开发阶段总览

```
Phase 0: 项目初始化     [已完成] 2026-06-26
Phase 1: 环境搭建       [待开始]
Phase 2: 红笔检测模块   [待开始]
Phase 3: 图像修复模块   [待开始]
Phase 4: 单图端到端流程 [待开始]
Phase 5: 批量处理       [待开始]
Phase 6: 优化与扩展     [待开始]
```

---

## Phase 0：项目初始化 ✅

**目标**：搭建项目骨架，明确需求和方案。

**产出**：
- [x] 项目目录结构 (`src/`, `docs/`, `logs/`, `samples/`)
- [x] 需求规格说明 (`docs/requirements.md`)
- [x] 技术方案文档 (`docs/technical-spec.md`)
- [x] 执行计划 (`docs/execution-plan.md`)
- [x] CLAUDE.md 工作指引

---

## Phase 1：环境搭建

**目标**：安装依赖库，验证环境可用。

**任务**：
1. 激活虚拟环境 `.venv`
2. 安装 `opencv-python`、`numpy`、`Pillow`、`PyMuPDF`、`tqdm`
3. 编写 `src/check_env.py` 环境验证脚本
4. 运行验证，确认所有库可正常导入

**产出**：
- `src/check_env.py`
- 可用的 Python 开发环境

**验证**：`python src/check_env.py` 全部通过

---

## Phase 2：红笔检测模块

**目标**：实现红笔像素检测，生成掩码，在样例图上可视化验证。

**任务**：
1. 编写 `src/red_mask.py`：
   - `detect_red_hsv(image)` → 掩码 A
   - `detect_red_rgb_diff(image)` → 掩码 B
   - `remove_black_border(image)` → 掩码 C
   - `merge_masks(mask_a, mask_b, mask_c)` → 最终掩码
2. 编写 `src/visualize.py`：
   - 掩码叠加原图可视化
   - 处理前后对比图生成
3. 在 4 张样例图上调试参数
4. 记录最优参数到开发日志

**产出**：
- `src/red_mask.py`
- `src/visualize.py`
- 4 张样例的掩码可视化结果

**验证**：肉眼检查掩码是否准确覆盖红笔区域，不覆盖学生笔迹

---

## Phase 3：图像修复模块

**目标**：基于掩码进行 Inpainting，消除红笔痕迹。

**任务**：
1. 在 `src/red_mask.py` 中添加：
   - `inpaint(image, mask)` → 修复后图片
2. 测试 Telea vs Navier-Stokes 效果差异
3. 调试 inpaint 半径参数

**产出**：
- 更新 `src/red_mask.py`（添加 inpaint 函数）
- 4 张样例的修复结果

**验证**：肉眼检查修复区域是否自然、无明显痕迹

---

## Phase 4：单图端到端流程

**目标**：串联所有模块，实现 "输入图片 → 输出干净图片" 的完整流程。

**任务**：
1. 编写 `src/pipeline.py`：
   - `process_image(input_path, output_path)` → 完整处理流程
   - 命令行接口：`python pipeline.py input.jpg -o output.jpg`
2. 编写 `src/config.py`：
   - 所有可调参数集中管理
   - 支持从配置文件读取

**产出**：
- `src/pipeline.py`
- `src/config.py`

**验证**：命令行单条指令完成处理，效果符合预期

---

## Phase 5：批量处理

**目标**：支持文件夹递归遍历和 PDF 拆分处理。

**任务**：
1. 编写 `src/batch_processor.py`：
   - 文件夹递归遍历
   - PDF → 图片拆分
   - 进度条显示
   - 错误日志记录
2. 用 100+ 页 PDF 做大规模测试

**产出**：
- `src/batch_processor.py`

**验证**：处理 100 页 PDF 不出错，处理速度可接受

---

## Phase 6：优化与扩展

**目标**：基于批量测试反馈优化参数，评估是否需要深度学习方案。

**任务**：
1. 统计分析失败案例
2. 调优参数
3. 评估方案 D（深度学习）的必要性
4. 如需要，启动深度学习方案调研

**产出**：
- 调优后的参数配置
- 失败案例分析报告

---

## 里程碑

| 里程碑 | 预计完成 | 关键产出 |
|--------|:------:|---------|
| M1: 环境就绪 | Phase 1 完成 | 可用开发环境 |
| M2: 红笔可检测 | Phase 2 完成 | 掩码可视化通过 |
| M3: 红笔可清除 | Phase 3 完成 | 修复效果通过 |
| M4: 单图流程打通 | Phase 4 完成 | CLI 工具可用 |
| M5: 批量处理就绪 | Phase 5 完成 | 批处理脚本可用 |
| M6: 生产可用 | Phase 6 完成 | 全流程稳定 |
