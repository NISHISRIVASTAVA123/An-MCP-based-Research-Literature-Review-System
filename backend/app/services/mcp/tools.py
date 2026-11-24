"""MCP Tool implementations wrapping academic providers and strategy services.

These tool functions serve both as direct internal Python services
and as registered tools on the official Python MCP server.
"""

from typing import List, Dict, Any, Optional
from backend.app.services.providers.openalex_provider import OpenAlexProvider
from backend.app.services.providers.semantic_scholar_provider import SemanticScholarProvider
from backend.app.services.providers.crossref_provider import CrossrefProvider
from backend.app.services.providers.arxiv_provider import ArxivProvider
from backend.app.services.literature.normalization_service import NormalizationService
from backend.app.services.planner.strategy_generator import strategy_planner


async def tool_search_openalex(
    query: str,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    limit: int = 15,
) -> List[Dict[str, Any]]:
    """Searches OpenAlex works and returns normalized records."""
    provider = OpenAlexProvider()
    records = await provider.search(query, start_year, end_year, limit)
    normalizer = NormalizationService()
    return [normalizer.normalize_record(r).model_dump() for r in records]


async def tool_search_semantic_scholar(
    query: str,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    limit: int = 15,
) -> List[Dict[str, Any]]:
    """Searches Semantic Scholar academic graph and returns normalized records."""
    provider = SemanticScholarProvider()
    records = await provider.search(query, start_year, end_year, limit)
    normalizer = NormalizationService()
    return [normalizer.normalize_record(r).model_dump() for r in records]


async def tool_search_crossref(
    query: str,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    limit: int = 15,
) -> List[Dict[str, Any]]:
    """Searches Crossref works and returns normalized records."""
    provider = CrossrefProvider()
    records = await provider.search(query, start_year, end_year, limit)
    normalizer = NormalizationService()
    return [normalizer.normalize_record(r).model_dump() for r in records]


async def tool_search_arxiv(
    query: str,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    limit: int = 15,
) -> List[Dict[str, Any]]:
    """Searches arXiv scientific preprints and returns normalized records."""
    provider = ArxivProvider()
    records = await provider.search(query, start_year, end_year, limit)
    normalizer = NormalizationService()
    return [normalizer.normalize_record(r).model_dump() for r in records]


async def tool_retrieve_paper_by_doi(doi: str, provider: str = "crossref") -> Optional[Dict[str, Any]]:
    """Retrieves authoritative paper metadata for a given DOI."""
    target_prov = provider.lower()
    if target_prov == "crossref":
        prov = CrossrefProvider()
    elif target_prov == "openalex":
        prov = OpenAlexProvider()
    elif target_prov in ("semantic_scholar", "semanticscholar"):
        prov = SemanticScholarProvider()
    else:
        prov = CrossrefProvider()

    record = await prov.retrieve_by_doi(doi)
    if not record:
        return None
    return NormalizationService().normalize_record(record).model_dump()


def tool_generate_search_strategy(
    topic: str,
    objective: str,
    domain: str,
    research_questions: List[str],
    preferred_databases: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Generates structured search concepts, keywords, and database queries."""
    dbs = preferred_databases or ["openalex", "semantic_scholar", "crossref", "arxiv"]
    return strategy_planner.generate(topic, objective, domain, research_questions, dbs)


def tool_screen_paper_content(
    title: str,
    abstract: str,
    topic: str,
    objective: str,
    start_year: int,
    end_year: int,
    publication_year: Optional[int] = None,
) -> Dict[str, Any]:
    """Performs staged screening evaluation on a paper's title and abstract."""
    from backend.app.models.paper import Paper
    from backend.app.models.research_request import ResearchRequest
    from backend.app.services.screening.criteria_evaluator import ScreeningCriteriaEvaluator

    dummy_paper = Paper(
        id="mcp-temp",
        request_id="mcp-req",
        title=title,
        normalized_title=title.lower(),
        abstract=abstract,
        publication_year=publication_year or start_year,
        keywords=[],
    )
    dummy_req = ResearchRequest(
        id="mcp-req",
        topic=topic,
        objective=objective,
        domain="AI",
        start_year=start_year,
        end_year=end_year,
    )
    evaluator = ScreeningCriteriaEvaluator()
    decision, reason, evaluated, satisfied, unsatisfied, missing, conf = evaluator.evaluate_paper(
        dummy_paper, dummy_req
    )
    return {
        "decision": decision,
        "reason": reason,
        "criteria_evaluated": evaluated,
        "criteria_satisfied": satisfied,
        "criteria_unsatisfied": unsatisfied,
        "missing_information": missing,
        "confidence_score": conf,
    }


async def tool_extract_paper_evidence(
    paper_id: str,
    title: str,
    abstract: Optional[str] = None,
    raw_text: Optional[str] = None,
) -> Dict[str, Any]:
    """Extracts structured research objectives, methodologies, datasets, findings, and limitations."""
    from backend.app.services.extraction.rule_extractor import RuleBasedEvidenceExtractor

    extractor = RuleBasedEvidenceExtractor()
    sections = []
    scope = "abstract_only"
    if raw_text and len(raw_text) > 100:
        sections = [{"page_number": 1, "heading": "Main Text", "text": raw_text}]
        scope = "full_text"

    res = await extractor.extract_evidence(
        paper_id=paper_id,
        title=title,
        abstract=abstract,
        fulltext_sections=sections,
        source_scope=scope,
    )
    return res.model_dump()


# ---------------------------------------------------------
# Phase 3: Evidence Graph MCP Tool Implementations
# ---------------------------------------------------------

def tool_build_evidence_graph(request_id: str, db: Optional[Any] = None) -> Dict[str, Any]:
    """Constructs knowledge graph for a research request from Phase 2 evidence."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.graph.graph_builder import EvidenceGraphBuilder
    from backend.app.services.graph.graph_validation_service import GraphValidationService

    session = db or SessionLocal()
    try:
        builder = EvidenceGraphBuilder(session)
        run = builder.build_graph(request_id, trigger_type="full_build")
        val = GraphValidationService(session).validate_graph(request_id, build_run_id=run.id)
        return {
            "status": "completed",
            "run_number": run.run_number,
            "total_nodes": run.total_nodes,
            "total_edges": run.total_edges,
            "nodes_added": run.nodes_added,
            "edges_added": run.edges_added,
            "papers_processed": run.papers_processed,
            "integrity_status": val.integrity_status,
        }
    finally:
        if db is None:
            session.close()


def tool_synchronize_evidence_graph(request_id: str, db: Optional[Any] = None) -> Dict[str, Any]:
    """Idempotently synchronizes newly extracted evidence into the graph."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.graph.graph_builder import EvidenceGraphBuilder

    session = db or SessionLocal()
    try:
        builder = EvidenceGraphBuilder(session)
        run = builder.build_graph(request_id, trigger_type="incremental_sync")
        return {
            "status": "synchronized",
            "run_number": run.run_number,
            "total_nodes": run.total_nodes,
            "total_edges": run.total_edges,
            "nodes_added": run.nodes_added,
            "nodes_updated": run.nodes_updated,
            "edges_added": run.edges_added,
        }
    finally:
        if db is None:
            session.close()


def tool_get_graph_statistics(request_id: str, db: Optional[Any] = None) -> Dict[str, Any]:
    """Retrieves real-time counts and verification stats of the evidence graph."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.persistence.graph_repository import GraphRepository

    session = db or SessionLocal()
    try:
        repo = GraphRepository(session)
        nodes = repo.get_nodes_by_request(request_id)
        edges = repo.get_edges_by_request(request_id)
        nodes_by_type = {}
        for n in nodes:
            nodes_by_type[n.node_type] = nodes_by_type.get(n.node_type, 0) + 1
        rels_by_type = {}
        for e in edges:
            rels_by_type[e.relationship_type] = rels_by_type.get(e.relationship_type, 0) + 1
        return {
            "request_id": request_id,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "nodes_by_type": nodes_by_type,
            "relationships_by_type": rels_by_type,
        }
    finally:
        if db is None:
            session.close()


def tool_query_papers_by_method(request_id: str, method_name: str, db: Optional[Any] = None) -> List[Dict[str, Any]]:
    """Finds all papers utilizing a particular methodology."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.graph.graph_query_service import EvidenceGraphQueryService

    session = db or SessionLocal()
    try:
        return EvidenceGraphQueryService(session).find_papers_by_method(request_id, method_name)
    finally:
        if db is None:
            session.close()


def tool_query_papers_by_dataset(request_id: str, dataset_name: str, db: Optional[Any] = None) -> List[Dict[str, Any]]:
    """Finds all papers evaluated on a benchmark dataset."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.graph.graph_query_service import EvidenceGraphQueryService

    session = db or SessionLocal()
    try:
        return EvidenceGraphQueryService(session).find_papers_by_dataset(request_id, dataset_name)
    finally:
        if db is None:
            session.close()


def tool_query_papers_by_model(request_id: str, model_name: str, db: Optional[Any] = None) -> List[Dict[str, Any]]:
    """Finds all papers using a specific model architecture."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.graph.graph_query_service import EvidenceGraphQueryService

    session = db or SessionLocal()
    try:
        return EvidenceGraphQueryService(session).find_papers_by_model(request_id, model_name)
    finally:
        if db is None:
            session.close()


def tool_get_paper_evidence_graph(paper_id: str, db: Optional[Any] = None) -> Dict[str, Any]:
    """Retrieves the connected neighborhood for a research paper."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.graph.graph_query_service import EvidenceGraphQueryService

    session = db or SessionLocal()
    try:
        sub = EvidenceGraphQueryService(session).get_paper_subgraph(paper_id)
        return {
            "paper_id": paper_id,
            "nodes_count": len(sub["nodes"]),
            "edges_count": len(sub["edges"]),
            "nodes": [{"id": n.id, "type": n.node_type, "label": n.label} for n in sub["nodes"]],
        }
    finally:
        if db is None:
            session.close()


def tool_get_claim_evidence(claim_id: str, db: Optional[Any] = None) -> List[Dict[str, Any]]:
    """Retrieves exact evidence passages supporting a claim."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.graph.graph_query_service import EvidenceGraphQueryService

    session = db or SessionLocal()
    try:
        return EvidenceGraphQueryService(session).find_passages_supporting_claim(claim_id)
    finally:
        if db is None:
            session.close()


def tool_get_evidence_provenance(claim_id: str, db: Optional[Any] = None) -> Dict[str, Any]:
    """Retrieves full provenance chain for a claim."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.graph.graph_query_service import EvidenceGraphQueryService

    session = db or SessionLocal()
    try:
        chain = EvidenceGraphQueryService(session).get_claim_provenance_chain(claim_id)
        return chain.model_dump()
    finally:
        if db is None:
            session.close()


def tool_get_graph_validation_report(request_id: str, db: Optional[Any] = None) -> Dict[str, Any]:
    """Audits graph integrity and provenance consistency."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.graph.graph_validation_service import GraphValidationService

    session = db or SessionLocal()
    try:
        val = GraphValidationService(session).validate_graph(request_id)
        return {
            "integrity_status": val.integrity_status,
            "total_nodes": val.total_nodes,
            "total_relationships": val.total_relationships,
            "claims_with_evidence": val.claims_with_evidence,
            "claims_without_evidence": val.claims_without_evidence,
            "orphan_nodes_count": val.orphan_nodes_count,
            "unresolved_entities_count": val.unresolved_entities_count,
        }
    finally:
        if db is None:
            session.close()


def tool_find_shared_methods(paper_id_a: str, paper_id_b: str, db: Optional[Any] = None) -> List[str]:
    """Identifies methods used by both papers."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.graph.graph_query_service import EvidenceGraphQueryService

    session = db or SessionLocal()
    try:
        return EvidenceGraphQueryService(session).find_shared_methods_between_papers(paper_id_a, paper_id_b)
    finally:
        if db is None:
            session.close()


def tool_find_shared_datasets(paper_id_a: str, paper_id_b: str, db: Optional[Any] = None) -> List[str]:
    """Identifies datasets evaluated in both papers."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.graph.graph_query_service import EvidenceGraphQueryService

    session = db or SessionLocal()
    try:
        return EvidenceGraphQueryService(session).find_shared_datasets_between_papers(paper_id_a, paper_id_b)
    finally:
        if db is None:
            session.close()



