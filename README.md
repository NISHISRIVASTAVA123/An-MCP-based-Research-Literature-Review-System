# MCP-Based Multi-Agent Framework for Autonomous Scientific Literature Review & Research Gap Assessment

> **Academic Capstone Research Project** | B.Tech Computer Science (Team of 3)  
> **12-Week Roadmap Target**: Autonomous Evidence Graph & Counterevidence Gap Verification System  
> **Current Status**: **Phase 1 & Phase 2 Complete (Retrieval, Screening & Structured Evidence Extraction)**

---

## 1. Research Overview & Hypothesis

This application investigates the following central research hypothesis:

> *"Does an integrated framework combining explicit counterevidence retrieval, evidence-graph-based claim verification, and coverage-aware research-gap classification reduce the false research-gap rate compared with conventional LLM-based and existing agentic literature-review approaches?"*

### 12-Week Roadmap Status

| Phase | Milestone Description | Status |
|---|---|---|
| **Phase 1** | **Research input, search strategy & academic literature retrieval** | 🟢 **COMPLETED** |
| **Phase 2** | **Paper screening and structured evidence extraction** | 🟢 **COMPLETED** |
| Phase 3 | Structured evidence database & evidence graph construction | ⚪ Queued |
| Phase 4 | Literature synthesis & baseline research-gap generation | ⚪ Queued |
| Phase 5 | Explicit counterevidence retrieval | ⚪ Queued |
| Phase 6 | Evidence-graph-based claim verification | ⚪ Queued |
| Phase 7 | Coverage-aware research-gap assessment (4-way classification) | ⚪ Queued |
| Phase 8 | Comprehensive literature review & gap report generator | ⚪ Queued |
| Phase 9 | Experimental evaluation, ablations & benchmark comparisons | ⚪ Queued |

---

## 2. Features Delivered (Phases 1 & 2)

### Phase 1: Literature Retrieval & Corpus Management
- **Research Input Interface**: Academic request form accepting topic, objective, dynamic research questions, scientific domain, publication timeframe, citation format, inclusion/exclusion criteria, and database targets with full validation.
- **Academic Strategy Generator**: Deterministic concept extraction, academic keyword expansion, synonym decomposition, and database-specific query builder (OpenAlex, Semantic Scholar, Crossref, arXiv).
- **Independent Academic Adapters**: OpenAlex Works API, Semantic Scholar Graph API, Crossref Works API, arXiv Preprints API.
- **Hierarchical Deduplication**: Multi-tier duplicate detection (exact DOI -> normalized title + publication year +/- 1 year tolerance) with provenance merging.
- **Relational Persistence**: SQLite database initialized with SQLAlchemy 2.0 ORM.

### Phase 2: Paper Screening & Evidence Extraction
- **Automated Multi-Stage Paper Screening**: 7-dimension criteria evaluator testing domain scope, timeframe, publication venue/type, methodology relevance, and empirical outcome presence.
- **Non-Destructive Human Overrides**: Complete audit trail preserving automated decisions, reviewer notes, and timestamps.
- **Legal Open-Access & arXiv Full-Text Retrieval**: Automated PDF fetching with magic-byte validation, cryptographic SHA-256 integrity, and user manual PDF upload support.
- **PyMuPDF Scientific Section Parsing**: Robust layout parser segmenting Abstract, Intro, Methodology, Experiments, Results, Discussion, Limitations, and isolating References.
- **Structured Evidence Extraction (Zero-Fabrication Principle)**: Granular extraction of objectives, methodology, datasets, evaluation metrics, findings, limitations, and epistemic uncertainties.
- **Verifiable Passage Tracking**: Source anchoring mapping every extracted scientific claim to a verbatim text passage, page number, and section heading with researcher verification workflow.
- **Model Context Protocol (MCP) Tools**: Native `screen_research_paper` and `extract_paper_evidence` tools.
- **Interactive UI**: Screening dashboard with real-time KPI metrics, criteria inspection, PDF upload, override controls, and tabbed evidence explorer.

---

## 3. Quick Start & Execution

### Prerequisites
- Python 3.11+ (Python 3.14 verified)
- Node.js 18+ (v24 verified)

### 3.1 Backend Setup & Startup
```powershell
# 1. Navigate to project root
cd "c:\Users\Nishi\Desktop\MCP based  Research Literature review system"

# 2. Start the FastAPI backend
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
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

### 4.1 Automated Test Suite
```powershell
$env:PYTHONPATH="."
python -m pytest backend/tests -v
```
*Executes all 35 automated test cases across research input, query generation, deduplication, mocked providers, PDF layout parsing, rule-based evidence extraction, and Phase 2 API endpoints.*

### 4.2 Frontend Production Build
```powershell
cd frontend
npm run build
```
*Verifies 100% clean TypeScript compilation and bundles production assets into `dist/`.*

---

## 5. Model Context Protocol (MCP) Integration

The server provides a native Model Context Protocol (MCP) server compatible with Claude Desktop and external LLM agents:

```json
{
  "mcpServers": {
    "academic-literature-reviewer": {
      "command": "python",
      "args": ["-m", "backend.app.services.mcp.server"],
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

### Available Tools:
1. `search_openalex`: Query OpenAlex for scientific works.
2. `search_semantic_scholar`: Query Semantic Scholar Graph API.
3. `search_crossref`: Query Crossref for works and DOI metadata.
4. `search_arxiv`: Query arXiv for preprints.
5. `retrieve_paper_by_doi`: Resolve DOI to canonical paper metadata.
6. `generate_academic_search_strategy`: Decompose research topic into boolean search queries.
7. `screen_research_paper`: Screen a paper against research scope and criteria.
8. `extract_paper_evidence`: Extract structured findings, metrics, limitations, and verbatim passages.
