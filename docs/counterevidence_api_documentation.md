# Phase 5 API Documentation: Counterevidence Retrieval & Verification

## Base URL
`/api`

## Endpoints

### 1. Counterevidence Search Triggers
- `POST /api/research-requests/{request_id}/gaps/{gap_id}/counterevidence/search`
  - Shorthand: `POST /api/counterevidence/gaps/{gap_id}/search`
  - Body: `{"databases": ["openalex", "semantic_scholar"], "max_results_per_query": 10}`
  - Returns: `CounterevidenceProfileResponse`
- `POST /api/research-requests/{request_id}/counterevidence/search-all`
  - Triggers batch search across all candidate gaps in the request.

### 2. Search Runs & Telemetry
- `GET /api/research-requests/{request_id}/counterevidence/runs`
  - Lists search runs for a research request.
- `GET /api/counterevidence/runs`
  - Shorthand listing of all recent counterevidence runs.
- `GET /api/counterevidence/runs/{run_id}`
  - Returns execution telemetry, status, and metrics for a specific run.

### 3. Decomposed Claims & Queries
- `GET /api/gaps/{gap_id}/counterevidence/claims`
  - Shorthand: `GET /api/counterevidence/gaps/{gap_id}/claims`
  - Returns list of empirical sub-claims decomposed from the gap.
- `GET /api/gaps/{gap_id}/counterevidence/queries`
  - Shorthand: `GET /api/counterevidence/gaps/{gap_id}/queries`
  - Returns generated queries with types, rationale, and execution status.

### 4. Publications & Assessments
- `GET /api/gaps/{gap_id}/counterevidence/publications`
  - Shorthand: `GET /api/counterevidence/gaps/{gap_id}/publications`
  - Returns discovered publications marked with discovery tags.
- `GET /api/gaps/{gap_id}/counterevidence/assessments`
  - Shorthand: `GET /api/counterevidence/gaps/{gap_id}/assessments?relevance={type}`
  - Returns structured assessments with evidence levels and embedded passage quotes.
- `PUT /api/counterevidence/assessments/{assessment_id}`
  - Shorthand: `POST /api/counterevidence/assessments/{assessment_id}/review`
  - Body: `{"reviewer_reference": "user_id", "relevance_classification": "partial_counterevidence", "reviewer_notes": "..."}`
  - Records human audit and triggers automatic recalculation of gap resilience profile.

### 5. Evidence Passages & Gap Profile
- `GET /api/gaps/{gap_id}/counterevidence/evidence`
  - Shorthand: `GET /api/counterevidence/gaps/{gap_id}/evidence`
  - Returns granular passage-level quotes with page numbers and section headings.
- `GET /api/gaps/{gap_id}/counterevidence/profile`
  - Shorthand: `GET /api/counterevidence/gaps/{gap_id}/profile`
  - Returns the aggregated gap resilience profile, impact classification, and remaining unresolved claims.
- `POST /api/gaps/{gap_id}/counterevidence/rebuild-profile`
  - Shorthand: `POST /api/counterevidence/gaps/{gap_id}/profile/rebuild`
  - Recalculates profile metrics and synthesis narrative based on current assessments.
