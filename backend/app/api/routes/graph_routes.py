"""API Routes for Evidence Graph Construction, Traversal, and Provenance (Phase 3)."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.services.persistence.database import get_db
from backend.app.services.graph.graph_builder import EvidenceGraphBuilder
from backend.app.services.graph.graph_validation_service import GraphValidationService
from backend.app.services.graph.graph_query_service import EvidenceGraphQueryService
from backend.app.services.graph.normalization_service import EntityNormalizationService
from backend.app.services.persistence.graph_repository import GraphRepository
from backend.app.schemas.graph import (
    GraphNodeResponse,
    GraphEdgeResponse,
    EvidenceGraphData,
    GraphStatisticsResponse,
    GraphBuildRunResponse,
    GraphValidationResponse,
    EntityAliasResponse,
    EntityResolutionRequest,
    ProvenanceChainResponse,
)

router = APIRouter(tags=["Evidence Graph"])


@router.post(
    "/api/research-requests/{request_id}/evidence-graph/build",
    response_model=GraphBuildRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Construct evidence knowledge graph",
)
def build_evidence_graph(
    request_id: str,
    db: Session = Depends(get_db),
):
    """Executes the complete 14-step knowledge graph construction pipeline from Phase 2 evidence."""
    builder = EvidenceGraphBuilder(db)
    try:
        run = builder.build_graph(request_id, trigger_type="full_build")
        # Automatically perform integrity validation
        validator = GraphValidationService(db)
        validator.validate_graph(request_id, build_run_id=run.id)
        return run
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evidence graph construction failed: {e}")


@router.post(
    "/api/research-requests/{request_id}/evidence-graph/synchronize",
    response_model=GraphBuildRunResponse,
    summary="Synchronize newly extracted evidence into graph",
)
def synchronize_evidence_graph(
    request_id: str,
    db: Session = Depends(get_db),
):
    """Idempotently synchronizes newly extracted evidence into the existing graph."""
    builder = EvidenceGraphBuilder(db)
    try:
        run = builder.build_graph(request_id, trigger_type="incremental_sync")
        validator = GraphValidationService(db)
        validator.validate_graph(request_id, build_run_id=run.id)
        return run
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph synchronization failed: {e}")


@router.get(
    "/api/research-requests/{request_id}/evidence-graph",
    response_model=EvidenceGraphData,
    summary="Get complete evidence graph for visualization",
)
def get_evidence_graph(
    request_id: str,
    node_type: Optional[str] = Query(None, description="Filter by node type: PAPER, METHOD, DATASET, CLAIM, etc."),
    node_types: Optional[str] = Query(None, description="Comma-separated node types to include"),
    paper_id: Optional[str] = Query(None, description="Filter subgraph to specific paper"),
    db: Session = Depends(get_db),
):
    """Retrieves all active nodes, edges, and statistics for graph visualization."""
    effective_node_types = node_types or node_type
    repo = GraphRepository(db)
    nodes = repo.get_nodes_by_request(request_id, node_type=effective_node_types, paper_id=paper_id)
    edges = repo.get_edges_by_request(request_id, paper_id=paper_id)

    # Compute Statistics
    all_nodes = repo.get_nodes_by_request(request_id)
    all_edges = repo.get_edges_by_request(request_id)

    nodes_by_type: Dict[str, int] = {}
    for n in all_nodes:
        nodes_by_type[n.node_type] = nodes_by_type.get(n.node_type, 0) + 1

    relationships_by_type: Dict[str, int] = {}
    for e in all_edges:
        relationships_by_type[e.relationship_type] = relationships_by_type.get(e.relationship_type, 0) + 1

    claim_count = nodes_by_type.get("CLAIM", 0)
    supported_claim_set = {
        e.target_node_id
        for e in all_edges
        if e.relationship_type == "SUPPORTS"
    }
    supported_claims_count = sum(1 for n in all_nodes if n.node_type == "CLAIM" and n.id in supported_claim_set)
    evidence_pct = round((supported_claims_count / claim_count * 100), 1) if claim_count > 0 else 100.0

    stats = GraphStatisticsResponse(
        request_id=request_id,
        total_nodes=len(all_nodes),
        total_edges=len(all_edges),
        nodes_by_type=nodes_by_type,
        relationships_by_type=relationships_by_type,
        papers_count=nodes_by_type.get("PAPER", 0),
        claims_count=claim_count,
        findings_count=nodes_by_type.get("FINDING", 0),
        evidence_passages_count=nodes_by_type.get("EVIDENCE_PASSAGE", 0),
        methods_count=nodes_by_type.get("METHOD", 0),
        datasets_count=nodes_by_type.get("DATASET", 0),
        limitations_count=nodes_by_type.get("LIMITATION", 0),
        claims_with_evidence_percentage=evidence_pct,
    )

    return EvidenceGraphData(
        request_id=request_id,
        nodes=[
            GraphNodeResponse(
                id=n.id,
                request_id=n.request_id,
                node_type=n.node_type,
                label=n.label,
                normalized_label=n.normalized_label,
                entity_key=n.entity_key,
                source_paper_id=n.source_paper_id,
                evidence_passage_id=n.evidence_passage_id,
                properties=n.properties or {},
                is_active=n.is_active,
                created_at=n.created_at,
                updated_at=n.updated_at,
            )
            for n in nodes
        ],
        edges=[
            GraphEdgeResponse(
                id=e.id,
                request_id=e.request_id,
                source_node_id=e.source_node_id,
                target_node_id=e.target_node_id,
                relationship_type=e.relationship_type,
                edge_key=e.edge_key,
                source_paper_id=e.source_paper_id,
                evidence_passage_id=e.evidence_passage_id,
                properties=e.properties or {},
                created_at=e.created_at,
            )
            for e in edges
        ],
        statistics=stats,
    )


@router.get(
    "/api/research-requests/{request_id}/evidence-graph/statistics",
    response_model=GraphStatisticsResponse,
    summary="Get graph metrics and counts",
)
def get_graph_statistics(
    request_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves real-time node, edge, and verification coverage metrics."""
    repo = GraphRepository(db)
    all_nodes = repo.get_nodes_by_request(request_id)
    all_edges = repo.get_edges_by_request(request_id)

    nodes_by_type: Dict[str, int] = {}
    for n in all_nodes:
        nodes_by_type[n.node_type] = nodes_by_type.get(n.node_type, 0) + 1

    relationships_by_type: Dict[str, int] = {}
    for e in all_edges:
        relationships_by_type[e.relationship_type] = relationships_by_type.get(e.relationship_type, 0) + 1

    claim_count = nodes_by_type.get("CLAIM", 0)
    supported_claim_set = {
        e.target_node_id
        for e in all_edges
        if e.relationship_type == "SUPPORTS"
    }
    supported_claims_count = sum(1 for n in all_nodes if n.node_type == "CLAIM" and n.id in supported_claim_set)
    evidence_pct = round((supported_claims_count / claim_count * 100), 1) if claim_count > 0 else 100.0

    return GraphStatisticsResponse(
        request_id=request_id,
        total_nodes=len(all_nodes),
        total_edges=len(all_edges),
        nodes_by_type=nodes_by_type,
        relationships_by_type=relationships_by_type,
        papers_count=nodes_by_type.get("PAPER", 0),
        claims_count=claim_count,
        findings_count=nodes_by_type.get("FINDING", 0),
        evidence_passages_count=nodes_by_type.get("EVIDENCE_PASSAGE", 0),
        methods_count=nodes_by_type.get("METHOD", 0),
        datasets_count=nodes_by_type.get("DATASET", 0),
        limitations_count=nodes_by_type.get("LIMITATION", 0),
        claims_with_evidence_percentage=evidence_pct,
    )


@router.get(
    "/api/research-requests/{request_id}/evidence-graph/validation",
    response_model=GraphValidationResponse,
    summary="Get graph validation and provenance audit report",
)
def get_graph_validation(
    request_id: str,
    db: Session = Depends(get_db),
):
    """Runs or retrieves the latest integrity audit for evidence provenance."""
    validator = GraphValidationService(db)
    rec = validator.validate_graph(request_id)
    return GraphValidationResponse(
        id=rec.id,
        request_id=rec.request_id,
        build_run_id=rec.build_run_id,
        integrity_status=rec.integrity_status,
        total_nodes=rec.total_nodes,
        total_relationships=rec.total_relationships,
        nodes_by_type=rec.nodes_by_type,
        relationships_by_type=rec.relationships_by_type,
        claims_with_evidence=rec.claims_with_evidence,
        claims_without_evidence=rec.claims_without_evidence,
        findings_with_passages=rec.findings_with_passages,
        orphan_nodes_count=rec.orphan_nodes_count,
        unresolved_entities_count=rec.unresolved_entities_count,
        abstract_only_count=rec.abstract_only_count,
        full_text_count=rec.full_text_count,
        validation_details=rec.validation_details,
        created_at=rec.created_at,
    )


@router.get(
    "/api/research-requests/{request_id}/evidence-graph/build-history",
    response_model=List[GraphBuildRunResponse],
    summary="Get graph construction run history",
)
def get_graph_build_history(
    request_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves all past graph build and synchronization runs for reproducibility."""
    repo = GraphRepository(db)
    runs = repo.get_build_runs(request_id)
    return [
        GraphBuildRunResponse(
            id=r.id,
            request_id=r.request_id,
            run_number=r.run_number,
            trigger_type=r.trigger_type,
            status=r.status,
            total_nodes=r.total_nodes,
            total_edges=r.total_edges,
            nodes_added=r.nodes_added,
            nodes_updated=r.nodes_updated,
            edges_added=r.edges_added,
            papers_processed=r.papers_processed,
            execution_time_seconds=r.execution_time_seconds,
            summary=r.summary or {},
            error_details=r.error_details,
            created_at=r.created_at,
        )
        for r in runs
    ]


@router.get(
    "/api/evidence-graph/nodes/{node_id}",
    response_model=GraphNodeResponse,
    summary="Get individual node details",
)
def get_graph_node(
    node_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves a specific graph node by UUID."""
    repo = GraphRepository(db)
    node = repo.get_node_by_id(node_id)
    if not node:
        raise HTTPException(status_code=404, detail=f"Graph node {node_id} not found")
    return GraphNodeResponse(
        id=node.id,
        request_id=node.request_id,
        node_type=node.node_type,
        label=node.label,
        normalized_label=node.normalized_label,
        entity_key=node.entity_key,
        source_paper_id=node.source_paper_id,
        evidence_passage_id=node.evidence_passage_id,
        properties=node.properties or {},
        is_active=node.is_active,
        created_at=node.created_at,
        updated_at=node.updated_at,
    )


@router.get(
    "/api/evidence-graph/claims/{claim_id}/provenance",
    response_model=ProvenanceChainResponse,
    summary="Get full claim provenance trace",
)
def get_claim_provenance(
    claim_id: str,
    db: Session = Depends(get_db),
):
    """Traces full provenance chain: Claim -> Supporting Passage -> Paper -> Document -> Run -> Request."""
    query_service = EvidenceGraphQueryService(db)
    try:
        return query_service.get_claim_provenance_chain(claim_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/api/research-requests/{request_id}/evidence-graph/query",
    summary="Execute predefined validated graph query",
)
def execute_graph_query(
    request_id: str,
    query_type: str = Query(..., description="Query type: papers_by_method, papers_by_dataset, papers_by_model, findings_by_paper, paper_subgraph, shared_methods, shared_datasets, cross_paper_limitations, unsupported_claims"),
    method_name: Optional[str] = None,
    dataset_name: Optional[str] = None,
    model_name: Optional[str] = None,
    paper_id_a: Optional[str] = None,
    paper_id_b: Optional[str] = None,
    limitation_origin: Optional[str] = None,
    param_a: Optional[str] = None,
    param_b: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Executes a parameterized semantic graph query without raw Cypher/SQL injection."""
    qs = EvidenceGraphQueryService(db)
    qt = query_type.lower()

    # Map generic params if provided
    method_name = method_name or param_a
    dataset_name = dataset_name or param_a
    model_name = model_name or param_a
    paper_id_a = paper_id_a or param_a
    paper_id_b = paper_id_b or param_b
    limitation_origin = limitation_origin or param_a

    if qt == "papers_by_method":
        if not method_name:
            raise HTTPException(status_code=400, detail="method_name parameter required")
        res = qs.find_papers_by_method(request_id, method_name)

    elif qt == "papers_by_dataset":
        if not dataset_name:
            raise HTTPException(status_code=400, detail="dataset_name parameter required")
        res = qs.find_papers_by_dataset(request_id, dataset_name)

    elif qt == "papers_by_model":
        if not model_name:
            raise HTTPException(status_code=400, detail="model_name parameter required")
        res = qs.find_papers_by_model(request_id, model_name)

    elif qt in ("findings_by_paper", "findings"):
        if not paper_id_a:
            raise HTTPException(status_code=400, detail="paper_id parameter required")
        res = qs.find_findings_by_paper(paper_id_a)

    elif qt == "paper_subgraph":
        if not paper_id_a:
            raise HTTPException(status_code=400, detail="paper_id parameter required")
        sub = qs.get_paper_subgraph(paper_id_a)
        res = {
            "nodes": [
                GraphNodeResponse(
                    id=n.id,
                    request_id=n.request_id,
                    node_type=n.node_type,
                    label=n.label,
                    normalized_label=n.normalized_label,
                    entity_key=n.entity_key,
                    source_paper_id=n.source_paper_id,
                    evidence_passage_id=n.evidence_passage_id,
                    properties=n.properties or {},
                    is_active=n.is_active,
                    created_at=n.created_at,
                    updated_at=n.updated_at,
                )
                for n in sub["nodes"]
            ],
            "edges": [
                GraphEdgeResponse(
                    id=e.id,
                    request_id=e.request_id,
                    source_node_id=e.source_node_id,
                    target_node_id=e.target_node_id,
                    relationship_type=e.relationship_type,
                    edge_key=e.edge_key,
                    source_paper_id=e.source_paper_id,
                    evidence_passage_id=e.evidence_passage_id,
                    properties=e.properties or {},
                    created_at=e.created_at,
                )
                for e in sub["edges"]
            ],
        }

    elif qt == "shared_methods":
        if not paper_id_a or not paper_id_b:
            raise HTTPException(status_code=400, detail="Both paper_id_a and paper_id_b are required")
        res = qs.find_shared_methods_between_papers(paper_id_a, paper_id_b)

    elif qt == "shared_datasets":
        if not paper_id_a or not paper_id_b:
            raise HTTPException(status_code=400, detail="Both paper_id_a and paper_id_b are required")
        res = qs.find_shared_datasets_between_papers(paper_id_a, paper_id_b)

    elif qt in ("cross_limitations", "cross_paper_limitations"):
        res = qs.find_limitations_cross_papers(request_id, limitation_origin)

    elif qt == "unsupported_claims":
        res = qs.find_unsupported_claims(request_id)

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported query_type '{query_type}'. Available: papers_by_method, papers_by_dataset, papers_by_model, findings_by_paper, paper_subgraph, shared_methods, shared_datasets, cross_paper_limitations, unsupported_claims.",
        )

    return {"query_type": query_type, "results": res}


@router.post(
    "/api/evidence-graph/entity-resolution",
    response_model=EntityAliasResponse,
    summary="Register manual entity alias resolution",
)
def resolve_entity_alias(
    payload: EntityResolutionRequest,
    db: Session = Depends(get_db),
):
    """Allows a researcher to manually resolve or merge an ambiguous entity alias."""
    target_raw = payload.target_raw_string
    if not target_raw:
        raise HTTPException(status_code=400, detail="raw_string or surface_form is required")

    normalizer = EntityNormalizationService(db)
    canon, method, conf, verified = normalizer.register_manual_resolution(
        raw_string=target_raw,
        canonical_name=payload.canonical_name,
        entity_type=payload.entity_type,
    )
    repo = GraphRepository(db)
    alias = repo.get_alias_by_raw(target_raw, payload.entity_type.lower())
    if not alias:
        raise HTTPException(status_code=500, detail="Failed to retrieve registered alias record")
    return EntityAliasResponse(
        id=alias.id,
        raw_string=alias.raw_string,
        normalized_name=alias.normalized_name,
        entity_type=alias.entity_type,
        resolution_method=alias.resolution_method,
        confidence=alias.confidence,
        is_verified=alias.is_verified,
        created_at=alias.created_at,
    )
