# Phase 1–4 Pre-Phase 5 Baseline Report

**Project Title**: An MCP-Based Multi-Agent Framework for Autonomous Scientific Literature Review and Research Gap Assessment  
**Evaluation Date**: 2026-11-27  
**Test Run Status**: 62 / 62 Tests Passed (100% Pass Rate in 8.88s)

---

## 1. Existing System Architecture

The project is an academic multi-agent research review platform structured across full-stack layers:
- **Backend**: FastAPI (Python 3.14), SQLAlchemy 2.0 ORM with asynchronous and synchronous database session management, SQLite persistence (with zero-code PostgreSQL readiness).
- **Processing & Analytics**: PyMuPDF (`fitz`) scientific PDF parser, deterministic regex/linguistic AST pattern extractors, NetworkX graph modeling, multi-provider academic APIs.
- **Protocol Layer**: Model Context Protocol (MCP) tool exposure (JSON-RPC over stdio / SSE).
- **Frontend**: React 19, TypeScript, Vite, custom academic design system with responsive metrics, modal dialogs, and SVG interactive graph exploration.

---

## 2. Phase 1–4 Implementation Status

### Phase 1: Research Input & Academic Literature Retrieval
- **Status**: Complete & Verified (12/12 features active).
- **Core Modules**: `ResearchRequest` formulation, dynamic research questions, deterministic query expansion (`strategy_planner`), asynchronous academic adapters for OpenAlex, Semantic Scholar, Crossref, and arXiv.
- **Deduplication Engine**: Multi-tier matching (exact DOI normalization -> Levenshtein title distance + publication year $\pm 1$ year window -> provenance merging into canonical `NormalizedPaper`).

### Phase 2: Paper Screening & Evidence Extraction
- **Status**: Complete & Verified (7/7 features active).
- **Core Modules**: PRISMA-compliant 7-dimension criteria evaluator (Topic match, Objective/RQ alignment, Year window, Pub type, Method presence, Empirical outcome presence, explicit Inclusion/Exclusion rules).
- **Full-Text Ingestion**: Legal Open-Access / arXiv PDF retrieval with magic-byte (`%PDF-`) validation and SHA-256 integrity checks; manual user PDF upload support.
- **Section Demarcation**: PyMuPDF page-indexed section parser (Abstract, Introduction, Related Work, Methodology, Experiments, Results, Discussion, Limitations, Conclusions, Reference segregation).
- **Zero-Fabrication Evidence Extraction**: Extraction of research objectives, methodologies, benchmark datasets, evaluation metrics, findings, and author-reported vs system-inferred limitations.
- **Verifiable Passage Tracking**: Claim-to-passage ground-truth anchoring (`evidence_passages` table) with PDF page numbers and section headings.
- **Human-in-the-Loop Override**: Non-destructive override preserves original automated decisions with reviewer notes and timestamps.

### Phase 3: Evidence Database & Evidence Graph Construction
- **Status**: Complete & Verified (6/6 features active).
- **Core Modules**: Heterogeneous Attributed Knowledge Graph ($G = (V, E)$) storing `GraphNode` (Papers, Objectives, Methodologies, Datasets, Metrics, Findings, Limitations, Passages) and `GraphEdge` (`USES_METHOD`, `EVALUATED_ON`, `REPORTS_METRIC`, `CLAIMS_FINDING`, `ACKNOWLEDGES_LIMITATION`, `SUPPORTED_BY_PASSAGE`, `CITES`).
- **Entity Normalization**: Ontology alias resolution (`entity_aliases` table) resolving algorithm and dataset synonyms.
- **Lineage Traversals**: $O(1)$ to $O(V+E)$ bidirectional provenance tracing from claims back to source passages and papers.

### Phase 4: Literature Synthesis & Candidate Gap Generation
- **Status**: Complete & Verified (6/6 features active).
- **Core Modules**: Cross-paper comparison matrix generator (`PaperComparisonMatrix`), recurring research theme discovery (`LiteratureTheme`), empirical & methodological pattern analyzer (`LiteraturePattern`), evidence-grounded candidate research gap generator (`CandidateResearchGap`), explicit gap-to-evidence links (`gap_evidence_links`), and human review audit trail (`human_review_records`).

---

## 3. Database Schema and State

The database currently maintains 17 core relational tables under `backend/app/models/`:
1. `research_requests`
2. `research_questions`
3. `search_strategies`
4. `strategy_queries`
5. `papers`
6. `paper_sources`
7. `search_executions`
8. `screening_runs`
9. `screening_decisions`
10. `fulltext_documents`
11. `extraction_runs`
12. `evidence_records`
13. `evidence_passages`
14. `graph_nodes`
15. `graph_edges`
16. `entity_aliases`
17. `graph_build_runs`
18. `graph_validation_records`
19. `synthesis_runs`
20. `literature_themes`
21. `literature_patterns`
22. `candidate_research_gaps`
23. `gap_evidence_links`
24. `human_review_records`

Database initialization is managed additively via `Base.metadata.create_all(bind=engine)`. No destructive schema resets are performed.

---

## 4. API Endpoints & MCP Tools Summary

- **REST Endpoints Active**:
  - `/api/research-requests` (CRUD, questions, history)
  - `/api/strategies` (query generation, updates)
  - `/api/search` (multi-provider execution)
  - `/api/papers` (filters, metadata, export CSV/JSON)
  - `/api/screening` (runs, results, human override)
  - `/api/documents` (OA fetch, PDF upload, section status)
  - `/api/evidence` (structured extraction, passage verification)
  - `/api/graph` (build, nodes, edges, subgraphs, path lineage)
  - `/api/synthesis` (runs, comparison matrix, themes, patterns, candidate gaps, review audit)
- **MCP Tools Registered**:
  - `search_openalex`, `search_semantic_scholar`, `search_crossref`, `search_arxiv`
  - `retrieve_paper_by_doi`, `generate_academic_search_strategy`
  - `screen_research_paper`, `extract_paper_evidence`
  - `build_evidence_graph`, `query_evidence_graph`, `get_claim_lineage`
  - `run_literature_synthesis`, `generate_candidate_research_gaps`, `get_candidate_gap_details`, `get_candidate_gap_evidence`, `update_candidate_gap_review`

---

## 5. Regression Test Results Baseline

Executed command:
```powershell
pytest backend/tests/ -q --tb=line
```
Output:
```text
62 passed in 8.88s
```
- `backend/tests/test_api_endpoints.py`: PASSED (4 tests)
- `backend/tests/test_research_input.py`: PASSED (3 tests)
- `backend/tests/test_strategy_generation.py`: PASSED (3 tests)
- `backend/tests/test_providers.py`: PASSED (4 tests)
- `backend/tests/test_normalization_and_deduplication.py`: PASSED (4 tests)
- `backend/tests/test_screening.py`: PASSED (6 tests)
- `backend/tests/test_pdf_processing.py`: PASSED (2 tests)
- `backend/tests/test_evidence_extraction.py`: PASSED (2 tests)
- `backend/tests/test_phase2_api_endpoints.py`: PASSED (2 tests)
- `backend/tests/test_entity_normalization.py`: PASSED (3 tests)
- `backend/tests/test_graph_construction.py`: PASSED (5 tests)
- `backend/tests/test_graph_queries.py`: PASSED (4 tests)
- `backend/tests/test_graph_api.py`: PASSED (6 tests)
- `backend/tests/test_synthesis_data_and_retrieval.py`: PASSED (4 tests)
- `backend/tests/test_comparison_matrix_and_themes.py`: PASSED (4 tests)
- `backend/tests/test_pattern_analysis_and_gap_generation.py`: PASSED (3 tests)
- `backend/tests/test_synthesis_api_and_mcp.py`: PASSED (3 tests)

Total: **62/62 Tests Passing**. Zero failures, zero regressions.

---

## 6. Known Limitations Identified Before Phase 5

1. **No External Disproval Mechanism**: Phase 4 generates candidate research gaps based strictly on the reviewed corpus. If the initial search missed newer papers or alternative terminology, candidate gaps may be false positives.
2. **Missing Decomposed Claims**: Candidate gaps currently exist as holistic hypotheses without decomposition into independently searchable sub-claims.
3. **Absence of Counterevidence Provenance**: No relational mapping currently exists between candidate gaps and counterevidence papers, queries, or disproving source passages.
4. **Scope Partitioning**: Discovered counterevidence publications must remain distinct from the primary literature review corpus (`counterevidence_discovered`) until explicitly triaged.

Phase 5 addresses each of these gaps directly.
