"""FastAPI routes for Research Requests."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.services.persistence.database import get_db
from backend.app.services.persistence.repositories import (
    ResearchRequestRepository,
    PaperRepository,
)
from backend.app.schemas.research import (
    ResearchRequestCreate,
    ResearchRequestUpdate,
    ResearchRequestResponse,
    ResearchRequestSummary,
    ResearchQuestionResponse,
)

router = APIRouter(prefix="/api/research-requests", tags=["Research Requests"])


@router.post("", response_model=ResearchRequestResponse, status_code=status.HTTP_201_CREATED)
def create_research_request(
    payload: ResearchRequestCreate,
    db: Session = Depends(get_db),
):
    """Creates a new research review request with validated questions and scope."""
    repo = ResearchRequestRepository(db)
    request_data = payload.model_dump(exclude={"research_questions"})
    questions = payload.research_questions

    created = repo.create(request_data, questions)
    return created


@router.get("", response_model=List[ResearchRequestSummary])
def list_research_requests(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Lists saved research requests with summary statistics."""
    repo = ResearchRequestRepository(db)
    paper_repo = PaperRepository(db)
    requests = repo.list(skip=skip, limit=limit)

    summaries = []
    for req in requests:
        paper_count = paper_repo.get_count_by_request(req.id)
        summaries.append(
            ResearchRequestSummary(
                id=req.id,
                topic=req.topic,
                objective=req.objective,
                domain=req.domain,
                start_year=req.start_year,
                end_year=req.end_year,
                max_papers=req.max_papers,
                created_at=req.created_at,
                updated_at=req.updated_at,
                total_papers=paper_count,
                total_questions=len(req.questions),
                has_strategy=req.strategy is not None,
            )
        )
    return summaries


@router.get("/{request_id}", response_model=ResearchRequestResponse)
def get_research_request(
    request_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves a specific research request by ID."""
    repo = ResearchRequestRepository(db)
    paper_repo = PaperRepository(db)
    req = repo.get_by_id(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Research request not found.")

    paper_count = paper_repo.get_count_by_request(req.id)

    response = ResearchRequestResponse.model_validate(req)
    response.has_strategy = req.strategy is not None
    response.has_retrieved_papers = paper_count > 0
    response.total_papers_count = paper_count
    return response


@router.put("/{request_id}", response_model=ResearchRequestResponse)
def update_research_request(
    request_id: str,
    payload: ResearchRequestUpdate,
    db: Session = Depends(get_db),
):
    """Updates an existing research request."""
    repo = ResearchRequestRepository(db)
    paper_repo = PaperRepository(db)

    update_dict = payload.model_dump(exclude_unset=True, exclude={"research_questions"})
    questions = payload.research_questions

    updated = repo.update(request_id, update_dict, questions)
    if not updated:
        raise HTTPException(status_code=404, detail="Research request not found.")

    paper_count = paper_repo.get_count_by_request(updated.id)
    res = ResearchRequestResponse.model_validate(updated)
    res.has_strategy = updated.strategy is not None
    res.has_retrieved_papers = paper_count > 0
    res.total_papers_count = paper_count
    return res


@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_research_request(
    request_id: str,
    db: Session = Depends(get_db),
):
    """Deletes a research request and all related strategies, queries, and papers."""
    repo = ResearchRequestRepository(db)
    success = repo.delete(request_id)
    if not success:
        raise HTTPException(status_code=404, detail="Research request not found.")
    return None

