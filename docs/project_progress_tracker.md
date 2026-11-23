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
| Phase 3 | Evidence database and evidence graph construction | Weeks 5–6 | ⚪ Queued | 0 / 5 Modules |
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

## 3. Phase 2 Implementation Checklist (Completed)

```
[ Phase 2 Progress: 7 / 7 Modules Completed - 100% ]
```

- [x] **Module A: Automated Paper Screening & Criteria Evaluator**:
  - 7-dimension criteria evaluation: Topic match, objective/RQ alignment, year window, publication type, methodology presence, empirical outcome presence, explicit inclusion/exclusion rules.
  - Multi-stage screening (`title_abstract` -> `full_text` -> `manual_override`).
  - Decisions categorized as `included`, `excluded`, or `needs_human_review` with confidence scoring and missing-information tracking.
  - Non-destructive human override mechanism with reviewer notes, timestamps, and preserved original decisions.
- [x] **Module B: Legal Open-Access Retrieval & Scientific PDF Processing**:
  - Direct arXiv PDF fetching and OpenAlex open-access resolution.
  - File magic-byte validation (`%PDF-`) and SHA-256 integrity digest computation.
  - User PDF file upload endpoint and storage under `data/fulltext_documents/`.
  - PyMuPDF (`fitz`) scientific document processing with regex-based section demarcation (Abstract, Intro, Related Work, Method, Experiments, Results, Discussion, Limitations, Conclusion, References).
  - Reference section boundary isolation and text-density quality scoring (`is_scanned_ocr`).
- [x] **Module C: Structured Scientific Evidence Extraction**:
  - Zero-fabrication principle: No hallucinated metrics, strict distinction between `full_text` and `abstract_only`.
  - Author-reported vs system-inferred limitation classification.
  - Pluggable extraction backends: Rule-based linguistic/regex extractor, mock extractor for fixtures, LLM extractor with prompt-injection defense.
  - Deep scientific schema: Research objective, methodology components, datasets, evaluation metrics, findings, limitations, future work, contributions, and epistemic uncertainties.
- [x] **Module D: Verifiable Passage Tracking**:
  - Relational passage anchoring linking extracted claims to verbatim text, page number, and section heading.
  - Passage verification workflow: `machine_extracted`, `user_verified`, `flagged_incorrect`, `unsupported_needs_review`.
- [x] **Module E: Relational Database Storage**:
  - SQLite schema extensions: `screening_runs`, `screening_decisions`, `fulltext_documents`, `extraction_runs`, `evidence_records`, `evidence_passages`.
  - Repository layer with transactional integrity.
- [x] **Module F: MCP Tools Exposure**:
  - `screen_research_paper` and `extract_paper_evidence` tools registered on `MCPServer`.
- [x] **Module G: Frontend Screening & Evidence Dashboard**:
  - Phase 2 active indicator on 12-week roadmap sidebar.
  - Screening view with real-time KPI metrics, filter pills, paper cards with criteria evaluation breakdown.
  - Human override controls with reason prompt.
  - Full-text download & PDF upload actions.
  - Evidence inspection modal with tabbed views, verbatim passage highlighting, and passage verification controls.
- [x] **Module H: Automated Tests & Documentation**:
  - 35/35 pytest tests passing with 0 errors (`backend/tests/`).
  - Frontend production build 100% clean (`tsc && vite build`).
  - Complete documentation: `phase2_implementation.md`, `screening_methodology.md`, `evidence_extraction_schema.md`, `pdf_processing.md`, `phase2_api_documentation.md`.

---

## 4. Next Phase: Phase 3 Scope & Roadmap
**Phase 3: Evidence Database and Evidence Graph Construction**
*Deliverables planned for Phase 3 (to begin only after user authorization):*
1. Structured evidence graph database schema.
2. Nodes: Papers, Objectives, Methods, Datasets, Metrics, Findings, Limitations, Passages.
3. Edges: `uses_method`, `evaluated_on`, `claims_finding`, `identifies_limitation`, `supported_by_passage`, `cites`.
4. Graph construction service and deduplication of entities (e.g., standardizing dataset and model names).
5. Interactive graph visualization in the frontend.
6. Traceability queries from claims to source papers.