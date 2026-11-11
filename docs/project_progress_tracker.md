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
| Phase 2 | Paper screening and evidence extraction | Weeks 3–4 | ⚪ Queued | 0 / 6 Modules |
| Phase 3 | Evidence database and evidence graph construction | Weeks 5–6 | ⚪ Queued | 0 / 5 Modules |
| Phase 4 | Literature synthesis and baseline research-gap generation | Week 7 | ⚪ Queued | 0 / 6 Modules |
| Phase 5 | Explicit counterevidence retrieval | Week 8 | ⚪ Queued | 0 / 5 Modules |
| Phase 6 | Evidence-graph-based claim verification | Week 9 | ⚪ Queued | 0 / 5 Modules |
| Phase 7 | Coverage-aware research-gap assessment | Week 10 | ⚪ Queued | 0 / 6 Modules |
| Phase 8 | Autonomous comprehensive report generation | Week 11 | ⚪ Queued | 0 / 7 Modules |
| Phase 9 | Experimental evaluation, ablations & benchmarking | Week 12 | ⚪ Queued | 0 / 10 Metrics |

---

## 2. Phase 1 Implementation Checklist

```
[ Phase 1 Progress: 12 / 12 Completed - 100% ]
```

- [x] **1.1 Workspace & Backend Core**: FastAPI initialization, Pydantic settings, logging, CORS, error middleware, static file serving.
- [x] **1.2 Database Schema & Migrations**: SQLAlchemy 2.0 models for Requests, Questions, Strategies, Queries, Papers, Sources, Executions.
- [x] **1.3 Strategy Generator**: Deterministic concept extraction, keywords, synonyms, query combinations, database-specific query builders.
- [x] **1.4 OpenAlex Provider Adapter**: Async client, polite pool header, filter by year, abstract reconstruction from inverted index, pagination.
- [x] **1.5 Semantic Scholar Provider Adapter**: Async client, graph API fields, external IDs, open-access PDF resolution, 429 rate-limit tolerance.
- [x] **1.6 Crossref Provider Adapter**: Async client, query resolution, bibliographic metadata normalization, JATS XML stripping, polite mailto.
- [x] **1.7 arXiv Provider Adapter**: Async client, Atom XML parser, category filter, relevance sorting, PDF link resolution.
- [x] **1.8 Normalization & Deduplication Service**: Canonical `NormalizedPaper` model, multi-tier deduplication (DOI -> Normalized Title + Year -> Authors), provenance tracking.
- [x] **1.9 REST API Endpoints**: Full CRUD for research requests, strategy generation/editing, retrieval execution, paper exploration, CSV/JSON export.
- [x] **1.10 Official Python MCP Server**: `MCPServer` tools exposing academic search, DOI lookup, and normalization for multi-agent workflows.
- [x] **1.11 Frontend User Interface**: Academic UI in React 19 + TypeScript + Vite, research form, strategy inspector, search dashboard, paper table with filters, details modal, and history reopening.
- [x] **1.12 Testing & Verification**: 24/24 Pytest unit & integration tests passing (mocked responses) and manual live integration test script verified against real APIs.

---

## 3. Work Completed Log
- **Phase 1 Complete**: Full end-to-end literature retrieval module developed, integrated, tested, and documented.
- **Automated Test Results**: 24 passed in 3.10s (`test_research_input.py`, `test_strategy_generation.py`, `test_normalization_and_deduplication.py`, `test_providers.py`, `test_api_endpoints.py`).
- **Live Integration Verification**: Real-world retrieval tested against OpenAlex, Crossref, and arXiv, demonstrating live DOI and PDF link extraction.
- **Frontend Production Build**: Clean TypeScript compilation (`tsc --noEmit`) and Vite production bundle generated without errors.

---

## 4. Next Phase: Phase 2 Scope & Roadmap
**Phase 2: Paper screening and evidence extraction**
*Deliverables planned for Phase 2 (to be started only after user authorization):*
1. Inclusion and exclusion criteria evaluation engine.
2. Automated paper screening (Title & Abstract filter agent).
3. Screening decision records with inclusion rationale.
4. PDF download and full-text section extractor (Methodology, Datasets, Results, Limitations, Future Work).
5. Source passage tracking and paragraph attribution.
