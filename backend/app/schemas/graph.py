"""Pydantic Schemas for Evidence Graph (Phase 3)."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class GraphNodeResponse(BaseModel):
    """Schema for graph node representation."""

    id: str
    request_id: str
    node_type: str
    label: str
    normalized_label: str
    entity_key: str
    source_paper_id: Optional[str] = None
    evidence_passage_id: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


class GraphEdgeResponse(BaseModel):
    """Schema for graph directed edge representation."""

    id: str
    request_id: str
    source_node_id: str
    target_node_id: str
    relationship_type: str
    edge_key: str
    source_paper_id: Optional[str] = None
    evidence_passage_id: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class GraphStatisticsResponse(BaseModel):
    """Real-time metrics and count aggregates of the evidence graph."""

    request_id: str
    total_nodes: int
    total_edges: int
    nodes_by_type: Dict[str, int] = Field(default_factory=dict)
    relationships_by_type: Dict[str, int] = Field(default_factory=dict)
    papers_count: int = 0
    claims_count: int = 0
    findings_count: int = 0
    evidence_passages_count: int = 0
    methods_count: int = 0
    datasets_count: int = 0
    limitations_count: int = 0
    claims_with_evidence_percentage: float = 0.0


class EvidenceGraphData(BaseModel):
    """Complete graph node and edge payload for visualization and analysis."""

    request_id: str
    nodes: List[GraphNodeResponse]
    edges: List[GraphEdgeResponse]
    statistics: GraphStatisticsResponse


class GraphBuildRunResponse(BaseModel):
    """Execution audit metadata for graph build batches."""

    id: str
    request_id: str
    run_number: int
    trigger_type: str
    status: str
    total_nodes: int
    total_edges: int
    nodes_added: int
    nodes_updated: int
    edges_added: int
    papers_processed: int
    execution_time_seconds: float
    summary: Dict[str, Any] = Field(default_factory=dict)
    error_details: Optional[str] = None
    created_at: datetime


class GraphValidationResponse(BaseModel):
    """Integrity audit report for evidence graph validation."""

    id: str
    request_id: str
    build_run_id: Optional[str] = None
    integrity_status: str  # valid, warnings_detected, critical_issues
    total_nodes: int
    total_relationships: int
    nodes_by_type: Dict[str, int] = Field(default_factory=dict)
    relationships_by_type: Dict[str, int] = Field(default_factory=dict)
    claims_with_evidence: int
    claims_without_evidence: int
    findings_with_passages: int
    orphan_nodes_count: int
    unresolved_entities_count: int
    abstract_only_count: int
    full_text_count: int
    validation_details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class EntityAliasResponse(BaseModel):
    """Canonical entity alias mapping record."""

    id: str
    raw_string: str
    normalized_name: str
    entity_type: str
    resolution_method: str
    confidence: float
    is_verified: bool
    created_at: datetime


class EntityResolutionRequest(BaseModel):
    """Request payload to manually resolve or merge an ambiguous entity alias."""

    raw_string: Optional[str] = None
    surface_form: Optional[str] = None
    canonical_name: str
    entity_type: str  # method, model, dataset, metric
    override_notes: Optional[str] = None
    request_id: Optional[str] = None

    @property
    def target_raw_string(self) -> str:
        return self.raw_string or self.surface_form or ""


class ProvenanceChainResponse(BaseModel):
    """End-to-end provenance trace for an extracted claim or finding."""

    claim_id: str
    claim_text: str
    claim_type: str
    verification_status: str

    # Direct evidence passage
    has_evidence_passage: bool
    evidence_passage_id: Optional[str] = None
    exact_passage: Optional[str] = None
    page_number: Optional[int] = None
    section_heading: Optional[str] = None

    # Source document & paper
    paper_id: str
    paper_title: str
    paper_doi: Optional[str] = None
    publication_year: Optional[int] = None
    source_scope: str  # full_text, abstract_only
    document_id: Optional[str] = None

    # Extraction context
    extraction_run_id: Optional[str] = None
    extractor_backend: Optional[str] = None
    research_request_id: str

    # Completeness verification
    is_provenance_complete: bool
    audit_notes: Optional[str] = None
