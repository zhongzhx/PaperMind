"""Export reports from a completed General Methods KB build.

Generates:
  - general_methods_summary.md  — human-readable overview
  - build_report.json           — structured build metadata
  - skipped_papers_report.md    — skipped files with reasons
  - failed_papers_report.md     — failed files with errors
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from researchos_learning_engine.general_methods_kb.schemas import (
    BuildRunRecord,
    MethodKnowledgeRecord,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def export_summary_md(
    records: List[MethodKnowledgeRecord],
    build_run: BuildRunRecord,
    output_dir: str,
    skipped: Optional[List[Dict[str, Any]]] = None,
    failed: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Generate a human-readable Markdown summary of the KB build.

    Phase 3: no longer filters by source_family — all processed papers
    are shown regardless of journal. Papers are grouped by source_tier
    and method_category instead of by source_family.

    Returns the path of the written file.
    """
    out = Path(output_dir) / "general_methods_summary.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    skipped_list = skipped or []
    failed_list = failed or []

    lines: List[str] = [
        "# General Methods Knowledge Base — Build Summary",
        "",
        f"**Build ID:** {build_run.build_id}",
        f"**Completed at:** {build_run.completed_at}",
        f"**Engine:** {build_run.engine_version} / Schema: {build_run.schema_version}",
        "",
        "---",
        "",
        "## Overview",
        "",
        f"| Metric | Value |",
        "|--------|-------|",
        f"| Total files found | {build_run.total_files_found} |",
        f"| Files processed (accepted) | {build_run.files_processed} |",
        f"| Files skipped | {build_run.files_skipped} |",
        f"| Files failed | {build_run.files_failed} |",
        f"| Uncertain metadata | {build_run.files_uncertain_metadata} |",
        "",
        "---",
        "",
        "## Accepted Papers",
        "",
    ]

    if records:
        lines.append(f"**{len(records)} papers accepted.**")
        lines.append("")
        lines.append("| # | Title | Journal | Year | Source Tier | Depth | Confidence |")
        lines.append("|---|-------|---------|------|-------------|-------|------------|")
        for i, r in enumerate(records, 1):
            title = r.title[:80] if r.title else "(untitled)"
            tier_display = r.source_tier.replace("tier_", "").replace("_", " ") if r.source_tier else "N/A"
            depth_display = r.learning_depth if r.learning_depth else "N/A"
            lines.append(
                f"| {i} | {title} | {r.journal} | "
                f"{r.year or 'n/a'} | {tier_display} | {depth_display} | {r.confidence_score} |"
            )
    else:
        lines.append("*No papers were accepted.*")

    # Source tier breakdown
    lines.extend(["", "---", "", "## Papers by Source Tier", ""])
    tier_counts: Dict[str, int] = {}
    for r in records:
        t = r.source_tier or "unknown"
        tier_counts[t] = tier_counts.get(t, 0) + 1
    if tier_counts:
        lines.append("| Source Tier | Count |")
        lines.append("|-------------|-------|")
        for tier, cnt in sorted(tier_counts.items()):
            lines.append(f"| {tier} | {cnt} |")
    else:
        lines.append("*No source tier data.*")

    # Learning depth breakdown
    lines.extend(["", "## Papers by Learning Depth", ""])
    depth_counts: Dict[str, int] = {}
    for r in records:
        d = r.learning_depth or "unknown"
        depth_counts[d] = depth_counts.get(d, 0) + 1
    if depth_counts:
        lines.append("| Learning Depth | Count |")
        lines.append("|----------------|-------|")
        for depth, cnt in sorted(depth_counts.items()):
            lines.append(f"| {depth} | {cnt} |")
    else:
        lines.append("*No learning depth data.*")

    # Category breakdown
    lines.extend(["", "---", "", "## Papers by Method Category", ""])
    cat_counts: Dict[str, int] = {}
    for r in records:
        cat_counts[r.method_category] = cat_counts.get(r.method_category, 0) + 1
    if cat_counts:
        lines.append("| Category | Count |")
        lines.append("|----------|-------|")
        for cat, cnt in sorted(cat_counts.items(), key=lambda x: -x[1]):
            lines.append(f"| {cat} | {cnt} |")
    else:
        lines.append("*No categories assigned.*")

    # Skipped
    if skipped_list:
        lines.extend(["", "---", "", f"## Skipped Papers ({len(skipped_list)})", ""])
        for s in skipped_list:
            lines.append(f"- `{s.get('file_path', '')}` — {s.get('reason', 'no reason')}")

    # Failed
    if failed_list:
        lines.extend(["", "---", "", f"## Failed Papers ({len(failed_list)})", ""])
        for f_item in failed_list:
            lines.append(f"- `{f_item.get('file_path', '')}` — {f_item.get('error_message', 'unknown')}")

    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    return str(out)


def export_build_report_json(
    build_run: BuildRunRecord,
    output_dir: str,
    extra: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate a structured build report as JSON.

    Returns the path of the written file.
    """
    out = Path(output_dir) / "build_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    report = build_run.to_dict()
    if extra:
        report["extra"] = extra
    report["exported_at"] = _now()

    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(out)


def export_skipped_report_md(
    skipped_papers: List[Dict[str, Any]],
    output_dir: str,
) -> str:
    """Generate a markdown report listing skipped papers.

    Returns the path of the written file.
    """
    out = Path(output_dir) / "skipped_papers_report.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    lines: List[str] = [
        "# Skipped Papers Report",
        "",
        f"**Total skipped:** {len(skipped_papers)}",
        "",
        "| File | Reason |",
        "|------|--------|",
    ]
    for sp in skipped_papers:
        lines.append(
            f"| `{sp.get('file_path', '')}` | {sp.get('reason', '')} |"
        )

    out.write_text("\n".join(lines), encoding="utf-8")
    return str(out)


def export_failed_report_md(
    failed_papers: List[Dict[str, Any]],
    output_dir: str,
) -> str:
    """Generate a markdown report listing failed papers.

    Returns the path of the written file.
    """
    out = Path(output_dir) / "failed_papers_report.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    lines: List[str] = [
        "# Failed Papers Report",
        "",
        f"**Total failed:** {len(failed_papers)}",
        "",
        "| File | Error |",
        "|------|-------|",
    ]
    for fp in failed_papers:
        lines.append(
            f"| `{fp.get('file_path', '')}` | {fp.get('error_message', '')} |"
        )

    out.write_text("\n".join(lines), encoding="utf-8")
    return str(out)


# ---------------------------------------------------------------------------
# Phase 2: Deep learning markdown exports
# ---------------------------------------------------------------------------


def _ensure_list(val: Any) -> List[str]:
    if isinstance(val, list):
        return [str(v) for v in val]
    return [str(val)] if val else []


def export_recent_five_years_deep_learning_md(
    records: List[MethodKnowledgeRecord],
    output_dir: str,
    recent_year_start: int = 2021,
) -> str:
    """Export a detailed Markdown report for recent (2021+) papers with deep learning.

    Returns the path of the written file.
    """
    out = Path(output_dir) / "recent_five_years_deep_learning.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    recent = [
        r for r in records
        if r.year is not None and r.year >= recent_year_start and r.deep_learning is not None
    ]

    lines: List[str] = [
        "# Recent Five Years — Deep Learning Report",
        "",
        f"**Year range:** {recent_year_start}–{recent_year_start + 5}",
        f"**Total recent papers with deep learning:** {len(recent)}",
        "",
        "---",
        "",
    ]

    if not recent:
        lines.append("*No recent papers with deep learning data.*")
        out.write_text("\n".join(lines), encoding="utf-8")
        return str(out)

    for idx, r in enumerate(recent, 1):
        dl = r.deep_learning
        lines.extend([
            f"## {idx}. {r.title}",
            "",
            f"**Year:** {r.year}  |  **Journal:** {r.journal}  |  **DOI:** {r.doi or 'N/A'}",
            "",
            "### 为什么是高价值文章",
            f"{dl.high_impact_value_cn}",
            "",
            "### 方法学核心",
            f"{dl.what_researchos_should_learn_cn}",
            "",
            "### 可复用实验设计逻辑",
            f"{dl.applicable_scenarios_cn}",
            "",
        ])

        if dl.core_protocol_steps:
            lines.extend(["### 操作参考点", ""])
            for step in dl.core_protocol_steps:
                lines.append(f"- {step}")
            lines.append("")

        if dl.quality_control_points:
            lines.extend(["### 质量控制点", ""])
            for qc in dl.quality_control_points:
                lines.append(f"- {qc}")
            lines.append("")

        if dl.analysis_workflow and dl.analysis_workflow != "not_reported":
            lines.extend(["### 数据分析逻辑", f"{dl.analysis_workflow}", ""])

        if dl.figure_logic_patterns:
            lines.extend(["### 图表逻辑", ""])
            for fig in dl.figure_logic_patterns:
                lines.append(f"- {fig}")
            lines.append("")

        if dl.reusable_research_patterns:
            lines.extend(["### 可转化为哪些模板或清单", ""])
            for pat in dl.reusable_research_patterns:
                lines.append(f"- {pat}")
            lines.append("")

        lines.append("---")
        lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")
    return str(out)


def export_animal_experiment_methods_summary_md(
    records: List[MethodKnowledgeRecord],
    output_dir: str,
) -> str:
    """Export a Markdown summary focused on animal experiment methods.

    Returns the path of the written file.
    """
    out = Path(output_dir) / "animal_experiment_methods_summary.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    animal_records = [
        r for r in records if r.method_category == "animal_experiment"
    ]

    lines: List[str] = [
        "# Animal Experiment Methods — Summary",
        "",
        f"**Total animal experiment papers:** {len(animal_records)}",
        "",
        "---",
        "",
        "## 1. 常见动物模型及适用场景",
        "",
    ]

    if not animal_records:
        lines.append("*No animal experiment papers in the knowledge base.*")
        lines.append("")
        lines.append("## 2. 造模")
        lines.append("")
        lines.append("*Data not available.*")
        lines.append("")
        lines.append("## 3. 给药")
        lines.append("*Data not available.*")
        lines.append("")
        lines.append("## 4. 麻醉")
        lines.append("*Data not available.*")
        lines.append("")
        lines.append("## 5. 手术")
        lines.append("*Data not available.*")
        lines.append("")
        lines.append("## 6. 取材")
        lines.append("*Data not available.*")
        lines.append("")
        lines.append("## 7. 血液采集")
        lines.append("*Data not available.*")
        lines.append("")
        lines.append("## 8. 组织采集")
        lines.append("*Data not available.*")
        lines.append("")
        lines.append("## 9. 终点标准")
        lines.append("*Data not available.*")
        lines.append("")
        lines.append("## 10. 动物福利")
        lines.append("*Data not available.*")
        lines.append("")
        out.write_text("\n".join(lines), encoding="utf-8")
        return str(out)

    for r in animal_records:
        subcats = ", ".join(r.method_subcategories) if r.method_subcategories else "N/A"
        lines.append(f"- **{r.title}** ({r.year}) — {r.journal}")
        lines.append(f"  - 子分类: {subcats}")
        dl = r.deep_learning
        if dl:
            if dl.core_protocol_steps:
                lines.append(f"  - 关键步骤: {'; '.join(dl.core_protocol_steps[:3])}")
            if dl.critical_parameters:
                lines.append(f"  - 关键参数: {'; '.join(dl.critical_parameters[:3])}")
            if dl.limitations and dl.limitations != ["not_reported"]:
                lines.append(f"  - 局限性: {'; '.join(dl.limitations[:2])}")
        lines.append("")

    lines.extend([
        "## 2. 造模",
        "以下内容来自已学习的动物实验论文：",
        "",
    ])
    for r in animal_records:
        if r.deep_learning and r.deep_learning.core_protocol_steps:
            lines.append(f"- {r.title}: {'; '.join(r.deep_learning.core_protocol_steps[:3])}")
    lines.append("")

    lines.extend([
        "## 3. 给药",
        "*Extract dosing methods from papers above.*",
        "",
        "## 4. 麻醉",
        "*Extract anesthesia methods from papers above.*",
        "",
        "## 5. 手术",
        "*Extract surgical methods from papers above.*",
        "",
        "## 6. 取材",
        "*Extract sampling methods from papers above.*",
        "",
        "## 7. 血液采集",
        "*Extract blood collection methods from papers above.*",
        "",
        "## 8. 组织采集",
        "*Extract tissue collection methods from papers above.*",
        "",
        "## 9. 终点标准",
        "*Extract endpoint criteria from papers above.*",
        "",
        "## 10. 动物福利",
        "*Extract welfare standards from papers above.*",
        "",
        "## 11. 随机化与盲法",
        "*Extract randomization and blinding methods from papers above.*",
        "",
        "## 12. 统计设计",
        "*Extract statistical design from papers above.*",
        "",
    ])

    out.write_text("\n".join(lines), encoding="utf-8")
    return str(out)


def export_omics_methods_summary_md(
    records: List[MethodKnowledgeRecord],
    output_dir: str,
) -> str:
    """Export a Markdown summary focused on omics methods.

    Returns the path of the written file.
    """
    out = Path(output_dir) / "omics_methods_summary.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    omics_records = [
        r for r in records
        if "omics" in r.method_category or "omics" in str(r.method_subcategories).lower()
    ]

    lines: List[str] = [
        "# Omics Methods — Summary",
        "",
        f"**Total omics papers:** {len(omics_records)}",
        "",
        "---",
        "",
        "## 1. 样本处理",
        "",
    ]

    if not omics_records:
        lines.append("*No omics papers in the knowledge base.*")
        lines.append("")
        for section in ["上机平台", "数据预处理", "质控", "批次效应", "差异分析",
                        "通路分析", "多组学整合", "图表逻辑", "结果解释边界"]:
            lines.append(f"## {section}")
            lines.append("*Data not available.*")
            lines.append("")
        out.write_text("\n".join(lines), encoding="utf-8")
        return str(out)

    for r in omics_records:
        lines.append(f"### {r.title} ({r.year}) — {r.journal}")
        dl = r.deep_learning
        if dl:
            if dl.core_protocol_steps:
                lines.append(f"- **关键步骤:** {'; '.join(dl.core_protocol_steps[:4])}")
            if dl.quality_control_points:
                lines.append(f"- **质控:** {'; '.join(dl.quality_control_points[:3])}")
            if dl.analysis_workflow and dl.analysis_workflow != "not_reported":
                lines.append(f"- **分析流程:** {dl.analysis_workflow}")
        lines.append("")

    lines.extend([
        "",
        "## 2. 上机平台",
        "*Extract platform details from papers above.*",
        "",
        "## 3. 数据预处理",
        "*Extract preprocessing methods from papers above.*",
        "",
        "## 4. 质控",
        "*Extract QC methods from papers above.*",
        "",
        "## 5. 批次效应",
        "*Extract batch effect correction methods from papers above.*",
        "",
        "## 6. 差异分析",
        "*Extract differential analysis methods from papers above.*",
        "",
        "## 7. 通路分析",
        "*Extract pathway analysis methods from papers above.*",
        "",
        "## 8. 多组学整合",
        "*Extract multi-omics integration methods from papers above.*",
        "",
        "## 9. 图表逻辑",
        "*Extract figure logic from papers above.*",
        "",
        "## 10. 结果解释边界",
        "*Extract interpretation boundaries from papers above.*",
        "",
    ])

    out.write_text("\n".join(lines), encoding="utf-8")
    return str(out)


# ---------------------------------------------------------------------------
# Phase 3: Classic foundational methods summary export
# ---------------------------------------------------------------------------


def export_classic_foundational_methods_summary_md(
    records: List[MethodKnowledgeRecord],
    output_dir: str,
) -> str:
    """Export a Markdown summary focused on classic foundational papers (pre-2021).

    Returns the path of the written file.
    """
    out = Path(output_dir) / "classic_foundational_methods_summary.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    classic = [
        r for r in records
        if r.publication_age_group == "classic_foundational"
    ]

    lines: List[str] = [
        "# Classic Foundational Methods — Summary",
        "",
        f"**Total classic foundational papers (pre-2021):** {len(classic)}",
        "",
        "---",
        "",
    ]

    if not classic:
        lines.append("*No classic foundational papers in the knowledge base.*")
        out.write_text("\n".join(lines), encoding="utf-8")
        return str(out)

    for idx, r in enumerate(classic, 1):
        lines.extend([
            f"## {idx}. {r.title}",
            "",
            f"**Year:** {r.year}  |  **Journal:** {r.journal}  |  **DOI:** {r.doi or 'N/A'}",
            f"**Source Tier:** {r.source_tier}  |  **Category:** {r.method_category}",
            f"**Article Role:** {r.article_role}  |  **Confidence:** {r.confidence_score}",
            "",
        ])

        dl = r.deep_learning
        if dl:
            if dl.high_impact_value_cn and dl.high_impact_value_cn != "not_reported":
                lines.extend(["### 为什么是高价值文章", f"{dl.high_impact_value_cn}", ""])
            if dl.what_researchos_should_learn_cn and dl.what_researchos_should_learn_cn != "not_reported":
                lines.extend(["### 方法学核心", f"{dl.what_researchos_should_learn_cn}", ""])
            if dl.applicable_scenarios_cn and dl.applicable_scenarios_cn != "not_reported":
                lines.extend(["### 可复用实验设计逻辑", f"{dl.applicable_scenarios_cn}", ""])
            if dl.core_protocol_steps:
                lines.extend(["### 操作参考点", ""])
                for step in dl.core_protocol_steps:
                    lines.append(f"- {step}")
                lines.append("")
            if dl.limitations:
                lines.extend(["### 局限性", ""])
                for lim in dl.limitations:
                    if lim and lim != "not_reported":
                        lines.append(f"- {lim}")
                lines.append("")

        # Evidence items summary
        if r.evidence_items:
            lines.extend(["### 证据项", ""])
            for ev in r.evidence_items[:5]:
                lines.append(f"- [{ev.evidence_type}] {ev.claim}")
            if len(r.evidence_items) > 5:
                lines.append(f"  *...and {len(r.evidence_items) - 5} more*")
            lines.append("")

        lines.append("---")
        lines.append("")

    out.write_text("\n".join(lines), encoding="utf-8")
    return str(out)
