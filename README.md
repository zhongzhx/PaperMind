# PaperMind — 科研论文结构化学习引擎

**将论文转化为可复用的研究知识，让每一篇高分文章都成为你的研究范式库。**

PaperMind 是一个纯 Python、零外部依赖的科研论文学习引擎。它从论文全文中提取结构化知识——实验设计模式、信号通路机制、图表逻辑、写作范式和可复用的研究洞察——并支持项目记忆评分、巩固与推荐。

## Why PaperMind?

传统文献管理工具（Zotero、Mendeley）和 RAG 系统只能"存储+检索"论文文本，PaperMind 更进一步：**将论文转化为结构化的研究范式**。

| 方面 | 传统 RAG | PaperMind |
|------|----------|-----------|
| **存储内容** | 原始文本块 | 结构化模式 + 可复用洞察 |
| **处理方式** | Embedding + 检索 | LLM 提取 + 规则合成 |
| **输出形式** | 排序后的文本段落 | 类型化 Schema（设计、机制、写作） |
| **使用场景** | 找到相关信息 | 学习如何设计、写作、推理 |
| **可复用性** | 上下文特定 | 跨项目通用范式 |

## 核心功能

### 📄 高分文章学习库
从高影响力论文中提取 5 类结构化知识：
- **实验设计模式** — 模型系统、分组方案、干预措施、检测指标、控制策略、验证链条
- **信号机制模式** — 信号通路、靶点、上下游因子、证据类型、claim 强度
- **图表逻辑模式** — 图表角色、数据类型、关键信息、支撑的 claim、可复用的可视化思路
- **写作模式** — 引言叙事逻辑、结果组织方式、讨论框架、创新性/局限性叙述策略
- **可复用研究洞察** — 跨项目的行动建议、实验灵感、应用方向

### 🧠 项目记忆巩固
Sleep Cycle 管线——项目知识自动评分、整合、归档：
- **记忆健康评分** — 置信度、用户确认、项目相关性、证据支持、检索有用性、时效性
- **矛盾检测** — 识别记忆之间的冲突
- **证据图构建** — 结构化证据边，追踪知识来源
- **项目摘要更新** — 自动生成新的项目全景摘要

## 快速开始

```bash
# 克隆
git clone https://github.com/your-org/paper-mind.git
cd paper-mind

# 运行全部测试
python3 run_tests.py

# 启动本地 Demo（浏览器可交互）
PYTHONPATH=src python3 demo_app/server.py
# 访问 http://127.0.0.1:8766
```

### 使用 Python API

```python
from researchos_learning_engine.adapters.llm.mock_llm import MockLLMAdapter
from researchos_learning_engine.paper_learning.library_service import learn_high_impact_paper
from researchos_learning_engine.paper_learning.schemas import HighImpactPaperRecord

paper = HighImpactPaperRecord(
    paper_id="paper_001",
    title="B. subtilis FPR suppresses inflammation via TLR4/MyD88/NF-κB",
    full_text="...",  # 论文全文
    journal="Frontiers in Immunology",
    doi="10.3389/fimmu.2024.1234567",
    year=2024,
)

result = learn_high_impact_paper(
    paper,
    llm=MockLLMAdapter(),
    project_id="immunomodulation",
    project_description="天然产物免疫调节机制研究",
)

print(f"质量分: {result.quality_score:.3f}")
print(f"实验设计模式: {len(result.experiment_design_patterns)}")
print(f"信号机制模式: {len(result.mechanism_patterns)}")
print(f"图表逻辑模式: {len(result.figure_logic_patterns)}")
print(f"写作模式: {len(result.writing_patterns)}")
print(f"可复用洞察: {len(result.reusable_insights)}")
```

### 运行记忆巩固

```python
from researchos_learning_engine.domain.schemas import ConsolidationInput
from researchos_learning_engine.interfaces.python_api import run_sleep_cycle

result = run_sleep_cycle(ConsolidationInput(
    project_id="immunomodulation",
    project_title="天然产物免疫调节机制",
    memory_records=[...],
    paper_records=[...],
    current_project_summary="...",
))

for mem in result.promoted_memories:
    print(f"提升: {mem.memory_id} (健康分: {mem.health_score:.3f})")
```

## 架构

```
┌──────────────────────────────────────────────┐
│               Interfaces                      │
│   Python API  │  HTTP Demo Server  │  CLI     │
├──────────────────────────────────────────────┤
│           Application Services                │
│   MemoryScoring │ PaperExtraction            │
│   Consolidation │ Recommendation             │
│   EvidenceGraph │ PaperLearning              │
├──────────────────┬───────────────────────────┤
│    Domain Layer  │        Adapters           │
│  ┌────────────┐  │  ┌──────────┐ ┌────────┐ │
│  │ schemas.py │  │  │ LLM     │ │Storage │ │
│  │ scoring.py │  │  │ MockLLM │ │JSON    │ │
│  │ constants  │  │  │ OpenAI  │ │SQLite  │ │
│  └────────────┘  │  └──────────┘ └────────┘ │
│                  │  ┌──────────┐ ┌────────┐ │
│                  │  │Embeddings│ │Vector  │ │
│                  │  │ Mock     │ │Store   │ │
│                  │  └──────────┘ └────────┘ │
└──────────────────┴───────────────────────────┘
```

**架构原则：** 端口与适配器模式。依赖方向向内——核心领域层零外部依赖。LLM、存储、Embedding、向量数据库均为可替换适配器。

## 目录结构

```
paper-mind/
├── README.md
├── LICENSE                    # MIT
├── pyproject.toml
├── run_tests.py               # 一键运行所有测试
├── examples/                  # 示例数据 + 真实文章测试
│   ├── high_impact_paper_input.json
│   ├── real_paper_learning_cases/
│   └── run_real_paper_cases.py
├── demo_app/                  # 本地 HTTP Demo
│   ├── server.py              # Python stdlib 服务器
│   ├── static/                # 中文前端
│   └── README.md
├── src/
│   └── researchos_learning_engine/
│       ├── domain/            # 核心领域模型
│       │   ├── schemas.py     # 数据类 Schema
│       │   ├── scoring.py     # 记忆评分引擎
│       │   └── constants.py   # 枚举、权重、阈值
│       ├── application/       # 应用服务
│       ├── paper_learning/    # ★ 高分文章学习库
│       │   ├── schemas.py     # 8 个文章学习数据类
│       │   ├── section_parser.py
│       │   ├── paper_quality_scoring.py
│       │   ├── experiment_design_extractor.py
│       │   ├── mechanism_extractor.py
│       │   ├── figure_logic_extractor.py
│       │   ├── writing_pattern_extractor.py
│       │   ├── project_relevance.py
│       │   └── library_service.py
│       ├── adapters/          # 可替换适配器
│       │   ├── llm/           # MockLLM / OpenAI
│       │   ├── storage/       # JSON / SQLite
│       │   ├── embeddings/
│       │   └── vectorstore/
│       └── interfaces/        # 外部接口
│           ├── python_api.py
│           └── cli.py
└── tests/                     # 122+ 测试
    ├── test_memory_scoring.py
    ├── test_paper_learning_library.py
    ├── test_real_paper_learning_cases.py
    ├── test_demo_app_server.py
    └── ...
```

## Demo

启动本地 Web 应用：

```bash
PYTHONPATH=src python3 demo_app/server.py
```

打开 **http://127.0.0.1:8766**，两个核心功能 Tab：

1. **高分文章学习库** — 选择示例文章 → 查看结构化提取结果
2. **项目记忆巩固** — 运行 Sleep Cycle → 查看记忆评分和整合结果

内置 3 篇完整真实风格测试文章（B. subtilis、Astragalus polysaccharide、β-glucan），全部使用 MockLLM，无需 API Key，结果确定可复现。

## 验证

```bash
# 运行全部 122+ 测试
python3 run_tests.py

# 批量运行 3 篇真实风格测试文章
PYTHONPATH=src python3 examples/run_real_paper_cases.py
```

测试覆盖：Schema 序列化/反序列化、Section 解析、质量评分、4 类提取器、项目相关性、完整管线集成、Demo 服务端路由。

## 使用真实 LLM

复制 `.env.example` 为 `.env`，配置 API Key：

```
LLM_API_KEY=sk-your-key-here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o
```

有 API Key 时引擎自动使用真实 LLM，否则回退到 MockLLM。

## 技术栈

- Python 3.9+，**零外部依赖**
- 端口与适配器架构（Ports & Adapters）
- 数据类 Schema + 递归 `to_dict()` / `from_dict()` 序列化
- 规则引擎（记忆评分、质量评分、项目相关性）
- LLM 提取 + 规则合成（Insight Synthesis）
- MockLLM 关键字路由，无 API Key 可完整测试

## 许可

MIT License。参见 [LICENSE](LICENSE)。

---

**PaperMind** — 从论文到范式，让每一篇文献都成为研究能力的一部分。
