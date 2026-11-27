"""Academic literature retrieval service specialized for counterevidence search."""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from backend.app.models.paper import Paper, PaperSource
from backend.app.models.counterevidence import (
    CounterevidenceSearchQuery,
    CounterevidencePublication,
)
from backend.app.services.providers.openalex_provider import OpenAlexProvider
from backend.app.services.providers.semantic_scholar_provider import SemanticScholarProvider
from backend.app.services.providers.crossref_provider import CrossrefProvider
from backend.app.services.providers.arxiv_provider import ArxivProvider
from backend.app.services.literature.normalization_service import NormalizationService
from backend.app.services.persistence.repositories import PaperRepository
from backend.app.services.persistence.counterevidence_repository import CounterevidenceRepository
from backend.app.core.logging import logger


class CounterevidenceRetrievalService:
    """Executes counterevidence queries across academic APIs, normalizes, deduplicates, and tracks discovery provenance."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = CounterevidenceRepository(db)
        self.paper_repo = PaperRepository(db)
        self.normalizer = NormalizationService()

        # Instantiate academic providers
        self.providers = {
            "openalex": OpenAlexProvider(),
            "semantic_scholar": SemanticScholarProvider(),
            "crossref": CrossrefProvider(),
            "arxiv": ArxivProvider(),
        }

    async def execute_query(
        self,
        query_model: CounterevidenceSearchQuery,
        research_request_id: str,
        limit: int = 10,
    ) -> List[Tuple[Paper, bool]]:
        """Executes a single counterevidence query against its target database.
        
        Returns list of (Paper, is_newly_discovered) tuples.
        """
        db_name = query_model.source_database.lower()
        provider = self.providers.get(db_name) or self.providers["crossref"]

        try:
            raw_records = await provider.search(query=query_model.query_text, limit=limit)
        except Exception as e:
            logger.warning(f"Counterevidence search on {db_name} failed: {e}")
            self.repo.update_query_execution(
                query_id=query_model.id,
                status="failed",
                results_count=0,
                error_message=str(e),
            )
            return []

        saved_papers: List[Tuple[Paper, bool]] = []

        for raw_rec in raw_records:
            normalized = self.normalizer.normalize_record(raw_rec)
            if not normalized.title:
                continue

            # Check if paper already exists in our database
            existing_paper = self._find_existing_paper(normalized.doi, normalized.normalized_title)
            is_new = False

            if existing_paper:
                paper = existing_paper
            else:
                # Create as new paper marked specifically for counterevidence
                paper = self._create_paper_record(normalized, research_request_id)
                is_new = True

            # Record discovery in counterevidence_publications
            self.repo.record_publication(
                candidate_gap_id=query_model.candidate_gap_id,
                search_run_id=query_model.search_run_id,
                paper_id=paper.id,
                discovery_source=db_name,
                discovery_query_id=query_model.id,
                is_newly_discovered=is_new,
                discovery_tag="counterevidence_discovered",
            )

            saved_papers.append((paper, is_new))

        # Update query record with execution telemetry
        self.repo.update_query_execution(
            query_id=query_model.id,
            status="success" if raw_records else "empty_results",
            results_count=len(saved_papers),
        )

        return saved_papers

    def _find_existing_paper(self, doi: Optional[str], normalized_title: str) -> Optional[Paper]:
        """Deduplicates against the existing database by DOI or normalized title."""
        if doi:
            stmt = select(Paper).where(Paper.doi == doi.lower().strip())
            found = self.db.execute(stmt).scalar_one_or_none()
            if found:
                return found

        if normalized_title:
            stmt = select(Paper).where(Paper.normalized_title == normalized_title)
            found = self.db.execute(stmt).scalar_one_or_none()
            if found:
                return found

        return None

    def _create_paper_record(self, norm, request_id: str) -> Paper:
        paper = Paper(
            request_id=request_id,
            title=norm.title,
            normalized_title=norm.normalized_title,
            authors=norm.authors or [],
            abstract=norm.abstract,
            publication_year=norm.publication_year,
            publication_date=norm.publication_date,
            doi=norm.doi.lower().strip() if norm.doi else None,
            url=norm.url,
            pdf_url=norm.pdf_url,
            venue=norm.venue,
            publication_type=norm.publication_type or "journal-article",
            keywords=norm.keywords or [],
            citation_count=norm.citation_count or 0,
            has_abstract=bool(norm.abstract and len(norm.abstract.strip()) > 20),
            has_pdf=bool(norm.pdf_url),
            has_doi=bool(norm.doi),
            is_open_access=norm.is_open_access,
        )
        self.db.add(paper)
        self.db.commit()
        self.db.refresh(paper)

        # Save source record
        for src in norm.sources:
            ps = PaperSource(
                paper_id=paper.id,
                source_database=src.source_database,
                external_source_id=src.external_source_id,
                source_url=src.source_url,
                raw_metadata=src.raw_metadata or {},
            )
            self.db.add(ps)
        self.db.commit()

        return paper
