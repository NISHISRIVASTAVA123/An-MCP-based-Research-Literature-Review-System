"""Database repository for Graph persistence, nodes, edges, aliases, and build history."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, desc, func
from sqlalchemy.orm import Session
from backend.app.models.graph import (
    GraphNode,
    GraphEdge,
    EntityAlias,
    GraphBuildRun,
    GraphValidationRecord,
)
from backend.app.models.paper import Paper
from backend.app.models.evidence import EvidencePassage


class GraphRepository:
    """Repository handling CRUD operations for Evidence Graph nodes and relationships."""

    def __init__(self, db: Session):
        self.db = db

    def upsert_node(
        self,
        request_id: str,
        node_type: str,
        label: str,
        normalized_label: str,
        entity_key: str,
        source_paper_id: Optional[str] = None,
        evidence_passage_id: Optional[str] = None,
        properties: Optional[dict] = None,
    ) -> Tuple[GraphNode, bool]:
        """Idempotently creates or updates a graph node using unique request_id + entity_key."""
        props = properties or {}
        stmt = (
            select(GraphNode)
            .where(
                GraphNode.request_id == request_id,
                GraphNode.entity_key == entity_key,
            )
            .limit(1)
        )
        existing = self.db.scalars(stmt).first()

        if existing:
            existing.label = label
            existing.normalized_label = normalized_label
            existing.node_type = node_type
            if source_paper_id:
                existing.source_paper_id = source_paper_id
            if evidence_passage_id:
                existing.evidence_passage_id = evidence_passage_id
            # Merge properties
            merged = dict(existing.properties or {})
            merged.update(props)
            existing.properties = merged
            existing.is_active = True
            existing.updated_at = datetime.now(timezone.utc)
            self.db.flush()
            return existing, False

        node = GraphNode(
            request_id=request_id,
            node_type=node_type,
            label=label,
            normalized_label=normalized_label,
            entity_key=entity_key,
            source_paper_id=source_paper_id,
            evidence_passage_id=evidence_passage_id,
            properties=props,
            is_active=True,
        )
        self.db.add(node)
        self.db.flush()
        return node, True

    def upsert_edge(
        self,
        request_id: str,
        source_node_id: str,
        target_node_id: str,
        relationship_type: str,
        edge_key: str,
        source_paper_id: Optional[str] = None,
        evidence_passage_id: Optional[str] = None,
        properties: Optional[dict] = None,
    ) -> Tuple[GraphEdge, bool]:
        """Idempotently creates or updates a directed graph relationship."""
        props = properties or {}
        stmt = (
            select(GraphEdge)
            .where(
                GraphEdge.request_id == request_id,
                GraphEdge.edge_key == edge_key,
            )
            .limit(1)
        )
        existing = self.db.scalars(stmt).first()

        if existing:
            merged = dict(existing.properties or {})
            merged.update(props)
            existing.properties = merged
            if source_paper_id:
                existing.source_paper_id = source_paper_id
            if evidence_passage_id:
                existing.evidence_passage_id = evidence_passage_id
            self.db.flush()
            return existing, False

        edge = GraphEdge(
            request_id=request_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            relationship_type=relationship_type,
            edge_key=edge_key,
            source_paper_id=source_paper_id,
            evidence_passage_id=evidence_passage_id,
            properties=props,
        )
        self.db.add(edge)
        self.db.flush()
        return edge, True

    def get_nodes_by_request(
        self,
        request_id: str,
        node_type: Optional[str] = None,
        paper_id: Optional[str] = None,
        active_only: bool = True,
    ) -> List[GraphNode]:
        stmt = select(GraphNode).where(GraphNode.request_id == request_id)
        if active_only:
            stmt = stmt.where(GraphNode.is_active == True)
        if node_type:
            if "," in node_type:
                types = [t.strip().upper() for t in node_type.split(",") if t.strip()]
                stmt = stmt.where(GraphNode.node_type.in_(types))
            else:
                stmt = stmt.where(GraphNode.node_type == node_type.upper())
        if paper_id:
            stmt = stmt.where(GraphNode.source_paper_id == paper_id)
        stmt = stmt.order_by(GraphNode.created_at.asc())
        return list(self.db.scalars(stmt).all())

    def get_edges_by_request(
        self,
        request_id: str,
        relationship_type: Optional[str] = None,
        paper_id: Optional[str] = None,
    ) -> List[GraphEdge]:
        stmt = select(GraphEdge).where(GraphEdge.request_id == request_id)
        if relationship_type:
            stmt = stmt.where(GraphEdge.relationship_type == relationship_type.upper())
        if paper_id:
            stmt = stmt.where(GraphEdge.source_paper_id == paper_id)
        return list(self.db.scalars(stmt).all())

    def get_node_by_id(self, node_id: str) -> Optional[GraphNode]:
        return self.db.get(GraphNode, node_id)

    def get_node_by_entity_key(self, request_id: str, entity_key: str) -> Optional[GraphNode]:
        stmt = (
            select(GraphNode)
            .where(GraphNode.request_id == request_id, GraphNode.entity_key == entity_key)
            .limit(1)
        )
        return self.db.scalars(stmt).first()

    def get_node_relationships(self, node_id: str) -> Dict[str, Any]:
        """Retrieves outgoing and incoming edges for a node."""
        node = self.get_node_by_id(node_id)
        if not node:
            return {"outgoing": [], "incoming": []}
        return {
            "outgoing": list(node.outgoing_edges),
            "incoming": list(node.incoming_edges),
        }

    # Build Runs
    def create_build_run(
        self,
        request_id: str,
        trigger_type: str,
        total_nodes: int,
        total_edges: int,
        nodes_added: int,
        nodes_updated: int,
        edges_added: int,
        papers_processed: int,
        execution_time_seconds: float,
        summary: dict,
        status: str = "completed",
        error_details: Optional[str] = None,
    ) -> GraphBuildRun:
        latest = self.get_latest_build_run(request_id)
        next_run_num = (latest.run_number + 1) if latest else 1

        run = GraphBuildRun(
            request_id=request_id,
            run_number=next_run_num,
            trigger_type=trigger_type,
            status=status,
            total_nodes=total_nodes,
            total_edges=total_edges,
            nodes_added=nodes_added,
            nodes_updated=nodes_updated,
            edges_added=edges_added,
            papers_processed=papers_processed,
            execution_time_seconds=execution_time_seconds,
            summary=summary,
            error_details=error_details,
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_latest_build_run(self, request_id: str) -> Optional[GraphBuildRun]:
        stmt = (
            select(GraphBuildRun)
            .where(GraphBuildRun.request_id == request_id)
            .order_by(desc(GraphBuildRun.run_number))
            .limit(1)
        )
        return self.db.scalars(stmt).first()

    def get_build_runs(self, request_id: str) -> List[GraphBuildRun]:
        stmt = (
            select(GraphBuildRun)
            .where(GraphBuildRun.request_id == request_id)
            .order_by(desc(GraphBuildRun.run_number))
        )
        return list(self.db.scalars(stmt).all())

    # Validations
    def create_validation_record(
        self,
        request_id: str,
        integrity_status: str,
        total_nodes: int,
        total_relationships: int,
        nodes_by_type: dict,
        relationships_by_type: dict,
        claims_with_evidence: int,
        claims_without_evidence: int,
        findings_with_passages: int,
        orphan_nodes_count: int,
        unresolved_entities_count: int,
        abstract_only_count: int,
        full_text_count: int,
        validation_details: dict,
        build_run_id: Optional[str] = None,
    ) -> GraphValidationRecord:
        record = GraphValidationRecord(
            request_id=request_id,
            build_run_id=build_run_id,
            integrity_status=integrity_status,
            total_nodes=total_nodes,
            total_relationships=total_relationships,
            nodes_by_type=nodes_by_type,
            relationships_by_type=relationships_by_type,
            claims_with_evidence=claims_with_evidence,
            claims_without_evidence=claims_without_evidence,
            findings_with_passages=findings_with_passages,
            orphan_nodes_count=orphan_nodes_count,
            unresolved_entities_count=unresolved_entities_count,
            abstract_only_count=abstract_only_count,
            full_text_count=full_text_count,
            validation_details=validation_details,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_latest_validation(self, request_id: str) -> Optional[GraphValidationRecord]:
        stmt = (
            select(GraphValidationRecord)
            .where(GraphValidationRecord.request_id == request_id)
            .order_by(desc(GraphValidationRecord.created_at))
            .limit(1)
        )
        return self.db.scalars(stmt).first()

    # Aliases
    def upsert_alias(
        self,
        raw_string: str,
        normalized_name: str,
        entity_type: str,
        resolution_method: str = "exact_rule",
        confidence: float = 1.0,
        is_verified: bool = True,
        request_id: Optional[str] = None,
    ) -> EntityAlias:
        stmt = (
            select(EntityAlias)
            .where(
                EntityAlias.raw_string == raw_string,
                EntityAlias.entity_type == entity_type,
            )
            .limit(1)
        )
        existing = self.db.scalars(stmt).first()
        if existing:
            existing.normalized_name = normalized_name
            existing.resolution_method = resolution_method
            existing.confidence = confidence
            existing.is_verified = is_verified
            self.db.commit()
            self.db.refresh(existing)
            return existing

        alias = EntityAlias(
            request_id=request_id,
            raw_string=raw_string,
            normalized_name=normalized_name,
            entity_type=entity_type,
            resolution_method=resolution_method,
            confidence=confidence,
            is_verified=is_verified,
        )
        self.db.add(alias)
        self.db.commit()
        self.db.refresh(alias)
        return alias

    def get_alias_by_raw(self, raw_string: str, entity_type: str) -> Optional[EntityAlias]:
        stmt = (
            select(EntityAlias)
            .where(
                EntityAlias.raw_string == raw_string,
                EntityAlias.entity_type == entity_type,
            )
            .limit(1)
        )
        return self.db.scalars(stmt).first()

    def get_aliases(self, entity_type: Optional[str] = None) -> List[EntityAlias]:
        stmt = select(EntityAlias)
        if entity_type:
            stmt = stmt.where(EntityAlias.entity_type == entity_type)
        stmt = stmt.order_by(EntityAlias.raw_string.asc())
        return list(self.db.scalars(stmt).all())
