# Learning Engine — ResearchOS Integration Guide

## Overview

This document describes how the Learning Engine will be merged into the main
ResearchOS backend. The engine is designed as a pluggable module that can be
integrated in three modes:

1. **Backend module** — direct Python call from ResearchOS service code
2. **Skill** — invoked from the ResearchOS agent runtime as a skill
3. **Background job** — scheduled or event-triggered consolidation

---

## Mode 1: Backend Module

The simplest integration. The main ResearchOS backend imports `run_sleep_cycle`
and calls it with data collected from its own stores.

### Minimal Calling Code

```python
from researchos_learning_engine.domain.schemas import (
    ConsolidationInput,
    MemoryRecord,
    PaperRecord,
)
from researchos_learning_engine.interfaces.python_api import run_sleep_cycle

# Collect data from ResearchOS stores
input_data = ConsolidationInput(
    project_id="proj_123",
    project_title="Cancer Metabolism Study",
    project_description="...",
    paper_records=[...],       # from paper/PDF storage
    memory_records=[...],      # from agent memory / project memory
    current_project_summary="...",  # from project metadata
)

# Run consolidation (blocking)
result = run_sleep_cycle(input_data)

# Write results back to ResearchOS stores
write_promoted_memories(result.promoted_memories)
write_archived_memories(result.archived_memories)
write_research_patterns(result.new_research_patterns)
write_evidence_edges(result.new_evidence_edges)
update_project_summary(result.updated_project_summary)
queue_literature_searches(result.recommended_literature_queries)
```

### Adapter Replacement

**LLM adapter** — replace MockLLM with the main project's LLM client:

```python
from researchos_learning_engine.adapters.llm.base import LLMAdapter
from researchos_learning_engine.application.consolidation_service import (
    ConsolidationService,
)

class ResearchOSLLMAdapter:
    """Wraps the main ResearchOS Minimax/OpenAI/Claude client."""

    def __init__(self, client):
        self._client = client

    def generate(self, system_prompt, user_message, temperature=0.7, max_tokens=2048):
        response = self._client.chat(system=system_prompt, messages=[{"role": "user", "content": user_message}])
        return response.text

    def generate_json(self, system_prompt, user_message, temperature=0.3, max_tokens=4096):
        response = self._client.chat(
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            response_format="json",
        )
        return json.loads(response.text)

# Usage
llm = ResearchOSLLMAdapter(researchos_client)
service = ConsolidationService(llm=llm)
result = service.run(input_data)
```

**Storage adapter** — replace JSON storage with ResearchOS database:

```python
from researchos_learning_engine.adapters.storage.base import StorageAdapter

class ResearchOSDatabaseAdapter:
    """Wraps the main ResearchOS database for Learning Engine storage."""

    def save_memory(self, memory):
        db.execute(
            "INSERT INTO memories (id, project_id, data) VALUES (%s, %s, %s) "
            "ON CONFLICT (id) DO UPDATE SET data = %s",
            memory.memory_id, memory.project_id, memory.to_dict(), memory.to_dict(),
        )

    def load_memories(self, project_id=None):
        if project_id:
            rows = db.query("SELECT data FROM memories WHERE project_id = %s", project_id)
        else:
            rows = db.query("SELECT data FROM memories")
        return [MemoryRecord.from_dict(r["data"]) for r in rows]

    # ... other methods follow the same pattern
```

---

## Mode 2: Skill Invocation

The Learning Engine can be exposed as a ResearchOS skill. The skill handler
collects data from the agent's context and calls `run_sleep_cycle`.

### Skill Interface

```python
# researchos/skills/consolidate_memories.py

@skill(
    name="consolidate_memories",
    description="Run memory consolidation to score, archive, and recommend",
    parameters={
        "project_id": {"type": "string", "description": "Project ID to consolidate"},
    },
)
async def consolidate_memories_skill(agent, project_id: str):
    # 1. Collect data from agent's current context
    memories = await agent.memory.list(project_id=project_id)
    papers = await agent.paper_store.list(project_id=project_id)
    summary = await agent.project.get_summary(project_id=project_id)
    conversations = await agent.conversation_log.list(project_id=project_id)
    skill_runs = await agent.skill_log.list(project_id=project_id)

    # 2. Build ConsolidationInput
    input_data = ConsolidationInput(
        project_id=project_id,
        project_title=project.title,
        paper_records=[paper_to_record(p) for p in papers],
        memory_records=[memory_to_record(m) for m in memories],
        current_project_summary=summary,
        recent_conversations=conversations,
        skill_runs=skill_runs,
    )

    # 3. Run consolidation
    result = run_sleep_cycle(input_data)

    # 4. Apply results back to agent state
    for mem in result.promoted_memories:
        await agent.memory.update_score(mem.memory_id, mem.health_score, mem.status)

    for mem in result.archived_memories:
        await agent.memory.archive(mem.memory_id)

    for mem in result.superseded_memories:
        await agent.memory.supersede(mem.memory_id)

    for pattern in result.new_research_patterns:
        await agent.pattern_library.add(pattern)

    for edge in result.new_evidence_edges:
        await agent.evidence_graph.add_edge(edge)

    if result.updated_project_summary:
        await agent.project.update_summary(project_id, result.updated_project_summary)

    for query in result.recommended_literature_queries:
        await agent.suggest_action("literature_search", query=query)

    return result
```

---

## Mode 3: Background Job

For periodic or event-driven consolidation, the engine runs as an async
background job. This is the preferred mode for unattended sleep-cycle
consolidation.

### Job Configuration

```python
# researchos/jobs/consolidation_job.py

from datetime import datetime, timedelta
from researchos_learning_engine.interfaces.python_api import run_sleep_cycle

JOB_INTERVAL = timedelta(hours=6)  # Run every 6 hours

async def run_consolidation_job():
    """Periodic consolidation for all active projects."""
    active_projects = await db.query("SELECT project_id FROM projects WHERE status = 'active'")

    for project_row in active_projects:
        project_id = project_row["project_id"]

        # Collect data
        input_data = await build_input(project_id)

        # Run (consider running in thread pool for CPU-bound work)
        result = await asyncio.to_thread(run_sleep_cycle, input_data)

        # Persist results
        await persist_result(project_id, result)
```

### Event-Triggered Consolidation

Consolidation can also be triggered by specific events:

- After a literature search completes (new paper evidence)
- After a user conversation ends (new user facts/decisions)
- After an experiment result is recorded (new experimental evidence)
- On demand via API/webhook

---

## What ResearchOS Should Pass In

| Data Source | ResearchOS Store | Maps To |
|-------------|-----------------|---------|
| Project metadata | `projects` table | `project_id`, `project_title`, `project_description` |
| Current summary | `projects.summary` | `current_project_summary` |
| Agent memories | `agent_memories` | `memory_records` |
| Paper references | `paper_store` / `pdf_store` | `paper_records` |
| RAG search results | `vector_store` query results | `rag_chunks` |
| Conversation logs | `conversation_log` | `recent_conversations` |
| Skill executions | `skill_log` | `skill_runs` |
| Experimental data | `experiment_store` / `data_store` | `data_contexts` |

## What ResearchOS Should Write Back

| Result Field | Target Store | Action |
|-------------|-------------|--------|
| `promoted_memories` | `agent_memories` | Update score, status, score_breakdown |
| `archived_memories` | `agent_memories` | Set status=archived, update score |
| `superseded_memories` | `agent_memories` | Set status=superseded, link to replacement |
| `new_research_patterns` | `pattern_library` | Insert new patterns for retrieval |
| `new_evidence_edges` | `evidence_graph` | Insert edges; update RAG metadata |
| `updated_project_summary` | `projects.summary` | Replace project summary |
| `recommended_literature_queries` | `action_queue` | Enqueue literature search tasks |
| `recommended_user_actions` | `notification_queue` | Present to user as suggestions |
| `contradictions_detected` | `project_alerts` | Flag for user review |

---

## Architecture Boundary Rules

When merging, preserve these rules:

1. **CLI must remain thin** — CLI only parses args, calls `run_sleep_cycle`, writes output. No business logic.
2. **Application services must not import adapters** — services receive adapters via constructor injection.
3. **Domain must not import adapters** — domain layer is pure data + business rules.
4. **Adapter implementations must be swappable** — any `LLMAdapter` or `StorageAdapter` protocol implementor works.
5. **No API keys in code** — keys come from `.env` or ResearchOS secrets manager.
6. **No hardcoded file paths** — all paths are passed in or relative to workspace root.
7. **Schema changes require version bump** — increment `SCHEMA_VERSION` in `domain/constants.py`.
