# Phase 1 Implementation Walkthrough

**Deliverable**: Research Input, Search Strategy, and Academic Literature Retrieval Module  
**Status**: 100% Implemented and Verified (24/24 Automated Tests Passed, Live APIs Verified)

---

## 1. Requirements Matrix & Verification

### 1.1 User Interface: Research Input Form
- [x] Clean academic layout built with React 19 + TypeScript + Vite.
- [x] Required inputs: Research Topic, Objective, Dynamic Research Questions (Add/Edit/Remove), Domain (with custom option), Start Year, End Year.
- [x] Optional inputs: Preferred databases checkboxes (OpenAlex, Semantic Scholar, Crossref, arXiv), Max Papers per query, Citation Style (IEEE, APA, Harvard, ACM), Inclusion/Exclusion Criteria.
- [x] Input validations: Blocks empty topics/objectives, validates year ordering (`start_year <= end_year`), validates positive paper counts.

### 1.2 Search Strategy Generation
- [x] Deterministic concept extraction and keyword expansion (`DeterministicStrategyPlanner`).
- [x] Academic domain synonym mapping (XAI, Fake News, Hallucination, Knowledge Graph, Counterevidence, Claim Verification, etc.).
- [x] Provider-specific query building:
  - OpenAlex: Focus phrases & keywords.
  - Semantic Scholar: Boolean & keyword pairs.
  - Crossref: Bibliographic terms.
  - arXiv: Field prefixes (`all:"..." AND all:"..."`).
- [x] Inspection and Editing: User can toggle queries, modify text, and add custom query variants before retrieval.
- [x] Pluggable Interface: `AbstractStrategyPlanner` allows seamless addition of LLM-based planners in future phases.

### 1.3 Academic Literature Retrieval
- [x] 4 independent modular provider adapters (`OpenAlexProvider`, `SemanticScholarProvider`, `CrossrefProvider`, `ArxivProvider`).
- [x] OpenAlex inverted index abstract reconstruction algorithm.
- [x] Crossref JATS XML tag stripping.
- [x] arXiv Atom XML parsing with open-access PDF resolution.
- [x] Resilience: Single provider failure (e.g. rate limit HTTP 429) does not abort the search pipeline; successes are recorded and failures isolated.

### 1.4 MCP Architecture
- [x] Exposes standard tools using the official Python MCP SDK (`mcp` v2):
  - `search_openalex`
  - `search_semantic_scholar`
  - `search_crossref`
  - `search_arxiv`
  - `retrieve_paper_by_doi`
  - `generate_academic_search_strategy`
- [x] Direct service invocation within FastAPI and CLI/agent invocation via stdio transport.

### 1.5 Metadata Normalization
- [x] Canonical `NormalizedPaper` and `PaperSource` models.
- [x] Preserves external IDs, URLs, and retrieval timestamps.
- [x] Distinguishes missing metadata from empty metadata without hallucinating values.

### 1.6 Duplicate Detection
- [x] Priority 1: Exact normalized DOI match.
- [x] Priority 2: Normalized title match with publication year verification (+/- 1 year allowance for preprint-to-journal delays).
- [x] Merges provenance sources, adopts richer abstracts, and combines citation counts.

### 1.7 Database Persistence
- [x] SQLite database with declarative SQLAlchemy 2.0 models.
- [x] Portable schema design for future PostgreSQL migration.
- [x] Stores Requests, Questions, Strategies, Strategy Queries, Papers, Sources, and Execution History.

### 1.8 Search Execution & Result Interface
- [x] Real-time metrics: Raw Retrieved, Unique Papers, Duplicates Merged, Provider Status Badges.
- [x] Client-side & server-side search within title, abstract, or DOI.
- [x] Year, Database, and Abstract/PDF filters.
- [x] Sorting by year, title, citations.
- [x] Paper details modal with provenance source inspection and raw JSON payloads.

### 1.9 Export Functionality
- [x] CSV export with full bibliographic columns and provenance IDs.
- [x] JSON export containing the complete request scope and paper array.

