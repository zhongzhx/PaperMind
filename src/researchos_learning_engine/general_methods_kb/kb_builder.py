"""Orchestrate the full General Methods KB build pipeline.

Pipeline:
  1. Scan input directory for paper files
  2. Load text content from each file
  3. Extract metadata (title, journal, year, DOI, source family)
  4. Skip truly unprocessable files (empty, corrupted, not-a-paper)
  5. Assess metadata quality (journal/year/DOI presence)
  6. Detect source tier (tier_1_high_impact .. tier_4_uncertain)
  7. Compute learning depth and publication age group
  8. Classify method category via keyword matching
  9. Deep learning extraction (if LLM provided)
  10. Score confidence (enhanced if deep data available)
  11. Build structured MethodKnowledgeRecord entries with all new fields
  12. Store to JSONL + SQLite
  13. Export summary reports + deep learning markdown
  14. Export manifest, skipped/uncertain_metadata/failed JSON reports
  15. Export ResearchOS import guide

Phase 3 policy: ALL user-provided papers are processed regardless of source
family. Non-Nature/Science/Cell papers receive lower source_tier and
potentially lower confidence, but are still extracted and learned.
Only truly unprocessable files are skipped (empty, corrupted, not-a-paper).

Single paper failures are isolated — one bad file cannot crash the whole build.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from researchos_learning_engine.domain.constants import ENGINE_VERSION, SCHEMA_VERSION
from researchos_learning_engine.general_methods_kb.confidence_scoring import (
    compute_confidence,
    compute_enhanced_confidence,
)
from researchos_learning_engine.general_methods_kb.export_service import (
    export_animal_experiment_methods_summary_md,
    export_build_report_json,
    export_classic_foundational_methods_summary_md,
    export_failed_report_md,
    export_omics_methods_summary_md,
    export_recent_five_years_deep_learning_md,
    export_skipped_report_md,
    export_summary_md,
)
from researchos_learning_engine.general_methods_kb.high_impact_method_extractor import (
    HighImpactMethodExtractor,
)
from researchos_learning_engine.general_methods_kb.kb_storage import save_jsonl, save_sqlite
from researchos_learning_engine.general_methods_kb.local_folder_scanner import scan_folder
from researchos_learning_engine.general_methods_kb.metadata_extractor import (
    detect_source_family,
    extract_doi,
    extract_journal,
    extract_title,
    extract_year,
)
from researchos_learning_engine.general_methods_kb.method_classifier import (
    MethodClassifier,
)
from researchos_learning_engine.general_methods_kb.paper_text_loader import load_text
from researchos_learning_engine.general_methods_kb.schemas import (
    BuildRunRecord,
    EvidenceItem,
    MethodKnowledgeRecord,
    SourceFamily,
    SourceType,
)
from researchos_learning_engine.general_methods_kb.source_filter import (
    assess_metadata_quality,
    should_skip_paper,
)
from researchos_learning_engine.general_methods_kb.taxonomy import (
    ArticleRole,
    MethodCategory,
    compute_publication_age_group,
    detect_learning_depth,
    detect_source_tier,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _detect_sections(text: str) -> Dict[str, bool]:
    """Detect which standard sections are present in the text via header matching."""
    lower = text.lower()
    section_patterns = {
        "abstract": ["abstract", "summary"],
        "introduction": ["introduction", "background"],
        "methods": ["methods", "materials and methods", "material and methods",
                     "experimental procedures", "experimental section"],
        "results": ["results", "findings"],
        "discussion": ["discussion"],
        "conclusion": ["conclusion"],
    }
    result: Dict[str, bool] = {}
    for section, patterns in section_patterns.items():
        result[section] = any(p in lower for p in patterns)
    return result


def _generate_paper_id(file_path: str) -> str:
    """Generate a deterministic paper ID from the file path."""
    h = hashlib.sha256(file_path.encode("utf-8")).hexdigest()[:12]
    return f"gmkb_{h}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _guess_source_type(ext: str) -> str:
    mapping = {".pdf": "pdf", ".txt": "txt", ".md": "md"}
    return mapping.get(ext, "unknown")


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def build_knowledge_base(
    input_dir: str,
    output_dir: str,
    recent_year_start: int = 2021,
    max_papers: int = 0,
    allowed_source_families: Optional[List[str]] = None,
    llm_adapter: Any = None,
) -> Dict[str, Any]:
    """Run the full General Methods KB build pipeline.

    Phase 3 policy: ALL papers are processed regardless of source family.
    The allowed_source_families parameter is kept for backward compatibility
    but is no longer used as a hard filter.

    Args:
        input_dir: Directory containing paper files (.txt, .md, .pdf)
        output_dir: Directory for output files (JSONL, SQLite, reports)
        recent_year_start: Year threshold for "recent" scoring (default 2021)
        max_papers: Max papers to process (0 = unlimited)
        allowed_source_families: Deprecated — kept for backward compat.
        llm_adapter: Optional LLM adapter for deep learning extraction.
                     If None, skips deep learning (backward compatible).

    Returns:
        Dict with build results summary.
    """
    build_id = f"build_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    start_time = _now()
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Prepare classifier and extractor (if LLM available)
    classifier = MethodClassifier(llm=llm_adapter)
    extractor = HighImpactMethodExtractor(llm_adapter) if llm_adapter is not None else None

    # Step 1: Scan
    scanned_files = scan_folder(input_dir, max_papers=max_papers)
    total_found = len(scanned_files)

    records: List[MethodKnowledgeRecord] = []
    skipped_papers: List[Dict[str, Any]] = []
    failed_papers: List[Dict[str, Any]] = []
    uncertain_metadata_papers: List[Dict[str, Any]] = []
    uncertain_metadata_count = 0

    # Step 2-8: Process each file
    for file_info in scanned_files:
        file_path = file_info["file_path"]
        paper_id = _generate_paper_id(file_path)

        try:
            # Load text
            text = load_text(file_path)

            # Extract metadata
            doi = extract_doi(text)
            year = extract_year(text, file_stem=file_info["file_stem"])
            journal = extract_journal(
                text,
                parent_dir_name=file_info["parent_dir_name"],
                file_name=file_info["file_name"],
            )
            source_family, source_journal_group = detect_source_family(journal)
            title = extract_title(text, file_stem=file_info["file_stem"])

            # Phase 3: Use should_skip_paper() for truly unprocessable files
            skip_reason = should_skip_paper(
                text=text,
                file_ext=file_info["ext"],
                text_length=len(text),
                source_family=source_family,
            )
            if skip_reason:
                skipped_papers.append({
                    "file_path": file_path,
                    "reason": skip_reason,
                    "skipped_at": _now(),
                })
                continue

            # Classify method category
            method_category, method_subcategories = classifier.classify(text, journal)
            article_role = classifier.infer_role(text)
            sections = _detect_sections(text)
            source_type_str = _guess_source_type(file_info["ext"])

            # Phase 3: Assess metadata quality
            metadata_assessment = assess_metadata_quality(
                source_family=source_family,
                journal=journal,
                year=year,
                doi=doi,
                text_length=len(text),
                file_ext=file_info["ext"],
            )

            # Phase 3: Track uncertain metadata (missing journal or year)
            if not metadata_assessment.get("has_journal", False) or not metadata_assessment.get("has_year", False):
                uncertain_metadata_count += 1
                uncertain_metadata_papers.append({
                    "file_path": file_path,
                    "source_family": source_family,
                    "journal": journal,
                    "title": title,
                    "reason": "Uncertain metadata — missing journal or year",
                    "detected_at": _now(),
                })

            # Phase 3: Detect source tier, learning depth, publication age
            source_tier = detect_source_tier(
                source_family=source_family,
                journal=journal,
                source_journal_group=source_journal_group,
            )
            learning_depth, learning_reason = detect_learning_depth(
                year=year,
                article_role=article_role,
                source_tier=source_tier,
                method_category=method_category,
                recent_year_start=recent_year_start,
            )
            pub_age_group = compute_publication_age_group(
                year=year,
                recent_year_start=recent_year_start,
            )
            is_recent = pub_age_group == "recent_five_years"
            is_classic = pub_age_group == "classic_foundational"

            # Deep learning extraction (if LLM available)
            metadata_for_extraction = {
                "title": title,
                "journal": journal,
                "doi": doi,
                "year": year,
            }

            if extractor is not None:
                deep_fields, evidence_items, extraction_warnings = (
                    extractor.extract_with_defaults(
                        text=text,
                        metadata=metadata_for_extraction,
                        year=year,
                        method_category=method_category,
                    )
                )
            else:
                deep_fields = None
                evidence_items = []
                extraction_warnings = []

            # Score confidence
            if deep_fields is not None:
                confidence = compute_enhanced_confidence(
                    source_family=source_family,
                    source_tier=source_tier,
                    year=year,
                    has_doi=bool(doi),
                    text=text,
                    source_type=source_type_str,
                    sections=sections,
                    recent_year_start=recent_year_start,
                    method_category=method_category,
                    core_protocol_steps=deep_fields.core_protocol_steps,
                    quality_control_points=deep_fields.quality_control_points,
                    evidence_items=evidence_items,
                    operation_reference_points=deep_fields.operation_reference_points,
                    deep_learning=deep_fields,
                    extraction_warnings=extraction_warnings,
                    is_recent=is_recent,
                    metadata_assessment=metadata_assessment,
                    is_classic_foundational=is_classic,
                )
            else:
                confidence = compute_confidence(
                    source_family=source_family,
                    source_tier=source_tier,
                    year=year,
                    has_doi=bool(doi),
                    text=text,
                    source_type=source_type_str,
                    sections=sections,
                    recent_year_start=recent_year_start,
                )

            # Build record with all Phase 3 fields
            record = MethodKnowledgeRecord(
                paper_id=paper_id,
                title=title[:300],
                year=year,
                journal=journal,
                doi=doi,
                source_family=source_family,
                source_journal_group=source_journal_group,
                source_type=source_type_str,
                source_tier=source_tier,
                journal_tier=source_journal_group,
                learning_depth=learning_depth,
                learning_reason=learning_reason,
                is_recent_five_years=is_recent,
                is_user_provided=True,
                is_classic_foundational=is_classic,
                publication_age_group=pub_age_group,
                method_category=method_category,
                method_subcategories=method_subcategories,
                article_role=article_role,
                confidence_score=confidence,
                evidence_items=evidence_items,
                extraction_warnings=extraction_warnings,
                deep_learning=deep_fields,
            )
            records.append(record)

        except Exception as exc:
            failed_papers.append({
                "file_path": file_path,
                "error_message": f"{type(exc).__name__}: {exc}",
                "failed_at": _now(),
            })
            continue

    completion_time = _now()

    # Phase 3: Compute aggregate stats
    records_by_source_tier: Dict[str, int] = {}
    records_by_publication_age_group: Dict[str, int] = {}
    records_by_learning_depth: Dict[str, int] = {}
    records_by_category: Dict[str, int] = {}
    for r in records:
        _increment(records_by_source_tier, r.source_tier or "unknown")
        _increment(records_by_publication_age_group, r.publication_age_group or "unknown")
        _increment(records_by_learning_depth, r.learning_depth or "unknown")
        _increment(records_by_category, r.method_category or "unknown")

    # Build run metadata
    build_run = BuildRunRecord(
        build_id=build_id,
        started_at=start_time,
        completed_at=completion_time,
        input_dir=input_dir,
        output_dir=output_dir,
        total_files_found=total_found,
        files_processed=len(records),
        files_skipped=len(skipped_papers),
        files_failed=len(failed_papers),
        files_uncertain_source=uncertain_metadata_count,
        files_uncertain_metadata=uncertain_metadata_count,
        records_by_source_tier=records_by_source_tier,
        records_by_publication_age_group=records_by_publication_age_group,
        records_by_learning_depth=records_by_learning_depth,
        records_by_category=records_by_category,
        engine_version=ENGINE_VERSION,
        schema_version=SCHEMA_VERSION,
        status="completed",
    )

    # Store
    jsonl_path = save_jsonl(records, str(out_path / "method_knowledge_records.jsonl"))
    db_path = save_sqlite(
        records,
        str(out_path / "method_knowledge_base.db"),
        build_run=build_run,
        skipped_papers=skipped_papers,
        failed_papers=failed_papers,
    )

    # Export standard reports
    summary_path = export_summary_md(records, build_run, output_dir, skipped_papers, failed_papers)
    report_path = export_build_report_json(build_run, output_dir)
    skip_report_path = export_skipped_report_md(skipped_papers, output_dir)
    fail_report_path = export_failed_report_md(failed_papers, output_dir)

    # Export deep learning reports
    deep_learning_path = export_recent_five_years_deep_learning_md(
        records, output_dir, recent_year_start,
    )
    animal_path = export_animal_experiment_methods_summary_md(records, output_dir)
    omics_path = export_omics_methods_summary_md(records, output_dir)

    # Phase 3: Export classic foundational summary
    classic_path = export_classic_foundational_methods_summary_md(records, output_dir)

    # ------------------------------------------------------------------
    # Phase 3: Additional output files for ResearchOS compatibility
    # ------------------------------------------------------------------

    # 1. build_manifest_resolved.json — every input file with its status
    manifest: List[Dict[str, Any]] = []
    for r in records:
        manifest.append({
            "paper_id": r.paper_id,
            "title": r.title,
            "status": "accepted",
            "source_tier": r.source_tier,
            "learning_depth": r.learning_depth,
            "publication_age_group": r.publication_age_group,
            "method_category": r.method_category,
            "confidence_score": r.confidence_score,
        })
    for sp in skipped_papers:
        manifest.append({
            "paper_id": _generate_paper_id(sp.get("file_path", "")),
            "title": "",
            "status": "skipped",
            "reason": sp.get("reason", ""),
        })
    for fp in failed_papers:
        manifest.append({
            "paper_id": _generate_paper_id(fp.get("file_path", "")),
            "title": "",
            "status": "failed",
            "reason": fp.get("error_message", ""),
        })
    for up in uncertain_metadata_papers:
        manifest.append({
            "paper_id": _generate_paper_id(up.get("file_path", "")),
            "title": up.get("title", ""),
            "status": "uncertain_metadata",
            "reason": up.get("reason", ""),
        })
    manifest_path = str(out_path / "build_manifest_resolved.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    # 2. skipped_papers.json (machine-readable)
    skipped_json_path = str(out_path / "skipped_papers.json")
    with open(skipped_json_path, "w", encoding="utf-8") as f:
        json.dump(skipped_papers, f, ensure_ascii=False, indent=2)

    # 3. uncertain_metadata_papers.json (Phase 3: renamed from uncertain_source)
    uncertain_json_path = str(out_path / "uncertain_metadata_papers.json")
    with open(uncertain_json_path, "w", encoding="utf-8") as f:
        json.dump(uncertain_metadata_papers, f, ensure_ascii=False, indent=2)
    # Also write legacy file name for backward compat
    legacy_uncertain_path = str(out_path / "uncertain_source_papers.json")
    with open(legacy_uncertain_path, "w", encoding="utf-8") as f:
        json.dump(uncertain_metadata_papers, f, ensure_ascii=False, indent=2)

    # 4. failed_papers.json (machine-readable)
    failed_json_path = str(out_path / "failed_papers.json")
    with open(failed_json_path, "w", encoding="utf-8") as f:
        json.dump(failed_papers, f, ensure_ascii=False, indent=2)

    # 5. Aliases for ResearchOS expected file names
    alias_jsonl = str(out_path / "method_records.jsonl")
    if jsonl_path != alias_jsonl:
        shutil.copy2(jsonl_path, alias_jsonl)
    alias_db = str(out_path / "researchos_general_methods_kb.sqlite")
    if db_path != alias_db:
        shutil.copy2(db_path, alias_db)

    # 6. ResearchOS import guide
    _write_import_guide(output_dir)

    return {
        "build_id": build_id,
        "status": "completed",
        "total_files_found": total_found,
        "files_processed": len(records),
        "files_skipped": len(skipped_papers),
        "files_failed": len(failed_papers),
        "files_uncertain_metadata": uncertain_metadata_count,
        "output_dir": output_dir,
        "jsonl_path": jsonl_path,
        "db_path": db_path,
        "summary_path": summary_path,
        "build_report_path": report_path,
        "deep_learning_report_path": str(deep_learning_path),
        "animal_experiment_report_path": str(animal_path),
        "omics_report_path": str(omics_path),
        "classic_foundational_report_path": str(classic_path),
        "manifest_path": manifest_path,
        "skipped_json_path": skipped_json_path,
        "uncertain_json_path": uncertain_json_path,
        "failed_json_path": failed_json_path,
        "alias_jsonl_path": alias_jsonl,
        "alias_db_path": alias_db,
    }


def _increment(counter: Dict[str, int], key: str) -> None:
    """Increment a counter dict entry by 1."""
    counter[key] = counter.get(key, 0) + 1


def _write_import_guide(output_dir: str) -> None:
    """Write RESEARCHOS_IMPORT_GUIDE.md to the output directory."""
    path = Path(output_dir) / "RESEARCHOS_IMPORT_GUIDE.md"
    guide = r"""# ResearchOS General Methods Knowledge Base — Import Guide

## 1. 这个知识库是什么

这个知识库是从用户提供的论文中自动构建的**通识方法学知识库**。它不包含任何用户的具体实验数据、项目记忆或私有信息。

**数据来源：** 本地文件夹中的方法学论文全文文本。

**覆盖范围：** 10 个方法学分类（qPCR, Western Blot, 流式细胞术, 动物实验, 组学, 细胞培养, 化学合成, 生物合成, 临床数据, 普通 PCR）。

**来源策略：** 所有用户提供的论文均被处理，不因期刊来源而过滤。Nature/Science/Cell 顶刊论文获得更高的 source_tier（tier_1_high_impact）和更高的基础置信度，低影响力期刊或元数据不完整的论文仍被学习但分配较低的 source_tier 和置信度。

**知识深度：** 近五年（2021+）文章经过完整深度学习提取（19 个字段），老旧文章标准/轻量提取（5-6 个核心字段）。

## 2. 它适合回答什么问题

这个知识库适合回答以下类型的问题：

- "Western blot 的实验步骤和质控点有哪些？"
- "动物实验的常用模型和给药方式？"
- "流式细胞术的配色原则和补偿方法？"
- "RNA-seq 的标准分析流程？"
- "高分文章的方法学设计思路？"
- "如何设置质控？"
- "实验中的常见陷阱？"

**不适合回答的问题：**

- "我上次实验的结果是什么？"（这是项目记忆）
- "帮我分析我的测序数据"（这是数据分析任务）
- "我的样品应该如何准备？"（这是具体实验设计，需要结合用户项目上下文）

## 3. 它包含哪些分类

| 一级分类 | 二级分类举例 |
|----------|-------------|
| qPCR_RT_qPCR | 染料法、探针法、相对定量、绝对定量、熔解曲线 |
| western_blot | — |
| flow_cytometry | 免疫表型、分选、凋亡检测、细胞周期 |
| PCR_general | 普通PCR、巢式PCR |
| omics_metabolomics_transcriptomics_proteomics | transcriptomics, proteomics, metabolomics, lipidomics, single_cell, spatial |
| cell_culture | 原代培养、细胞系、共培养、3D培养 |
| chemical_synthesis | — |
| biosynthesis | — |
| clinical_data | 队列研究、临床试验、观察性研究 |
| animal_experiment | 造模、给药、麻醉、手术、取材、血液采集、组织采集、终点标准、动物福利 |

## 4. JSONL 如何导入 ResearchOS

```python
import json

def load_methods_kb(jsonl_path):
    records = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records

# 每条记录包含：
# - paper_id, title, year, journal, doi
# - source_family, source_journal_group
# - source_tier, learning_depth, publication_age_group
# - method_category, method_subcategories
# - article_role
# - confidence_score
# - methodological_learning_value_cn
# - evidence_items (结构化证据列表)
# - deep_learning (深度学习方法学字段)
```

JSONL 格式兼容常见数据处理工具（Python json, pandas, Spark 等），可以直接导入 ResearchOS 的 memory bank 或 context compiler。

## 5. SQLite 如何被 ResearchOS 查询

```python
import sqlite3
import json

conn = sqlite3.connect("researchos_general_methods_kb.sqlite")
conn.row_factory = sqlite3.Row

# 查询某类方法
cur = conn.execute(
    "SELECT p.*, m.methodological_learning_value_cn "
    "FROM papers p LEFT JOIN method_records m ON p.paper_id = m.paper_id "
    "WHERE p.method_category = ?", ("animal_experiment",)
)

# 查询近五年文章
cur = conn.execute(
    "SELECT * FROM papers WHERE is_recent_five_years = 1"
)

# 按 source_tier 筛选
cur = conn.execute(
    "SELECT * FROM papers WHERE source_tier = 'tier_1_high_impact'"
)

# 查询深度学习字段
cur = conn.execute(
    "SELECT operation_reference_points, quality_control_points "
    "FROM deep_learning_fields WHERE paper_id = ?", (paper_id,)
)
# 解析 JSON 列表
ops = json.loads(row["operation_reference_points"] or "[]")
```

## 6. Research Context Compiler 调用方式

推荐在 ResearchOS 的 Research Context Compiler (RCC) 中注册为**通识知识源**：

```python
class GeneralMethodsKnowledgeSource:
    priority = 3  # 低于项目记忆和用户事实
    source_type = "domain_knowledge"

    def get_relevant_context(self, user_query, top_k=5):
        # 1. 解析 query 中的方法学关键词
        # 2. 在 SQLite 中按 keyword 搜索
        # 3. 按 confidence_score 和 source_tier 排序
        # 4. 取 top_k 条返回
        # 5. 附上证据项和来源信息
        pass
```

**查询优先级建议：**

1. 项目私有记忆（最高优先级）
2. 用户实验记录
3. **通识方法学知识库**（本模块）
4. PDF/文献知识库
5. 通用模型知识

## 7. 回答用户问题时如何带来源

当 RCC 使用了知识库中的信息，在回答末尾应注明来源。推荐格式：

> **来源：** General Methods KB
> **论文：** 《Title》 (Journal, Year) — DOI: 10.xxx
> **置信度：** 0.85
> **来源等级：** tier_1_high_impact
> **证据类型：** protocol_step / parameter / quality_control

## 8. 如何使用 evidence_items

每条 evidence_items 包含：

```python
{
    "claim": "方法灵敏度达到单细胞级别",
    "short_quote": "single-cell sensitivity was achieved",
    "section": "results",
    "evidence_type": "parameter",
    "confidence": 0.9
}
```

**不应当把这些证据：**
- 当作用户的实验数据
- 用于回答关于用户项目状态的问题
- 替代原始论文的完整阅读

---
*这份文档由 PaperMind General Methods KB Builder 自动生成。*
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(guide, encoding="utf-8")
