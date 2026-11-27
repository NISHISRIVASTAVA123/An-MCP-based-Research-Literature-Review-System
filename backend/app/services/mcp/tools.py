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


# ==============================================================================
# PHASE 4 MCP TOOLS: Literature Synthesis & Candidate Gap Generation
# ==============================================================================

def tool_generate_literature_synthesis(
    request_id: str,
    selected_paper_ids: Optional[List[str]] = None,
    db: Optional[Any] = None,
) -> Dict[str, Any]:
    """Generates a complete literature synthesis run with themes, patterns, and candidate gaps."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.synthesis.synthesis_orchestrator import SynthesisOrchestrator
    from backend.app.schemas.synthesis import SynthesisRunCreate

    session = db or SessionLocal()
    try:
        orchestrator = SynthesisOrchestrator(session)
        payload = SynthesisRunCreate(selected_paper_ids=selected_paper_ids)
        run = orchestrator.execute_synthesis_run(request_id, payload)
        return {
            "run_id": run.id,
            "status": run.status,
            "run_number": run.run_number,
            "selected_papers_count": len(run.selected_paper_ids or []),
            "created_at": run.created_at.isoformat() if run.created_at else None,
        }
    finally:
        if db is None:
            session.close()


def tool_get_literature_synthesis(
    request_id: str,
    run_id: Optional[str] = None,
    db: Optional[Any] = None,
) -> Dict[str, Any]:
    """Retrieves the narrative and structured literature synthesis for a run."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.persistence.synthesis_repository import SynthesisRepository

    session = db or SessionLocal()
    try:
        repo = SynthesisRepository(session)
        run = repo.get_synthesis_run(run_id) if run_id else repo.get_latest_synthesis_run(request_id)
        if not run:
            return {"error": "No synthesis run found."}
        return {
            "run_id": run.id,
            "status": run.status,
            "summary_narrative": run.summary_narrative,
            "created_at": run.created_at.isoformat() if run.created_at else None,
        }
    finally:
        if db is None:
            session.close()


def tool_get_paper_comparison_matrix(
    request_id: str,
    method: Optional[str] = None,
    dataset: Optional[str] = None,
    model: Optional[str] = None,
    year: Optional[int] = None,
    db: Optional[Any] = None,
) -> Dict[str, Any]:
    """Constructs dynamic multidimensional comparison matrix across papers."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.synthesis.comparison_matrix_service import PaperComparisonMatrixService

    session = db or SessionLocal()
    try:
        matrix = PaperComparisonMatrixService(session).generate_matrix(
            request_id=request_id,
            method_filter=method,
            dataset_filter=dataset,
            model_filter=model,
            year_filter=year,
        )
        return matrix.model_dump()
    finally:
        if db is None:
            session.close()


def tool_identify_research_themes(
    request_id: str,
    db: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Discovers recurring research themes across retrieved literature."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.synthesis.theme_service import ResearchThemeService

    session = db or SessionLocal()
    try:
        return ResearchThemeService(session).identify_themes(request_id)
    finally:
        if db is None:
            session.close()


def tool_analyze_methodology_trends(
    request_id: str,
    db: Optional[Any] = None,
) -> Dict[str, Any]:
    """Analyzes methodology usage frequencies and combinations across papers."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.synthesis.pattern_analysis_service import PatternAnalysisService

    session = db or SessionLocal()
    try:
        patterns = PatternAnalysisService(session).analyze_patterns(request_id)
        meth_pat = next((p for p in patterns if p["pattern_type"] == "methodology"), None)
        return meth_pat or {"error": "No methodology pattern detected."}
    finally:
        if db is None:
            session.close()


def tool_analyze_dataset_trends(
    request_id: str,
    db: Optional[Any] = None,
) -> Dict[str, Any]:
    """Analyzes benchmark dataset distributions and method-dataset cross-tabulations."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.synthesis.pattern_analysis_service import PatternAnalysisService

    session = db or SessionLocal()
    try:
        patterns = PatternAnalysisService(session).analyze_patterns(request_id)
        ds_pat = next((p for p in patterns if p["pattern_type"] == "dataset"), None)
        return ds_pat or {"error": "No dataset pattern detected."}
    finally:
        if db is None:
            session.close()


def tool_analyze_research_trends(
    request_id: str,
    db: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Analyzes comprehensive empirical, evaluation, and publication year trends."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.synthesis.pattern_analysis_service import PatternAnalysisService

    session = db or SessionLocal()
    try:
        return PatternAnalysisService(session).analyze_patterns(request_id)
    finally:
        if db is None:
            session.close()


def tool_generate_candidate_research_gaps(
    request_id: str,
    synthesis_run_id: Optional[str] = None,
    db: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Generates traceable candidate research gaps from literature patterns."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.persistence.synthesis_repository import SynthesisRepository
    from backend.app.services.synthesis.gap_generator import CandidateResearchGapGenerator

    session = db or SessionLocal()
    try:
        repo = SynthesisRepository(session)
        run = repo.get_synthesis_run(synthesis_run_id) if synthesis_run_id else repo.get_latest_synthesis_run(request_id)
        if not run:
            # Trigger run if none exists
            from backend.app.services.synthesis.synthesis_orchestrator import SynthesisOrchestrator
            run = SynthesisOrchestrator(session).execute_synthesis_run(request_id)

        gaps = repo.get_candidate_gaps_by_run(run.id)
        return [
            {
                "id": g.id,
                "title": g.title,
                "category": g.category,
                "preliminary_confidence": g.preliminary_confidence,
                "supporting_papers_count": len(g.supporting_paper_ids or []),
                "review_status": g.human_review_status,
            }
            for g in gaps
        ]
    finally:
        if db is None:
            session.close()


def tool_get_candidate_gap_details(
    gap_id: str,
    db: Optional[Any] = None,
) -> Dict[str, Any]:
    """Retrieves full candidate research gap description, rationale, and assumptions."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.synthesis.review_service import SynthesisReviewService

    session = db or SessionLocal()
    try:
        gap = SynthesisReviewService(session).get_gap_with_provenance(gap_id)
        return gap or {"error": f"Candidate gap '{gap_id}' not found."}
    finally:
        if db is None:
            session.close()


def tool_get_candidate_gap_evidence(
    gap_id: str,
    db: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Retrieves verbatim evidence passages and grounding links backing a candidate gap."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.synthesis.review_service import SynthesisReviewService

    session = db or SessionLocal()
    try:
        gap = SynthesisReviewService(session).get_gap_with_provenance(gap_id)
        if not gap:
            return [{"error": f"Candidate gap '{gap_id}' not found."}]
        return gap.get("evidence_links", [])
    finally:
        if db is None:
            session.close()


def tool_update_candidate_gap_review(
    gap_id: str,
    action: str,
    reviewer: str = "agent",
    comment: Optional[str] = None,
    revised_title: Optional[str] = None,
    revised_description: Optional[str] = None,
    db: Optional[Any] = None,
) -> Dict[str, Any]:
    """Records a human or agent review decision on a candidate research gap."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.synthesis.review_service import SynthesisReviewService
    from backend.app.schemas.synthesis import HumanReviewRequest

    session = db or SessionLocal()
    try:
        req = HumanReviewRequest(
            reviewer_reference=reviewer,
            review_action=action,
            reviewer_comment=comment,
            revised_title=revised_title,
            revised_description=revised_description,
        )
        updated_gap = SynthesisReviewService(session).review_candidate_gap(gap_id, req)
        return {
            "id": updated_gap.id,
            "title": updated_gap.title,
            "human_review_status": updated_gap.human_review_status,
            "updated_at": updated_gap.updated_at.isoformat() if updated_gap.updated_at else None,
        }
    finally:
        if db is None:
            session.close()


def tool_get_synthesis_history(
    request_id: str,
    db: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Lists past synthesis runs with version metadata for reproducibility."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.persistence.synthesis_repository import SynthesisRepository

    session = db or SessionLocal()
    try:
        runs = SynthesisRepository(session).get_synthesis_runs_by_request(request_id)
        return [
            {
                "id": r.id,
                "run_number": r.run_number,
                "status": r.status,
                "paper_count": len(r.selected_paper_ids or []),
                "graph_version": r.evidence_graph_version,
                "model_name": r.model_name,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in runs
        ]
    finally:
        if db is None:
            session.close()


# ==========================================
# Phase 5 MCP Tools: Explicit Counterevidence Retrieval
# ==========================================

def tool_generate_counterevidence_queries(
    gap_id: str,
    db: Optional[Any] = None,
) -> Dict[str, Any]:
    """Decomposes a candidate gap into empirical claims and generates counterevidence queries."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.models.synthesis import CandidateResearchGap
    from backend.app.services.counterevidence.claim_decomposer import GapClaimDecomposer
    from backend.app.services.counterevidence.query_generator import CounterevidenceQueryGenerator
    from sqlalchemy import select

    session = db or SessionLocal()
    try:
        gap = session.execute(
            select(CandidateResearchGap).where(CandidateResearchGap.id == gap_id)
        ).scalar_one_or_none()
        if not gap:
            return {"error": f"Candidate gap '{gap_id}' not found."}

        claims = GapClaimDecomposer().decompose_gap(gap)
        queries = CounterevidenceQueryGenerator().generate_queries_for_claims(
            candidate_gap_id=gap.id,
            gap_title=gap.title,
            claims=claims,
        )
        return {
            "candidate_gap_id": gap_id,
            "gap_title": gap.title,
            "decomposed_claims": claims,
            "generated_queries": queries,
        }
    finally:
        if db is None:
            session.close()


async def tool_search_counterevidence(
    gap_id: str,
    request_id: str,
    databases: Optional[List[str]] = None,
    max_results: int = 10,
    db: Optional[Any] = None,
) -> Dict[str, Any]:
    """Runs autonomous counterevidence retrieval, relevance assessment, and profile aggregation for a gap."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.counterevidence.counterevidence_orchestrator import CounterevidenceOrchestrator

    session = db or SessionLocal()
    try:
        orchestrator = CounterevidenceOrchestrator(session)
        return await orchestrator.execute_search_for_gap(
            candidate_gap_id=gap_id,
            research_request_id=request_id,
            databases=databases,
            max_results_per_query=max_results,
        )
    finally:
        if db is None:
            session.close()


def tool_get_counterevidence_search_status(
    run_id: str,
    db: Optional[Any] = None,
) -> Dict[str, Any]:
    """Gets the execution status and metrics of a counterevidence search run."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.persistence.counterevidence_repository import CounterevidenceRepository

    session = db or SessionLocal()
    try:
        run = CounterevidenceRepository(session).get_search_run(run_id)
        if not run:
            return {"error": f"Search run '{run_id}' not found."}
        return {
            "id": run.id,
            "status": run.status,
            "candidate_gap_id": run.candidate_gap_id,
            "claims_count": run.total_claims_decomposed,
            "queries_count": run.total_queries_executed,
            "publications_found": run.total_publications_found,
            "newly_discovered_count": run.newly_discovered_count,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None,
            "error_message": run.error_message,
        }
    finally:
        if db is None:
            session.close()


def tool_get_counterevidence_publications(
    gap_id: str,
    db: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Retrieves publications discovered specifically through counterevidence queries for a candidate gap."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.persistence.counterevidence_repository import CounterevidenceRepository

    session = db or SessionLocal()
    try:
        pubs = CounterevidenceRepository(session).get_publications_by_gap(gap_id)
        results = []
        for p in pubs:
            paper = p.paper
            results.append({
                "id": p.id,
                "paper_id": p.paper_id,
                "title": paper.title if paper else None,
                "authors": paper.authors if paper else [],
                "year": paper.publication_year if paper else None,
                "doi": paper.doi if paper else None,
                "discovery_source": p.discovery_source,
                "is_newly_discovered": p.is_newly_discovered,
                "screening_status": p.screening_status,
                "retrieved_at": p.retrieved_at.isoformat() if p.retrieved_at else None,
            })
        return results
    finally:
        if db is None:
            session.close()


def tool_assess_counterevidence_relevance(
    gap_id: str,
    paper_id: str,
    db: Optional[Any] = None,
) -> Dict[str, Any]:
    """Assesses whether an individual paper directly, partially, or weakly challenges a candidate gap."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.persistence.counterevidence_repository import CounterevidenceRepository
    from backend.app.services.counterevidence.relevance_assessor import CounterevidenceRelevanceAssessor
    from backend.app.models.paper import Paper
    from backend.app.models.synthesis import CandidateResearchGap
    from backend.app.models.document import FulltextDocument
    from sqlalchemy import select

    session = db or SessionLocal()
    try:
        paper = session.execute(select(Paper).where(Paper.id == paper_id)).scalar_one_or_none()
        gap = session.execute(select(CandidateResearchGap).where(CandidateResearchGap.id == gap_id)).scalar_one_or_none()
        if not paper or not gap:
            return {"error": "Paper or CandidateGap not found."}

        ft_doc = session.execute(select(FulltextDocument).where(FulltextDocument.paper_id == paper_id)).scalar_one_or_none()
        assessment = CounterevidenceRelevanceAssessor().assess_paper_against_gap(paper, gap, fulltext_doc=ft_doc)
        return assessment
    finally:
        if db is None:
            session.close()


def tool_extract_counterevidence_evidence(
    gap_id: str,
    db: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    """Retrieves inspectable verbatim source passages supporting counterevidence assessments."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.persistence.counterevidence_repository import CounterevidenceRepository

    session = db or SessionLocal()
    try:
        items = CounterevidenceRepository(session).get_evidence_items_by_gap(gap_id)
        return [
            {
                "id": it.id,
                "paper_id": it.paper_id,
                "verbatim_passage": it.verbatim_passage,
                "page_number": it.page_number,
                "section_heading": it.section_heading,
                "evidence_type": it.evidence_type,
                "evidence_summary": it.evidence_summary,
                "verification_status": it.verification_status,
            }
            for it in items
        ]
    finally:
        if db is None:
            session.close()


def tool_get_counterevidence_profile(
    gap_id: str,
    db: Optional[Any] = None,
) -> Dict[str, Any]:
    """Retrieves the aggregated counterevidence impact assessment profile for a candidate gap."""
    from backend.app.services.persistence.database import SessionLocal
    from backend.app.services.persistence.counterevidence_repository import CounterevidenceRepository

    session = db or SessionLocal()
    try:
        profile = CounterevidenceRepository(session).get_profile_by_gap(gap_id)
        if not profile:
            return {"error": f"Counterevidence profile for gap '{gap_id}' has not been generated yet."}
        return {
            "candidate_gap_id": profile.candidate_gap_id,
            "impact_assessment": profile.impact_assessment,
            "total_retrieved": profile.total_retrieved,
            "direct_counterevidence_count": profile.direct_counterevidence_count,
            "partial_counterevidence_count": profile.partial_counterevidence_count,
            "related_evidence_count": profile.related_evidence_count,
            "irrelevant_count": profile.irrelevant_count,
            "inconclusive_count": profile.inconclusive_count,
            "executive_summary": profile.executive_summary,
            "remaining_unresolved_claims": profile.remaining_unresolved_claims,
            "verification_status": profile.verification_status,
            "generated_at": profile.generated_at.isoformat() if profile.generated_at else None,
        }
    finally:
        if db is None:
            session.close()





