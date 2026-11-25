# Synthesis Reproducibility & Versioning (Phase 4)

## 1. Principles of Academic Reproducibility

A central requirement of the research framework is that all synthesis runs, theme clusters, and candidate research gaps must be **fully reproducible, auditable, and version-tracked**.

---

## 2. Versioning Architecture

Each execution of the literature synthesis pipeline creates a persistent `SynthesisRun` record capturing:

1. **Input State Snapshot**:
   - `research_request_id`: Primary research topic and objective identifier.
   - `selected_paper_ids`: Explicit list of paper primary keys included in the run.
   - `evidence_graph_version`: SHA/UUID version hash of the active Phase 3 Evidence Graph build.
2. **Model & Configuration Provenance**:
   - `prompt_version`: Version string of the synthesis prompt template (e.g. `v1.0-academic`).
   - `model_provider`: LLM or deterministic backend provider (e.g. `groq`, `openai`, `rule_deterministic`).
   - `model_name`: Specific model checkpoint used for execution (e.g. `llama-3.3-70b-versatile`, `deterministic-engine`).
   - `synthesis_configuration`: Parameter dictionary storing thresholds (e.g. `min_paper_threshold: 1`).
3. **Execution Metadata**:
   - `execution_started_at` & `execution_completed_at`: High-precision ISO timestamps.
   - `status`: Execution state machine (`pending`, `identifying_themes`, `analyzing_patterns`, `generating_narrative`, `formulating_gaps`, `completed`, `failed`).
   - `error_details`: Exception trace if a stage fails.

---

## 3. Historical Run Comparison

The `SynthesisReviewService.compare_synthesis_runs(run_id_a, run_id_b)` endpoint enables direct side-by-side comparison between runs:
- Highlights newly emerged vs. lost themes.
- Compares pattern shifts between different model checkpoints or time windows.
- Tracks evolution of candidate gaps as new literature is incorporated.
