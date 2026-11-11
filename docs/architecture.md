# System Architecture & Technical Design

**Project**: An MCP-Based Multi-Agent Framework for Autonomous Scientific Literature Review and Research Gap Assessment  
**Current Phase**: Phase 1 (Academic Retrieval, Strategy Generation & Normalization)

---

## 1. High-Level Architectural Flow

The Phase 1 architecture is structured around four decoupled layers:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Academic Web Interface                           │
│     (React 19 + TypeScript + Vite + Tailwind CSS + Lucide Icons)       │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ HTTP REST (JSON)
┌──────────────────────────────────▼─────────────────────────────────────┐
│                           FastAPI Backend                              │
│  - Research Request Management      - Strategy Generation & Editing    │
│  - Parallel Search Orchestration    - Paper Exploration & Filtering    │
│  - CSV / JSON Corpus Exporter       - MCP Tools Directory Endpoint     │
└──────────┬───────────────────────┬─────────────────────────┬───────────┘
           │                       │                         │
┌──────────▼────────────┐ ┌────────▼──────────────┐ ┌────────▼───────────┐
│  Search Planner Engine │ │  Retrieval Pipeline   │ │   MCP Python SDK   │
│ - Concept Extractor   │ │ - Concurrency Manager │ │ - StdIO / SSE      │
│ - Domain Vocabulary   │ │ - Error Isolation     │ │   Server           │
│ - Database Builders   │ │ - Normalization Serv. │ │ - Agent Tools      │
└───────────────────────┘ │ - Deduplication Serv. │ └────────────────────┘
                          └────────┬──────────────┘
                                   │
      ┌────────────────────────────┼───────────────────────────┐
      │                            │                           │
┌─────▼───────┐             ┌──────▼────────┐           ┌──────▼───────┐
│  OpenAlex   │             │ SemanticSchol │           │   Crossref   │ ... [arXiv]
│   Adapter   │             │    Adapter    │           │   Adapter    │
└─────────────┘             └───────────────┘           └──────────────┘
```

---

## 2. Component Specifications

### 2.1 Academic Provider Adapters (`backend/app/services/providers/`)
All provider integrations inherit from the contract defined in `BaseAcademicProvider`:
- **`OpenAlexProvider`**:
  - Endpoint: `https://api.openalex.org/works`
  - Inverted Abstract Reconstruction: OpenAlex abstracts are transmitted as `{ token: [char_indices] }`. Our `reconstruct_openalex_abstract()` algorithm reconstructs continuous readable sentences deterministically.
  - Rate-limit courtesy: Transmits `mailto: ...` in the query and header to access the polite pool.
- **`SemanticScholarProvider`**:
  - Endpoint: `https://api.semanticscholar.org/graph/v1/paper/search`
  - Retrieves citation counts, open-access PDF links, publication venue, and external IDs.
  - Handles HTTP 429 rate limits gracefully with `ProviderRateLimitError` so other databases complete uninhibited.
- **`CrossrefProvider`**:
  - Endpoint: `https://api.crossref.org/works`
  - Filters by `from-pub-date` and `until-pub-date`.
  - Cleans JATS XML tags (`<jats:p>`, `<jats:italic>`) from abstracts to yield clean plaintext.
- **`ArxivProvider`**:
  - Endpoint: `https://export.arxiv.org/api/query`
  - Parses Atom XML feed using Python's `xml.etree.ElementTree`.
  - Automatically identifies PDF download links from entry link elements.

### 2.2 Normalization Engine (`backend/app/services/literature/normalization_service.py`)
Converts raw dictionaries into `NormalizedPaper`:
- Deterministic paper ID generation: `doi_<sha256(doi)>` or `paper_<sha256(title_year)>`.
- Sanitized author names, cleaned titles, validated abstracts (>15 characters), boolean flags (`has_abstract`, `has_pdf`, `has_doi`, `is_open_access`).
- Source provenance records tracked in `sources` list.

### 2.3 Deduplication Engine (`backend/app/services/literature/deduplication_service.py`)
Multi-tier hierarchical deduplication:
1. **Tier 1 (Exact DOI Match)**: Strips `https://doi.org/`, lowercases, and matches.
2. **Tier 2 (Normalized Title + Year)**: Lowercases, removes punctuation, collapses whitespace. Matches exact title with publication year within +/- 1 year tolerance to account for preprint-to-conference delays.
3. **Merge Logic**: Merges provenance sources, adopts the longer/richer abstract, takes higher citation count, and merges PDF links.

### 2.4 Model Context Protocol (MCP) Server (`backend/app/services/mcp/`)
Built with the official Python `mcp` SDK (`MCPServer`). Exposes tool decorators that agents can invoke via stdio or SSE transport.

---

## 3. Database Entity Relationship Diagram

```
┌───────────────────────┐          1:N         ┌───────────────────────┐
│    ResearchRequest    ├──────────────────────►   ResearchQuestion    │
│-----------------------│                      │-----------------------│
│ id (PK)               │                      │ id (PK)               │
│ topic                 │                      │ request_id (FK)       │
│ objective             │                      │ question_text         │
│ domain                │                      │ order_index           │
│ start_year / end_year │                      └───────────────────────┘
│ max_papers            │
│ created_at            │          1:1         ┌───────────────────────┐
│                       ├──────────────────────►    SearchStrategy     │
└───────────┬───────────┘                      │-----------------------│
            │                                  │ id (PK)               │
            │ 1:N                              │ request_id (FK)       │
            │                                  │ concepts (JSON)       │
┌───────────▼───────────┐                      │ keywords (JSON)       │
│    SearchExecution    │                      └───────────┬───────────┘
│-----------------------│                                  │ 1:N
│ id (PK)               │                      ┌───────────▼───────────┐
│ request_id (FK)       │                      │     StrategyQuery     │
│ total_raw_retrieved   │                      │-----------------------│
│ total_unique_papers   │                      │ id (PK)               │
│ total_duplicates      │                      │ strategy_id (FK)      │
│ provider_statuses     │                      │ target_database       │
│ executed_at           │                      │ query_text            │
└───────────────────────┘                      │ is_enabled            │
            │                                  └───────────────────────┘
            │ 1:N
┌───────────▼───────────┐          1:N         ┌───────────────────────┐
│         Paper         ├──────────────────────►      PaperSource      │
│-----------------------│                      │-----------------------│
│ id (PK - hash)        │                      │ id (PK)               │
│ request_id (FK)       │                      │ paper_id (FK)         │
│ title                 │                      │ source_database       │
│ normalized_title      │                      │ external_source_id    │
│ authors (JSON)        │                      │ source_url            │
│ abstract              │                      │ raw_metadata (JSON)   │
│ publication_year      │                      │ retrieved_at          │
│ doi                   │                      └───────────────────────┘
│ url / pdf_url         │
│ venue                 │
│ citation_count        │
│ has_abstract / has_pdf│
└───────────────────────┘
```

