# Literature Synthesis REST API Documentation (Phase 4)

## 1. Route Overview

Phase 4 mounts 10 REST API endpoints under `/api/research-requests`:

| Method | Endpoint | Summary | Response Model |
|---|---|---|---|
| `POST` | `/api/research-requests/{id}/synthesis/runs` | Execute versioned literature synthesis run | `SynthesisRunResponse` |
| `GET` | `/api/research-requests/{id}/synthesis/runs` | List all historical synthesis runs | `List[SynthesisRunResponse]` |
| `GET` | `/api/research-requests/{id}/synthesis/runs/{run_id}` | Get detailed synthesis run result | `SynthesisRunResponse` |
| `GET` | `/api/research-requests/{id}/synthesis/matrix` | Generate multidimensional paper matrix | `PaperComparisonMatrixResponse` |
| `GET` | `/api/research-requests/{id}/synthesis/matrix/export` | Export matrix to CSV or Markdown | `text/csv` or `text/markdown` |
| `GET` | `/api/research-requests/{id}/synthesis/themes` | List recurring literature themes | `List[LiteratureThemeResponse]` |
| `GET` | `/api/research-requests/{id}/synthesis/patterns` | List quantified empirical patterns | `List[LiteraturePatternResponse]` |
| `GET` | `/api/research-requests/{id}/synthesis/candidate-gaps` | List evidence-grounded candidate gaps | `List[CandidateResearchGapResponse]` |
| `GET` | `/api/research-requests/{id}/synthesis/candidate-gaps/{gap_id}` | Get candidate gap with provenance | `CandidateResearchGapResponse` |
| `POST` | `/api/research-requests/{id}/synthesis/candidate-gaps/{gap_id}/review` | Submit human review action | `CandidateResearchGapResponse` |
| `GET` | `/api/research-requests/{id}/synthesis/overview` | Get synthesis summary KPIs | `SynthesisOverviewStats` |

---

## 2. Example: Trigger Synthesis Run

**Request**:
```http
POST /api/research-requests/req-001/synthesis/runs
Content-Type: application/json

{
  "selected_paper_ids": ["paper-1", "paper-2"],
  "prompt_version": "v1.0-academic",
  "model_provider": "rule_deterministic",
  "model_name": "deterministic-engine",
  "synthesis_configuration": {
    "min_paper_threshold": 1
  }
}
```

**Response (201 Created)**:
```json
{
  "id": "run-uuid-1234",
  "research_request_id": "req-001",
  "run_number": 1,
  "status": "completed",
  "selected_paper_ids": ["paper-1", "paper-2"],
  "evidence_graph_version": "graph-build-v1",
  "theme_count": 5,
  "pattern_count": 4,
  "gap_count": 3,
  "created_at": "2026-11-24T18:00:00Z"
}
```
