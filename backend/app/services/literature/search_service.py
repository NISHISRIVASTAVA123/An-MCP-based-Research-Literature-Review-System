"""Literature Search Orchestration Service.

Concurrently executes searches across independent provider adapters, collects raw metadata,
resiliently tolerates single-provider failures, normalizes schema, deduplicates records,
and persists results to database.
"""

import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.core.logging import logger
from backend.app.models.research_request import ResearchRequest
from backend.app.models.search_strategy import SearchStrategy, StrategyQuery
from backend.app.services.providers.base_provider import BaseAcademicProvider, RawPaperRecord
from backend.app.services.providers.openalex_provider import OpenAlexProvider
from backend.app.services.providers.semantic_scholar_provider import SemanticScholarProvider
from backend.app.services.providers.crossref_provider import CrossrefProvider
from backend.app.services.providers.arxiv_provider import ArxivProvider
from backend.app.services.literature.normalization_service import NormalizationService
from backend.app.services.literature.deduplication_service import DeduplicationService
from backend.app.services.persistence.repositories import (
    PaperRepository,
    SearchExecutionRepository,
)


class LiteratureSearchService:
    """Orchestrates multi-source academic retrieval pipeline."""

    def __init__(self):
        # Register independent provider adapters
        self.providers: Dict[str, BaseAcademicProvider] = {
            "openalex": OpenAlexProvider(),
            "semantic_scholar": SemanticScholarProvider(),
            "crossref": CrossrefProvider(),
            "arxiv": ArxivProvider(),
        }
        self.normalizer = NormalizationService()
        self.deduplicator = DeduplicationService()

    async def execute_search(
        self,
        db: Session,
        request: ResearchRequest,
        queries_to_run: Optional[List[StrategyQuery]] = None,
        max_papers_per_provider: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Executes parallel search across configured providers.
        Guarantees that temporary failure of one source does not crash the search workflow.
        """
        paper_repo = PaperRepository(db)
        execution_repo = SearchExecutionRepository(db)

        # Determine queries to execute
        if queries_to_run is None:
            if not request.strategy or not request.strategy.queries:
                raise ValueError("No search strategy or queries configured for this research request.")
            queries_to_run = [q for q in request.strategy.queries if q.is_enabled]

        if not queries_to_run:
            raise ValueError("No active/enabled search queries to execute.")

        limit_per_source = max_papers_per_provider or min(request.max_papers, 30)

        # Prepare coroutines for enabled queries
        tasks = []
        task_metadata = []

        for q in queries_to_run:
            target = q.target_database.lower()
            provider = self.providers.get(target)
            if provider:
                tasks.append(
                    provider.search(
                        query=q.query_text,
                        start_year=request.start_year,
                        end_year=request.end_year,
                        limit=limit_per_source,
                    )
                )
                task_metadata.append((target, q.query_text))
            else:
                logger.warning(f"Unknown target provider: {target}")

        logger.info(f"Executing {len(tasks)} queries across academic providers for request: {request.id}")

        # Execute concurrently with error isolation
        results = await asyncio.gather(*tasks, return_exceptions=True)

        raw_records: List[RawPaperRecord] = []
        provider_statuses: Dict[str, Dict[str, Any]] = {}
        executed_queries_list: List[str] = []

        for (target, query_str), res in zip(task_metadata, results):
            executed_queries_list.append(f"[{target.upper()}] {query_str}")
            if isinstance(res, Exception):
                logger.error(f"Provider '{target}' query failed: {res}")
                provider_statuses[target] = {
                    "status": "failed",
                    "retrieved_count": 0,
                    "error": str(res),
                }
            else:
                count = len(res)
                logger.info(f"Provider '{target}' successfully returned {count} records.")
                raw_records.extend(res)
                existing = provider_statuses.get(target, {"status": "success", "retrieved_count": 0, "error": None})
                existing["retrieved_count"] += count
                provider_statuses[target] = existing

        total_raw = len(raw_records)

        # Step 1: Normalize all raw records
        normalized_papers = self.normalizer.normalize_records(raw_records)

        # Step 2: Deduplicate
        unique_papers, duplicates_removed = self.deduplicator.deduplicate(normalized_papers)
        total_unique = len(unique_papers)

        logger.info(
            f"Retrieval summary: Raw={total_raw}, Unique={total_unique}, Duplicates={duplicates_removed}"
        )

        # Step 3: Persist to Database
        new_saved, updated = paper_repo.save_normalized_papers(request.id, unique_papers)

        overall_status = "completed"
        if any(s.get("status") == "failed" for s in provider_statuses.values()):
            if all(s.get("status") == "failed" for s in provider_statuses.values()):
                overall_status = "failed"
            else:
                overall_status = "partial_failure"

        # Step 4: Record Execution History
        execution = execution_repo.create(
            request_id=request.id,
            status=overall_status,
            total_raw=total_raw,
            total_unique=total_unique,
            total_duplicates=duplicates_removed,
            provider_statuses=provider_statuses,
            queries_executed=executed_queries_list,
        )

        return {
            "execution_id": execution.id,
            "status": overall_status,
            "total_raw_retrieved": total_raw,
            "total_unique_papers": total_unique,
            "total_duplicates_removed": duplicates_removed,
            "new_papers_saved": new_saved,
            "papers_updated": updated,
            "provider_statuses": provider_statuses,
            "queries_executed": executed_queries_list,
        }

