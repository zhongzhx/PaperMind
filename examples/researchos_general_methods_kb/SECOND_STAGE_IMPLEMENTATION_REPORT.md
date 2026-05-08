# Stage 2 Implementation Report: High-Impact Method Deep Learning

## Overview

Stage 2 extends the General Methods KB with structured deep learning extraction. It adds 19 fields of methodological knowledge per paper, with richer extraction for recent (2021–2026) papers and lighter extraction for older ones. All extraction is LLM-powered and fully mockable for testing — no real API key needed.

## Modules Created/Modified

### Phase 2a: Schema & Foundation

| File | Change | Description |
|------|--------|-------------|
| `schemas.py` | Modified | Added `EvidenceType` enum (9 values), `DeepLearningFields` dataclass (19 fields), `deep_learning` field on `MethodKnowledgeRecord` |
| `confidence_scoring.py` | Modified | Added 12-factor enhanced scoring (new weights + 6 new scoring functions). Old `compute_confidence()` kept for backward compat. |
| `adapters/llm/mock_llm.py` | Modified | Added 3 keyword routes: `"deep method extraction"`, `"standard method extraction"`, `"evidence extraction"` |
| `method_classifier.py` | **NEW** | `MethodClassifier` class with keyword + optional LLM disambiguation. `CATEGORY_KEYWORDS` moved from `kb_builder.py`. Role inference for 5 article types. |

### Phase 2b: Extraction Modules

| File | Description |
|------|-------------|
| `evidence_normalizer.py` | Rule-based extraction of protocol steps, QC points, parameters + optional LLM enhancement. Dedup, 20-item max, 200-char quote limit. |
| `recent_paper_deep_learner.py` | `learn()` for recent papers (19 fields via LLM), `learn_light()` for older papers (5 core fields). Missing fields → `"not_reported"`. |
| `high_impact_method_extractor.py` | Orchestrator: determines recency, routes to deep/light learner, runs evidence extraction, collects warnings. Follows `BasePatternExtractor` pattern. |

### Phase 2c: Pipeline Integration

| File | Change | Description |
|------|--------|-------------|
| `kb_builder.py` | Modified | `build_knowledge_base()` gains `llm_adapter` parameter. Runs deep learning + enhanced confidence when LLM provided. Backward compatible without LLM. |
| `kb_storage.py` | Modified | New `deep_learning_fields` SQLite table (20 columns). List fields stored as JSON. |
| `export_service.py` | Modified | 3 new markdown exports: deep learning report (recent papers), animal experiment summary, omics summary. |

### Phase 2d: Tests

| File | Tests | Description |
|------|-------|-------------|
| `test_researchos_general_methods_deep_schema.py` | 10 | EvidenceType, DeepLearningFields round-trip, MethodKnowledgeRecord with deep_learning |
| `test_researchos_general_methods_classifier.py` | 13 | All 10 method categories, role inference, convenience function, keyword coverage |
| `test_researchos_general_methods_evidence.py` | 12 | Rule-based extraction, LLM extraction, dedup, limits, confidence range |
| `test_researchos_high_impact_method_extractor.py` | 7 | Recent/older/no-year, failure modes, warnings, boundary condition |
| `test_researchos_general_methods_deep_markdown_export.py` | 7 | All 3 export functions, empty lists, record filtering |

## Test Results

- **Total tests:** 137 (90 existing + 47 new)
- **Passing:** 137 (100%)
- **Failing:** 0

## Key Design Decisions

1. **Recency boundary**: `year >= 2021` is treated as recent → full 19-field extraction. Pre-2021 → light extraction (5 fields).
2. **Deterministic fallback**: LLM field gaps use `"not_reported"` or `[]` — never `None` or missing.
3. **Single paper isolation**: Each paper's extraction is wrapped in try/except. One failure doesn't block the batch.
4. **Backward compatibility**: Old `compute_confidence()`, `build_knowledge_base()` without LLM, and all 90 existing tests pass unmodified.
5. **Mockable**: All LLM calls go through `LLMAdapter` Protocol. Tests use `MockLLMAdapter` with keyword routing — no API key needed.

## Architecture Flow

```
kb_builder.build_knowledge_base(texts, llm_adapter=...)
  → scan + load + extract metadata + filter
  → MethodClassifier.classify(text, journal)  →  (category, subcategories)
  → HighImpactMethodExtractor.extract(text, metadata, year, category)
      ├─ RecentPaperDeepLearner.learn()  or  .learn_light()  →  DeepLearningFields
      └─ EvidenceNormalizer.extract()                      →  List[EvidenceItem]
  → compute_enhanced_confidence() or compute_confidence()
  → MethodKnowledgeRecord (with deep_learning + evidence_items)
  → save JSONL + SQLite + 6 Markdown reports
```

## Enhanced Confidence Scoring (12 factors)

| Factor | Weight | Description |
|--------|--------|-------------|
| Source tier | 0.20 | Nature/Science/Cell tier |
| Section completeness | 0.15 | How many paper sections present |
| Core protocol steps | 0.10 | Number of protocol steps extracted |
| Recency | 0.10 | Year within 2021–2026 |
| Recent + deep learned | 0.10 | Deep learning was applied to recent paper |
| Evidence items | 0.05 | Number of evidence items |
| Quality control points | 0.05 | QC points extracted |
| Operation reference points | 0.05 | Operation reference points |
| DOI presence | 0.05 | DOI is present |
| Text length | 0.05 | Paper has substantial text |
| File type | 0.05 | PDF vs text |
| Warning penalty | 0.05 | Deduction for extraction warnings |
| **Total** | **1.00** | |
