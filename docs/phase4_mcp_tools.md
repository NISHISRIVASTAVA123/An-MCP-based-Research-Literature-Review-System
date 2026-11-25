# Model Context Protocol (MCP) Tools: Literature Synthesis (Phase 4)

## 1. Overview

Phase 4 registers **12 new official MCP tools**, expanding the autonomous multi-agent toolset of the system to **32 tools total** (Phase 1: 8 tools, Phase 2: 12 tools, Phase 3: 12 tools, Phase 4: 12 tools).

These tools enable LLM agents to autonomously generate multi-paper comparisons, detect literature themes, quantify research trends, generate grounded candidate gaps, inspect evidence provenance, and submit human reviews.

---

## 2. Phase 4 Tool Registry

| Tool Name | Parameters | Description |
|---|---|---|
| `generate_literature_synthesis` | `request_id`, `paper_ids`, `config` | Runs full literature synthesis pipeline and candidate gap generation. |
| `get_literature_synthesis` | `request_id`, `run_id` | Retrieves structured and narrative synthesis for a run. |
| `get_paper_comparison_matrix` | `request_id`, `method`, `dataset`, `model`, `year` | Constructs dynamic comparative matrix with optional dimensional filters. |
| `identify_research_themes` | `request_id` | Discovers recurring methodological, empirical, and limitation themes. |
| `analyze_methodology_trends` | `request_id` | Computes methodology frequencies and cross-combinations across papers. |
| `analyze_dataset_trends` | `request_id` | Analyzes benchmark dataset distributions and method-dataset intersections. |
| `analyze_research_trends` | `request_id` | Comprehensive empirical, evaluation, and temporal publication trends. |
| `generate_candidate_research_gaps` | `request_id`, `synthesis_run_id` | Formulates evidence-grounded candidate gaps across 10 categories. |
| `get_candidate_gap_details` | `gap_id` | Retrieves full gap description, rationale, assumptions, and validation queries. |
| `get_candidate_gap_evidence` | `gap_id` | Retrieves verbatim evidence passages and grounding links backing a candidate gap. |
| `update_candidate_gap_review` | `gap_id`, `action`, `reviewer`, `comment`, `revised_title`, `revised_category` | Updates review status (accept, reject, edit, request_more_evidence) with audit log. |
| `get_synthesis_history` | `request_id` | Lists past synthesis runs with version metadata for reproducibility. |

---

## 3. Autonomous Agent Invocation Example

An autonomous synthesis agent can invoke:
```json
{
  "name": "generate_candidate_research_gaps",
  "arguments": {
    "request_id": "req-001"
  }
}
```
And inspect the exact evidence passage for any returned gap:
```json
{
  "name": "get_candidate_gap_evidence",
  "arguments": {
    "gap_id": "gap-uuid-4567"
  }
}
```
