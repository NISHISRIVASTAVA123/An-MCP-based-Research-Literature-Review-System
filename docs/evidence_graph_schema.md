# Evidence Graph Data Model and Schema Specification

## 1. Overview

The Evidence Graph serves as the formal knowledge layer of the literature review system. Rather than storing flat unstructured text or generic nodes, the graph employs **14 strongly typed scientific nodes** interconnected by **semantically defined directional edges**.

The database uses hybrid relational graph tables in SQLAlchemy 2.0 (`graph_nodes` and `graph_edges`), optimized with composite indexes and natural entity keys.

---

## 2. Node Types Specification

| Node Type | Description | Key Properties | Deterministic Entity Key Format |
|---|---|---|---|
| **`RESEARCH_REQUEST`** | User's active research project | `topic`, `objective`, `domain`, `start_year`, `end_year` | `REQUEST:{request_id}` |
| **`RESEARCH_QUESTION`**| Specific research question | `question_text`, `order_index` | `QUESTION:{question_id}` |
| **`RESEARCH_OBJECTIVE`** | Goal of review or paper | `objective_text`, `objective_type` (`user_defined`, `paper_reported`) | `OBJECTIVE:{request_id}:{hash}` |
| **`PAPER`** | Canonical academic publication | `paper_id`, `title`, `doi`, `publication_year`, `venue`, `has_abstract`, `has_full_text` | `PAPER:{paper_id}` |
| **`AUTHOR`** | Academic author | `author_name`, `orcid`, `external_id` | `AUTHOR:{canonical_author_name}` |
| **`METHOD`** | Algorithmic approach or methodology | `method_name`, `normalized_name`, `resolution_method`, `confidence` | `METHOD:{normalized_name}` |
| **`MODEL`** | Specific model architecture | `model_name`, `model_family`, `version` | `MODEL:{normalized_name}` |
| **`DATASET`** | Benchmark or experimental dataset | `dataset_name`, `normalized_name`, `sample_size`, `domain` | `DATASET:{normalized_name}` |
| **`METRIC`** | Quantitative evaluation metric | `metric_name`, `normalized_name`, `unit`, `reported_value` | `METRIC:{normalized_name}` |
| **`FINDING`** | Empirical research outcome | `statement`, `finding_type`, `empirical_support`, `significance` | `FINDING:{paper_id}:{hash}` |
| **`CLAIM`** | Scientific assertion made in paper | `claim_text`, `claim_type`, `verification_status`, `source_scope` | `CLAIM:{paper_id}:{hash}` |
| **`LIMITATION`** | Reported or inferred constraint | `limitation_text`, `limitation_origin` (`author_reported`, `system_inferred`), `severity` | `LIMITATION:{paper_id}:{hash}` |
| **`FUTURE_DIRECTION`** | Future research recommendation | `direction_text`, `category`, `rationale` | `DIRECTION:{paper_id}:{hash}` |
| **`EVIDENCE_PASSAGE`** | Exact verbatim text passage | `exact_passage`, `page_number`, `section_heading`, `char_start`, `char_end`, `verification_status` | `PASSAGE:{evidence_passage_id}` |

---

## 3. Relationships Specification

| Relationship Type | Source Node Type | Target Node Type | Description | Deterministic Edge Key Format |
|---|---|---|---|---|
| **`HAS_QUESTION`** | `RESEARCH_REQUEST` | `RESEARCH_QUESTION` | Request contains question | `{request_node.id}:HAS_QUESTION:{q_node.id}` |
| **`HAS_OBJECTIVE`** | `RESEARCH_REQUEST` | `RESEARCH_OBJECTIVE` | Request defines objective | `{request_node.id}:HAS_OBJECTIVE:{obj_node.id}` |
| **`INCLUDES_PAPER`** | `RESEARCH_REQUEST` | `PAPER` | Screened included paper | `{request_node.id}:INCLUDES_PAPER:{paper_node.id}` |
| **`AUTHORED_BY`** | `PAPER` | `AUTHOR` | Paper authorship attribution | `{paper_node.id}:AUTHORED_BY:{author_node.id}` |
| **`USES_METHOD`** | `PAPER` | `METHOD` | Method employed in study | `{paper_node.id}:USES_METHOD:{method_node.id}` |
| **`USES_MODEL`** | `PAPER` | `MODEL` | Architecture utilized | `{paper_node.id}:USES_MODEL:{model_node.id}` |
| **`USES_DATASET`** | `PAPER` | `DATASET` | Dataset evaluated | `{paper_node.id}:USES_DATASET:{dataset_node.id}` |
| **`EVALUATED_USING`** | `PAPER` | `METRIC` | Metric measured in paper | `{paper_node.id}:EVALUATED_USING:{metric_node.id}` |
| **`REPORTS_FINDING`** | `PAPER` | `FINDING` | Finding reported by paper | `{paper_node.id}:REPORTS_FINDING:{finding_node.id}` |
| **`REPORTS_CLAIM`** | `PAPER` | `CLAIM` | Scientific claim asserted | `{paper_node.id}:REPORTS_CLAIM:{claim_node.id}` |
| **`REPORTS_LIMITATION`**| `PAPER` | `LIMITATION` | Constraint documented | `{paper_node.id}:REPORTS_LIMITATION:{lim_node.id}` |
| **`PROPOSES_FUTURE_DIRECTION`**| `PAPER` | `FUTURE_DIRECTION`| Recommendation suggested | `{paper_node.id}:PROPOSES_FUTURE_DIRECTION:{dir_node.id}` |
| **`HAS_EVIDENCE`** | `PAPER` | `EVIDENCE_PASSAGE` | Extracted source excerpt | `{paper_node.id}:HAS_EVIDENCE:{passage_node.id}` |
| **`SUPPORTS`** | `EVIDENCE_PASSAGE` | `CLAIM` / `FINDING` / `LIMITATION` | Verbatim text ground | `{passage_node.id}:SUPPORTS:{target_node.id}` |

---

## 4. Relational Database Tables

### 4.1 `graph_nodes`
- `id`: UUID (Primary Key)
- `request_id`: Foreign key to `research_requests.id` (Indexed)
- `node_type`: String (Indexed)
- `label`: Display string
- `normalized_label`: Lowercase alphanumeric string for search (Indexed)
- `entity_key`: Deterministic natural key (Unique per request)
- `source_paper_id`: Optional foreign key to `papers.id` (Indexed)
- `evidence_passage_id`: Optional foreign key to `evidence_passages.id` (Indexed)
- `properties`: JSON dictionary of entity attributes
- `is_active`: Boolean
- `created_at` / `updated_at`: Timestamps

### 4.2 `graph_edges`
- `id`: UUID (Primary Key)
- `request_id`: Foreign key to `research_requests.id` (Indexed)
- `source_node_id`: Foreign key to `graph_nodes.id`
- `target_node_id`: Foreign key to `graph_nodes.id`
- `relationship_type`: String (Indexed)
- `edge_key`: Deterministic string `src_id:REL:tgt_id` (Unique per request)
- `source_paper_id`: Optional foreign key to `papers.id` (Indexed)
- `evidence_passage_id`: Optional foreign key to `evidence_passages.id`
- `properties`: JSON dictionary of edge attributes
- `created_at`: Timestamp

### 4.3 `entity_aliases`
- `id`: UUID (Primary Key)
- `raw_string`: Surface form extracted from text
- `normalized_name`: Canonical standardized name
- `entity_type`: `method`, `model`, `dataset`, `metric`
- `resolution_method`: `exact_rule`, `stemmed_rule`, `unverified_alias`, `manual_user_override`
- `confidence`: Float between 0.0 and 1.0
- `is_verified`: Boolean
- `request_id`: Optional foreign key to `research_requests.id`
- `created_at`: Timestamp

---

## 5. Invariants & Academic Integrity Constraints

1. **No Phantom Papers**: A `PAPER` node cannot exist in the active graph unless its corresponding `ScreeningDecision` record has `decision != 'excluded'`.
2. **Deterministic Idempotency**: Re-running graph construction on identical data guarantees identical node and edge identifiers.
3. **Verbatim Passage Invariance**: `EVIDENCE_PASSAGE` nodes must retain the unaltered raw excerpt extracted from the source PDF or abstract; paraphrasing is prohibited.
4. **Limitation Origin Rigor**: System-inferred limitations must never be labeled `author_reported`.
