# Final Report: ResearchOS General Methods Knowledge Base

## 1. 项目目标

构建一个独立的、结构化的**通识方法学知识库**，从 Nature / Science / Cell 三大顶刊家族的高分方法学文章中自动提取结构化的方法学知识，支持查询服务、ResearchOS 导入接口和最终验收。

**三个阶段的总体目标：**

- **Phase 1（已完成）：** 本地扫描、来源过滤、知识库 schema、基础输出（JSONL / SQLite / Markdown）
- **Phase 2（已完成）：** 高分方法学深度学习提取、近五年文章完整提取（19 字段）、老旧文章轻量提取（5 字段）、增强置信度评分（12 因子）
- **Phase 3（本轮完成）：** 查询服务、ResearchOS 导入接口、CLI 查询脚本、输出稳定化、最终报告

## 2. 当前实现了什么

| 功能 | 状态 |
|------|------|
| 扫描本地论文文件夹（.txt / .md / .pdf） | ✅ |
| 提取元数据（标题、期刊、年份、DOI） | ✅ |
| 过滤 Nature / Science / Cell 体系文章 | ✅ |
| 分类方法学类别（10 个一级分类） | ✅ |
| 基础置信度评分（6 因子） | ✅ |
| 增强置信度评分（12 因子） | ✅ |
| 输出 JSONL + SQLite + Markdown summary | ✅ |
| 近五年文章深度学习提取（19 字段） | ✅ |
| 老旧文章轻量提取（5 字段） | ✅ |
| 证据规范化（rule-based + LLM） | ✅ |
| SQLite 查询服务（8 个查询函数） | ✅ |
| Python 公共 API（build / load / query） | ✅ |
| CLI 查询脚本 | ✅ |
| ResearchOS 导入指南 | ✅ |
| 输出稳定化（别名文件 + JSON 报告） | ✅ |
| MockLLM 支持（无需 API key） | ✅ |
| 完整测试套件（184 个测试） | ✅ |

## 3. 新增文件

### Phase 1 新增（6 个模块 + 1 个示例 + 7 个测试 = 14 个文件）

```
src/researchos_learning_engine/general_methods_kb/
├── local_folder_scanner.py       — 文件夹扫描
├── paper_text_loader.py          — 文本加载（.txt / .md / .pdf）
├── metadata_extractor.py         — 元数据提取
├── source_filter.py              — 来源过滤
├── taxonomy.py                   — 分类枚举和子分类
├── schemas.py                    — 数据 schema（MethodKnowledgeRecord 等）
├── kb_storage.py                 — JSONL / SQLite 存储
├── export_service.py             — Markdown 报告导出
├── confidence_scoring.py         — 置信度评分
├── kb_builder.py                 — 构建管道编排

tests/
├── test_researchos_general_methods_taxonomy.py
├── test_researchos_general_methods_scanner.py
├── test_researchos_general_methods_metadata_extractor.py
├── test_researchos_general_methods_source_filter.py
├── test_researchos_general_methods_schema.py
├── test_researchos_general_methods_confidence.py
├── test_researchos_general_methods_builder.py

examples/researchos_general_methods_kb/
└── build_from_local_folder.py
```

### Phase 2 新增（4 个模块 + 1 个修改 + 5 个测试 = 10 个文件）

```
src/researchos_learning_engine/general_methods_kb/
├── method_classifier.py          — 方法学分类器（关键词 + LLM 辅助）
├── evidence_normalizer.py        — 证据规范化（rule-based + LLM）
├── recent_paper_deep_learner.py  — 近五年文章深度学习提取器
├── high_impact_method_extractor.py — 高影响力方法提取器（编排器）
├── adapters/llm/mock_llm.py      — MockLLM 新增 3 个关键词路由

tests/
├── test_researchos_general_methods_classifier.py
├── test_researchos_general_methods_evidence.py
├── test_researchos_general_methods_deep_schema.py
├── test_researchos_general_methods_deep_markdown_export.py
├── test_researchos_high_impact_method_extractor.py
```

### Phase 3 新增（本轮 — 1 个模块 + 4 个测试 + 1 个示例 + 1 个指南 = 7 个文件）

```
src/researchos_learning_engine/general_methods_kb/
├── query_service.py              — SQLite 查询服务（8 个查询函数）
├── __init__.py                   — 公共 API（build / load / query）

tests/
├── test_researchos_general_methods_query.py
├── test_researchos_general_methods_public_api.py
├── test_researchos_general_methods_cli.py
├── test_researchos_general_methods_researchos_import_guide.py

examples/researchos_general_methods_kb/
└── query_kb.py                   — CLI 查询脚本
```

## 4. 修改文件

| 文件 | Phase 2 修改 | Phase 3 修改 |
|------|-------------|-------------|
| `schemas.py` | 新增 EvidenceType、DeepLearningFields、deep_learning 字段 | — |
| `mock_llm.py` | 新增 3 个关键词路由 | — |
| `confidence_scoring.py` | 新增 12 因子增强评分 | — |
| `kb_builder.py` | 集成 LLM 管道 | 新增 manifest / JSON 报告 / import guide 导出 |
| `export_service.py` | 新增 3 个深度学习 Markdown 导出 | — |
| `kb_storage.py` | 新增 deep_learning_fields 表 | — |
| `build_from_local_folder.py` | — | 新增 --mock-llm 支持，--llm 适配 |
| `__init__.py` | — | 新增 3 个公共 API 函数 |

## 5. 如何构建知识库

```bash
# 从本地论文文件夹构建知识库（无 LLM，仅基础元数据提取）
PYTHONPATH=src python examples/researchos_general_methods_kb/build_from_local_folder.py \
  --input-dir "/path/to/papers" \
  --output-dir "./kb_output"

# 带 MockLLM 的完整构建（含深度学习提取，无需 API key）
PYTHONPATH=src python examples/researchos_general_methods_kb/build_from_local_folder.py \
  --input-dir "/path/to/papers" \
  --output-dir "./kb_output" \
  --mock-llm

# 使用 Python API
from researchos_learning_engine.general_methods_kb import build_general_methods_kb
result = build_general_methods_kb(
    input_dir="/path/to/papers",
    output_dir="./kb_output",
    llm=my_llm_adapter,  # Optional
    max_papers=100,
)
```

## 6. 如何查询知识库

```bash
# CLI 查询
PYTHONPATH=src python examples/researchos_general_methods_kb/query_kb.py \
  --sqlite-path ./kb_output/researchos_general_methods_kb.sqlite \
  --category animal_experiment

# 带 --mock-llm 构建后查询
PYTHONPATH=src python examples/researchos_general_methods_kb/query_kb.py \
  --sqlite-path ./kb_output/researchos_general_methods_kb.sqlite \
  --query "protocol"

# 仅查询近五年文章
PYTHONPATH=src python examples/researchos_general_methods_kb/query_kb.py \
  --sqlite-path ./kb_output/researchos_general_methods_kb.sqlite \
  --recent-only

# 查询动物实验子分类
PYTHONPATH=src python examples/researchos_general_methods_kb/query_kb.py \
  --sqlite-path ./kb_output/researchos_general_methods_kb.sqlite \
  --animal-subcategory dosing

# 使用 Python API
from researchos_learning_engine.general_methods_kb import query_general_methods_kb
results = query_general_methods_kb(
    sqlite_path="./kb_output/researchos_general_methods_kb.sqlite",
    query="western blot protocol",
    category="western_blot",
    recent_only=True,
    limit=5,
)
```

## 7. 输出文件说明

构建完成后 `output_dir` 下包含以下文件：

| 文件 | 说明 |
|------|------|
| `build_manifest_resolved.json` | 所有输入文件的构建结果清单（accepted / skipped / failed / uncertain） |
| `method_records.jsonl` | 结构化知识库记录（JSONL 格式）— ResearchOS 兼容名 |
| `method_knowledge_records.jsonl` | 同上（内部兼容名） |
| `researchos_general_methods_kb.sqlite` | SQLite 数据库 — ResearchOS 兼容名 |
| `method_knowledge_base.db` | 同上（内部兼容名） |
| `general_methods_summary.md` | 人类可读的构建摘要 |
| `recent_five_years_deep_learning.md` | 近五年论文的深度学习详细报告 |
| `animal_experiment_methods_summary.md` | 动物实验方法汇总 |
| `omics_methods_summary.md` | 组学方法汇总 |
| `build_report.json` | 结构化构建报告 |
| `skipped_papers.json` | 被跳过的论文（机器可读 JSON） |
| `uncertain_source_papers.json` | 来源不确定的论文 |
| `failed_papers.json` | 处理失败的论文 |
| `skipped_papers_report.md` | 跳过论文报告（Markdown） |
| `failed_papers_report.md` | 失败论文报告（Markdown） |
| `RESEARCHOS_IMPORT_GUIDE.md` | ResearchOS 导入指南 |

## 8. 近五年文章如何深度学习

1. **确定「近五年」阈值：** `recent_year_start = 2021`（可配置）
2. **完整提取（19 字段）：** 对 `year >= 2021` 的文章，调用 LLM 的 `"deep method extraction"` 系统提示，提取全部 19 个 DeepLearningFields
3. **轻量提取（5 字段）：** 对 `year < 2021` 或年份未知的文章，仅提取 `high_impact_value_cn`、`what_researchos_should_learn_cn`、`applicable_scenarios_cn`、`core_protocol_steps`、`limitations`，其余字段设为 `"not_reported"`
4. **确定性回退：** 任何 LLM 未填充的字段 → `"not_reported"` 或 `[]`，从不返回 `None` 或缺失
5. **证据提取：** 仅对近五年文章使用 LLM 增强证据提取；规则提取始终运行

## 9. 如何过滤 Nature / Science / Cell 体系外文章

过滤流程：

1. `metadata_extractor.detect_source_family(journal)` → 返回 `(family, journal_group)`
2. `source_filter.classify_source(source_family, journal, ...)` → 返回 `"accepted"` / `"uncertain"` / `"skipped"`
3. `kb_builder.build_knowledge_base(allowed_source_families=["Nature", "Science", "Cell"])` → 仅保留指定家族的论文

**source_family 检测规则：**

- **Nature 家族：** Nature、Nature Methods、Nature Protocols、Nature Biotechnology 等 90+ 期刊
- **Science 家族：** Science、Science Advances、Science Translational Medicine 等
- **Cell 家族：** Cell、Cell Reports、Cell Metabolism、Molecular Cell 等 70+ 期刊

**不确定来源处理：** 当 journal 名称无法精确匹配时（如仅从文件名或父目录提取），标记为 `"uncertain"` 但仍允许处理，在报告中单独列出。

## 10. 如何处理 skipped、uncertain、failed

### Skipped
- 来源家族不在允许列表中（如 arXiv、bioRxiv、Springer 非 Nature 系列期刊）
- 记录在 `skipped_papers.json` 和 SQLite `skipped_papers` 表
- 原因包含具体的源家族或检测信息

### Uncertain
- `source_filter.classify_source()` 返回 `"uncertain"`
- 论文仍被处理，但标记为不确定来源
- 记录在 `uncertain_source_papers.json`
- 构建报告的 `files_uncertain_source` 字段有计数

### Failed
- 文件读取失败（如 PDF 损坏）
- 元数据提取异常
- LLM 调用异常
- 异常被 try/except 隔离，单文件失败不影响整体构建
- 记录在 `failed_papers.json` 和 SQLite `failed_papers` 表

## 11. SQLite 表结构

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| `papers` | 论文基本信息 | paper_id, title, year, journal, doi, source_family, method_category, article_role, confidence_score |
| `method_records` | 方法学记录 | paper_id, method_category, method_subcategories, methodological_learning_value_cn |
| `evidence_items` | 证据项 | paper_id, claim, short_quote, section, evidence_type, confidence |
| `retrieval_keywords` | 检索关键词 | paper_id, language, keyword |
| `deep_learning_fields` | 深度学习字段 | paper_id + 19 个方法学字段（列表字段存储为 JSON 文本） |
| `build_runs` | 构建运行记录 | build_id, timestamps, 计数, 版本 |
| `skipped_papers` | 跳过论文 | file_path, reason |
| `failed_papers` | 失败论文 | file_path, error_message |

## 12. JSONL 字段结构

每条 JSONL 行是一个完整的 `MethodKnowledgeRecord.to_dict()` 输出，包含以下顶级字段：

- `paper_id`, `title`, `authors`, `year`, `journal`, `doi`
- `source_family`, `source_journal_group`, `source_type`
- `is_recent_five_years`, `method_category`, `method_subcategories`
- `article_role`
- `abstract_summary_cn`, `methodological_learning_value_cn`, `method_scope_cn`
- `retrieval_keywords_cn`, `retrieval_keywords_en`
- `confidence_score` (float, 0.0–1.0)
- `extraction_warnings` (List[str])
- `evidence_items` (List[EvidenceItem.to_dict()])
- `deep_learning` (DeepLearningFields.to_dict() 或 null)

## 13. ResearchOS 后续接入方式

详细见 `RESEARCHOS_IMPORT_GUIDE.md`，包含：

- JSONL / SQLite 两种数据格式的导入示例
- Python `sqlite3` 查询示例
- Research Context Compiler 注册为通识知识源的架构建议
- 回答问题时带来源的格式规范
- evidence_items 的使用建议
- 通识知识 vs 项目私有记忆的区分方法

**核心原则：**
- 本知识库仅提供通识方法学证据，**不能替代用户实验数据**
- 任何引用必须带来源（论文、DOI、置信度）
- 不能把通识知识当作用户的实验事实

## 14. 运行过的测试命令

```bash
# Phase 1 测试
PYTHONPATH=src python3 -m unittest discover tests/ -v
# 结果: 90 tests, all OK

# Phase 2 测试
PYTHONPATH=src python3 -m unittest discover tests/ -v
# 结果: 137 tests, all OK

# Phase 3 测试
PYTHONPATH=src python3 -m unittest discover tests/ -v
# 结果: 184 tests, all OK
```

## 15. 测试结果

最终测试结果：**184 个测试全部通过** (0.779s)

覆盖的测试文件（17 个）：

| 测试文件 | 测试数 | 覆盖范围 |
|----------|--------|----------|
| `test_researchos_general_methods_taxonomy.py` | 10 | 枚举、子分类、允许期刊 |
| `test_researchos_general_methods_scanner.py` | 7 | 文件夹扫描、文件过滤 |
| `test_researchos_general_methods_metadata_extractor.py` | 22 | DOI、年份、标题、期刊提取 |
| `test_researchos_general_methods_source_filter.py` | 13 | 来源分类、论文过滤 |
| `test_researchos_general_methods_schema.py` | 12 | 数据 schema 序列化、前向兼容 |
| `test_researchos_general_methods_confidence.py` | 9 | 原始 + 增强置信度评分 |
| `test_researchos_general_methods_builder.py` | 11 | 完整构建管道 |
| `test_researchos_general_methods_classifier.py` | 13 | 方法分类器 |
| `test_researchos_general_methods_evidence.py` | 12 | 证据规范化 |
| `test_researchos_general_methods_deep_schema.py` | 10 | 深度学习 schema |
| `test_researchos_general_methods_deep_markdown_export.py` | 7 | 深度学习 Markdown 导出 |
| `test_researchos_high_impact_method_extractor.py` | 7 | 高影响力方法提取器 |
| **Phase 3 新增：** | | |
| `test_researchos_general_methods_query.py` | 20 | 查询服务（全部 8 个查询函数） |
| `test_researchos_general_methods_public_api.py` | 9 | 公共 API |
| `test_researchos_general_methods_cli.py` | 12 | CLI 查询脚本 |
| `test_researchos_general_methods_researchos_import_guide.py` | 4 | ResearchOS 导入指南 |
| **总计** | **184** | |

所有测试均在无真实论文、无真实 LLM、无网络连接的环境下运行。

## 16. 当前局限

1. **PDF 文本提取质量依赖 PDF 结构：** 某些 PDF 的文本提取可能产生乱码或缺失内容
2. **MockLLM 仅用于测试：** 实际使用需要接入真实 LLM（如 Claude API）
3. **无全文搜索索引：** SQLite 查询使用 `LIKE` 而非 FTS5 全文索引
4. **无增量更新：** 每次构建都是全量重建
5. **深度学习方法学提取目前只支持 10 个分类：** 如需要更大范围的细颗粒度（如 PCR 的引物设计策略），需要进一步扩充分类和优化 prompt
6. **置信度评分依赖启发式规则：** 而非从实际使用效果中学习

## 17. 下一步建议

1. **SQLite FTS5 全文索引：** 提升 keyword 搜索速度和准确度
2. **增量更新支持：** 只处理新增/修改的文件，避免全量重建
3. **更多 LLM 适配：** 接入 Claude API、OpenAI API 等真实生产级 LLM
4. **更细粒度的原文定位：** 在深度学习提取时记录段落/页码引用
5. **知识图谱集成：** 将方法学提取结果构建为知识图谱（方法 → 论文 → 证据 → 参数）
6. **跨语言支持：** 目前仅中英双语；可扩展到日、韩、德、法等
7. **置信度评分校准：** 通过用户反馈或使用频率来校准评分权重
8. **Research Context Compiler 集成：** 将本知识库注册为 RCC 的通识知识源

---

*此报告由 PaperMind General Methods KB Builder 自动生成。*
