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
            {
                "name": "screen_research_paper",
                "description": "Evaluates paper eligibility against research scope and criteria (Phase 2)",
                "parameters": {
                    "title": "string (required)",
                    "abstract": "string (required)",
                    "topic": "string (required)",
                    "objective": "string (required)",
                    "start_year": "integer (required)",
                    "end_year": "integer (required)",
                    "publication_year": "integer (optional)",
                },
            },
            {
                "name": "extract_paper_evidence",
                "description": "Extracts structured research objectives, methodologies, datasets, findings, and limitations (Phase 2)",
                "parameters": {
                    "paper_id": "string (required)",
                    "title": "string (required)",
                    "abstract": "string (optional)",
                    "raw_text": "string (optional)",
                },
            },
            {
                "name": "build_evidence_graph",
                "description": "Constructs knowledge graph for a research request from Phase 2 evidence (Phase 3)",
                "parameters": {
                    "request_id": "string (required)",
                },
            },
            {
                "name": "synchronize_evidence_graph",
                "description": "Idempotently synchronizes newly extracted evidence into the graph (Phase 3)",
                "parameters": {
                    "request_id": "string (required)",
                },
            },
            {
                "name": "get_graph_statistics",
                "description": "Retrieves real-time counts and verification stats of the evidence graph (Phase 3)",
                "parameters": {
                    "request_id": "string (required)",
                },
            },
            {
                "name": "query_papers_by_method",
                "description": "Finds all papers utilizing a particular methodology (Phase 3)",
                "parameters": {
                    "request_id": "string (required)",
                    "method_name": "string (required)",
                },
            },
            {
                "name": "query_papers_by_dataset",
                "description": "Finds all papers evaluated on a benchmark dataset (Phase 3)",
                "parameters": {
                    "request_id": "string (required)",
                    "dataset_name": "string (required)",
                },
            },
            {
                "name": "query_papers_by_model",
                "description": "Finds all papers using a specific model architecture (Phase 3)",
                "parameters": {
                    "request_id": "string (required)",
                    "model_name": "string (required)",
                },
            },
            {
                "name": "get_paper_evidence_graph",
                "description": "Retrieves the connected neighborhood for a research paper (Phase 3)",
                "parameters": {
                    "paper_id": "string (required)",
                },
            },
            {
                "name": "get_claim_evidence",
                "description": "Retrieves exact evidence passages supporting a claim (Phase 3)",
                "parameters": {
                    "claim_id": "string (required)",
                },
            },
            {
                "name": "get_evidence_provenance",
                "description": "Retrieves full provenance chain for a claim (Phase 3)",
                "parameters": {
                    "claim_id": "string (required)",
                },
            },
            {
                "name": "get_graph_validation_report",
                "description": "Audits graph integrity and provenance consistency (Phase 3)",
                "parameters": {
                    "request_id": "string (required)",
                },
            },
            {
                "name": "find_shared_methods",
                "description": "Identifies methods used by both papers (Phase 3)",
                "parameters": {
                    "paper_id_a": "string (required)",
                    "paper_id_b": "string (required)",
                },
            },
            {
                "name": "find_shared_datasets",
                "description": "Identifies datasets evaluated in both papers (Phase 3)",
                "parameters": {
                    "paper_id_a": "string (required)",
                    "paper_id_b": "string (required)",
                },
            },

        ],
    }

