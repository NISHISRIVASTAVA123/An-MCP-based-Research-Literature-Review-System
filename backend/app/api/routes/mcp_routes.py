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
            {
                "name": "generate_literature_synthesis",
                "description": "Executes a full literature synthesis run producing themes, patterns, and candidate gaps (Phase 4)",
                "parameters": {
                    "request_id": "string (required)",
                    "selected_paper_ids": "array of strings (optional)",
                },
            },
            {
                "name": "get_literature_synthesis",
                "description": "Retrieves structured narrative literature synthesis and section overviews (Phase 4)",
                "parameters": {
                    "request_id": "string (required)",
                    "run_id": "string (optional)",
                },
            },
            {
                "name": "get_paper_comparison_matrix",
                "description": "Extracts a multidimensional comparison matrix across screened papers (Phase 4)",
                "parameters": {
                    "request_id": "string (required)",
                    "method": "string (optional)",
                    "dataset": "string (optional)",
                    "model": "string (optional)",
                    "year": "integer (optional)",
                },
            },
            {
                "name": "identify_research_themes",
                "description": "Identifies recurring methodological, empirical, and theoretical research themes (Phase 4)",
                "parameters": {
                    "request_id": "string (required)",
                },
            },
            {
                "name": "analyze_methodology_trends",
                "description": "Analyzes methodology frequencies and algorithmic combinations across literature (Phase 4)",
                "parameters": {
                    "request_id": "string (required)",
                },
            },
            {
                "name": "analyze_dataset_trends",
                "description": "Analyzes benchmark dataset usage and method-dataset cross-tabulations (Phase 4)",
                "parameters": {
                    "request_id": "string (required)",
                },
            },
            {
                "name": "analyze_research_trends",
                "description": "Analyzes empirical patterns across methods, datasets, models, metrics, and years (Phase 4)",
                "parameters": {
                    "request_id": "string (required)",
                },
            },
            {
                "name": "generate_candidate_research_gaps",
                "description": "Generates evidence-backed candidate research gaps across 10 gap categories (Phase 4)",
                "parameters": {
                    "request_id": "string (required)",
                    "synthesis_run_id": "string (optional)",
                },
            },
            {
                "name": "get_candidate_gap_details",
                "description": "Retrieves full candidate research gap description, rationale, assumptions, and validation queries (Phase 4)",
                "parameters": {
                    "gap_id": "string (required)",
                },
            },
            {
                "name": "get_candidate_gap_evidence",
                "description": "Retrieves verbatim evidence passages and grounding links backing a candidate gap (Phase 4)",
                "parameters": {
                    "gap_id": "string (required)",
                },
            },
            {
                "name": "update_candidate_gap_review",
                "description": "Records human review decisions (accept, reject, request_evidence, edit) on a candidate gap (Phase 4)",
                "parameters": {
                    "gap_id": "string (required)",
                    "action": "string (required: accept, reject, request_evidence, edit)",
                    "reviewer": "string (optional, default 'agent')",
                    "comment": "string (optional)",
                    "revised_title": "string (optional)",
                    "revised_description": "string (optional)",
                },
            },
            {
                "name": "get_synthesis_history",
                "description": "Retrieves previous synthesis runs and configuration snapshots for reproducibility (Phase 4)",
                "parameters": {
                    "request_id": "string (required)",
                },
            },
            {
                "name": "generate_counterevidence_queries",
                "description": "Decomposes a candidate gap into empirical claims and generates multi-perspective counterevidence queries (Phase 5)",
                "parameters": {
                    "gap_id": "string (required)",
                },
            },
            {
                "name": "search_counterevidence",
                "description": "Runs autonomous counterevidence retrieval, relevance classification, and profile generation for a gap (Phase 5)",
                "parameters": {
                    "gap_id": "string (required)",
                    "request_id": "string (required)",
                    "databases": "array of strings (optional)",
                    "max_results": "integer (optional, default 10)",
                },
            },
            {
                "name": "get_counterevidence_search_status",
                "description": "Retrieves the status, metrics, and error logs of a counterevidence search execution (Phase 5)",
                "parameters": {
                    "run_id": "string (required)",
                },
            },
            {
                "name": "get_counterevidence_publications",
                "description": "Retrieves publications discovered through counterevidence queries targeting a candidate gap (Phase 5)",
                "parameters": {
                    "gap_id": "string (required)",
                },
            },
            {
                "name": "assess_counterevidence_relevance",
                "description": "Assesses whether an individual paper directly, partially, or weakly challenges a candidate gap (Phase 5)",
                "parameters": {
                    "gap_id": "string (required)",
                    "paper_id": "string (required)",
                },
            },
            {
                "name": "extract_counterevidence_evidence",
                "description": "Retrieves inspectable verbatim source passages and page numbers supporting counterevidence claims (Phase 5)",
                "parameters": {
                    "gap_id": "string (required)",
                },
            },
            {
                "name": "get_counterevidence_profile",
                "description": "Retrieves the aggregated counterevidence impact assessment profile for a candidate gap (Phase 5)",
                "parameters": {
                    "gap_id": "string (required)",
                },
            },

        ],
    }

