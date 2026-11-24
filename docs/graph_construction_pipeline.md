# Evidence Graph Construction Pipeline

## 1. Overview

The `EvidenceGraphBuilder` service implements an idempotent, deterministic 14-step pipeline that transforms raw Phase 1 bibliographic metadata and Phase 2 structured extraction records into an interconnected knowledge graph.

The pipeline ensures:
1. **Screening Gatekeeping**: Papers marked as `excluded` in Phase 2 screening are excluded from the graph.
2. **Deterministic Rebuilds**: The graph can be recomputed at any time without duplicating nodes or edges.
3. **Incremental Synchronization**: Newly extracted papers or updated evidence records can be merged cleanly via `POST /api/research-requests/{id}/evidence-graph/synchronize`.
4. **Reproducibility Tracking**: Every execution creates an immutable `GraphBuildRun` audit record.

---

## 2. 14-Step Construction Sequence

```
1. Research Request Validation
   └── Retrieve ResearchRequest model; abort if invalid.

2. Screening Gatekeeping
   └── Fetch latest Phase 2 ScreeningRun. Filter out all papers marked 'excluded'.
   └── Abort with error if no screening run has been executed.

3. Root Research Request Node
   └── Upsert node with entity_key 'REQUEST:{request_id}'.

4. Research Questions & Objectives
   └── Upsert RESEARCH_QUESTION nodes; create HAS_QUESTION edges.
   └── Upsert RESEARCH_OBJECTIVE nodes; create HAS_OBJECTIVE edges.

5. Screened Paper Subgraphs
   └── For each eligible paper: upsert PAPER node; create INCLUDES_PAPER edge.

6. Authorship Attribution
   └── For each author in paper.authors: upsert AUTHOR node; create AUTHORED_BY edge.

7. Exact Evidence Passages
   └── Ingest verbatim EvidencePassage records from Phase 2 text extraction.
   └── Upsert EVIDENCE_PASSAGE node; create HAS_EVIDENCE edge from paper.

8. Methodologies Ingestion & Normalization
   └── Extract methodology list; normalize via EntityNormalizationService.
   └── Upsert METHOD node; create USES_METHOD edge from paper.

9. Models & Architectures
   └── Extract model/architecture elements; normalize against model family rules.
   └── Upsert MODEL node; create USES_MODEL edge from paper.

10. Benchmark Datasets
    └── Extract dataset mentions; resolve canonical names conservatively.
    └── Upsert DATASET node; create USES_DATASET edge from paper.

11. Evaluation Metrics & Numerical Results
    └── Ingest reported metrics and values (e.g. Accuracy, F1-Score).
    └── Upsert METRIC node; create EVALUATED_USING edge from paper.

12. Empirical Research Findings
    └── Generate deterministic MD5 hash for statement.
    └── Upsert FINDING node; create REPORTS_FINDING edge from paper.

13. Scientific Claims & Evidence Grounding
    └── Upsert CLAIM node; create REPORTS_CLAIM edge from paper.
    └── Create SUPPORTS edge from matching EVIDENCE_PASSAGE to CLAIM and FINDING.

14. Limitations, Future Directions & Integrity Validation
    └── Upsert LIMITATION and FUTURE_DIRECTION nodes.
    └── Link supporting passages via SUPPORTS edges.
    └── Invoke GraphValidationService to audit coverage and log execution statistics.
```

---

## 3. Idempotency and Natural Keys

Every entity and edge in the Evidence Graph derives its primary identity from a deterministic, human-readable composite natural key:

| Object | Natural Key Formula | Example |
|---|---|---|
| Request Node | `REQUEST:{request_id}` | `REQUEST:req-8c8925` |
| Paper Node | `PAPER:{paper_id}` | `PAPER:p1-8c8925` |
| Method Node | `METHOD:{canonical_name.lower()}` | `METHOD:shap` |
| Dataset Node | `DATASET:{canonical_name.lower()}` | `DATASET:liar` |
| Claim Node | `CLAIM:{paper_id}:{md5(claim_text)[:10]}` | `CLAIM:p1-8c8925:3a4b9c1d` |
| Passage Node | `PASSAGE:{evidence_passage_id}` | `PASSAGE:pas-10293` |
| Graph Edge | `{source_node_id}:{REL_TYPE}:{target_node_id}` | `node-p1:USES_METHOD:node-shap` |

When a build run executes:
- If a node with matching `(request_id, entity_key)` exists, its label, properties, and timestamps are updated (`nodes_updated += 1`).
- If no node exists, a new record is inserted (`nodes_added += 1`).
- Edges follow the same uniqueness constraint on `(request_id, edge_key)`.

### Verification Test Result
Re-running the graph builder immediately following a full build results in:
```
Rebuild Run #2: Nodes added = 0, Edges added = 0
Idempotency test passed: 0 duplicate entities generated.
```

---

## 4. Execution Triggers

1. **Full Build (`trigger_type="full_build"`)**:
   - Executed via `POST /api/research-requests/{request_id}/evidence-graph/build` or MCP tool `build_evidence_graph`.
   - Re-evaluates all screening decisions, re-indexes all eligible papers, rebuilds normalization aliases, and triggers validation.
2. **Incremental Synchronization (`trigger_type="incremental_sync"`)**:
   - Executed via `POST /api/research-requests/{request_id}/evidence-graph/synchronize` or MCP tool `synchronize_evidence_graph`.
   - Idempotently ingests newly added or newly extracted papers without disturbing unchanged nodes.
