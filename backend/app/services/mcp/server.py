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


if __name__ == "__main__":
    # Runs the MCP server with stdio transport
    mcp_server.run()

