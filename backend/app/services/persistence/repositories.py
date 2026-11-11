"""Repository pattern implementations for database persistence."""

from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func, desc, asc, or_, and_

from backend.app.models.research_request import ResearchRequest, ResearchQuestion
from backend.app.models.search_strategy import SearchStrategy, StrategyQuery
from backend.app.models.paper import Paper, PaperSource
from backend.app.models.search_execution import SearchExecution
from backend.app.models.base import generate_uuid, utc_now


class ResearchRequestRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, request_data: dict, questions: List[str]) -> ResearchRequest:
        db_request = ResearchRequest(**request_data)
        self.db.add(db_request)
        self.db.flush()

        for idx, q_text in enumerate(questions):
            q = ResearchQuestion(
                request_id=db_request.id,
                question_text=q_text.strip(),
                order_index=idx,
            )
            self.db.add(q)

        self.db.commit()
        self.db.refresh(db_request)
        return db_request

    def get_by_id(self, request_id: str) -> Optional[ResearchRequest]:
        stmt = (
            select(ResearchRequest)
            .options(
                joinedload(ResearchRequest.questions),
                joinedload(ResearchRequest.strategy).joinedload(SearchStrategy.queries),
            )
            .where(ResearchRequest.id == request_id)
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def list(self, skip: int = 0, limit: int = 50) -> List[ResearchRequest]:
        stmt = (
            select(ResearchRequest)
            .options(
                joinedload(ResearchRequest.questions),
                joinedload(ResearchRequest.strategy),
            )
            .order_by(desc(ResearchRequest.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.execute(stmt).unique().scalars().all())

    def update(self, request_id: str, update_data: dict, questions: Optional[List[str]] = None) -> Optional[ResearchRequest]:
        req = self.get_by_id(request_id)
        if not req:
            return None

        for k, v in update_data.items():
            if v is not None and hasattr(req, k):
                setattr(req, k, v)

        if questions is not None:
            # Delete old questions and replace
            for old_q in req.questions:
                self.db.delete(old_q)
            self.db.flush()
            for idx, q_text in enumerate(questions):
                if q_text.strip():
                    new_q = ResearchQuestion(
                        request_id=req.id,
                        question_text=q_text.strip(),
                        order_index=idx,
                    )
                    self.db.add(new_q)

        req.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(req)
        return req

    def delete(self, request_id: str) -> bool:
        req = self.get_by_id(request_id)
        if not req:
            return False
        self.db.delete(req)
        self.db.commit()
        return True


class StrategyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_request_id(self, request_id: str) -> Optional[SearchStrategy]:
        stmt = (
            select(SearchStrategy)
            .options(joinedload(SearchStrategy.queries))
            .where(SearchStrategy.request_id == request_id)
        )
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def create_or_update(
        self,
        request_id: str,
        concepts: list,
        keywords: list,
        synonyms: dict,
        query_combinations: list,
        queries: List[dict],
    ) -> SearchStrategy:
        strategy = self.get_by_request_id(request_id)
        if not strategy:
            strategy = SearchStrategy(
                request_id=request_id,
                concepts=concepts,
                keywords=keywords,
                synonyms=synonyms,
                query_combinations=query_combinations,
            )
            self.db.add(strategy)
            self.db.flush()
        else:
            strategy.concepts = concepts
            strategy.keywords = keywords
            strategy.synonyms = synonyms
            strategy.query_combinations = query_combinations
            strategy.updated_at = utc_now()
            # Clear old queries
            for q in strategy.queries:
                self.db.delete(q)
            self.db.flush()

        # Add new queries
        for idx, q_data in enumerate(queries):
            sq = StrategyQuery(
                strategy_id=strategy.id,
                target_database=q_data["target_database"],
                query_text=q_data["query_text"],
                is_enabled=q_data.get("is_enabled", True),
                order_index=idx,
            )
            self.db.add(sq)

        self.db.commit()
        self.db.refresh(strategy)
        return strategy

    def update_queries(self, strategy_id: str, queries_data: List[dict]) -> Optional[SearchStrategy]:
        stmt = select(SearchStrategy).options(joinedload(SearchStrategy.queries)).where(SearchStrategy.id == strategy_id)
        strategy = self.db.execute(stmt).unique().scalar_one_or_none()
        if not strategy:
            return None

        # Replace queries
        for q in strategy.queries:
            self.db.delete(q)
        self.db.flush()

        for idx, q_data in enumerate(queries_data):
            sq = StrategyQuery(
                strategy_id=strategy.id,
                target_database=q_data["target_database"],
                query_text=q_data["query_text"],
                is_enabled=q_data.get("is_enabled", True),
                order_index=idx,
            )
            self.db.add(sq)

        strategy.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(strategy)
        return strategy


class PaperRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, paper_id: str) -> Optional[Paper]:
        stmt = select(Paper).options(joinedload(Paper.sources)).where(Paper.id == paper_id)
        return self.db.execute(stmt).unique().scalar_one_or_none()

    def get_count_by_request(self, request_id: str) -> int:
        stmt = select(func.count(Paper.id)).where(Paper.request_id == request_id)
        return self.db.execute(stmt).scalar() or 0

    def list_by_request(
        self,
        request_id: str,
        query: Optional[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        source_database: Optional[str] = None,
        has_abstract_only: Optional[bool] = None,
        has_pdf_only: Optional[bool] = None,
        sort_by: str = "year",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Paper], int]:
        stmt = (
            select(Paper)
            .options(joinedload(Paper.sources))
            .where(Paper.request_id == request_id)
        )

        if query:
            search_pattern = f"%{query.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Paper.title).like(search_pattern),
                    func.lower(Paper.abstract).like(search_pattern),
                    func.lower(Paper.doi).like(search_pattern),
                )
            )

        if year_from is not None:
            stmt = stmt.where(Paper.publication_year >= year_from)
        if year_to is not None:
            stmt = stmt.where(Paper.publication_year <= year_to)

        if has_abstract_only:
            stmt = stmt.where(Paper.has_abstract.is_(True))
        if has_pdf_only:
            stmt = stmt.where(Paper.has_pdf.is_(True))

        if source_database:
            stmt = stmt.join(Paper.sources).where(PaperSource.source_database == source_database)

        # Count total matching
        subq = stmt.order_by(None).subquery()
        count_stmt = select(func.count()).select_from(subq)
        total = self.db.execute(count_stmt).scalar() or 0

        # Sort order
        order_col = Paper.publication_year
        if sort_by == "title":
            order_col = Paper.title
        elif sort_by == "citations":
            order_col = Paper.citation_count
        elif sort_by == "created_at":
            order_col = Paper.created_at

        if sort_order.lower() == "asc":
            stmt = stmt.order_by(asc(order_col), asc(Paper.title))
        else:
            stmt = stmt.order_by(desc(order_col), asc(Paper.title))

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        papers = list(self.db.execute(stmt).unique().scalars().all())
        return papers, total

    def save_normalized_papers(self, request_id: str, normalized_papers: List[Any]) -> Tuple[int, int]:
        """Saves unique papers and their provenance sources. Returns (new_saved, updated)."""
        new_count = 0
        updated_count = 0

        for np in normalized_papers:
            existing = self.db.execute(
                select(Paper).where(Paper.id == np.id, Paper.request_id == request_id)
            ).scalar_one_or_none()

            if not existing:
                paper = Paper(
                    id=np.id,
                    request_id=request_id,
                    title=np.title,
                    normalized_title=np.normalized_title,
                    authors=np.authors,
                    abstract=np.abstract,
                    publication_year=np.publication_year,
                    publication_date=np.publication_date,
                    doi=np.doi,
                    url=np.url,
                    pdf_url=np.pdf_url,
                    venue=np.venue,
                    publication_type=np.publication_type,
                    keywords=np.keywords,
                    citation_count=np.citation_count,
                    has_abstract=np.has_abstract,
                    has_pdf=np.has_pdf,
                    has_doi=np.has_doi,
                    is_open_access=np.is_open_access,
                )
                self.db.add(paper)
                new_count += 1
            else:
                # Merge more complete data if available
                if not existing.abstract and np.abstract:
                    existing.abstract = np.abstract
                    existing.has_abstract = True
                if not existing.pdf_url and np.pdf_url:
                    existing.pdf_url = np.pdf_url
                    existing.has_pdf = True
                if not existing.doi and np.doi:
                    existing.doi = np.doi
                    existing.has_doi = True
                if np.citation_count and (not existing.citation_count or np.citation_count > existing.citation_count):
                    existing.citation_count = np.citation_count
                updated_count += 1

            self.db.flush()

            # Record provenance sources
            for src in np.sources:
                existing_src = self.db.execute(
                    select(PaperSource).where(
                        PaperSource.paper_id == np.id,
                        PaperSource.source_database == src.source_database,
                        PaperSource.external_source_id == src.external_source_id,
                    )
                ).scalar_one_or_none()

                if not existing_src:
                    ps = PaperSource(
                        paper_id=np.id,
                        source_database=src.source_database,
                        external_source_id=src.external_source_id,
                        source_url=src.source_url,
                        raw_metadata=src.raw_metadata or {},
                    )
                    self.db.add(ps)

        self.db.commit()
        return new_count, updated_count


class SearchExecutionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        request_id: str,
        status: str,
        total_raw: int,
        total_unique: int,
        total_duplicates: int,
        provider_statuses: dict,
        queries_executed: list,
    ) -> SearchExecution:
        execution = SearchExecution(
            request_id=request_id,
            status=status,
            total_raw_retrieved=total_raw,
            total_unique_papers=total_unique,
            total_duplicates_removed=total_duplicates,
            provider_statuses=provider_statuses,
            queries_executed=queries_executed,
        )
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        return execution

    def list_by_request(self, request_id: str) -> List[SearchExecution]:
        stmt = (
            select(SearchExecution)
            .where(SearchExecution.request_id == request_id)
            .order_by(desc(SearchExecution.executed_at))
        )
        return list(self.db.execute(stmt).scalars().all())

