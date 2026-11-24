"""Graph Integrity and Provenance Audit Validation Service (Phase 3).

Audits evidence graph consistency, verifies claims against source passages,
detects orphan nodes, tracks unresolved entities, and produces reproducible quality reports.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.models.graph import GraphNode, GraphEdge, GraphValidationRecord
from backend.app.services.persistence.graph_repository import GraphRepository
from backend.app.core.logging import logger


class GraphValidationService:
    """Performs rigorous integrity validation and provenance tracking on the evidence graph."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = GraphRepository(db)

    def validate_graph(
        self,
        request_id: str,
        build_run_id: Optional[str] = None,
    ) -> GraphValidationRecord:
        """Audits graph nodes, relationships, and evidence passage linkages."""
        nodes = self.repo.get_nodes_by_request(request_id)
        edges = self.repo.get_edges_by_request(request_id)

        node_map = {n.id: n for n in nodes}
        nodes_by_type: Dict[str, int] = {}
        for n in nodes:
            nodes_by_type[n.node_type] = nodes_by_type.get(n.node_type, 0) + 1

        relationships_by_type: Dict[str, int] = {}
        for e in edges:
            relationships_by_type[e.relationship_type] = relationships_by_type.get(e.relationship_type, 0) + 1

        # Track degree connectivity
        node_degrees: Dict[str, int] = {n.id: 0 for n in nodes}
        for e in edges:
            if e.source_node_id in node_degrees:
                node_degrees[e.source_node_id] += 1
            if e.target_node_id in node_degrees:
                node_degrees[e.target_node_id] += 1

        orphan_nodes = [nid for nid, deg in node_degrees.items() if deg == 0]

        # Audit Claims & Findings support
        claim_nodes = [n for n in nodes if n.node_type == "CLAIM"]
        finding_nodes = [n for n in nodes if n.node_type == "FINDING"]

        # Support edges
        claims_with_evidence_set = set()
        findings_with_passage_set = set()

        for e in edges:
            if e.relationship_type == "SUPPORTS":
                target_node = node_map.get(e.target_node_id)
                if target_node:
                    if target_node.node_type == "CLAIM":
                        claims_with_evidence_set.add(target_node.id)
                    elif target_node.node_type == "FINDING":
                        findings_with_passage_set.add(target_node.id)

        claims_with_evidence = len(claims_with_evidence_set)
        claims_without_evidence = len(claim_nodes) - claims_with_evidence
        findings_with_passages = len(findings_with_passage_set)

        # Unresolved Entities Audit
        unresolved_count = 0
        for n in nodes:
            if n.node_type in ("METHOD", "MODEL", "DATASET", "METRIC"):
                res_method = (n.properties or {}).get("resolution_method", "")
                conf = (n.properties or {}).get("confidence", 1.0)
                if res_method == "normalized_fallback" or conf < 0.8:
                    unresolved_count += 1

        # Scope distribution
        abstract_only_count = 0
        full_text_count = 0
        for n in nodes:
            if n.node_type == "PAPER":
                scope = (n.properties or {}).get("source_scope", "abstract_only")
                if scope == "full_text":
                    full_text_count += 1
                else:
                    abstract_only_count += 1

        # Overall Status
        if len(orphan_nodes) > 0 or claims_without_evidence > (len(claim_nodes) * 0.5):
            integrity_status = "warnings_detected"
        else:
            integrity_status = "valid"

        validation_details = {
            "orphan_node_ids": orphan_nodes[:20],
            "claims_without_evidence_ids": [
                n.id for n in claim_nodes if n.id not in claims_with_evidence_set
            ][:20],
            "unresolved_entities_sample": [
                {"id": n.id, "label": n.label, "type": n.node_type}
                for n in nodes
                if n.node_type in ("METHOD", "MODEL", "DATASET", "METRIC")
                and (n.properties or {}).get("confidence", 1.0) < 0.8
            ][:15],
            "total_papers_in_graph": nodes_by_type.get("PAPER", 0),
            "evidence_passages_in_graph": nodes_by_type.get("EVIDENCE_PASSAGE", 0),
        }

        record = self.repo.create_validation_record(
            request_id=request_id,
            build_run_id=build_run_id,
            integrity_status=integrity_status,
            total_nodes=len(nodes),
            total_relationships=len(edges),
            nodes_by_type=nodes_by_type,
            relationships_by_type=relationships_by_type,
            claims_with_evidence=claims_with_evidence,
            claims_without_evidence=claims_without_evidence,
            findings_with_passages=findings_with_passages,
            orphan_nodes_count=len(orphan_nodes),
            unresolved_entities_count=unresolved_count,
            abstract_only_count=abstract_only_count,
            full_text_count=full_text_count,
            validation_details=validation_details,
        )

        logger.info(
            f"Graph Validation completed for {request_id}: {integrity_status} "
            f"({len(nodes)} nodes, {len(edges)} edges, {claims_with_evidence}/{len(claim_nodes)} claims verified)."
        )
        return record
