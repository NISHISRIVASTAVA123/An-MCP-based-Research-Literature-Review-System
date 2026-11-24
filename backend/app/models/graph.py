"""Graph Database Models for Evidence Graph (Phase 3).

Stores knowledge graph nodes, relationships, entity resolution aliases,
graph build execution runs, and audit validation reports.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import (
    String,
    Integer,
    Text,
    JSON,
    DateTime,
    ForeignKey,
    Boolean,
    Float,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, generate_uuid, utc_now


class GraphNode(Base):
    """Represents an entity node in the scientific evidence graph."""

    __tablename__ = "graph_nodes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("research_requests.id", ondelete="CASCADE"), nullable=False
    )
    node_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # PAPER, AUTHOR, RESEARCH_QUESTION, RESEARCH_OBJECTIVE, METHOD, MODEL, DATASET, METRIC, FINDING, CLAIM, LIMITATION, FUTURE_DIRECTION, EVIDENCE_PASSAGE, RESEARCH_REQUEST
    label: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_label: Mapped[str] = mapped_column(String(500), nullable=False)
    entity_key: Mapped[str] = mapped_column(
        String(500), nullable=False
    )  # Deterministic key e.g. METHOD:transformer or PAPER:paper_uuid

    source_paper_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("papers.id", ondelete="CASCADE"), nullable=True
    )
    evidence_passage_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("evidence_passages.id", ondelete="SET NULL"), nullable=True
    )

    properties: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    outgoing_edges: Mapped[List["GraphEdge"]] = relationship(
        "GraphEdge",
        foreign_keys="GraphEdge.source_node_id",
        back_populates="source_node",
        cascade="all, delete-orphan",
    )
    incoming_edges: Mapped[List["GraphEdge"]] = relationship(
        "GraphEdge",
        foreign_keys="GraphEdge.target_node_id",
        back_populates="target_node",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("request_id", "entity_key", name="uq_graph_nodes_request_entity_key"),
        Index("idx_graph_nodes_request_type", "request_id", "node_type"),
        Index("idx_graph_nodes_paper", "source_paper_id"),
        Index("idx_graph_nodes_passage", "evidence_passage_id"),
        Index("idx_graph_nodes_norm_label", "normalized_label"),
    )


class GraphEdge(Base):
    """Represents a directed typed relationship between two entities."""

    __tablename__ = "graph_edges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("research_requests.id", ondelete="CASCADE"), nullable=False
    )
    source_node_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False
    )
    target_node_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False
    )
    relationship_type: Mapped[str] = mapped_column(
        String(60), nullable=False
    )  # AUTHORED_BY, USES_METHOD, USES_MODEL, USES_DATASET, EVALUATED_USING, REPORTS_FINDING, REPORTS_CLAIM, REPORTS_LIMITATION, PROPOSES_FUTURE_DIRECTION, HAS_EVIDENCE, SUPPORTS, CONTRADICTS, HAS_QUESTION, HAS_OBJECTIVE, INCLUDES_PAPER, ADDRESSED_BY, RELATED_TO
    edge_key: Mapped[str] = mapped_column(
        String(500), nullable=False
    )  # Deterministic e.g. src_id:USES_METHOD:tgt_id

    source_paper_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("papers.id", ondelete="CASCADE"), nullable=True
    )
    evidence_passage_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("evidence_passages.id", ondelete="SET NULL"), nullable=True
    )

    properties: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    source_node: Mapped["GraphNode"] = relationship(
        "GraphNode", foreign_keys=[source_node_id], back_populates="outgoing_edges"
    )
    target_node: Mapped["GraphNode"] = relationship(
        "GraphNode", foreign_keys=[target_node_id], back_populates="incoming_edges"
    )

    __table_args__ = (
        UniqueConstraint("request_id", "edge_key", name="uq_graph_edges_request_edge_key"),
        Index("idx_graph_edges_request_rel", "request_id", "relationship_type"),
        Index("idx_graph_edges_src_tgt", "source_node_id", "target_node_id"),
        Index("idx_graph_edges_paper", "source_paper_id"),
    )


class EntityAlias(Base):
    """Controlled entity resolution and canonical synonym alias registry."""

    __tablename__ = "entity_aliases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    request_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("research_requests.id", ondelete="CASCADE"), nullable=True
    )
    raw_string: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # method, model, dataset, metric, concept
    resolution_method: Mapped[str] = mapped_column(
        String(50), default="exact_rule", nullable=False
    )  # exact_rule, alias_dictionary, manual_user_override
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    __table_args__ = (
        UniqueConstraint("raw_string", "entity_type", name="uq_entity_alias_raw_type"),
        Index("idx_entity_aliases_norm", "normalized_name", "entity_type"),
    )


class GraphBuildRun(Base):
    """Tracks execution provenance of graph construction batches."""

    __tablename__ = "graph_build_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("research_requests.id", ondelete="CASCADE"), nullable=False
    )
    run_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    trigger_type: Mapped[str] = mapped_column(
        String(50), default="full_build", nullable=False
    )  # full_build, incremental_sync, manual
    status: Mapped[str] = mapped_column(
        String(30), default="completed", nullable=False
    )  # pending, running, completed, failed, requires_review

    total_nodes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_edges: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    nodes_added: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    nodes_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    edges_added: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    papers_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    execution_time_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    summary: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    error_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    __table_args__ = (
        Index("idx_graph_build_runs_request", "request_id", "run_number"),
    )


class GraphValidationRecord(Base):
    """Audit report for graph integrity, provenance validity, and orphan tracking."""

    __tablename__ = "graph_validation_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("research_requests.id", ondelete="CASCADE"), nullable=False
    )
    build_run_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("graph_build_runs.id", ondelete="CASCADE"), nullable=True
    )

    total_nodes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_relationships: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    nodes_by_type: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    relationships_by_type: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    claims_with_evidence: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    claims_without_evidence: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    findings_with_passages: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    orphan_nodes_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unresolved_entities_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    abstract_only_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    full_text_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    integrity_status: Mapped[str] = mapped_column(
        String(30), default="valid", nullable=False
    )  # valid, warnings_detected, critical_issues
    validation_details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    __table_args__ = (
        Index("idx_graph_val_request", "request_id"),
    )
