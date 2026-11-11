"""FastAPI routes for Paper exploration, filtering, and inspection."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.services.persistence.database import get_db
from backend.app.services.persistence.repositories import (
    ResearchRequestRepository,
    PaperRepository,
)
from backend.app.schemas.paper import (
    PaperResponse,
    PaperListResponse,
)

router = APIRouter(tags=["Papers"])


@router.get("/api/research-requests/{request_id}/papers", response_model=PaperListResponse)
def list_request_papers(
    request_id: str,
    query: Optional[str] = Query(None, description="Search term in title, abstract, or DOI"),
    year_from: Optional[int] = Query(None, description="Minimum publication year"),
    year_to: Optional[int] = Query(None, description="Maximum publication year"),
    source_database: Optional[str] = Query(None, description="Filter by source database (openalex, semantic_scholar, crossref, arxiv)"),
    has_abstract_only: Optional[bool] = Query(None, description="Only papers with abstracts"),
    has_pdf_only: Optional[bool] = Query(None, description="Only papers with direct PDF links"),
    sort_by: str = Query("year", description="Field to sort by: year, title, citations, created_at"),
    sort_order: str = Query("desc", description="asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """Retrieves normalized academic papers collected for a research review."""
    req_repo = ResearchRequestRepository(db)
    req = req_repo.get_by_id(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Research request not found.")

    paper_repo = PaperRepository(db)
    papers, total = paper_repo.list_by_request(
        request_id=request_id,
        query=query,
        year_from=year_from,
        year_to=year_to,
        source_database=source_database,
        has_abstract_only=has_abstract_only,
        has_pdf_only=has_pdf_only,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1

    return PaperListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=[PaperResponse.model_validate(p) for p in papers],
    )


@router.get("/api/papers/{paper_id}", response_model=PaperResponse)
def get_paper_details(
    paper_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves full normalized metadata and provenance sources for a single paper."""
    paper_repo = PaperRepository(db)
    paper = paper_repo.get_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")
    return PaperResponse.model_validate(paper)

