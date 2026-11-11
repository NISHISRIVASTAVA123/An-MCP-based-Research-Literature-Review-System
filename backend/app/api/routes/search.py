"""FastAPI routes for executing academic literature searches and viewing history."""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.services.persistence.database import get_db
from backend.app.services.persistence.repositories import (
    ResearchRequestRepository,
    SearchExecutionRepository,
)
from backend.app.services.literature.search_service import LiteratureSearchService
from backend.app.schemas.search import (
    SearchExecutionSummary,
    SearchExecutionRequest,
)

router = APIRouter(prefix="/api/research-requests", tags=["Search Execution"])
search_service = LiteratureSearchService()


@router.post("/{request_id}/search", response_model=Dict[str, Any])
async def execute_search(
    request_id: str,
    payload: SearchExecutionRequest = SearchExecutionRequest(),
    db: Session = Depends(get_db),
):
    """
    Executes academic retrieval across configured providers.
    Normalizes metadata, removes duplicates, and records provenance.
    """
    req_repo = ResearchRequestRepository(db)
    req = req_repo.get_by_id(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Research request not found.")

    if not req.strategy or not req.strategy.queries:
        raise HTTPException(
            status_code=400,
            detail="Research request does not have a generated search strategy. Generate one before executing search."
        )

    try:
        result = await search_service.execute_search(
            db=db,
            request=req,
            max_papers_per_provider=payload.max_papers_per_provider,
        )
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search execution failed: {str(exc)}"
        )


@router.get("/{request_id}/search-history", response_model=List[SearchExecutionSummary])
def get_search_history(
    request_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves all historical search executions for a research request."""
    exec_repo = SearchExecutionRepository(db)
    executions = exec_repo.list_by_request(request_id)
    return executions

