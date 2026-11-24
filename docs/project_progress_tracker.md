# Research Project Progress & Roadmap Tracker

**Project Title**: An MCP-Based Multi-Agent Framework for Autonomous Scientific Literature Review and Research Gap Assessment  
**Research Team**: 3 B.Tech Computer Science Students  
**Project Duration**: 12 Weeks Academic Research Capstone  
**Central Hypothesis**:
> *"Does an integrated framework combining explicit counterevidence retrieval, evidence-graph-based claim verification, and coverage-aware research-gap classification reduce the false research-gap rate compared with conventional LLM-based and existing agentic literature-review approaches?"*

---

## 1. Overall 12-Week Roadmap Status

| Phase | Milestone Description | Planned Schedule | Status | Deliverables Complete |
|---|---|---|---|---|
| **Phase 1** | **Research input, search strategy, and academic literature retrieval** | **Weeks 1–2** | 🟢 **COMPLETED** | **12 / 12 Subtasks Done (100%)** |
| **Phase 2** | **Paper screening and structured evidence extraction** | **Weeks 3–4** | 🟢 **COMPLETED** | **7 / 7 Modules Done (100%)** |
| **Phase 3** | **Evidence database and evidence graph construction** | **Weeks 5–6** | 🟢 **COMPLETED** | **6 / 6 Modules Done (100%)** |
| Phase 4 | Literature synthesis and baseline research-gap generation | Week 7 | ⚪ Queued | 0 / 6 Modules |
| Phase 5 | Explicit counterevidence retrieval | Week 8 | ⚪ Queued | 0 / 5 Modules |
| Phase 6 | Evidence-graph-based claim verification | Week 9 | ⚪ Queued | 0 / 5 Modules |
| Phase 7 | Coverage-aware research-gap assessment | Week 10 | ⚪ Queued | 0 / 6 Modules |
| Phase 8 | Autonomous comprehensive report generation | Week 11 | ⚪ Queued | 0 / 7 Modules |
| Phase 9 | Experimental evaluation, ablations & benchmarking | Week 12 | ⚪ Queued | 0 / 10 Metrics |

---

## 2. Phase 1 Implementation Summary (Completed)
- **1.1 Workspace & Backend Core**: FastAPI initialization, Pydantic settings, logging, CORS, error middleware.
- **1.2 Database Schema**: SQLAlchemy 2.0 models for Requests, Questions, Strategies, Queries, Papers, Sources, Executions.
- **1.3 Strategy Generator**: Deterministic concept extraction, keywords, synonyms, query builders.
- **1.4 Academic Providers**: OpenAlex, Semantic Scholar, Crossref, and arXiv API clients with rate-limiting and polite headers.
- **1.5 Deduplication**: Canonical `NormalizedPaper` model, multi-tier deduplication.
- **1.6 REST API & MCP Server**: Comprehensive REST endpoints and Model Context Protocol search tools.
- **1.7 Literature Dashboard**: Academic frontend in React 19 + TypeScript + Vite.

---

## 3. Phase 2 Implementation Summary (Completed)
- **2.1 Automated Paper Screening**: 7-dimension criteria evaluation, multi-stage screening (`title_abstract` -> `full_text` -> `manual_override`), confidence scoring, missing-information tracking, human override mechanism.
- **2.2 PDF Processing & Section Extraction**: arXiv download, open-access resolution, SHA-256 digests, PyMuPDF scientific section demarcation.
- **2.3 Structured Evidence Extraction**: Rule-based extractor, mock extractor, LLM extractor, author-reported vs system-inferred limitation classification.
- **2.4 Verifiable Passage Tracking**: Character offset and page/section anchoring.
- **2.5 Relational Storage**: `screening_runs`, `screening_decisions`, `fulltext_documents`, `extraction_runs`, `evidence_records`, `evidence_passages`.

---

## 4. Phase 3 Implementation Checklist (Completed)

```
[ Phase 3 Progress: 6 / 6 Modules Completed - 100% ]
```

- [x] **Module A: Evidence Graph Data Model & Relational Graph Schema**:
  - 14 semantically typed node entities: `RESEARCH_REQUEST`, `RESEARCH_QUESTION`, `RESEARCH_OBJECTIVE`, `PAPER`, `AUTHOR`, `METHOD`, `MODEL`, `DATASET`, `METRIC`, `FINDING`, `CLAIM`, `LIMITATION`, `FUTURE_DIRECTION`, `EVIDENCE_PASSAGE`.
  - Directional semantic relationships: `HAS_QUESTION`, `HAS_OBJECTIVE`, `INCLUDES_PAPER`, `AUTHORED_BY`, `USES_METHOD`, `USES_MODEL`, `USES_DATASET`, `EVALUATED_USING`, `REPORTS_FINDING`, `REPORTS_CLAIM`, `REPORTS_LIMITATION`, `PROPOSES_FUTURE_DIRECTION`, `HAS_EVIDENCE`, `SUPPORTS`.
  - SQLAlchemy models (`GraphNode`, `GraphEdge`, `EntityAlias`, `GraphBuildRun`, `GraphValidationRecord`) with composite uniqueness constraints and high-speed indexing.
- [x] **Module B: Controlled Entity Normalization & Synonym Resolution Engine**:
  - Conservative resolution policy to prevent false scientific entity merges.
  - Curated dictionaries for methods, model families, metrics, and benchmark datasets.
  - Whitespace, hyphen, underscore, and suffix stemming normalizer.
  - Unverified alias queue (`entity_aliases`) with confidence scoring.
  - Manual entity resolution API (`POST /api/evidence-graph/entity-resolution`) with immediate `manual_user_override` propagation.
- [x] **Module C: Idempotent Graph Construction Pipeline**:
  - Deterministic 14-step pipeline in `EvidenceGraphBuilder`.
  - Strict screening exclusion enforcement: non-included papers are strictly omitted from active graph.
  - Zero-fabrication principle: nodes and edges strictly derived from authenticated Phase 1 & 2 records.
  - Deterministic natural keys (`entity_key`, `edge_key`) ensuring 0 duplicate entities on rebuilds.
  - Reproducibility run logging via `GraphBuildRun`.
- [x] **Module D: Graph Integrity Validation Service**:
  - Automated post-build audit checking claim evidence grounding rate, orphan nodes, and unverified aliases.
  - Real-time integrity status: `valid`, `warning`, `error`.
- [x] **Module E: Semantic Graph Query Engine**:
  - 14 parameterized, safe query operations in `EvidenceGraphQueryService` (papers by method/dataset/model, findings by paper, cross-paper limitations, passage support, shared methods/datasets, unsupported claims, paper subgraph).
  - End-to-end claim provenance tracing linking Claim -> Passage -> Paper -> Document -> Run -> Request (`get_claim_provenance_chain`).
- [x] **Module F: REST API Endpoints & 12 MCP Tools**:
  - 10 dedicated REST API endpoints under `/api/.../evidence-graph` and `/api/evidence-graph/...`.
  - 12 Model Context Protocol tools registered on `mcp_server` for autonomous agent reasoning.
- [x] **Module G: Interactive Evidence Graph Frontend**:
  - SVG visual canvas with node clustering, zoom/pan, search, entity type filter pills, floating legend, slide-over inspector drawer, and claim provenance modal.
  - Integrated into step 5 of research workflow and accessible from screening view.
- [x] **Module H: Automated Tests, Live Verification & Documentation**:
  - **53 / 53 automated tests passing** across Phase 1, Phase 2, and Phase 3 (`backend/tests/`).
  - Phase 3 end-to-end live verification script passing with 0 errors (`backend/scripts/phase3_live_test.py`).
  - Clean frontend production build (`tsc && vite build`) in 4.52s.
  - Complete documentation suite: `phase3_implementation.md`, `evidence_graph_schema.md`, `entity_normalization.md`, `graph_construction_pipeline.md`, `evidence_provenance.md`, `graph_query_reference.md`, `phase3_api_documentation.md`.

---

## 5. Next Phase: Phase 4 Scope & Roadmap
**Phase 4: Literature Synthesis and Baseline Research-Gap Generation**
*Deliverables planned for Phase 4 (to begin only after user authorization):*
1. Structured synthesis across evidence graph clusters.
2. Cross-paper method-dataset matrix generation.
3. Baseline LLM-based research gap generator (for subsequent experimental baseline comparison).
4. Evidence-supported gap candidate extraction.
5. Conflict and contradiction identification across findings and limitations.
6. Literature review synthesis dashboard.
