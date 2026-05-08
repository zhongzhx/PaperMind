# Source Policy Update Report

## Overview

The General Methods KB module has been updated from a hard Nature/Science/Cell source filter to a graduated tier system. All user-provided papers are now processed regardless of source journal, with appropriate tiering rather than filtering.

## Old Behavior

- `classify_source()` acted as a hard filter: papers from non-Nature/Science/Cell journals were flagged as "uncertain" and skipped
- `filter_papers()` returned those as skipped entries
- Only three categories: accepted, skipped, uncertain
- No graduated confidence based on journal tier — a binary Nature/Science/Cell vs. everything-else

## New Behavior

| Concept | Before | After |
|---|---|---|
| Source filtering | Hard Nature/Science/Cell gate | `should_skip_paper()` — only truly unreadable files |
| Metadata handling | Papers skipped if source uncertain | Papers processed with `tier_4_uncertain_or_low_metadata` + metadata quality flags |
| Source tiering | Binary (NSC / not) | 4 tiers: tier_1_high_impact → tier_4_uncertain_or_low_metadata |
| Learning depth | Uniform | Time-based: 2021+ = deep, pre-2021 foundational = standard, pre-2021 others = light |
| Confidence scoring | 2-factor source check | 15-factor enhanced scoring including tier, metadata quality, method clarity |
| Deprecated functions | — | `classify_source()`, `filter_papers()` kept for backward compat |

## New Files & Functions

### `taxonomy.py` (updated with new detection functions)

| Function | Purpose |
|---|---|
| `detect_source_tier(source_family, journal, source_journal_group)` | Returns one of 4 `SourceTier` values using two-tier journal list matching |
| `detect_learning_depth(year, article_role, source_tier, method_category)` | Returns `(LearningDepth, reason)` based on recency, role, and source tier |
| `compute_publication_age_group(year)` | Returns `recent_five_years`, `classic_foundational`, or `unknown` |

### `source_filter.py` (updated, with deprecations)

| Function | Purpose |
|---|---|
| `should_skip_paper(text, file_type, file_size, source_family)` | Replaces old filter — only skips truly unprocessable files |
| `assess_metadata_quality(source_family, journal, year, doi, text_length, file_type)` | Returns boolean flags: has_journal, has_year, has_doi, has_content |
| `classify_source()` | **Deprecated** — always returns "accepted" |
| `filter_papers()` | **Deprecated** — returns all as accepted |

### `confidence_scoring.py` (enhanced)

| Function | Purpose |
|---|---|
| `_score_source_tier_from_tier(source_tier)` | Maps tier_1→1.0, tier_2→0.8, tier_3→0.6, tier_4→0.3 |
| `_score_metadata_quality(metadata_assessment)` | Scores based on completeness of journal/year/DOI/content |
| `_score_method_category_clarity(method_category)` | Higher score for specific method categories |
| `_score_is_classic_foundational(is_classic_foundational)` | Small bonus for classic papers |
| `compute_enhanced_confidence()` | Full 15-factor confidence scoring |

## Source Tier Detection Algorithm

```
source_family in (Nature, Science, Cell)?
  ├── Journal matches tier_1 list → tier_1_high_impact
  ├── Journal matches tier_2 list → tier_2_field_leading
  ├── Has journal name (any) → tier_2_field_leading
  └── No journal → tier_3_standard_peer_reviewed

No family:
  ├── Journal matches tier_1 list → tier_1_high_impact
  ├── Journal matches tier_2 list → tier_2_field_leading
  ├── Journal name > 3 chars → tier_3_standard_peer_reviewed
  └── No/short journal → tier_4_uncertain_or_low_metadata
```

## Learning Depth Decisions

| Condition | Depth | Reason |
|---|---|---|
| year >= 2021 | Deep | Recent publication window |
| Foundational role (protocol/method/benchmark) | Standard | Historical value |
| Review/guideline from tier 1/2 | Standard | High-value overview |
| tier_4 metadata | Light | Limited metadata |
| Pre-2021 with method category | Standard | Identifiable method category |
| Pre-2021 without clear category | Light | No clear category |

## Per-File Processing Pipeline

```
file_path
  → should_skip_paper()           [skip empty/corrupted/not-a-paper]
  → extract_metadata()            [title, year, journal, DOI, etc.]
  → assess_metadata_quality()     [flags for journal/year/DOI/content]
  → detect_source_tier()          [tier_1..tier_4]
  → classify()                    [method category + subcategories]
  → detect_learning_depth()       [deep/standard/light + reason]
  → compute_publication_age_group()
  → deep_learning (if LLM available)
  → compute_enhanced_confidence()
  → build MethodKnowledgeRecord
```

## Aggregate Statistics

Build reports now include:
- `records_by_source_tier` — count per tier
- `records_by_publication_age_group` — recent vs classic vs unknown
- `records_by_learning_depth` — deep vs standard vs light
- `records_by_category` — count per method category

## Test Results

```
Ran 224 tests in 0.744s
OK
```

- Existing tests from Phase 1/2 continue to pass unmodified
- New taxonomy tests: 24 cases including edge cases for `_journal_matches()`
- New source_filter tests: 14 cases for `should_skip_paper()` and `assess_metadata_quality()`
- Updated builder tests verify the new pipeline processes all papers, skips only empties
- Updated query/CLI tests use the new 20-column papers table schema
- Fixed critical bug in `_journal_matches()`: single-word patterns now require exact match (not substring), preventing false positives like "cell" matching "Cell Reports"
