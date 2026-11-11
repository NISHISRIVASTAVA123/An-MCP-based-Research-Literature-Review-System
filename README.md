# MCP-Based Multi-Agent Framework for Autonomous Scientific Literature Review & Research Gap Assessment

> **Academic Capstone Research Project** | B.Tech Computer Science (Team of 3)  
> **12-Week Roadmap Target**: Autonomous Evidence Graph & Counterevidence Gap Verification System  
> **Current Status**: **Phase 1 Complete (Research Input, Search Strategy & Academic Literature Retrieval)**

---

## 1. Research Overview & Hypothesis

This application investigates the following central research hypothesis:

> *"Does an integrated framework combining explicit counterevidence retrieval, evidence-graph-based claim verification, and coverage-aware research-gap classification reduce the false research-gap rate compared with conventional LLM-based and existing agentic literature-review approaches?"*

### 12-Week Roadmap Status

| Phase | Milestone Description | Status |
|---|---|---|
| **Phase 1** | **Research input, search strategy & academic literature retrieval** | **COMPLETED** |
| Phase 2 | Paper screening & structured evidence extraction | Queued |
| Phase 3 | Structured evidence database & evidence graph construction | Queued |
| Phase 4 | Literature synthesis & baseline research-gap generation | Queued |
| Phase 5 | Explicit counterevidence retrieval | Queued |
| Phase 6 | Evidence-graph-based claim verification | Queued |
| Phase 7 | Coverage-aware research-gap assessment (4-way classification) | Queued |
| Phase 8 | Comprehensive literature review & gap report generator | Queued |
| Phase 9 | Experimental evaluation, ablations & benchmark comparisons | Queued |

---

## 2. Phase 1 Features Delivered

- **Research Input Interface**: Academic request form accepting topic, objective, dynamic research questions, scientific domain, publication timeframe, citation format, inclusion/exclusion criteria, and database targets with full validation.
- **Academic Strategy Generator**: Deterministic concept extraction, academic keyword expansion, synonym decomposition, and database-specific query builder (OpenAlex, Semantic Scholar, Crossref, arXiv).
- **Independent Academic Adapters**:
  - **OpenAlex Works API**: Full bibliographic retrieval, author disambiguation, abstract reconstruction from inverted index, polite pool contact header.
  - **Semantic Scholar Graph API**: Academic citation metadata, open-access PDF resolution, venue tracking, API key support.
  - **Crossref Works API**: Direct DOI resolution, JATS XML abstract cleaning, polite mailto rate-limit optimization.
  - **arXiv Preprints API**: Atom XML feed parser, category tagging, direct open-access PDF extraction.
- **Canonical Normalization**: Standardized `NormalizedPaper` and `PaperSource` models preserving source provenance and external IDs.
- **Hierarchical Deduplication**: Multi-tier duplicate detection (exact DOI -> normalized title + publication year +/- 1 year tolerance) with provenance merging.
- **Relational Persistence**: SQLite (with zero-change PostgreSQL migration readiness via SQLAlchemy 2.0).
- **Official Model Context Protocol (MCP) Server**: Python MCP server exposing tools (`search_openalex`, `search_semantic_scholar`, `search_crossref`, `search_arxiv`, `retrieve_paper_by_doi`, `generate_academic_search_strategy`) for autonomous agents.
- **Academic Frontend Dashboard**: React 19 + TypeScript + Vite dashboard featuring metrics cards, real-time filtering, year range selection, sorting, interactive abstract preview, provenance inspector, CSV & JSON export, and past review reopening.

---

## 3. Quick Start & Execution

### Prerequisites
- Python 3.11+ (Python 3.14 verified)
- Node.js 18+ (v24 verified)

### 3.1 Backend Setup & Startup
```powershell
# 1. Navigate to project root
cd "c:\Users\Nishi\Desktop\MCP based  Research Literature review system"

# 2. Configure environment (optional custom keys)
copy backend\.env.example backend\.env

# 3. Start the FastAPI backend
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
Once started:
- **Interactive API Documentation (Swagger)**: http://127.0.0.1:8000/docs
- **ReDoc API Reference**: http://127.0.0.1:8000/redoc
- **MCP Tools Directory**: http://127.0.0.1:8000/api/mcp/tools
- **Full Application UI** (served directly from backend): http://127.0.0.1:8000/

### 3.2 Frontend Development Server (Optional)
If working on frontend components with hot-module reload:
```powershell
cd frontend
npm run dev
```
Open **http://localhost:5173** (API calls are automatically proxied to port 8000).

---

## 4. Running the Tests

### 4.1 Automated Unit & Integration Tests (Mocked APIs)
```powershell
$env:PYTHONPATH="."
python -m pytest backend/tests -v
```
*Executes all 24 automated test cases across request validation, query generation, metadata normalization, multi-tier deduplication, mocked provider adapters, and REST API endpoints.*

### 4.2 Live Real-World Academic Retrieval Test
```powershell
$env:PYTHONPATH="."
python backend/scripts/live_integration_test.py
```
*Queries live OpenAlex, Semantic Scholar, Crossref, and arXiv APIs over the internet, demonstrating live parsing, rate-limit resilience, normalization, and deduplication.*

---

## 5. Model Context Protocol (MCP) Integration

The project exposes standard MCP tools for autonomous AI agent pair-programming:

```powershell
# Run the MCP server with stdio transport
python -m backend.app.services.mcp.server
```

### Registered MCP Tools:
1. `search_openalex(query, start_year, end_year, limit)`: Searches OpenAlex repository.
2. `search_semantic_scholar(query, start_year, end_year, limit)`: Searches Semantic Scholar graph.
3. `search_crossref(query, start_year, end_year, limit)`: Searches Crossref registry.
4. `search_arxiv(query, start_year, end_year, limit)`: Searches arXiv preprints.
5. `retrieve_paper_by_doi(doi, provider)`: Resolves paper metadata by DOI.
6. `generate_academic_search_strategy(topic, objective, domain, research_questions)`: Generates query combinations.

---

## 6. Project Architecture & Directory Layout

```
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI application & static server
│   │   ├── core/                       # Settings, config, logging
│   │   ├── models/                     # SQLAlchemy 2.0 schema (Requests, Papers, Executions)
│   │   ├── schemas/                    # Pydantic v2 validation models
│   │   ├── services/
│   │   │   ├── planner/                # Concept extractor, keyword expander, query builders
│   │   │   ├── providers/              # OpenAlex, Semantic Scholar, Crossref, arXiv adapters
│   │   │   ├── literature/             # Normalization, deduplication, search orchestrator
│   │   │   ├── mcp/                    # Python MCP server & tools
│   │   │   └── persistence/            # DB engine, session maker, repositories
│   │   └── api/routes/                 # REST endpoints (research, strategy, search, papers, export)
│   ├── tests/                          # 24 pytest test suites
│   ├── scripts/                        # Live API integration test script
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/                 # Academic UI components (Form, Strategy, Dashboard, Modals)
│   │   ├── services/api.ts             # Typed API client
│   │   ├── types/index.ts              # TypeScript domain types
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── docs/                               # Architecture, progress tracker, API documentation
└── README.md
```

---

## 7. Next Phase: Phase 2 Preparation

Phase 1 provides the foundational literature ingestion and deduplication layer. In **Phase 2**, we will implement:
- User-configurable Inclusion/Exclusion screening criteria.
- Automated title/abstract paper screening agent.
- PDF download and full-text section parser (extracting methodology, datasets, findings, and limitations).
- Source passage attribution tracking.

