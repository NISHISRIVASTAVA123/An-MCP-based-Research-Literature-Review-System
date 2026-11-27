# MCP-Based Multi-Agent Framework for Autonomous Scientific Literature Review & Research Gap Assessment

> **Academic Capstone Research Project** | B.Tech Computer Science (Team of 3)  
> **12-Week Roadmap Target**: Autonomous Evidence Graph & Counterevidence Gap Verification System  
> **Current Status**: **Phases 1 through 5 Complete (Retrieval, Screening, Evidence Extraction, Evidence Graph Construction, Literature Synthesis / Gap Generation, & Explicit Counterevidence Retrieval)**

### Phase 5: Explicit Counterevidence Retrieval & Evidence Traceability
- **Candidate Gap Decomposition**: Breaks high-level candidate gaps into 3–6 atomic empirical sub-claims (`unexplored_problem`, `missing_methodology`, `missing_dataset_evaluation`, `untested_assumptions`).
- **Adversarial Multi-Angle Query Formulation**: Formulates targeted queries across 4 categories (Direct Counter, Methodology Application, Synonym Expansion, Newer Publications) designed to retrieve contradictory findings.
- **Academic Retrieval & Provenance Segregation**: Concurrently queries OpenAlex, Semantic Scholar, Crossref, and arXiv; deduplicates against the existing corpus and isolates newly discovered papers (`discovery_tag="counterevidence_discovered"`).
- **Strict Evidence Hierarchy & Relevance Classification**: 5-tier classification (`direct_counterevidence`, `partial_counterevidence`, `related_evidence`, `not_relevant`, `insufficient_information`). Enforces Level 1 (Full-Text) ground truth for authoritative direct counterevidence and flags abstract-only evidence.
- **Traceable Source Passage Anchoring**: Extracts verbatim quotes, page coordinates, and section headings with complete verification status.
- **Gap Resilience Impact Aggregator**: Evaluates balance of evidence to assign an impact assessment (`strongly_challenged` through `unchallenged`) and list remaining unresolved sub-claims.
- **Human Auditor Review Workflow**: Complete UI review controls with override capability, reviewer rationale notes, and automatic profile recalculation.
- **7 New Phase 5 MCP Tools**: Expands multi-agent tool suite to 39 tools total.
- **Full Phase 1–5 Test Suite**: 67 automated regression tests passing with zero failures.

---

## 1. Research Overview & Hypothesis

This application investigates the following central research hypothesis:

> *"Does an integrated framework combining explicit counterevidence retrieval, evidence-graph-based claim verification, and coverage-aware research-gap classification reduce the false research-gap rate compared with conventional LLM-based and existing agentic literature-review approaches?"*

### 12-Week Roadmap Status

| Phase | Milestone Description | Status |
|---|---|---|
| **Phase 1** | **Research input, search strategy & academic literature retrieval** | 🟢 **COMPLETED** |
| **Phase 2** | **Paper screening and structured evidence extraction** | 🟢 **COMPLETED** |
| **Phase 3** | **Structured evidence database & evidence graph construction** | 🟢 **COMPLETED** |
| **Phase 4** | **Literature synthesis & baseline candidate research-gap generation** | 🟢 **COMPLETED** |
| **Phase 5** | **Explicit counterevidence retrieval & evidence traceability** | 🟢 **COMPLETED** |
| Phase 6 | Evidence-graph-based claim verification | ⚪ Queued |
| Phase 7 | Coverage-aware research-gap assessment (4-way classification) | ⚪ Queued |
| Phase 8 | Comprehensive literature review & gap report generator | ⚪ Queued |
| Phase 9 | Experimental evaluation, ablations & benchmark comparisons | ⚪ Queued |

### Phase 5: Explicit Counterevidence Retrieval & Evidence Traceability
- **Candidate Gap Decomposition**: Breaks high-level candidate gaps into 3–6 atomic empirical sub-claims (`unexplored_problem`, `missing_methodology`, `missing_dataset_evaluation`, `untested_assumptions`).
- **Adversarial Multi-Angle Query Formulation**: Formulates targeted queries across 4 categories (Direct Counter, Methodology Application, Synonym Expansion, Newer Publications) designed to retrieve contradictory findings.
- **Academic Retrieval & Provenance Segregation**: Concurrently queries OpenAlex, Semantic Scholar, Crossref, and arXiv; deduplicates against the existing corpus and isolates newly discovered papers (`discovery_tag="counterevidence_discovered"`).
- **Strict Evidence Hierarchy & Relevance Classification**: 5-tier classification (`direct_counterevidence`, `partial_counterevidence`, `related_evidence`, `not_relevant`, `insufficient_information`). Enforces Level 1 (Full-Text) ground truth for authoritative direct counterevidence and flags abstract-only evidence.
- **Traceable Source Passage Anchoring**: Extracts verbatim quotes, page coordinates, and section headings with complete verification status.
- **Gap Resilience Impact Aggregator**: Evaluates balance of evidence to assign an impact assessment (`strongly_challenged` through `unchallenged`) and list remaining unresolved sub-claims.
- **Human Auditor Review Workflow**: Complete UI review controls with override capability, reviewer rationale notes, and automatic profile recalculation.
- **7 New Phase 5 MCP Tools**: Expands multi-agent tool suite to 39 tools total.
- **Full Phase 1–5 Test Suite**: 67 automated regression tests passing with zero failures.

---

## 2. Features Delivered Across Phases

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

### Phase 3: Evidence Database & Evidence Graph Construction
- **Semantic Graph Data Model**: 14 strictly typed node entities (`PAPER`, `AUTHOR`, `RESEARCH_QUESTION`, `RESEARCH_OBJECTIVE`, `METHOD`, `MODEL`, `DATASET`, `METRIC`, `FINDING`, `CLAIM`, `LIMITATION`, `FUTURE_DIRECTION`, `EVIDENCE_PASSAGE`, `RESEARCH_REQUEST`) and typed directional relationships (`AUTHORED_BY`, `USES_METHOD`, `USES_MODEL`, `EVALUATED_ON`, `REPORTS_FINDING`, `REPORTS_LIMITATION`, `SUPPORTS`, `ADDRESSES_QUESTION`, etc.).
- **Hybrid Relational Graph Storage**: Indexed SQL tables (`graph_nodes`, `graph_edges`) delivering ACID compliance, sub-millisecond graph queries, and zero-daemon deployment portability.
- **Conservative Entity Normalization**: Normalization engine with curated domain dictionaries (Methods, Models, Metrics, Datasets), space/hyphen/case-insensitive matching, and human override registry.
- **Idempotent 14-Step Graph Construction Pipeline**: Pipeline that strictly enforces Phase 2 screening gatekeeping (omitting excluded papers), creates cross-paper shared entities, and establishes bidirectional `SUPPORTS` grounding between claims/findings and verbatim evidence passages.
- **Graph Integrity Validation Service**: Automated audits reporting Claim-to-Evidence Grounding Rate, orphan nodes, and unverified aliases with structured `PASS`/`WARNING`/`FAIL` metrics.
- **14 Predefined Safe Queries & Provenance Tracing**: Complete API and service queries including multi-paper claim consensus, solitary claims, cross-paper dataset evaluations, and end-to-end claim provenance traversal (`Claim -> Evidence Passage -> Paper -> Section -> Page`).
- **Interactive SVG Visual Graph Interface**: React 19 visual canvas with force-directed physics, zoom/pan controls, dynamic node-type color coding, connected-component clustering, node inspection drawer, live claim provenance modal, and graph build trigger modal.
- **12 Phase 3 Model Context Protocol (MCP) Tools**: Total 20 autonomous tools exposed to agentic frameworks (Claude Desktop, Antigravity, LLM agents).

### Phase 4: Literature Synthesis & Baseline Candidate Research-Gap Generation
- **Dynamic Paper Comparison Matrix**: 13-dimensional comparative synthesis table across eligible papers with "Not reported" defaults and instant export to JSON, CSV, and GitHub Markdown.
- **Recurring Research Theme Identification**: Automated clustering of methodological frameworks, empirical benchmark testbeds, and author-reported limitation themes with explicit sample size denominators.
- **Quantified Pattern & Trend Analysis**: Frequencies and distributions for methodologies, models, datasets, evaluation metrics, and publication year trajectories with statistical honesty.
- **Publication-Ready Academic Narrative Synthesis**: Structured 9-section synthesis covering executive summary, methodology landscape, benchmark datasets, evaluation metrics, convergent findings, contextual divergence, limitations, future work, and scope boundaries.
- **Evidence-Grounded Candidate Gap Generation**: Formulates candidate research gaps across 10 academic gap categories (`empirical_gap`, `methodological_gap`, `generalisation_gap`, `evaluation_gap`, etc.) with preliminary confidence scoring (0.60–0.88).
- **Strict Zero-Fabrication & Reference Validation**: Validates all referenced paper and passage IDs against SQLite database before persistence; strictly connects every gap to source literature via `GapEvidenceLink`.
- **Phase 5 Forward-Compatible Validation Queries**: Automated counterevidence query formulations designed for downstream refutation retrieval.
- **Human Review Workspace**: Full review lifecycle (accept, reject, edit, request evidence) with an immutable audit log (`HumanReviewRecord`) and slide-over gap detail drawer.
- **12 New Phase 4 Model Context Protocol (MCP) Tools**: Expands multi-agent tool suite to 32 tools total.

### Phase 5: Explicit Counterevidence Retrieval & Evidence Traceability
- **Candidate Gap Decomposition**: Breaks high-level candidate gaps into 3–6 atomic empirical sub-claims (`unexplored_problem`, `missing_methodology`, `missing_dataset_evaluation`, `untested_assumptions`).
- **Adversarial Multi-Angle Query Formulation**: Formulates targeted queries across 4 categories (Direct Counter, Methodology Application, Synonym Expansion, Newer Publications) designed to retrieve contradictory findings.
- **Academic Retrieval & Provenance Segregation**: Concurrently queries OpenAlex, Semantic Scholar, Crossref, and arXiv; deduplicates against the existing corpus and isolates newly discovered papers (`discovery_tag="counterevidence_discovered"`).
- **Strict Evidence Hierarchy & Relevance Classification**: 5-tier classification (`direct_counterevidence`, `partial_counterevidence`, `related_evidence`, `not_relevant`, `insufficient_information`). Enforces Level 1 (Full-Text) ground truth for authoritative direct counterevidence and flags abstract-only evidence.
- **Traceable Source Passage Anchoring**: Extracts verbatim quotes, page coordinates, and section headings with complete verification status.
- **Gap Resilience Impact Aggregator**: Evaluates balance of evidence to assign an impact assessment (`strongly_challenged` through `unchallenged`) and list remaining unresolved sub-claims.
- **Human Auditor Review Workflow**: Complete UI review controls with override capability, reviewer rationale notes, and automatic profile recalculation.
- **7 New Phase 5 MCP Tools**: Expands multi-agent tool suite to 39 tools total.
- **Full Phase 1–5 Test Suite**: 67 automated regression tests passing with zero failures.

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

### Phase 5: Explicit Counterevidence Retrieval & Evidence Traceability
- **Candidate Gap Decomposition**: Breaks high-level candidate gaps into 3–6 atomic empirical sub-claims (`unexplored_problem`, `missing_methodology`, `missing_dataset_evaluation`, `untested_assumptions`).
- **Adversarial Multi-Angle Query Formulation**: Formulates targeted queries across 4 categories (Direct Counter, Methodology Application, Synonym Expansion, Newer Publications) designed to retrieve contradictory findings.
- **Academic Retrieval & Provenance Segregation**: Concurrently queries OpenAlex, Semantic Scholar, Crossref, and arXiv; deduplicates against the existing corpus and isolates newly discovered papers (`discovery_tag="counterevidence_discovered"`).
- **Strict Evidence Hierarchy & Relevance Classification**: 5-tier classification (`direct_counterevidence`, `partial_counterevidence`, `related_evidence`, `not_relevant`, `insufficient_information`). Enforces Level 1 (Full-Text) ground truth for authoritative direct counterevidence and flags abstract-only evidence.
- **Traceable Source Passage Anchoring**: Extracts verbatim quotes, page coordinates, and section headings with complete verification status.
- **Gap Resilience Impact Aggregator**: Evaluates balance of evidence to assign an impact assessment (`strongly_challenged` through `unchallenged`) and list remaining unresolved sub-claims.
- **Human Auditor Review Workflow**: Complete UI review controls with override capability, reviewer rationale notes, and automatic profile recalculation.
- **7 New Phase 5 MCP Tools**: Expands multi-agent tool suite to 39 tools total.
- **Full Phase 1–5 Test Suite**: 67 automated regression tests passing with zero failures.

---

## 4. Running the Tests & Live Verifications

### 4.1 Automated Test Suite
```powershell
backend/env/Scripts/pytest.exe -v
```
*Executes all 62 automated test cases across 17 test modules covering research input, query generation, deduplication, mocked academic providers, PDF layout parsing, rule-based evidence extraction, entity normalization, graph construction, graph queries, comparison matrices, theme clustering, pattern analysis, candidate gap generation, and Phase 1-4 REST API & MCP endpoints.*

### 4.2 Live End-to-End Verification Scripts
```powershell
# Phase 3 Live Graph Verification:
backend/env/Scripts/python.exe backend/scripts/phase3_live_test.py

# Phase 4 Live Synthesis & Candidate Gap Verification:
backend/env/Scripts/python.exe backend/scripts/phase4_live_test.py
```
*Simulates a complete real-world workflow from request creation, paper screening, multi-dimensional evidence extraction, graph construction, comparison matrix generation, theme clustering, trend analysis, narrative review synthesis, candidate gap formulation, and human review acceptance.*

### 4.3 Frontend Production Build
```powershell
cd frontend
npm run build
```
*Verifies 100% clean TypeScript compilation and bundles production assets into `dist/` in < 3s.*

### Phase 5: Explicit Counterevidence Retrieval & Evidence Traceability
- **Candidate Gap Decomposition**: Breaks high-level candidate gaps into 3–6 atomic empirical sub-claims (`unexplored_problem`, `missing_methodology`, `missing_dataset_evaluation`, `untested_assumptions`).
- **Adversarial Multi-Angle Query Formulation**: Formulates targeted queries across 4 categories (Direct Counter, Methodology Application, Synonym Expansion, Newer Publications) designed to retrieve contradictory findings.
- **Academic Retrieval & Provenance Segregation**: Concurrently queries OpenAlex, Semantic Scholar, Crossref, and arXiv; deduplicates against the existing corpus and isolates newly discovered papers (`discovery_tag="counterevidence_discovered"`).
- **Strict Evidence Hierarchy & Relevance Classification**: 5-tier classification (`direct_counterevidence`, `partial_counterevidence`, `related_evidence`, `not_relevant`, `insufficient_information`). Enforces Level 1 (Full-Text) ground truth for authoritative direct counterevidence and flags abstract-only evidence.
- **Traceable Source Passage Anchoring**: Extracts verbatim quotes, page coordinates, and section headings with complete verification status.
- **Gap Resilience Impact Aggregator**: Evaluates balance of evidence to assign an impact assessment (`strongly_challenged` through `unchallenged`) and list remaining unresolved sub-claims.
- **Human Auditor Review Workflow**: Complete UI review controls with override capability, reviewer rationale notes, and automatic profile recalculation.
- **7 New Phase 5 MCP Tools**: Expands multi-agent tool suite to 39 tools total.
- **Full Phase 1–5 Test Suite**: 67 automated regression tests passing with zero failures.

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

### Available Tools (32 Total):

#### Phase 1: Retrieval & Strategy (6 Tools)
1. `search_openalex`: Query OpenAlex for scientific works.
2. `search_semantic_scholar`: Query Semantic Scholar Graph API.
3. `search_crossref`: Query Crossref for works and DOI metadata.
4. `search_arxiv`: Query arXiv for preprints.
5. `retrieve_paper_by_doi`: Resolve DOI to canonical paper metadata.
6. `generate_academic_search_strategy`: Decompose research topic into boolean search queries.

#### Phase 2: Screening & Extraction (2 Tools)
7. `screen_research_paper`: Screen a paper against research scope and criteria.
8. `extract_paper_evidence`: Extract structured findings, metrics, limitations, and verbatim passages.

#### Phase 3: Evidence Graph & Normalization (12 Tools)
9. `build_evidence_graph`: Execute the 14-step idempotent pipeline to build the knowledge graph from screened literature.
10. `validate_evidence_graph`: Audit graph integrity, checking claim evidence grounding, orphan nodes, and unverified aliases.
11. `get_graph_statistics`: Return total counts of nodes and edges by semantic type.
12. `query_evidence_graph`: Run any of the 14 predefined safe graph queries (method usage, dataset evaluation, findings, limitations).
13. `trace_claim_provenance`: Deep traversal mapping a claim ID to its backing evidence passages, source papers, sections, and pages.
14. `find_papers_by_method`: Retrieve all papers employing a specific research methodology.
15. `find_papers_by_dataset`: Retrieve all papers evaluated on a specific benchmark or dataset.
16. `find_claims_supported_by_multiple_papers`: Identify consensus scientific claims supported by 2+ distinct papers.
17. `find_solitary_claims`: Identify single-paper claims that may represent research gaps or unverified findings.
18. `find_unreviewed_evidence`: Locate extracted evidence records pending researcher review.
19. `resolve_entity_alias`: Normalize a raw entity name (method, model, dataset, metric) to its canonical standard representation.
20. `add_entity_alias_override`: Register a human expert normalization override.

#### Phase 4: Literature Synthesis & Candidate Gap Generation (12 Tools)
21. `generate_literature_synthesis`: Trigger full versioned literature synthesis pipeline and candidate gap generation.
22. `get_literature_synthesis`: Retrieve structured and narrative synthesis for a run.
23. `get_paper_comparison_matrix`: Generate multidimensional paper matrix with dimensional filters.
24. `identify_research_themes`: Discover recurring methodological, empirical, and limitation themes.
25. `analyze_methodology_trends`: Compute methodology usage frequencies and cross-combinations across papers.
26. `analyze_dataset_trends`: Analyze benchmark dataset distributions and method-dataset cross-tabulations.
27. `analyze_research_trends`: Analyze comprehensive empirical, evaluation, and publication year trends.
28. `generate_candidate_research_gaps`: Formulate evidence-grounded candidate gaps across 10 academic categories.
29. `get_candidate_gap_details`: Retrieve full candidate gap description, rationale, assumptions, and validation queries.
30. `get_candidate_gap_evidence`: Retrieve verbatim evidence passages and grounding links backing a candidate gap.
31. `update_candidate_gap_review`: Submit human review decision (accept, reject, edit, request evidence) with audit log.
32. `get_synthesis_history`: List past versioned synthesis runs for reproducibility and audit comparisons.

### Phase 5: Explicit Counterevidence Retrieval & Evidence Traceability
- **Candidate Gap Decomposition**: Breaks high-level candidate gaps into 3–6 atomic empirical sub-claims (`unexplored_problem`, `missing_methodology`, `missing_dataset_evaluation`, `untested_assumptions`).
- **Adversarial Multi-Angle Query Formulation**: Formulates targeted queries across 4 categories (Direct Counter, Methodology Application, Synonym Expansion, Newer Publications) designed to retrieve contradictory findings.
- **Academic Retrieval & Provenance Segregation**: Concurrently queries OpenAlex, Semantic Scholar, Crossref, and arXiv; deduplicates against the existing corpus and isolates newly discovered papers (`discovery_tag="counterevidence_discovered"`).
- **Strict Evidence Hierarchy & Relevance Classification**: 5-tier classification (`direct_counterevidence`, `partial_counterevidence`, `related_evidence`, `not_relevant`, `insufficient_information`). Enforces Level 1 (Full-Text) ground truth for authoritative direct counterevidence and flags abstract-only evidence.
- **Traceable Source Passage Anchoring**: Extracts verbatim quotes, page coordinates, and section headings with complete verification status.
- **Gap Resilience Impact Aggregator**: Evaluates balance of evidence to assign an impact assessment (`strongly_challenged` through `unchallenged`) and list remaining unresolved sub-claims.
- **Human Auditor Review Workflow**: Complete UI review controls with override capability, reviewer rationale notes, and automatic profile recalculation.
- **7 New Phase 5 MCP Tools**: Expands multi-agent tool suite to 39 tools total.
- **Full Phase 1–5 Test Suite**: 67 automated regression tests passing with zero failures.

---

## 6. Phase Documentation Suite

Comprehensive architecture specifications, schemas, and API guides are available in the `docs/` directory:

- [Project Progress Tracker](file:///d:/projects/An-MCP-based-Research-Literature-Review-System/docs/project_progress_tracker.md) - Living status of 12-week roadmap milestones
- [Phase 4 Implementation Report](file:///d:/projects/An-MCP-based-Research-Literature-Review-System/docs/phase4_implementation.md) - Full Phase 4 architectural overview, validation results, and review guide
- [Literature Synthesis Architecture](file:///d:/projects/An-MCP-based-Research-Literature-Review-System/docs/literature_synthesis_architecture.md) - Pipeline sequence, orchestrator, and 9 academic narrative sections
- [Paper Comparison Matrix Specification](file:///d:/projects/An-MCP-based-Research-Literature-Review-System/docs/paper_comparison_matrix.md) - 13 comparative dimensions and JSON/CSV/Markdown export formats
- [Research Theme Identification Specification](file:///d:/projects/An-MCP-based-Research-Literature-Review-System/docs/research_theme_identification.md) - Methodological, empirical, and limitation theme discovery
- [Research Pattern Analysis Specification](file:///d:/projects/An-MCP-based-Research-Literature-Review-System/docs/research_pattern_analysis.md) - Methodology, dataset, and evaluation metric distributions
- [Candidate Research Gap Generation](file:///d:/projects/An-MCP-based-Research-Literature-Review-System/docs/candidate_research_gap_generation.md) - 10-category gap formulation and zero-hallucination validation
- [Candidate Gap Evidence Traceability](file:///d:/projects/An-MCP-based-Research-Literature-Review-System/docs/candidate_gap_evidence_traceability.md) - Bidirectional passage provenance chain traversal
- [Synthesis REST API Documentation](file:///d:/projects/An-MCP-based-Research-Literature-Review-System/docs/synthesis_api_documentation.md) - 10 REST endpoints with example payloads and schemas
- [Phase 4 MCP Tools Guide](file:///d:/projects/An-MCP-based-Research-Literature-Review-System/docs/phase4_mcp_tools.md) - 12 Model Context Protocol tools for autonomous synthesis agents
- [Synthesis Reproducibility & Versioning](file:///d:/projects/An-MCP-based-Research-Literature-Review-System/docs/synthesis_reproducibility.md) - Parameter snapshots, graph version linking, and run comparisons
- [Phase 4 Testing & Validation Suite](file:///d:/projects/An-MCP-based-Research-Literature-Review-System/docs/phase4_testing.md) - Pytest suite and live test instructions
- [Phase 3 Implementation Report](file:///d:/projects/An-MCP-based-Research-Literature-Review-System/docs/phase3_implementation.md) - Evidence graph construction overview
- [Evidence Graph Schema Specification](file:///d:/projects/An-MCP-based-Research-Literature-Review-System/docs/evidence_graph_schema.md) - 14 node types and relationship definitions
- [Entity Normalization Guide](file:///d:/projects/An-MCP-based-Research-Literature-Review-System/docs/entity_normalization.md) - Normalization rules, dictionary catalog, and human override registry
- [Graph Construction Pipeline](file:///d:/projects/An-MCP-based-Research-Literature-Review-System/docs/graph_construction_pipeline.md) - 14-step idempotent pipeline and screening gatekeeping
- [Evidence Provenance Model](file:///d:/projects/An-MCP-based-Research-Literature-Review-System/docs/evidence_provenance.md) - Verifiable passage tracking and provenance chain traversal
- [Graph Query Reference](file:///d:/projects/An-MCP-based-Research-Literature-Review-System/docs/graph_query_reference.md) - Reference for the 14 safe predefined graph queries
- [Phase 3 REST API Reference](file:///d:/projects/An-MCP-based-Research-Literature-Review-System/docs/phase3_api_documentation.md) - Swagger/REST endpoint specifications and payload schemas
