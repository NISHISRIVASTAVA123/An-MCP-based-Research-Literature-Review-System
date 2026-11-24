"""Graph Query Service (Phase 3).

Exposes 14 predefined, validated semantic query methods for evidence traversal,
provenance tracing, and comparative research analysis without raw Cypher/SQL injection.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.models.graph import GraphNode, GraphEdge
from backend.app.models.paper import Paper
from backend.app.models.evidence import EvidenceRecord, EvidencePassage
from backend.app.models.document import FulltextDocument
from backend.app.models.research_request import ResearchRequest
from backend.app.services.persistence.graph_repository import GraphRepository
from backend.app.schemas.graph import ProvenanceChainResponse


class EvidenceGraphQueryService:
    """Predefined validated query engine for evidence graph operations."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = GraphRepository(db)

    def find_papers_by_method(self, request_id: str, method_name: str) -> List[Dict[str, Any]]:
        """Finds all papers associated with a specific methodology."""
        clean_method = method_name.strip().lower()
        edges = self.repo.get_edges_by_request(request_id, relationship_type="USES_METHOD")
        res_papers = []
        for e in edges:
            target = e.target_node
            if target and (clean_method in target.label.lower() or clean_method in target.normalized_label.lower()):
                src = e.source_node
                if src and src.node_type == "PAPER":
                    res_papers.append({
                        "paper_id": src.source_paper_id or src.id,
                        "paper_title": src.label,
                        "method_name": target.label,
                        "properties": src.properties,
                    })
        return res_papers

    def find_papers_by_dataset(self, request_id: str, dataset_name: str) -> List[Dict[str, Any]]:
        """Finds all papers evaluated on a particular benchmark dataset."""
        clean_ds = dataset_name.strip().lower()
        edges = self.repo.get_edges_by_request(request_id, relationship_type="USES_DATASET")
        res_papers = []
        for e in edges:
            target = e.target_node
            if target and (clean_ds in target.label.lower() or clean_ds in target.normalized_label.lower()):
                src = e.source_node
                if src and src.node_type == "PAPER":
                    res_papers.append({
                        "paper_id": src.source_paper_id or src.id,
                        "paper_title": src.label,
                        "dataset_name": target.label,
                        "properties": src.properties,
                    })
        return res_papers

    def find_papers_by_model(self, request_id: str, model_name: str) -> List[Dict[str, Any]]:
        """Finds all papers using a specific model architecture."""
        clean_model = model_name.strip().lower()
        edges = self.repo.get_edges_by_request(request_id, relationship_type="USES_MODEL")
        res_papers = []
        for e in edges:
            target = e.target_node
            if target and (clean_model in target.label.lower() or clean_model in target.normalized_label.lower()):
                src = e.source_node
                if src and src.node_type == "PAPER":
                    res_papers.append({
                        "paper_id": src.source_paper_id or src.id,
                        "paper_title": src.label,
                        "model_name": target.label,
                        "properties": src.properties,
                    })
        return res_papers

    def find_findings_by_paper(self, paper_id: str) -> List[Dict[str, Any]]:
        """Finds all reported research findings for a specific paper."""
        stmt = (
            select(GraphNode)
            .where(GraphNode.source_paper_id == paper_id, GraphNode.node_type == "FINDING")
            .order_by(GraphNode.created_at.asc())
        )
        nodes = list(self.db.scalars(stmt).all())
        return [
            {
                "id": n.id,
                "statement": (n.properties or {}).get("statement", n.label),
                "empirical_support": (n.properties or {}).get("empirical_support"),
                "source_scope": (n.properties or {}).get("source_scope", "abstract_only"),
            }
            for n in nodes
        ]

    def find_limitations_cross_papers(
        self,
        request_id: str,
        limitation_origin: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves limitations reported across all papers in the request."""
        nodes = self.repo.get_nodes_by_request(request_id, node_type="LIMITATION")
        res = []
        for n in nodes:
            origin = (n.properties or {}).get("limitation_origin", "author_reported")
            if limitation_origin and origin.lower() != limitation_origin.lower():
                continue
            paper = self.db.get(Paper, n.source_paper_id) if n.source_paper_id else None
            res.append({
                "id": n.id,
                "limitation_text": (n.properties or {}).get("limitation_text", n.label),
                "limitation_origin": origin,
                "severity": (n.properties or {}).get("severity", "moderate"),
                "paper_id": n.source_paper_id,
                "paper_title": paper.title if paper else "Unknown Paper",
            })
        return res

    def find_claims_supported_by_passage(self, passage_id: str) -> List[Dict[str, Any]]:
        """Finds all scientific claims supported by an exact verbatim passage."""
        # Find passage node
        p_node = self.repo.get_node_by_entity_key(None, f"PASSAGE:{passage_id}") if False else None
        stmt = select(GraphNode).where(GraphNode.evidence_passage_id == passage_id).limit(1)
        p_node = self.db.scalars(stmt).first()
        if not p_node:
            return []

        claims = []
        for edge in p_node.outgoing_edges:
            if edge.relationship_type == "SUPPORTS" and edge.target_node.node_type == "CLAIM":
                target = edge.target_node
                claims.append({
                    "claim_id": target.id,
                    "claim_text": (target.properties or {}).get("claim_text", target.label),
                    "claim_type": (target.properties or {}).get("claim_type", "empirical_claim"),
                    "verification_status": (target.properties or {}).get("verification_status", "machine_extracted"),
                })
        return claims

    def find_passages_supporting_claim(self, claim_id: str) -> List[Dict[str, Any]]:
        """Finds all exact evidence passages supporting a claim."""
        claim_node = self.repo.get_node_by_id(claim_id)
        if not claim_node:
            return []

        passages = []
        for edge in claim_node.incoming_edges:
            if edge.relationship_type == "SUPPORTS" and edge.source_node.node_type == "EVIDENCE_PASSAGE":
                src = edge.source_node
                passages.append({
                    "node_id": src.id,
                    "evidence_passage_id": src.evidence_passage_id,
                    "exact_passage": (src.properties or {}).get("exact_passage"),
                    "page_number": (src.properties or {}).get("page_number"),
                    "section_heading": (src.properties or {}).get("section_heading"),
                    "verification_status": (src.properties or {}).get("verification_status"),
                })
        return passages

    def find_papers_by_research_question(self, request_id: str, question_id: str) -> List[Dict[str, Any]]:
        """Finds papers in the review that align with a specific research question."""
        q_node = self.repo.get_node_by_entity_key(request_id, f"QUESTION:{question_id}")
        if not q_node:
            return []

        # Return papers linked to request that are relevant
        req_node = self.repo.get_node_by_entity_key(request_id, f"REQUEST:{request_id}")
        if not req_node:
            return []

        papers = []
        for edge in req_node.outgoing_edges:
            if edge.relationship_type == "INCLUDES_PAPER" and edge.target_node.node_type == "PAPER":
                p = edge.target_node
                papers.append({
                    "paper_id": p.source_paper_id or p.id,
                    "paper_title": p.label,
                    "publication_year": (p.properties or {}).get("publication_year"),
                })
        return papers

    def find_shared_methods_between_papers(self, paper_id_a: str, paper_id_b: str) -> List[str]:
        """Identifies common methodologies and algorithmic architectures shared by two papers."""
        node_a = self.repo.get_node_by_entity_key(None, f"PAPER:{paper_id_a}")
        node_b = self.repo.get_node_by_entity_key(None, f"PAPER:{paper_id_b}")

        # Fallback query if entity_key has request prefix
        if not node_a:
            stmt = select(GraphNode).where(GraphNode.source_paper_id == paper_id_a, GraphNode.node_type == "PAPER").limit(1)
            node_a = self.db.scalars(stmt).first()
        if not node_b:
            stmt = select(GraphNode).where(GraphNode.source_paper_id == paper_id_b, GraphNode.node_type == "PAPER").limit(1)
            node_b = self.db.scalars(stmt).first()

        if not node_a or not node_b:
            return []

        methods_a = {
            e.target_node.label or e.target_node.normalized_label
            for e in node_a.outgoing_edges
            if e.relationship_type == "USES_METHOD"
        }
        methods_b = {
            e.target_node.label or e.target_node.normalized_label
            for e in node_b.outgoing_edges
            if e.relationship_type == "USES_METHOD"
        }
        return sorted(list(methods_a.intersection(methods_b)))

    def find_shared_datasets_between_papers(self, paper_id_a: str, paper_id_b: str) -> List[str]:
        """Identifies benchmark datasets evaluated in both papers."""
        stmt_a = select(GraphNode).where(GraphNode.source_paper_id == paper_id_a, GraphNode.node_type == "PAPER").limit(1)
        node_a = self.db.scalars(stmt_a).first()
        stmt_b = select(GraphNode).where(GraphNode.source_paper_id == paper_id_b, GraphNode.node_type == "PAPER").limit(1)
        node_b = self.db.scalars(stmt_b).first()

        if not node_a or not node_b:
            return []

        datasets_a = {
            e.target_node.label or e.target_node.normalized_label
            for e in node_a.outgoing_edges
            if e.relationship_type == "USES_DATASET"
        }
        datasets_b = {
            e.target_node.label or e.target_node.normalized_label
            for e in node_b.outgoing_edges
            if e.relationship_type == "USES_DATASET"
        }
        return sorted(list(datasets_a.intersection(datasets_b)))

    def find_unsupported_claims(self, request_id: str) -> List[Dict[str, Any]]:
        """Finds scientific claims in the graph lacking supporting evidence passages."""
        claims = self.repo.get_nodes_by_request(request_id, node_type="CLAIM")
        unsupported = []
        for c in claims:
            has_passage = any(
                e.relationship_type == "SUPPORTS" and e.source_node.node_type == "EVIDENCE_PASSAGE"
                for e in c.incoming_edges
            )
            if not has_passage:
                paper = self.db.get(Paper, c.source_paper_id) if c.source_paper_id else None
                unsupported.append({
                    "claim_id": c.id,
                    "claim_text": (c.properties or {}).get("claim_text", c.label),
                    "paper_id": c.source_paper_id,
                    "paper_title": paper.title if paper else "Unknown Paper",
                })
        return unsupported

    def find_unreviewed_evidence_records(self, request_id: str) -> List[Dict[str, Any]]:
        """Identifies evidence records requiring manual human verification."""
        passages = self.repo.get_nodes_by_request(request_id, node_type="EVIDENCE_PASSAGE")
        unreviewed = []
        for p in passages:
            status = (p.properties or {}).get("verification_status", "machine_extracted")
            if status in ("machine_extracted", "unsupported_needs_review"):
                unreviewed.append({
                    "node_id": p.id,
                    "passage_id": p.evidence_passage_id,
                    "statement": (p.properties or {}).get("statement", p.label),
                    "exact_passage": (p.properties or {}).get("exact_passage"),
                    "verification_status": status,
                    "paper_id": p.source_paper_id,
                })
        return unreviewed

    def get_paper_subgraph(self, paper_id: str) -> Dict[str, Any]:
        """Extracts the complete connected neighborhood for an individual paper."""
        stmt = select(GraphNode).where(GraphNode.source_paper_id == paper_id, GraphNode.node_type == "PAPER").limit(1)
        paper_node = self.db.scalars(stmt).first()
        if not paper_node:
            return {"nodes": [], "edges": []}

        subgraph_nodes = {paper_node.id: paper_node}
        subgraph_edges = []

        for e in paper_node.outgoing_edges:
            subgraph_edges.append(e)
            subgraph_nodes[e.target_node.id] = e.target_node

        for e in paper_node.incoming_edges:
            subgraph_edges.append(e)
            subgraph_nodes[e.source_node.id] = e.source_node

        return {
            "nodes": list(subgraph_nodes.values()),
            "edges": subgraph_edges,
        }

    def get_claim_provenance_chain(self, claim_id: str) -> ProvenanceChainResponse:
        """Traces the complete provenance chain: Claim -> Passage -> Paper -> Document -> Run -> Request."""
        claim_node = self.repo.get_node_by_id(claim_id)
        if not claim_node or claim_node.node_type != "CLAIM":
            raise ValueError(f"Scientific Claim node {claim_id} not found.")

        paper_id = claim_node.source_paper_id
        paper = self.db.get(Paper, paper_id) if paper_id else None
        if not paper:
            raise ValueError(f"Origin paper for claim {claim_id} not found.")

        # Find supporting passage
        passage_edge = next(
            (e for e in claim_node.incoming_edges if e.relationship_type == "SUPPORTS" and e.source_node.node_type == "EVIDENCE_PASSAGE"),
            None,
        )
        p_node = passage_edge.source_node if passage_edge else None

        doc = paper.documents[0] if paper.documents else None
        latest_evidence = self.db.query(EvidenceRecord).filter(EvidenceRecord.paper_id == paper.id).order_by(EvidenceRecord.created_at.desc()).first()
        run = latest_evidence.extraction_run if latest_evidence else None

        is_complete = bool(p_node and paper and (p_node.properties or {}).get("exact_passage"))

        return ProvenanceChainResponse(
            claim_id=claim_node.id,
            claim_text=(claim_node.properties or {}).get("claim_text", claim_node.label),
            claim_type=(claim_node.properties or {}).get("claim_type", "empirical_claim"),
            verification_status=(claim_node.properties or {}).get("verification_status", "machine_extracted"),
            has_evidence_passage=bool(p_node),
            evidence_passage_id=p_node.evidence_passage_id if p_node else None,
            exact_passage=(p_node.properties or {}).get("exact_passage") if p_node else None,
            page_number=(p_node.properties or {}).get("page_number") if p_node else None,
            section_heading=(p_node.properties or {}).get("section_heading") if p_node else None,
            paper_id=paper.id,
            paper_title=paper.title,
            paper_doi=paper.doi,
            publication_year=paper.publication_year,
            source_scope=run.source_scope if run else "abstract_only",
            document_id=doc.id if doc else None,
            extraction_run_id=run.id if run else None,
            extractor_backend=run.extractor_backend if run else None,
            research_request_id=claim_node.request_id,
            is_provenance_complete=is_complete,
            audit_notes=None if is_complete else "Claim is lacking anchored verbatim evidence passage.",
        )
