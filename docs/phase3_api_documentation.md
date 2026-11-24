# Phase 3 API and MCP Tool Documentation

## 1. REST API Endpoints

### 1.1 `POST /api/research-requests/{request_id}/evidence-graph/build`
- **Description**: Triggers the 14-step idempotent knowledge graph construction pipeline from Phase 2 evidence.
- **Status Code**: `201 Created`
- **Response**: `GraphBuildRunResponse`

### 1.2 `POST /api/research-requests/{request_id}/evidence-graph/synchronize`
- **Description**: Idempotently synchronizes newly extracted evidence into the graph without recreating existing entities.
- **Status Code**: `200 OK`
- **Response**: `GraphBuildRunResponse`

### 1.3 `GET /api/research-requests/{request_id}/evidence-graph`
- **Description**: Retrieves active nodes, edges, and real-time statistics for interactive visualization.
- **Query Parameters**:
  - `node_type` / `node_types`: Comma-separated filter (e.g. `METHOD,DATASET`)
  - `paper_id`: Filter subgraph to specific paper
- **Response**: `EvidenceGraphData` containing `nodes`, `edges`, and `statistics`.

### 1.4 `GET /api/research-requests/{request_id}/evidence-graph/statistics`
- **Description**: Returns live node and edge counts, verification coverage, and dimension summaries.
- **Response**: `GraphStatisticsResponse`

### 1.5 `GET /api/research-requests/{request_id}/evidence-graph/validation`
- **Description**: Audits graph integrity, claim evidence grounding rate, orphan nodes, and unverified aliases.
- **Response**: `GraphValidationResponse`

### 1.6 `GET /api/research-requests/{request_id}/evidence-graph/build-history`
- **Description**: Retrieves history of all past build and sync runs for reproducibility.
- **Response**: `List[GraphBuildRunResponse]`

### 1.7 `GET /api/evidence-graph/nodes/{node_id}`
- **Description**: Retrieves detailed properties and attributes of a specific graph node.
- **Response**: `GraphNodeResponse`

### 1.8 `GET /api/evidence-graph/claims/{claim_id}/provenance`
- **Description**: Traces complete lineage from scientific claim back to verbatim text passage and source document.
- **Response**: `ProvenanceChainResponse`

### 1.9 `GET /api/research-requests/{request_id}/evidence-graph/query`
- **Description**: Executes parameterized semantic graph queries.
- **Query Parameters**:
  - `query_type`: e.g. `papers_by_method`, `papers_by_dataset`, `shared_methods`, `shared_datasets`, `cross_paper_limitations`, `unsupported_claims`, `paper_subgraph`
  - `param_a`, `param_b`, `method_name`, `dataset_name`, etc.
- **Response**: `{ "query_type": "...", "results": [...] }`

### 1.10 `POST /api/evidence-graph/entity-resolution`
- **Description**: Allows a domain expert to resolve or override an ambiguous entity alias.
- **Payload**:
  ```json
  {
    "entity_type": "METHOD",
    "surface_form": "lime feature weightings",
    "canonical_name": "LIME",
    "override_notes": "Synonym resolution"
  }
  ```
- **Response**: `EntityAliasResponse`

---

## 2. Model Context Protocol (MCP) Tool Reference

Autonomous AI agents interact with the Evidence Graph via **12 official MCP tools** registered on `mcp_server`:

| MCP Tool Name | Description | Key Parameters | Return Type |
|---|---|---|---|
| `build_evidence_graph` | Constructs full knowledge graph from Phase 2 evidence | `request_id: str` | `Dict[str, Any]` (run stats, integrity status) |
| `synchronize_evidence_graph` | Idempotently syncs newly extracted evidence | `request_id: str` | `Dict[str, Any]` (delta counts) |
| `get_graph_statistics` | Returns real-time counts and verification stats | `request_id: str` | `Dict[str, Any]` (node/edge breakdowns) |
| `query_papers_by_method` | Finds papers employing a specific method | `request_id: str`, `method_name: str` | `List[Dict[str, Any]]` |
| `query_papers_by_dataset` | Finds papers evaluating a specific dataset | `request_id: str`, `dataset_name: str`| `List[Dict[str, Any]]` |
| `query_papers_by_model` | Finds papers utilizing a model family | `request_id: str`, `model_name: str` | `List[Dict[str, Any]]` |
| `get_paper_evidence_graph` | Retrieves connected neighborhood for a paper | `paper_id: str` | `Dict[str, Any]` (subgraph) |
| `get_claim_evidence` | Retrieves exact evidence passages supporting a claim | `claim_id: str` | `List[Dict[str, Any]]` |
| `get_evidence_provenance` | Retrieves complete provenance chain for a claim | `claim_id: str` | `Dict[str, Any]` (`ProvenanceChainResponse`) |
| `get_graph_validation_report`| Audits graph integrity and provenance consistency | `request_id: str` | `Dict[str, Any]` |
| `find_shared_methods` | Identifies methods common to two papers | `paper_id_a: str`, `paper_id_b: str` | `List[str]` |
| `find_shared_datasets` | Identifies datasets common to two papers | `paper_id_a: str`, `paper_id_b: str` | `List[str]` |
