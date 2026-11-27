# Phase 5 Implementation Report: Explicit Counterevidence Retrieval & Evidence Traceability

## 1. Executive Summary
Phase 5 introduces **Explicit Counterevidence Retrieval** into the multi-agent literature review framework. Rather than assuming that candidate research gaps generated in Phase 4 are automatically valid, the framework actively seeks contradictory scientific publications, empirical evaluations, and implementations that may disprove, challenge, or qualify candidate gaps.

Every counterevidence finding is anchored to verifiable passage-level ground truth (verbatim text, page numbers, and section headings). Abstract-only findings are strictly tagged and precluded from being presented as authoritative full-text disproofs.

## 2. Core Architecture & Modules
The Phase 5 subsystem consists of modular, loosely-coupled services:
1. **`ClaimDecomposer` (`GapClaimDecomposer`)**:
   Decomposes candidate research gaps into 3–6 atomic empirical sub-claims:
   - Primary unexplored problem
   - Missing methodology / technique
   - Missing dataset / benchmark
   - Untested assumptions
   - Generalization / evaluation limitations
2. **`CounterevidenceQueryGenerator`**:
   Generates targeted, multi-perspective queries across 4 distinct categories:
   - Direct Counter queries (searching for implementations/solutions)
   - Methodology Application queries (searching for technical applications)
   - Synonym Expansion queries (expanding domain terminology)
   - Newer Publications queries (targeting recent literature)
3. **`CounterevidenceRetrievalService`**:
   Orchestrates concurrent retrieval across OpenAlex, Semantic Scholar, Crossref, and arXiv.
   Deduplicates results against the primary corpus and flags new papers with `is_newly_discovered=True`.
4. **`CounterevidenceRelevanceAssessor`**:
   Enforces a strict evidence hierarchy (Levels 1–4). Categorizes papers into:
   - `direct_counterevidence` (requires Level 1 full-text passage ground truth)
   - `partial_counterevidence` (addresses sub-aspects or abstract-only claims)
   - `related_evidence` (shares vocabulary without resolving gap)
   - `not_relevant` (off-target retrieval noise)
   - `insufficient_information` (metadata only)
5. **`CounterevidenceEvidenceLinker`**:
   Extracts verifiable quotes, coordinates (section, page), and maintains full provenance.
6. **`CounterevidenceProfileAggregator`**:
   Synthesizes queries, discoveries, and assessments into a structured `CounterevidenceProfile`, rating gap resilience (`strongly_challenged`, `partially_challenged`, `weakly_challenged`, `unchallenged`, `inconclusive`).
7. **`CounterevidenceOrchestrator`**:
   Manages background asynchronous execution, telemetry tracking, and transactional state persistence.

## 3. Database Models (SQLite & SQLAlchemy 2.0)
Additive migrations added 7 entities without modifying or dropping prior tables:
- `CounterevidenceSearchRun`: Versioned telemetry, execution timestamps, and aggregate counts.
- `CounterevidenceClaim`: Decomposed sub-claims with confidence scores and order indices.
- `CounterevidenceSearchQuery`: Generated queries with search rationale, target provider, and execution state.
- `CounterevidencePublication`: Discovered papers marked with `discovery_tag="counterevidence_discovered"`.
- `CounterevidenceAssessment`: Algorithmic classifications and human researcher review overrides.
- `CounterevidenceEvidence`: Granular verbatim source passages with verified coordinates.
- `CounterevidenceProfile`: Gap resilience summary and unresolved claims list.

## 4. MCP Tools & API Integration
Exposed 7 MCP tools:
- `tool_generate_counterevidence_queries`
- `tool_search_counterevidence`
- `tool_get_counterevidence_search_status`
- `tool_get_counterevidence_publications`
- `tool_assess_counterevidence_relevance`
- `tool_extract_counterevidence_evidence`
- `tool_get_counterevidence_profile`

All tools are registered on the JSON-RPC FastMCP server and cataloged in `/api/mcp/tools`.

## 5. UI Integration
Added the **Counterevidence Analysis View** (`CounterevidenceView.tsx`), offering:
- Candidate gap selector with resilience badge.
- Sub-tabs for Decomposed Claims, Adversarial Queries, Discovered Literature, and Granular Passages.
- Human Auditor Review modal for researcher oversight and override capability.
- Step 7 in Header and PhaseRoadmap updated to "PHASE 5 ACTIVE".
