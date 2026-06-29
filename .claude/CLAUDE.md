# RubriClean — Claude 工作指引

## 项目简介

RubriClean 是一个作业扫描件红笔痕迹清除工具。从已批改/订正的作业扫描件中自动检测并清除红色笔迹（教师批改、标注、订正），还原学生原始答案，用于构建批改作业大模型的训练数据库。

## 核心文档索引

| 文档 | 路径 | 用途 |
|------|------|------|
| 需求规格说明 | [docs/requirements.md](docs/requirements.md) | 项目背景、核心需求、输入输出规格、约束条件 |
| 技术方案 | [docs/technical-spec.md](docs/technical-spec.md) | 方案 C 详细技术路线、算法 Pipeline、参数说明 |
| 执行计划 | [docs/execution-plan.md](docs/execution-plan.md) | 分阶段开发计划、里程碑、验证方式 |
| 研究资料 | [docs/research-reference.md](docs/research-reference.md) | 红笔清除相关论文、开源工具、技术对比 |
| 开发日志 | [logs/](logs/) | 每日开发记录，按日期命名 (YYYY-MM-DD.md) |

## 技术栈

- **语言**：Python 3.9
- **核心库**：OpenCV (`cv2`)、NumPy、Pillow
- **PDF 支持**：PyMuPDF (fitz) 或 pdf2image
- **虚拟环境**：`.venv/`（已创建，位于项目根目录）

## 项目结构

```
RubriClean/
├── .claude/
│   └── CLAUDE.md              # 本文件
├── docs/
│   ├── requirements.md        # 需求规格说明
│   ├── technical-spec.md      # 技术方案
│   └── execution-plan.md      # 执行计划
├── logs/                      # 每日开发日志
├── samples/                   # 测试样例图片
├── src/                       # 源代码
└── .venv/                     # Python 虚拟环境
```

## 工作约定

### 开发原则
1. **渐进式开发**：每次只实现一个模块，验证通过后再进行下一步
2. **先读后写**：修改或扩展现有代码前，先阅读相关文件理解上下文
3. **小步提交**：每个功能点完成后及时记录到开发日志
4. **参数可调**：所有阈值和参数集中管理，方便后期调优

### 每日流程
1. 查看 [logs/](logs/) 中最新的开发日志，了解当前进度
2. 参考 [docs/execution-plan.md](docs/execution-plan.md) 确定当前阶段
3. 开发完成后更新开发日志，记录完成事项和待办

### 文档维护
- 需求变更时更新 [docs/requirements.md](docs/requirements.md)
- 技术方案调整时更新 [docs/technical-spec.md](docs/technical-spec.md)
- 每天结束时创建/更新 `logs/YYYY-MM-DD.md`

### 依赖管理
- 安装新依赖前先确认虚拟环境已激活
- 依赖变更后更新 [docs/technical-spec.md](docs/technical-spec.md) 中的依赖清单

## 当前状态

- **阶段**：Phase 2-3 完成（v3 基线），待推进 Phase 4/5（生产化）
- **方案**：方案 C — HSV + RGB 混合检测 + Inpainting（v3 生产基线）
- **最新日志**：[logs/2026-06-26.md](logs/2026-06-26.md)
