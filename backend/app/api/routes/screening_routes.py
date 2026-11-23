"""API Routes for Paper Screening (Phase 2)."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.services.persistence.database import get_db
from backend.app.services.screening.screening_service import ScreeningService
from backend.app.services.persistence.screening_repository import ScreeningRepository
from backend.app.schemas.screening import (
    ScreeningRunResponse,
    ScreeningDecisionResponse,
    HumanOverrideRequest,
)

router = APIRouter(tags=["Paper Screening"])


@router.post(
    "/api/research-requests/{request_id}/screening-runs",
    response_model=ScreeningRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute automated paper screening batch",
)
def create_screening_run(
    request_id: str,
    db: Session = Depends(get_db),
):
    """Executes staged multi-dimension automated paper screening on all retrieved papers."""
    service = ScreeningService(db)
    try:
        run = service.execute_screening_run(request_id)
        return ScreeningRunResponse(
            id=run.id,
            request_id=run.request_id,
            run_number=run.run_number,
            criteria_snapshot=run.criteria_snapshot,
            total_papers=run.total_papers,
            included_count=run.included_count,
            excluded_count=run.excluded_count,
            review_needed_count=run.review_needed_count,
            executed_at=run.executed_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Screening execution failed: {e}")


@router.get(
    "/api/research-requests/{request_id}/screening-runs",
    response_model=List[ScreeningRunResponse],
    summary="Get screening execution history",
)
def list_screening_runs(
    request_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves all historical screening runs for reproducibility audit."""
    repo = ScreeningRepository(db)
    runs = repo.get_runs_by_request(request_id)
    return [
        ScreeningRunResponse(
            id=r.id,
            request_id=r.request_id,
            run_number=r.run_number,
            criteria_snapshot=r.criteria_snapshot,
            total_papers=r.total_papers,
            included_count=r.included_count,
            excluded_count=r.excluded_count,
            review_needed_count=r.review_needed_count,
            executed_at=r.executed_at,
        )
        for r in runs
    ]


@router.get(
    "/api/research-requests/{request_id}/screening-results",
    response_model=List[ScreeningDecisionResponse],
    summary="Get paper screening decisions",
)
def get_screening_results(
    request_id: str,
    run_id: Optional[str] = Query(None, description="Optional run ID; defaults to latest"),
    decision: Optional[str] = Query(None, description="Filter: included, excluded, needs_human_review"),
    db: Session = Depends(get_db),
):
    """Retrieves paper-by-paper screening decisions for the request."""
    repo = ScreeningRepository(db)
    if not run_id:
        latest = repo.get_latest_run(request_id)
        if not latest:
            return []
        run_id = latest.id

    decisions = repo.get_decisions_for_run(run_id, decision_filter=decision)
    res = []
    for d in decisions:
        paper = d.paper
        res.append(
            ScreeningDecisionResponse(
                id=d.id,
                run_id=d.run_id,
                paper_id=d.paper_id,
                paper_title=paper.title if paper else None,
                paper_authors=paper.authors if paper else [],
                paper_year=paper.publication_year if paper else None,
                paper_venue=paper.venue if paper else None,
                has_abstract=paper.has_abstract if paper else False,
                has_pdf=paper.has_pdf if paper else False,
                decision=d.decision,
                stage=d.stage,
                reason=d.reason,
                criteria_evaluated=d.criteria_evaluated,
                criteria_satisfied=d.criteria_satisfied,
                criteria_unsatisfied=d.criteria_unsatisfied,
                missing_information=d.missing_information,
                confidence_score=d.confidence_score,
                screening_method=d.screening_method,
                is_human_override=d.is_human_override,
                original_decision=d.original_decision,
                reviewer_notes=d.reviewer_notes,
                reviewed_at=d.reviewed_at,
                created_at=d.created_at,
            )
        )
    return res


@router.put(
    "/api/papers/{paper_id}/screening-decision",
    response_model=ScreeningDecisionResponse,
    summary="Manually override paper screening decision",
)
def override_screening_decision(
    paper_id: str,
    payload: HumanOverrideRequest,
    db: Session = Depends(get_db),
):
    """Allows a human reviewer to override an automated screening decision, preserving original."""
    repo = ScreeningRepository(db)
    updated = repo.update_human_override(
        paper_id=paper_id,
        new_decision=payload.decision,
        reviewer_notes=payload.reviewer_notes,
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"No screening decision found for paper {paper_id}")

    paper = updated.paper
    return ScreeningDecisionResponse(
        id=updated.id,
        run_id=updated.run_id,
        paper_id=updated.paper_id,
        paper_title=paper.title if paper else None,
        paper_authors=paper.authors if paper else [],
        paper_year=paper.publication_year if paper else None,
        paper_venue=paper.venue if paper else None,
        has_abstract=paper.has_abstract if paper else False,
        has_pdf=paper.has_pdf if paper else False,
        decision=updated.decision,
        stage=updated.stage,
        reason=updated.reason,
        criteria_evaluated=updated.criteria_evaluated,
        criteria_satisfied=updated.criteria_satisfied,
        criteria_unsatisfied=updated.criteria_unsatisfied,
        missing_information=updated.missing_information,
        confidence_score=updated.confidence_score,
        screening_method=updated.screening_method,
        is_human_override=updated.is_human_override,
        original_decision=updated.original_decision,
        reviewer_notes=updated.reviewer_notes,
        reviewed_at=updated.reviewed_at,
        created_at=updated.created_at,
    )

