# REST API Documentation (Phase 1)

Base URL: `http://127.0.0.1:8000`  
Interactive OpenAPI UI: `http://127.0.0.1:8000/docs`

---

## 1. Research Requests

### `POST /api/research-requests`
Creates a new research review request.

#### Request Body
```json
{
  "topic": "Explainable AI for Fake News Detection",
  "objective": "Identify limitations and verification gaps in existing explainable fake news models",
  "domain": "Artificial Intelligence",
  "start_year": 2018,
  "end_year": 2024,
  "max_papers": 30,
  "citation_style": "IEEE",
  "research_questions": [
    "What explanation mechanisms are most prevalent in fake news detection?",
    "Are existing explanations robust against adversarial perturbations?"
  ],
  "inclusion_criteria": ["Peer-reviewed publications", "Focus on text disinformation"],
  "exclusion_criteria": ["Image-only detection", "Articles before 2018"],
  "preferred_databases": ["openalex", "semantic_scholar", "crossref", "arxiv"]
}
```

#### Response (`201 Created`)
```json
{
  "id": "7b0d91d9-7603-4f96-857e-07a82cfa23e1",
  "topic": "Explainable AI for Fake News Detection",
  "objective": "Identify limitations and verification gaps in existing explainable fake news models",
  "domain": "Artificial Intelligence",
  "start_year": 2018,
  "end_year": 2024,
  "max_papers": 30,
  "citation_style": "IEEE",
  "questions": [
    {
      "id": "e93ad315-9a84-48d8-b1fc-e547fa90847b",
      "request_id": "7b0d91d9-7603-4f96-857e-07a82cfa23e1",
      "question_text": "What explanation mechanisms are most prevalent in fake news detection?",
      "order_index": 0
    }
  ],
  "has_strategy": false,
  "has_retrieved_papers": false,
  "total_papers_count": 0,
  "created_at": "2026-11-11T19:40:00Z",
  "updated_at": "2026-11-11T19:40:00Z"
}
```

---

### `GET /api/research-requests`
Lists previous research requests with summary counts.

#### Response (`200 OK`)
```json
[
  {
    "id": "7b0d91d9-7603-4f96-857e-07a82cfa23e1",
    "topic": "Explainable AI for Fake News Detection",
    "domain": "Artificial Intelligence",
    "start_year": 2018,
    "end_year": 2024,
    "total_papers": 24,
    "total_questions": 2,
    "has_strategy": true,
    "created_at": "2026-11-11T19:40:00Z"
  }
]
```

---

### `GET /api/research-requests/{request_id}`
Retrieves complete details of a single request.

---

## 2. Search Strategy

### `POST /api/research-requests/{request_id}/strategy`
Decomposes the research request and generates database-specific queries.

#### Response (`201 Created`)
```json
{
  "id": "strat_9831f28b",
  "request_id": "7b0d91d9-7603-4f96-857e-07a82cfa23e1",
  "concepts": ["Explainable AI for Fake News Detection", "Model Interpretability", "Misinformation"],
  "keywords": ["explainable ai", "fake news detection", "shap", "lime", "misinformation"],
  "synonyms": {
    "explainable ai": ["xai", "model interpretability", "interpretable machine learning"]
  },
  "query_combinations": [
    "\"explainable ai\" AND \"fake news detection\"",
    "\"misinformation\" AND \"shap\""
  ],
  "queries": [
    {
      "id": "q_1",
      "target_database": "openalex",
      "query_text": "\"explainable ai\" \"fake news detection\"",
      "is_enabled": true
    },
    {
      "id": "q_2",
      "target_database": "arxiv",
      "query_text": "all:\"explainable ai\" AND all:\"fake news detection\"",
      "is_enabled": true
    }
  ]
}
```

---

### `PUT /api/research-requests/{request_id}/strategy`
Updates search queries or parameters before execution.

---

## 3. Literature Retrieval & Papers

### `POST /api/research-requests/{request_id}/search`
Executes parallel retrieval across OpenAlex, Semantic Scholar, Crossref, and arXiv, normalizes metadata, deduplicates, and saves papers.

#### Response (`200 OK`)
```json
{
  "execution_id": "exec_5521a0",
  "status": "completed",
  "total_raw_retrieved": 35,
  "total_unique_papers": 28,
  "total_duplicates_removed": 7,
  "provider_statuses": {
    "openalex": { "status": "success", "retrieved_count": 10, "error": null },
    "semantic_scholar": { "status": "success", "retrieved_count": 8, "error": null },
    "crossref": { "status": "success", "retrieved_count": 10, "error": null },
    "arxiv": { "status": "success", "retrieved_count": 7, "error": null }
  }
}
```

---

### `GET /api/research-requests/{request_id}/papers`
Retrieves paginated papers with search, filtering, and sorting parameters.

#### Query Parameters:
- `query`: Text search in title, abstract, or DOI
- `year_from`, `year_to`: Filter by publication year
- `source_database`: Filter by source (openalex, semantic_scholar, crossref, arxiv)
- `has_abstract_only`: Boolean
- `has_pdf_only`: Boolean
- `sort_by`: `year`, `title`, `citations`
- `sort_order`: `desc` or `asc`
- `page`: Page integer (1-indexed)
- `page_size`: Items per page (default 20)

---

### `GET /api/papers/{paper_id}`
Returns full normalized metadata and all provenance source records for a single paper.

---

## 4. Exports

### `GET /api/research-requests/{request_id}/export?format=csv`
Streams a downloaded CSV file containing normalized bibliographic fields, citation counts, open-access status, and provider source IDs.

### `GET /api/research-requests/{request_id}/export?format=json`
Returns complete JSON document containing the request scope and normalized paper array.

---

## 5. Model Context Protocol (MCP)

### `GET /api/mcp/tools`
Lists registered MCP tool definitions and parameter signatures.

