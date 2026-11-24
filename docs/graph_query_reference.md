# Evidence Graph Query Reference

## 1. Overview

The `EvidenceGraphQueryService` implements 14 strongly typed, validated semantic graph queries. Rather than allowing raw Cypher or SQL injection, these methods provide safe, parameterized operations that support literature synthesis, cross-paper comparison, and research-gap identification.

All queries can be executed via:
1. Direct Python service calls (`EvidenceGraphQueryService(db)`)
2. REST API endpoint (`GET /api/research-requests/{request_id}/evidence-graph/query`)
3. Specialized Phase 3 MCP agent tools

---

## 2. Query Operations Reference

### 2.1 `find_papers_by_method(request_id, method_name)`
- **Goal**: Identifies all screened papers that employ a specific scientific method.
- **REST**: `GET .../query?query_type=papers_by_method&param_a=SHAP`
- **MCP Tool**: `query_papers_by_method(request_id, method_name)`
- **Returns**: List of papers with titles, IDs, and matched method labels.

### 2.2 `find_papers_by_dataset(request_id, dataset_name)`
- **Goal**: Retrieves all papers evaluated on a benchmark dataset.
- **REST**: `GET .../query?query_type=papers_by_dataset&param_a=LIAR`
- **MCP Tool**: `query_papers_by_dataset(request_id, dataset_name)`
- **Returns**: List of papers evaluating the dataset.

### 2.3 `find_papers_by_model(request_id, model_name)`
- **Goal**: Finds papers that utilize a particular model family or architecture.
- **REST**: `GET .../query?query_type=papers_by_model&param_a=BERT`
- **MCP Tool**: `query_papers_by_model(request_id, model_name)`
- **Returns**: List of papers with matched model entities.

### 2.4 `find_findings_by_paper(paper_id)`
- **Goal**: Returns all empirical findings reported by a specific paper.
- **REST**: `GET .../query?query_type=findings_by_paper&param_a={paper_id}`
- **Returns**: Finding statements, significance, empirical support, and evidence status.

### 2.5 `find_claims_by_paper(paper_id)`
- **Goal**: Retrieves all scientific claims made in a paper.
- **REST**: `GET .../query?query_type=claims_by_paper&param_a={paper_id}`
- **Returns**: List of scientific claims with verification badges.

### 2.6 `find_limitations_cross_papers(request_id, limitation_origin)`
- **Goal**: Compares limitations catalogued across all included papers.
- **Parameters**: `limitation_origin` (`author_reported`, `system_inferred`, or `None` for all).
- **REST**: `GET .../query?query_type=cross_paper_limitations&param_a=author_reported`
- **Returns**: List of limitations, source papers, and severity ratings.

### 2.7 `find_passages_supporting_claim(claim_id)`
- **Goal**: Returns verbatim source excerpts that directly support a scientific claim.
- **REST**: `GET .../query?query_type=passages_supporting_claim&param_a={claim_id}`
- **MCP Tool**: `get_claim_evidence(claim_id)`
- **Returns**: Verbatim text passages, page numbers, and section headings.

### 2.8 `find_claims_supported_by_passage(passage_id)`
- **Goal**: Given an exact text quotation, identifies all claims grounded on it.
- **REST**: `GET .../query?query_type=claims_supported_by_passage&param_a={passage_id}`
- **Returns**: Linked claim nodes.

### 2.9 `find_shared_methods_between_papers(paper_id_a, paper_id_b)`
- **Goal**: Identifies the intersection of methodologies used by two publications.
- **REST**: `GET .../query?query_type=shared_methods&param_a={p1}&param_b={p2}`
- **MCP Tool**: `find_shared_methods(paper_id_a, paper_id_b)`
- **Returns**: Alphabetical list of shared method names (e.g. `["SHAP"]`).

### 2.10 `find_shared_datasets_between_papers(paper_id_a, paper_id_b)`
- **Goal**: Identifies benchmark datasets common to both papers.
- **REST**: `GET .../query?query_type=shared_datasets&param_a={p1}&param_b={p2}`
- **MCP Tool**: `find_shared_datasets(paper_id_a, paper_id_b)`
- **Returns**: Alphabetical list of shared datasets (e.g. `["LIAR"]`).

### 2.11 `find_unsupported_claims(request_id)`
- **Goal**: Identifies claims lacking supporting evidence passages for audit and verification.
- **REST**: `GET .../query?query_type=unsupported_claims`
- **Returns**: List of ungrounded claims requiring human or agent investigation.

### 2.12 `get_paper_subgraph(paper_id)`
- **Goal**: Extracts the complete connected neighborhood for a research publication (authors, methods, datasets, metrics, findings, limitations).
- **REST**: `GET .../query?query_type=paper_subgraph&param_a={paper_id}`
- **MCP Tool**: `get_paper_evidence_graph(paper_id)`
- **Returns**: Subgraph dictionary containing `{ "nodes": [...], "edges": [...] }`.

### 2.13 `find_papers_by_research_question(request_id, question_id)`
- **Goal**: Finds literature in the active review that directly addresses a specific research question.
- **Returns**: Aligned papers with publication years and titles.

### 2.14 `get_claim_provenance_chain(claim_id)`
- **Goal**: Generates end-to-end provenance trace from Claim -> Verbatim Passage -> Paper -> Document -> Run -> Request.
- **REST**: `GET /api/evidence-graph/claims/{claim_id}/provenance`
- **MCP Tool**: `get_evidence_provenance(claim_id)`
- **Returns**: `ProvenanceChainResponse` object.
