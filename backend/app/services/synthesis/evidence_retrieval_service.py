"""Evidence Retrieval Service (Phase 4).

Extracts structured, screened, and validated scientific evidence from the
Phase 3 Evidence Graph and Phase 1-2 repositories for synthesis and gap analysis.
Strictly respects research request boundaries and screening exclusions.
"""

from typing import List, Dict, Any, Optional, Set
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from backend.app.models.paper import Paper
from backend.app.models.screening import ScreeningDecision, ScreeningRun
from backend.app.models.evidence import EvidenceRecord, EvidencePassage
from backend.app.models.graph import GraphNode, GraphEdge, GraphBuildRun
from backend.app.models.research_request import ResearchRequest, ResearchQuestion
from backend.app.services.persistence.graph_repository import GraphRepository


class EvidenceRetrievalService:
    """Dedicated retrieval engine querying Phase 3 Evidence Graph and Phase 1-2 records."""

    def __init__(self, db: Session):
        self.db = db
        self.graph_repo = GraphRepository(db)

    def get_eligible_papers_for_request(self, request_id: str) -> List[Paper]:
        """Retrieves eligible papers for a request, strictly filtering by screening inclusion."""
        # 1. Identify latest screening run for this request
        run_stmt = (
            select(ScreeningRun)
            .where(ScreeningRun.request_id == request_id)
            .order_by(ScreeningRun.executed_at.desc())
            .limit(1)
        )
        screening_run = self.db.scalar(run_stmt)

        included_paper_ids: Set[str] = set()
        if screening_run:
            # Check decisions: decision is included/excluded/needs_human_review
            dec_stmt = select(ScreeningDecision).where(ScreeningDecision.run_id == screening_run.id)
            decisions = list(self.db.scalars(dec_stmt).all())
            for d in decisions:
                if d.decision == "included":
                    included_paper_ids.add(d.paper_id)

            if not included_paper_ids:
                return []

            stmt = select(Paper).where(Paper.id.in_(included_paper_ids), Paper.request_id == request_id)
            return list(self.db.scalars(stmt).all())
        else:
            # Fallback if no screening run was executed: query all papers for this request
            stmt = select(Paper).where(Paper.request_id == request_id)
            return list(self.db.scalars(stmt).all())

    def get_paper_screening_status_map(self, request_id: str) -> Dict[str, str]:
        """Returns map of paper_id -> effective screening decision (included, excluded, needs_review)."""
        run_stmt = (
            select(ScreeningRun)
            .where(ScreeningRun.request_id == request_id)
            .order_by(ScreeningRun.executed_at.desc())
            .limit(1)
        )
        screening_run = self.db.scalar(run_stmt)
        if not screening_run:
            return {}

        dec_stmt = select(ScreeningDecision).where(ScreeningDecision.run_id == screening_run.id)
        decisions = list(self.db.scalars(dec_stmt).all())
        return {d.paper_id: d.decision for d in decisions}

    def get_latest_graph_build_version(self, request_id: str) -> Optional[str]:
        """Retrieves the latest completed graph build run ID or version for the request."""
        stmt = (
            select(GraphBuildRun)
            .where(GraphBuildRun.request_id == request_id, GraphBuildRun.status == "completed")
            .order_by(GraphBuildRun.created_at.desc())
            .limit(1)
        )
        run = self.db.scalar(stmt)
        return run.id if run else None

    def get_research_questions(self, request_id: str) -> List[str]:
        """Retrieves defined research questions for the research request."""
        stmt = (
            select(ResearchQuestion)
            .where(ResearchQuestion.request_id == request_id)
            .order_by(ResearchQuestion.order_index.asc())
        )
        questions = list(self.db.scalars(stmt).all())
        return [q.question_text for q in questions]

    def get_structured_evidence_by_paper(self, paper_id: str) -> Optional[EvidenceRecord]:
        """Retrieves the primary EvidenceRecord for a paper."""
        stmt = (
            select(EvidenceRecord)
            .where(EvidenceRecord.paper_id == paper_id)
            .order_by(EvidenceRecord.created_at.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)

    def get_evidence_passages_by_paper(self, paper_id: str) -> List[EvidencePassage]:
        """Retrieves all verbatim evidence passages for a paper."""
        stmt = (
            select(EvidencePassage)
            .where(EvidencePassage.paper_id == paper_id)
            .order_by(EvidencePassage.page_number.asc(), EvidencePassage.char_start.asc())
        )
        return list(self.db.scalars(stmt).all())

    def get_graph_nodes_by_type(self, request_id: str, node_type: str) -> List[GraphNode]:
        """Retrieves all graph nodes of a given semantic type for a request."""
        return self.graph_repo.get_nodes_by_request(request_id, node_type=node_type)

    def get_graph_edges_by_type(self, request_id: str, relationship_type: str) -> List[GraphEdge]:
        """Retrieves all graph edges of a given relationship type for a request."""
        return self.graph_repo.get_edges_by_request(request_id, relationship_type=relationship_type)

    def get_methods_with_associated_papers(self, request_id: str) -> Dict[str, List[str]]:
        """Maps normalized method names to lists of paper IDs using them."""
        edges = self.get_graph_edges_by_type(request_id, "USES_METHOD")
        method_map: Dict[str, List[str]] = {}
        for e in edges:
            paper_node = e.source_node
            method_node = e.target_node
            if paper_node and method_node and paper_node.source_paper_id:
                m_label = method_node.label
                method_map.setdefault(m_label, []).append(paper_node.source_paper_id)
        return method_map

    def get_datasets_with_associated_papers(self, request_id: str) -> Dict[str, List[str]]:
        """Maps dataset names to lists of paper IDs evaluated on them."""
        edges = self.get_graph_edges_by_type(request_id, "USES_DATASET")
        dataset_map: Dict[str, List[str]] = {}
        for e in edges:
            paper_node = e.source_node
            dataset_node = e.target_node
            if paper_node and dataset_node and paper_node.source_paper_id:
                d_label = dataset_node.label
                dataset_map.setdefault(d_label, []).append(paper_node.source_paper_id)
        return dataset_map

    def get_models_with_associated_papers(self, request_id: str) -> Dict[str, List[str]]:
        """Maps model names to lists of paper IDs using them."""
        edges = self.get_graph_edges_by_type(request_id, "USES_MODEL")
        model_map: Dict[str, List[str]] = {}
        for e in edges:
            paper_node = e.source_node
            model_node = e.target_node
            if paper_node and model_node and paper_node.source_paper_id:
                m_label = model_node.label
                model_map.setdefault(m_label, []).append(paper_node.source_paper_id)
        return model_map

    def get_metrics_with_associated_papers(self, request_id: str) -> Dict[str, List[str]]:
        """Maps metric names to lists of paper IDs evaluating them."""
        edges = self.get_graph_edges_by_type(request_id, "EVALUATED_USING")
        metric_map: Dict[str, List[str]] = {}
        for e in edges:
            paper_node = e.source_node
            metric_node = e.target_node
            if paper_node and metric_node and paper_node.source_paper_id:
                met_label = metric_node.label
                metric_map.setdefault(met_label, []).append(paper_node.source_paper_id)
        return metric_map

    def get_all_claims_with_evidence(self, request_id: str) -> List[Dict[str, Any]]:
        """Retrieves all CLAIM nodes for a request, along with supporting passages."""
        claims = self.get_graph_nodes_by_type(request_id, "CLAIM")
        results = []
        for c in claims:
            # Find supporting passages via incoming or outgoing SUPPORTS/HAS_EVIDENCE edges
            passages = []
            if c.evidence_passage_id:
                p_stmt = select(EvidencePassage).where(EvidencePassage.id == c.evidence_passage_id)
                pass_obj = self.db.scalar(p_stmt)
                if pass_obj:
                    passages.append({
                        "id": pass_obj.id,
                        "exact_passage": pass_obj.verbatim_passage or pass_obj.statement,
                        "section_heading": pass_obj.section_heading,
                        "page_number": pass_obj.page_number,
                    })

            if not passages and c.source_paper_id:
                incoming_edges = self.graph_repo.get_node_relationships(c.id)["incoming"]
                for e in incoming_edges:
                    if e.evidence_passage_id:
                        p_stmt = select(EvidencePassage).where(EvidencePassage.id == e.evidence_passage_id)
                        pass_obj = self.db.scalar(p_stmt)
                        if pass_obj:
                            passages.append({
                                "id": pass_obj.id,
                                "exact_passage": pass_obj.verbatim_passage or pass_obj.statement,
                                "section_heading": pass_obj.section_heading,
                                "page_number": pass_obj.page_number,
                            })
                if not passages:
                    paper_passages = self.get_evidence_passages_by_paper(c.source_paper_id)
                    for pp in paper_passages:
                        if pp.category in ["finding", "claim", "contribution"]:
                            passages.append({
                                "id": pp.id,
                                "exact_passage": pp.verbatim_passage or pp.statement,
                                "section_heading": pp.section_heading,
                                "page_number": pp.page_number,
                            })

            results.append({
                "claim_node_id": c.id,
                "label": c.label,
                "claim_type": (c.properties or {}).get("claim_type", "general_conclusion"),
                "paper_id": c.source_paper_id,
                "passages": passages,
            })
        return results

    def get_all_limitations_with_evidence(self, request_id: str) -> List[Dict[str, Any]]:
        """Retrieves all LIMITATION nodes for a request."""
        limits = self.get_graph_nodes_by_type(request_id, "LIMITATION")
        results = []
        for lim in limits:
            passages = []
            if lim.evidence_passage_id:
                p_stmt = select(EvidencePassage).where(EvidencePassage.id == lim.evidence_passage_id)
                pass_obj = self.db.scalar(p_stmt)
                if pass_obj:
                    passages.append({
                        "id": pass_obj.id,
                        "exact_passage": pass_obj.verbatim_passage or pass_obj.statement,
                        "section_heading": pass_obj.section_heading,
                        "page_number": pass_obj.page_number,
                    })

            if not passages and lim.source_paper_id:
                incoming_edges = self.graph_repo.get_node_relationships(lim.id)["incoming"]
                for e in incoming_edges:
                    if e.evidence_passage_id:
                        p_stmt = select(EvidencePassage).where(EvidencePassage.id == e.evidence_passage_id)
                        pass_obj = self.db.scalar(p_stmt)
                        if pass_obj:
                            passages.append({
                                "id": pass_obj.id,
                                "exact_passage": pass_obj.verbatim_passage or pass_obj.statement,
                                "section_heading": pass_obj.section_heading,
                                "page_number": pass_obj.page_number,
                            })
                if not passages:
                    paper_passages = self.get_evidence_passages_by_paper(lim.source_paper_id)
                    for pp in paper_passages:
                        if pp.category == "limitation":
                            passages.append({
                                "id": pp.id,
                                "exact_passage": pp.verbatim_passage or pp.statement,
                                "section_heading": pp.section_heading,
                                "page_number": pp.page_number,
                            })

            results.append({
                "limitation_node_id": lim.id,
                "label": lim.label,
                "origin": (lim.properties or {}).get("origin", "author_reported"),
                "paper_id": lim.source_paper_id,
                "passages": passages,
            })
        return results

    def get_all_future_directions(self, request_id: str) -> List[Dict[str, Any]]:
        """Retrieves all FUTURE_DIRECTION nodes for a request."""
        directions = self.get_graph_nodes_by_type(request_id, "FUTURE_DIRECTION")
        return [
            {
                "direction_node_id": d.id,
                "label": d.label,
                "paper_id": d.source_paper_id,
                "category": (d.properties or {}).get("category", "unclassified"),
            }
            for d in directions
        ]
