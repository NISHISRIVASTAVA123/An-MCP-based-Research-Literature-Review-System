# Phase 2 REST API & MCP Tool Documentation

## 1. REST Endpoints

### 1.1 Screening Endpoints

#### `POST /api/research-requests/{request_id}/screening-runs`
Triggers an automated screening run across all retrieved papers for the specified research request.
- **Request Parameters**: `request_id` (path string)
- **Response** (200 OK): `ScreeningRunResponse`
```json
{
  "id": "run-b1a9c3d4",
  "request_id": "req-12345678",
  "run_number": 1,
  "criteria_snapshot": { ... },
  "total_papers": 30,
  "included_count": 18,
  "excluded_count": 9,
  "review_needed_count": 3,
  "executed_at": "2026-11-21T10:30:00Z"
}
```

#### `GET /api/research-requests/{request_id}/screening-results`
Lists screening decisions for papers associated with the request.
- **Query Parameters**:
  - `run_id` (optional string): Filter to specific run.
  - `decision` (optional string): Filter by `included`, `excluded`, or `needs_human_review`.
- **Response** (200 OK): Array of `ScreeningDecisionResponse`

#### `PUT /api/papers/{paper_id}/screening-decision`
Submits a non-destructive human override for a paper's screening decision.
- **Request Body**:
```json
{
  "decision": "included",
  "reviewer_notes": "Contains novel benchmark evaluation on transformer architectures.",
  "reviewed_by": "Researcher A"
}
```
- **Response** (200 OK): Updated `ScreeningDecisionResponse` with `is_human_override: true` and `original_decision` preserved.

---

### 1.2 Full-Text Document Endpoints

#### `POST /api/papers/{paper_id}/retrieve-full-text`
Attempts legal Open-Access / arXiv download and triggers PyMuPDF section parsing.
- **Response** (200 OK):
```json
{
  "paper_id": "paper-123",
  "success": true,
  "document_id": "doc-456",
  "source_type": "arxiv_pdf",
  "source_url": "https://arxiv.org/pdf/2301.00001.pdf",
  "extraction_status": "success",
  "page_count": 12,
  "message": "Full-text document retrieved and parsed successfully"
}
```

#### `POST /api/papers/{paper_id}/upload-pdf`
Uploads a user-provided PDF file for a paper.
- **Request**: `multipart/form-data` with `file: <binary PDF>`
- **Response** (200 OK): `DocumentRetrieveResponse`

#### `GET /api/papers/{paper_id}/document-status`
Retrieves document parsing and quality status.
- **Response** (200 OK):
```json
{
  "paper_id": "paper-123",
  "has_document": true,
  "document_id": "doc-456",
  "source_type": "user_upload",
  "file_size_bytes": 1048576,
  "page_count": 14,
  "extraction_status": "success",
  "section_headings": ["Abstract", "Introduction", "Methodology", "Results", "Conclusion"],
  "total_characters_extracted": 42150
}
```

---

### 1.3 Evidence Extraction & Passage Endpoints

#### `POST /api/papers/{paper_id}/extract-evidence`
Extracts structured scientific evidence from full-text or abstract.
- **Query Parameters**: `backend` (`rule_based` | `mock` | `llm_openai`, default `rule_based`)
- **Response** (200 OK): `EvidenceRecordResponse`

#### `GET /api/papers/{paper_id}/evidence`
Retrieves existing structured evidence record for the paper.
- **Response** (200 OK): `EvidenceRecordResponse` or `null` (404)

#### `GET /api/papers/{paper_id}/evidence-passages`
Returns all verifiable text passages anchored to the paper.
- **Response** (200 OK): Array of `EvidencePassageResponse`

#### `PUT /api/evidence-passages/{passage_id}`
Updates researcher verification status of an evidence passage.
- **Request Body**:
```json
{
  "verification_status": "user_verified",
  "user_notes": "Verified against Figure 3 and Table 2 in source PDF."
}
```
- **Response** (200 OK): Updated `EvidencePassageResponse`

---

## 2. Model Context Protocol (MCP) Tools

The system exposes two native Phase 2 MCP tools:

### `screen_research_paper`
- **Description**: Evaluates an academic paper against a research objective, questions, and inclusion/exclusion criteria.
- **Input Schema**:
```json
{
  "paper_id": "string",
  "request_id": "string",
  "override_decision": "string (optional: included | excluded | needs_human_review)",
  "override_reason": "string (optional)"
}
```

### `extract_paper_evidence`
- **Description**: Extracts structured scientific evidence, findings, limitations, and source passages from a paper.
- **Input Schema**:
```json
{
  "paper_id": "string",
  "request_id": "string",
  "backend": "string (optional: rule_based | llm_openai | mock)",
  "force_reextract": "boolean (optional)"
}
```
