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

