"""FastAPI routes exposing MCP tool definitions and server metadata."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/mcp", tags=["Model Context Protocol (MCP)"])


@router.get("/tools")
def list_mcp_tools():
    """Returns metadata for all exposed academic MCP tools."""
    return {
        "mcp_server": "academic-literature-review-mcp",
        "protocol_version": "2024-11-05",
        "tools": [
            {
                "name": "search_openalex",
                "description": "Searches OpenAlex works index (250M+ scientific publications)",
                "parameters": {
                    "query": "string (required)",
                    "start_year": "integer (optional)",
                    "end_year": "integer (optional)",
                    "limit": "integer (optional, default 15)",
                },
            },
            {
                "name": "search_semantic_scholar",
                "description": "Searches Semantic Scholar academic graph with citation metadata",
                "parameters": {
                    "query": "string (required)",
                    "start_year": "integer (optional)",
                    "end_year": "integer (optional)",
                    "limit": "integer (optional, default 15)",
                },
            },
            {
                "name": "search_crossref",
                "description": "Searches Crossref registry for published DOI works",
                "parameters": {
                    "query": "string (required)",
                    "start_year": "integer (optional)",
                    "end_year": "integer (optional)",
                    "limit": "integer (optional, default 15)",
                },
            },
            {
                "name": "search_arxiv",
                "description": "Searches arXiv preprint repository with category metadata",
                "parameters": {
                    "query": "string (required)",
                    "start_year": "integer (optional)",
                    "end_year": "integer (optional)",
                    "limit": "integer (optional, default 15)",
                },
            },
            {
                "name": "retrieve_paper_by_doi",
                "description": "Resolves exact paper metadata for a specific DOI",
                "parameters": {
                    "doi": "string (required)",
                    "provider": "string (optional: crossref, openalex, semantic_scholar)",
                },
            },
            {
                "name": "generate_academic_search_strategy",
                "description": "Decomposes a research request into concepts, keywords, and database queries",
                "parameters": {
                    "topic": "string (required)",
                    "objective": "string (required)",
                    "domain": "string (required)",
                    "research_questions": "list of strings (required)",
                    "preferred_databases": "list of strings (optional)",
                },
            },
        ],
    }

