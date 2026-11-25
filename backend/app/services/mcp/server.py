"""Official Python MCP Server for Academic Literature Retrieval.

Exposes standardized MCP tools allowing autonomous AI research agents
to search academic databases, resolve DOIs, and construct search strategies.
"""

from typing import List, Optional, Dict, Any
from mcp.server.mcpserver import MCPServer
from backend.app.services.mcp.tools import (
    tool_search_openalex,
    tool_search_semantic_scholar,
    tool_search_crossref,
    tool_search_arxiv,
    tool_retrieve_paper_by_doi,
    tool_generate_search_strategy,
    tool_screen_paper_content,
    tool_extract_paper_evidence,
    tool_build_evidence_graph,
    tool_synchronize_evidence_graph,
    tool_get_graph_statistics,
    tool_query_papers_by_method,
    tool_query_papers_by_dataset,
    tool_query_papers_by_model,
    tool_get_paper_evidence_graph,
    tool_get_claim_evidence,
    tool_get_evidence_provenance,
    tool_get_graph_validation_report,
    tool_find_shared_methods,
    tool_find_shared_datasets,
    tool_get_literature_synthesis,
    tool_generate_literature_synthesis,
    tool_get_paper_comparison_matrix,
    tool_identify_research_themes,
    tool_analyze_methodology_trends,
    tool_analyze_dataset_trends,
    tool_analyze_research_trends,
    tool_generate_candidate_research_gaps,
    tool_get_candidate_gap_details,
    tool_get_candidate_gap_evidence,
    tool_update_candidate_gap_review,
    tool_get_synthesis_history,
)

# Initialize MCP server
mcp_server = MCPServer("academic-literature-review-mcp")


@mcp_server.tool()
async def search_openalex(
    query: str,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    limit: int = 15,
) -> List[Dict[str, Any]]:
    """Searches OpenAlex works repository.

    Args:
        query: Academic search query string or topic.
        start_year: Minimum publication year filter.
        end_year: Maximum publication year filter.
        limit: Number of results to return (max 50).
    """
    return await tool_search_openalex(query, start_year, end_year, limit)


@mcp_server.tool()
async def search_semantic_scholar(
    query: str,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    limit: int = 15,
) -> List[Dict[str, Any]]:
    """Searches Semantic Scholar academic graph.

    Args:
        query: Academic search query.
        start_year: Minimum publication year filter.
        end_year: Maximum publication year filter.
        limit: Number of results to return (max 50).
    """
    return await tool_search_semantic_scholar(query, start_year, end_year, limit)


@mcp_server.tool()
async def search_crossref(
    query: str,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    limit: int = 15,
) -> List[Dict[str, Any]]:
    """Searches Crossref bibliographic database.

    Args:
        query: Search query for titles, authors, and bibliographic works.
        start_year: Minimum publication year filter.
        end_year: Maximum publication year filter.
        limit: Number of results to return (max 50).
    """
    return await tool_search_crossref(query, start_year, end_year, limit)


@mcp_server.tool()
async def search_arxiv(
    query: str,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    limit: int = 15,
) -> List[Dict[str, Any]]:
    """Searches arXiv preprint repository.

    Args:
        query: Scientific search query (e.g., all:"transformer" AND all:"interpretability").
        start_year: Minimum publication year filter.
        end_year: Maximum publication year filter.
        limit: Number of results to return (max 50).
    """
    return await tool_search_arxiv(query, start_year, end_year, limit)


@mcp_server.tool()
async def retrieve_paper_by_doi(
    doi: str,
    provider: str = "crossref",
) -> Optional[Dict[str, Any]]:
    """Retrieves authoritative paper metadata for a specific DOI identifier.

    Args:
        doi: Clean DOI (e.g. 10.1145/3308558.3313704) or URL.
        provider: Provider to consult ("crossref", "openalex", "semantic_scholar").
    """
    return await tool_retrieve_paper_by_doi(doi, provider)


@mcp_server.tool()
def generate_academic_search_strategy(
    topic: str,
    objective: str,
    domain: str,
    research_questions: List[str],
    preferred_databases: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Generates structured academic concepts, keywords, synonyms, and database queries.

    Args:
        topic: Core scientific research topic.
        objective: Main research objective of review.
        domain: Academic domain (e.g. Artificial Intelligence, NLP).
        research_questions: Specific research questions.
        preferred_databases: List of target databases (openalex, semantic_scholar, crossref, arxiv).
    """
    return tool_generate_search_strategy(topic, objective, domain, research_questions, preferred_databases)


@mcp_server.tool()
def screen_research_paper(
    title: str,
    abstract: str,
    topic: str,
    objective: str,
    start_year: int,
    end_year: int,
    publication_year: Optional[int] = None,
) -> Dict[str, Any]:
    """Evaluates paper eligibility against research scope and criteria (Phase 2).

    Args:
        title: Scientific paper title.
        abstract: Paper abstract text.
        topic: Research topic to screen against.
        objective: Primary research objective.
        start_year: Minimum publication year.
        end_year: Maximum publication year.
        publication_year: Optional publication year of paper.
    """
    return tool_screen_paper_content(
        title, abstract, topic, objective, start_year, end_year, publication_year
    )


@mcp_server.tool()
async def extract_paper_evidence(
    paper_id: str,
    title: str,
    abstract: Optional[str] = None,
    raw_text: Optional[str] = None,
) -> Dict[str, Any]:
    """Extracts structured research objectives, methodologies, datasets, findings, and limitations (Phase 2).

    Args:
        paper_id: Paper unique identifier.
        title: Title of research article.
        abstract: Abstract text.
        raw_text: Optional full-text extracted paper content.
    """
    return await tool_extract_paper_evidence(paper_id, title, abstract, raw_text)


# ---------------------------------------------------------
# Phase 3: Evidence Graph MCP Tools
# ---------------------------------------------------------

@mcp_server.tool()
def build_evidence_graph(request_id: str) -> Dict[str, Any]:
    """Constructs knowledge graph for a research request from Phase 2 evidence (Phase 3)."""
    return tool_build_evidence_graph(request_id)


@mcp_server.tool()
def synchronize_evidence_graph(request_id: str) -> Dict[str, Any]:
    """Idempotently synchronizes newly extracted evidence into the graph (Phase 3)."""
    return tool_synchronize_evidence_graph(request_id)


@mcp_server.tool()
def get_graph_statistics(request_id: str) -> Dict[str, Any]:
    """Retrieves real-time counts and verification stats of the evidence graph (Phase 3)."""
    return tool_get_graph_statistics(request_id)


@mcp_server.tool()
def query_papers_by_method(request_id: str, method_name: str) -> List[Dict[str, Any]]:
    """Finds all papers utilizing a particular methodology (Phase 3)."""
    return tool_query_papers_by_method(request_id, method_name)


@mcp_server.tool()
def query_papers_by_dataset(request_id: str, dataset_name: str) -> List[Dict[str, Any]]:
    """Finds all papers evaluated on a benchmark dataset (Phase 3)."""
    return tool_query_papers_by_dataset(request_id, dataset_name)


@mcp_server.tool()
def query_papers_by_model(request_id: str, model_name: str) -> List[Dict[str, Any]]:
    """Finds all papers using a specific model architecture (Phase 3)."""
    return tool_query_papers_by_model(request_id, model_name)


@mcp_server.tool()
def get_paper_evidence_graph(paper_id: str) -> Dict[str, Any]:
    """Retrieves the connected neighborhood for a research paper (Phase 3)."""
    return tool_get_paper_evidence_graph(paper_id)


@mcp_server.tool()
def get_claim_evidence(claim_id: str) -> List[Dict[str, Any]]:
    """Retrieves exact evidence passages supporting a claim (Phase 3)."""
    return tool_get_claim_evidence(claim_id)


@mcp_server.tool()
def get_evidence_provenance(claim_id: str) -> Dict[str, Any]:
    """Retrieves full provenance chain for a claim (Phase 3)."""
    return tool_get_evidence_provenance(claim_id)


@mcp_server.tool()
def get_graph_validation_report(request_id: str) -> Dict[str, Any]:
    """Audits graph integrity and provenance consistency (Phase 3)."""
    return tool_get_graph_validation_report(request_id)


@mcp_server.tool()
def find_shared_methods(paper_id_a: str, paper_id_b: str) -> List[str]:
    """Identifies methods used by both papers (Phase 3)."""
    return tool_find_shared_methods(paper_id_a, paper_id_b)


@mcp_server.tool()
def find_shared_datasets(paper_id_a: str, paper_id_b: str) -> List[str]:
    """Identifies datasets evaluated in both papers (Phase 3)."""
    return tool_find_shared_datasets(paper_id_a, paper_id_b)


# ==============================================================================
# PHASE 4 TOOLS: Literature Synthesis & Candidate Research-Gap Generation
# ==============================================================================

@mcp_server.tool()
def generate_literature_synthesis(
    request_id: str,
    selected_paper_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Executes a full literature synthesis run producing themes, patterns, and candidate gaps (Phase 4)."""
    return tool_generate_literature_synthesis(request_id, selected_paper_ids)


@mcp_server.tool()
def get_literature_synthesis(
    request_id: str,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Retrieves structured narrative literature synthesis and section overviews (Phase 4)."""
    return tool_get_literature_synthesis(request_id, run_id)


@mcp_server.tool()
def get_paper_comparison_matrix(
    request_id: str,
    method: Optional[str] = None,
    dataset: Optional[str] = None,
    model: Optional[str] = None,
    year: Optional[int] = None,
) -> Dict[str, Any]:
    """Extracts a multidimensional comparison matrix across screened papers (Phase 4)."""
    return tool_get_paper_comparison_matrix(request_id, method, dataset, model, year)


@mcp_server.tool()
def identify_research_themes(
    request_id: str,
) -> List[Dict[str, Any]]:
    """Identifies recurring methodological, empirical, and theoretical research themes (Phase 4)."""
    return tool_identify_research_themes(request_id)


@mcp_server.tool()
def analyze_methodology_trends(
    request_id: str,
) -> Dict[str, Any]:
    """Analyzes methodology frequencies and algorithmic combinations across literature (Phase 4)."""
    return tool_analyze_methodology_trends(request_id)


@mcp_server.tool()
def analyze_dataset_trends(
    request_id: str,
) -> Dict[str, Any]:
    """Analyzes benchmark dataset usage and method-dataset cross-tabulations (Phase 4)."""
    return tool_analyze_dataset_trends(request_id)


@mcp_server.tool()
def analyze_research_trends(
    request_id: str,
) -> List[Dict[str, Any]]:
    """Analyzes empirical patterns across methods, datasets, models, metrics, and years (Phase 4)."""
    return tool_analyze_research_trends(request_id)


@mcp_server.tool()
def generate_candidate_research_gaps(
    request_id: str,
    synthesis_run_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Generates evidence-backed candidate research gaps across 10 gap categories (Phase 4)."""
    return tool_generate_candidate_research_gaps(request_id, synthesis_run_id)


@mcp_server.tool()
def get_candidate_gap_details(
    gap_id: str,
) -> Dict[str, Any]:
    """Retrieves full candidate research gap description, rationale, assumptions, and validation queries (Phase 4)."""
    return tool_get_candidate_gap_details(gap_id)


@mcp_server.tool()
def get_candidate_gap_evidence(
    gap_id: str,
) -> List[Dict[str, Any]]:
    """Retrieves verbatim evidence passages and grounding links backing a candidate gap (Phase 4)."""
    return tool_get_candidate_gap_evidence(gap_id)


@mcp_server.tool()
def update_candidate_gap_review(
    gap_id: str,
    action: str,
    reviewer: str = "agent",
    comment: Optional[str] = None,
    revised_title: Optional[str] = None,
    revised_description: Optional[str] = None,
) -> Dict[str, Any]:
    """Records human review decisions (accept, reject, request_evidence, edit) on a candidate gap (Phase 4)."""
    return tool_update_candidate_gap_review(
        gap_id, action, reviewer, comment, revised_title, revised_description
    )


@mcp_server.tool()
def get_synthesis_history(
    request_id: str,
) -> List[Dict[str, Any]]:
    """Retrieves previous synthesis runs and configuration snapshots for reproducibility (Phase 4)."""
    return tool_get_synthesis_history(request_id)


if __name__ == "__main__":
    # Runs the MCP server with stdio transport
    mcp_server.run()

