# Learning Engine Contract

## Positioning

The ResearchOS Learning Engine is a **standalone, pluggable module** that provides structured learning, memory scoring, consolidation, contradiction detection, and recommendation capabilities for scientific research projects.

It is **not**:
- A frontend service
- A real-time chat completion engine
- A model training/fine-tuning pipeline
- A PDF ingestion service

It **is**:
- A batch-oriented consolidation service
- A rule-based memory scoring engine
- A structured knowledge extraction pipeline
- A recommendation generator for literature discovery

## How ResearchOS Should Call It

The main ResearchOS backend never imports from internal application services. It calls a single function:

```python
from researchos_learning_engine.interfaces.python_api import run_sleep_cycle

result = run_sleep_cycle(input_data)
```

Where `input_data` is a `ConsolidationInput` and `result` is a `ConsolidationResult`.

Input comes from the ResearchOS agent runtime: agent memory, paper records, RAG chunks, skill execution logs, experimental data, and the current project summary.

Output is written back to multiple ResearchOS stores: agent memory (new scores/statuses), project memory (archived/deprecated), evidence graph (new edges), research pattern library, and project metadata (updated summary).

---

## ConsolidationInput JSON Format

```json
{
  "schema_version": "1.0",
  "project_id": "proj_cancer_metabolism",
  "project_title": "Cancer Metabolism: Targeting Glycolysis in Pancreatic Cancer",
  "project_description": "This project investigates the role of aerobic glycolysis...",
  "recent_conversations": [
    {"id": "conv_001", "summary": "Discussed HK2 inhibitor specificity", "date": "2026-05-06"}
  ],
  "paper_records": [
    {
      "paper_id": "paper_001",
      "title": "The Warburg Effect...",
      "authors": ["Jane Smith"],
      "year": 2023,
      "journal": "Nature Reviews Cancer",
      "doi": "10.1038/s41568-023-00572-w",
      "source_type": "oa_pdf",
      "full_text": "Cancer cells exhibit...",
      "chunks": ["Chunk 1...", "Chunk 2..."],
      "project_relevance_score": 0.95,
      "evidence_value_score": 0.9,
      "status": "processed",
      "abstract": "The Warburg effect describes..."
    }
  ],
  "rag_chunks": [
    {"chunk_id": "rag_001", "source": "paper_001", "content": "HIF-1alpha upregulates HK2...", "relevance_score": 0.9}
  ],
  "memory_records": [
    {
      "memory_id": "mem_001",
      "project_id": "proj_cancer_metabolism",
      "memory_type": "paper_evidence",
      "content": "Warburg effect is characterized by increased aerobic glycolysis...",
      "source_refs": ["paper_001"],
      "confidence": 0.9,
      "importance": 0.9,
      "recency_score": 1.0,
      "project_relevance": 0.95,
      "evidence_level": "L4",
      "retrieval_count": 15,
      "contradiction_count": 0,
      "status": "active",
      "health_score": 0.0,
      "score_breakdown": null,
      "created_at": "2026-04-01T10:00:00+00:00",
      "updated_at": "2026-05-07T14:00:00+00:00",
      "last_reviewed": "2026-05-01T12:00:00+00:00"
    }
  ],
  "skill_runs": [
    {"run_id": "skill_001", "skill_name": "pubmed_search", "params": {"query": "glycolysis inhibitor"}, "result_count": 47, "timestamp": "2026-05-01T11:00:00+00:00"}
  ],
  "data_contexts": [
    {"context_id": "ctx_001", "type": "experiment_metadata", "content": "Cell lines: PANC-1, MIA PaCa-2..."}
  ],
  "current_project_summary": "This project targets glycolysis in pancreatic cancer..."
}
```

### Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | string | yes | Schema version for forward compatibility |
| `project_id` | string | **yes** | Unique project identifier |
| `project_title` | string | no | Human-readable project name |
| `project_description` | string | no | Free-text project description |
| `recent_conversations` | array[object] | no | Recent agent-user conversation summaries |
| `paper_records` | array[PaperRecord] | no | Papers to extract patterns from |
| `rag_chunks` | array[object] | no | RAG chunk metadata |
| `memory_records` | array[MemoryRecord] | no | Project memories to score |
| `skill_runs` | array[object] | no | Skill execution records |
| `data_contexts` | array[object] | no | Experimental context data |
| `current_project_summary` | string | no | Existing project summary text |

---

## ConsolidationResult JSON Format

```json
{
  "project_id": "proj_cancer_metabolism",
  "schema_version": "1.0",
  "engine_version": "0.1.0",
  "promoted_memories": [...],
  "archived_memories": [...],
  "superseded_memories": [...],
  "new_research_patterns": [...],
  "new_evidence_edges": [...],
  "contradictions_detected": [...],
  "updated_project_summary": "...",
  "recommended_literature_queries": ["mock query: recent advances..."],
  "recommended_user_actions": ["Search for recent clinical trials..."],
  "warnings": [],
  "processing_log": ["[Step 1] Scoring 8 memories...", ...]
}
```

### Field Reference

| Field | Type | Always present | Description |
|-------|------|----------------|-------------|
| `project_id` | string | yes | Project identifier matching input |
| `schema_version` | string | yes | Schema version |
| `engine_version` | string | yes | Engine version |
| `promoted_memories` | array[MemoryRecord] | yes | Memories whose status improved |
| `archived_memories` | array[MemoryRecord] | yes | Memories moved to archived/deprecated |
| `superseded_memories` | array[MemoryRecord] | yes | Memories replaced by newer information |
| `new_research_patterns` | array[ResearchPattern] | yes | Patterns extracted from papers |
| `new_evidence_edges` | array[EvidenceGraphEdge] | yes | Evidence graph edges discovered |
| `contradictions_detected` | array[object] | yes | Contradiction pairs found |
| `updated_project_summary` | string | yes | Consolidated project summary |
| `recommended_literature_queries` | array[string] | yes | Suggested literature search queries |
| `recommended_user_actions` | array[string] | yes | Suggested user actions |
| `warnings` | array[string] | yes | Non-fatal warnings |
| `processing_log` | array[string] | yes | Step-by-step processing log |

---

## Core Field Semantics

### Status Lifecycle

```
                    ┌──────────┐
                    │  active  │ ◄──── promoted
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │  normal  │
                    └────┬─────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
         ┌────▼───┐ ┌────▼────┐ ┌──▼──────────┐
         │archived│ │deprecated│ │ superseded  │
         └────────┘ └─────────┘ └─────────────┘
```

- **active** — Memory is trusted and actively used (score ≥ 0.75).
- **normal** — Memory exists but hasn't reached active confidence (0.45–0.75).
- **archived** — Below active threshold; not surfaced by default but still queryable (0.20–0.45).
- **deprecated** — Too low confidence to be useful; kept for audit trail (< 0.20).
- **superseded** — Explicitly replaced by newer, contradictory information. Never physically deleted.

### archived vs deprecated vs superseded

| Status | Meaning | Can be revived? | Kept in output? |
|--------|---------|----------------|-----------------|
| `archived` | Below relevance threshold, but potentially useful | Yes, if new evidence raises score | Yes, always |
| `deprecated` | Too low confidence, likely noise | Technically yes, but unlikely | Yes, always |
| `superseded` | Replaced by contradictory evidence | No — explicitly replaced | Yes, always |

### Evidence Levels

| Level | Meaning | Example |
|-------|---------|---------|
| L0 | Casual thought, unconfirmed input | "I think lactate is just waste" |
| L1 | User-confirmed project fact | User confirmed: "Yes, HK2 is the target" |
| L2 | From traceable literature/PDF | Paper says: "HIF-1alpha regulates HK2" |
| L3 | From user's experimental data | Experiment: "2-DG reduced ATP by 60%" |
| L4 | Multi-source, used in decisions | Multiple papers + own data agree |
| L5 | Formalized in paper/report/SOP | Published conclusion in a peer-reviewed paper |

### Memory Types

| Type | Meaning |
|------|---------|
| `user_fact` | Fact stated or confirmed by user |
| `project_fact` | Fact about the project itself |
| `paper_evidence` | Evidence extracted from literature |
| `experiment_result` | Result from an experiment |
| `decision` | A project decision made |
| `failure` | A recorded failure/negative result |
| `skill_run` | A skill/tool execution record |
| `data_conclusion` | Conclusion drawn from data analysis |

---

## Memory Scoring Formula

```
final_score = max(0, min(1,
    0.25 × source_confidence
    + 0.20 × user_confirmation
    + 0.20 × project_relevance
    + 0.15 × evidence_support
    + 0.10 × retrieval_usefulness
    + 0.05 × recency
    - 0.20 × contradiction_penalty
    - 0.10 × redundancy_penalty
))
```

### Component Details

| Component | Weight | Source | Range |
|-----------|--------|--------|-------|
| source_confidence | 0.25 | `memory.confidence` field | 0–1 |
| user_confirmation | 0.20 | From memory_type (decision/user_fact → high) | 0–1 |
| project_relevance | 0.20 | `memory.project_relevance` field | 0–1 |
| evidence_support | 0.15 | From evidence_level (L0→0.1, L5→1.0) | 0–1 |
| retrieval_usefulness | 0.10 | Sigmoid of retrieval_count: 1 - exp(-0.3 * n) | 0–1 |
| recency | 0.05 | Exponential decay: 2^(-days / 30) | 0–1 |
| contradiction_penalty | -0.20 per count | Min(1.0, 0.20 × contradiction_count) | 0–1 |
| redundancy_penalty | -0.10 | Placeholder for future dedup | 0–1 |

### Thresholds

| Score Range | Status |
|-------------|--------|
| ≥ 0.75 | active |
| 0.45 – 0.75 | normal |
| 0.20 – 0.45 | archived |
| < 0.20 | deprecated |

---

## Schema Versioning

- Current schema version: `1.0`
- Schema version is included in both `ConsolidationInput` and `ConsolidationResult`
- Schema follows semantic versioning: major bumps for breaking changes, minor bumps for additive changes
- `from_dict()` silently filters unknown fields — forward compatibility is maintained for additive changes
- `to_dict()` never outputs Python objects, datetimes, or Enums — only plain JSON types
