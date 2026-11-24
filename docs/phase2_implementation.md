# Phase 2 Implementation: Paper Screening & Structured Evidence Extraction

## 1. Executive Summary

Phase 2 builds directly upon the Phase 1 academic retrieval foundation to establish a rigorous, reproducible, and verifiable scientific paper screening and evidence extraction pipeline. 

In this phase, we implemented:
1. **Automated Multi-Stage Paper Screening**: A 7-dimension criteria evaluator testing domain scope, timeframe, publication venue/type, methodology relevance, and empirical outcome presence.
2. **Human-in-the-Loop Override & Auditability**: Non-destructive human decision overrides preserving original automated decisions, reviewer identities, timestamps, and rationales.
3. **Legal Open-Access Full-Text Retrieval & Scientific PDF Processing**: Automated retrieval from arXiv and unpaywalled OpenAlex sources with byte-level validation, fallback user PDF uploads, and PyMuPDF-based scientific section demarcation with page indexing.
4. **Structured Scientific Evidence Extraction**: Granular extraction of objectives, methodology (models, theoretical foundations, assumptions), benchmark datasets, quantitative evaluation metrics, author-reported findings, limitations, future work, and epistemic uncertainties.
5. **Verifiable Passage Tracking**: Source anchoring mapping every extracted scientific claim to a verbatim text passage, page number, and section heading with manual verification workflows.
6. **MCP Server Integration**: Native Model Context Protocol tools (`screen_research_paper`, `extract_paper_evidence`).
7. **Interactive Researcher UI**: Complete frontend dashboard with real-time KPI metrics, criteria inspection, PDF upload, override modal, and tabbed evidence explorer.

---

## 2. Architecture & Component Workflow

```
+-----------------------------------------------------------------------------------+
|                        Phase 1 Canonical Paper Corpus                             |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        Module A: Criteria Evaluator                               |
|   * Topic Relevance             * Publication Year Window    * Empirical Findings |
|   * Research Objectives / RQs   * Publication Types (Peer/Conf)                   |
|   * Inclusion / Exclusion Rules * Methodological Framing                          |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                   Module A: Screening Service & Audit Trail                       |
|   * Decisions: included | excluded | needs_human_review                            |
|   * Non-destructive human overrides with reviewer notes & audit history           |
+-----------------------------------------------------------------------------------+
                                          |
                   +----------------------+----------------------+
                   |                                             |
                   v                                             v
+-------------------------------------+       +-------------------------------------+
|  Module B: Document Downloader      |       |  Module B: PyMuPDF Scientific Parser |
|  * arXiv PDF Direct Retrieval       |       |  * Page-indexed section demarcation |
|  * Unpaywalled OpenAlex Endpoints   |       |  * Abstract, Method, Results parsing|
|  * User Manual PDF Upload Support   |       |  * Quality & corruption validation  |
+-------------------------------------+       +-------------------------------------+
                   |                                             |
                   +----------------------+----------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                   Module C & D: Structured Evidence Extraction                    |
|   * Backends: Rule-based (Linguistic/Regex), Mock (Fixtures), LLM (Groq/OpenAI)   |
|   * Extracted Dimensions: Objectives, Methods, Datasets, Metrics, Findings,        |
|     Limitations, Epistemic Uncertainties, Open Questions                          |
|   * Verifiable Passage Tracking: Verbatim quote, page number, section heading     |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                     Module E: Relational Database Storage                         |
|   * screening_runs        * fulltext_documents        * evidence_passages         |
|   * screening_decisions   * extraction_runs           * evidence_records          |
+-----------------------------------------------------------------------------------+
```

---

## 3. Database Schema Extensions

Phase 2 non-destructively added the following tables with cascading foreign keys:

### `screening_runs`
- `id` (VARCHAR PK): Unique run identifier.
- `request_id` (VARCHAR FK -> `research_requests.id`): Parent research scope.
- `run_number` (INTEGER): Monotonically increasing run index.
- `criteria_snapshot` (JSON): Frozen snapshot of inclusion/exclusion criteria.
- `total_papers`, `included_count`, `excluded_count`, `review_needed_count`: Pre-aggregated run KPIs.
- `executed_at` (DATETIME): Timestamp.

### `screening_decisions`
- `id` (VARCHAR PK): Decision UUID.
- `run_id` (VARCHAR FK -> `screening_runs.id`): Run reference.
- `paper_id` (VARCHAR FK -> `papers.id`): Paper evaluated.
- `decision` (VARCHAR): Current active decision (`included`, `excluded`, `needs_human_review`).
- `stage` (VARCHAR): Stage where decision was determined (`title_abstract`, `full_text`, `manual_override`).
- `reason` (TEXT): Natural language explanation.
- `criteria_evaluated`, `criteria_satisfied`, `criteria_unsatisfied`, `missing_information` (JSON): Detailed rule evaluations.
- `confidence_score` (FLOAT): Evaluation confidence [0.0 - 1.0].
- `is_human_override` (BOOLEAN): Flag indicating researcher intervention.
- `original_decision` (VARCHAR): Preserved automated decision before override.
- `reviewer_notes` (TEXT): Justification provided by the researcher.
- `reviewed_at` (DATETIME): Time of manual review.

### `fulltext_documents`
- `id` (VARCHAR PK): Document record UUID.
- `paper_id` (VARCHAR FK -> `papers.id`, UNIQUE): 1-to-1 paper linkage.
- `source_type` (VARCHAR): Source provenance (`arxiv_pdf`, `openalex_pdf`, `user_upload`, `publisher_open_access`).
- `source_url` (VARCHAR): Retrieval URL.
- `file_path` (VARCHAR): Local storage path under `data/fulltext_documents/`.
- `file_size_bytes`, `page_count` (INTEGER): Physical file dimensions.
- `sha256_hash` (VARCHAR): Cryptographic content hash for integrity.
- `extraction_status` (VARCHAR): `success`, `partial`, `corrupted_pdf`, `unsupported_format`, `scanned_image_ocr_needed`.
- `raw_text` (TEXT): Complete sanitized extracted text.
- `sections` (JSON): Structured list of `{heading, text, page_number, order_index}`.
- `has_tables`, `has_equations`, `is_scanned_ocr` (BOOLEAN): Content quality flags.

### `evidence_records`
- `id` (VARCHAR PK): Record UUID.
- `paper_id` (VARCHAR FK -> `papers.id`): Associated paper.
- `extraction_run_id` (VARCHAR): Extraction run batch.
- `source_scope` (VARCHAR): Strictly distinguishes `full_text` from `abstract_only`.
- `extractor_backend` (VARCHAR): Extractor employed (`rule_based`, `llm_openai`, `mock`).
- `research_objective`, `methodology`, `datasets`, `evaluation_metrics`, `findings`, `limitations`, `future_work`, `key_contributions`, `uncertainties` (JSON): Deep structured scientific dimensions.

### `evidence_passages`
- `id` (VARCHAR PK): Passage UUID.
- `paper_id` (VARCHAR FK -> `papers.id`): Paper origin.
- `category` (VARCHAR): `finding`, `limitation`, `methodology`, `metric`, `objective`.
- `statement` (TEXT): Extracted scientific claim or finding.
- `verbatim_passage` (TEXT): Exact quotation from source document.
- `page_number` (INTEGER): Exact page in PDF.
- `section_heading` (VARCHAR): Section title where passage appears.
- `verification_status` (VARCHAR): `machine_extracted`, `user_verified`, `flagged_incorrect`, `unsupported_needs_review`.
- `user_notes` (TEXT): Researcher audit notes.

---

## 4. Verification & Automated Test Coverage

The test suite contains 42 passing tests spanning unit, service, parser, MCP tools, and API integration levels with 0 errors (including 18 dedicated Phase 2 tests and 24 Phase 1 regression tests):
- `backend/tests/test_screening.py`: 8 tests validating criteria matching, timeframe boundaries, publication types, user inclusion/exclusion rules, stage evaluation, and decision persistence.
- `backend/tests/test_pdf_processing.py`: 3 tests verifying PyMuPDF layout parsing, section demarcation, partial text density, and corrupt byte rejection.
- `backend/tests/test_evidence_extraction.py`: 4 tests verifying rule-based extraction, zero-fabrication constraints, source scope labeling (full-text vs abstract-only), passage linkage, and user verification workflows.
- `backend/tests/test_phase2_api_endpoints.py`: 3 comprehensive integration tests validating end-to-end API routes (screening execution, human overrides, document retrieval, evidence extraction, passage verification), user PDF file uploads (`/api/papers/{id}/upload-pdf`), and native Model Context Protocol (MCP) screening and evidence tools.
- `backend/scripts/phase2_live_test.py`: Standalone live pipeline verification script executing screening, human overrides, structured evidence extraction, and passage persistence.
