"""REST API Routes for Literature Synthesis & Candidate Research-Gap Generation (Phase 4).

Exposes endpoints for triggering synthesis runs, fetching comparison matrices (JSON/CSV/Markdown),
listing research themes, retrieving empirical patterns, inspecting candidate research gaps
with full evidence provenance, and recording human reviews.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy.orm import Session

from backend.app.services.persistence.database import get_db
from backend.app.schemas.synthesis import (
    SynthesisRunCreate,
    SynthesisRunResponse,
    LiteratureThemeResponse,
    LiteraturePatternResponse,
    CandidateResearchGapResponse,
    PaperComparisonMatrixResponse,
    HumanReviewRequest,
    SynthesisOverviewStats,
)
from backend.app.services.synthesis.synthesis_orchestrator import SynthesisOrchestrator
from backend.app.services.synthesis.comparison_matrix_service import PaperComparisonMatrixService
from backend.app.services.persistence.synthesis_repository import SynthesisRepository
from backend.app.services.synthesis.review_service import SynthesisReviewService

router = APIRouter(prefix="/api/research-requests", tags=["Literature Synthesis (Phase 4)"])


def _format_run_response(run, repo: SynthesisRepository) -> SynthesisRunResponse:
    themes = repo.get_themes_by_run(run.id)
    patterns = repo.get_patterns_by_run(run.id)
    gaps = repo.get_candidate_gaps_by_run(run.id)
    return SynthesisRunResponse(
        id=run.id,
        research_request_id=run.research_request_id,
        run_number=run.run_number,
        status=run.status,
        selected_paper_ids=run.selected_paper_ids or [],
        evidence_graph_version=run.evidence_graph_version,
        synthesis_configuration=run.synthesis_configuration or {},
        prompt_version=run.prompt_version,
        model_provider=run.model_provider,
        model_name=run.model_name,
        summary_narrative=run.summary_narrative or {},
        execution_started_at=run.execution_started_at,
        execution_completed_at=run.execution_completed_at,
        error_details=run.error_details,
        theme_count=len(themes),
        pattern_count=len(patterns),
        gap_count=len(gaps),
        created_at=run.created_at,
        updated_at=run.updated_at,
    )


@router.post(
    "/{request_id}/synthesis/runs",
    response_model=SynthesisRunResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute Literature Synthesis Run",
)
def create_synthesis_run(
    request_id: str,
    payload: Optional[SynthesisRunCreate] = None,
    db: Session = Depends(get_db),
):
    """Executes a full, versioned literature synthesis pipeline for a research request."""
    orchestrator = SynthesisOrchestrator(db)
    repo = SynthesisRepository(db)
    try:
        run = orchestrator.execute_synthesis_run(request_id, payload)
        return _format_run_response(run, repo)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Synthesis run failed: {str(e)}",
        )


@router.get(
    "/{request_id}/synthesis/runs",
    response_model=List[SynthesisRunResponse],
    summary="List Synthesis Runs for Request",
)
def list_synthesis_runs(
    request_id: str,
    db: Session = Depends(get_db),
):
    """Lists all previous versioned synthesis runs for reproducibility and comparison."""
    repo = SynthesisRepository(db)
    runs = repo.get_synthesis_runs_by_request(request_id)
    return [_format_run_response(r, repo) for r in runs]


@router.get(
    "/{request_id}/synthesis/runs/{run_id}",
    response_model=SynthesisRunResponse,
    summary="Get Synthesis Run Details",
)
def get_synthesis_run(
    request_id: str,
    run_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves metadata and execution status for a specific synthesis run."""
    repo = SynthesisRepository(db)
    run = repo.get_synthesis_run(run_id)
    if not run or run.research_request_id != request_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Synthesis run not found.")
    return _format_run_response(run, repo)


@router.get(
    "/{request_id}/synthesis/overview",
    response_model=SynthesisOverviewStats,
    summary="Get Literature Synthesis Overview Statistics",
)
def get_synthesis_overview(
    request_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves consolidated KPI metrics for the Literature Synthesis dashboard."""
    review_service = SynthesisReviewService(db)
    return review_service.get_overview_statistics(request_id)


@router.get(
    "/{request_id}/synthesis/comparison",
    summary="Get Multi-Paper Comparison Matrix",
)
def get_paper_comparison(
    request_id: str,
    method: Optional[str] = Query(None, description="Filter by method name"),
    dataset: Optional[str] = Query(None, description="Filter by dataset name"),
    model: Optional[str] = Query(None, description="Filter by model name"),
    year: Optional[int] = Query(None, description="Filter by publication year"),
    sort_by: str = Query("year_desc", description="Sort order: year_desc, year_asc, title_asc, evidence_count"),
    export_format: str = Query("json", description="Export format: json, csv, markdown"),
    limit: Optional[int] = Query(None, description="Pagination limit"),
    offset: int = Query(0, description="Pagination offset"),
    db: Session = Depends(get_db),
):
    """Generates a dynamic multi-paper comparison matrix in JSON, CSV, or Markdown format."""
    matrix_service = PaperComparisonMatrixService(db)
    matrix = matrix_service.generate_matrix(
        request_id=request_id,
        method_filter=method,
        dataset_filter=dataset,
        model_filter=model,
        year_filter=year,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
    )

    if export_format.lower() == "csv":
        csv_content = matrix_service.export_matrix_csv(matrix)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="paper_comparison_{request_id[:8]}.csv"'},
        )
    elif export_format.lower() in ("markdown", "md"):
        md_content = matrix_service.export_matrix_markdown(matrix)
        return PlainTextResponse(content=md_content)

    return matrix


@router.get(
    "/{request_id}/synthesis/runs/{run_id}/themes",
    response_model=List[LiteratureThemeResponse],
    summary="Get Discovered Research Themes for Run",
)
def get_run_themes(
    request_id: str,
    run_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves all recurring research themes identified in a synthesis run."""
    repo = SynthesisRepository(db)
    return repo.get_themes_by_run(run_id)


@router.get(
    "/{request_id}/synthesis/runs/{run_id}/patterns",
    response_model=List[LiteraturePatternResponse],
    summary="Get Analyzed Empirical Patterns for Run",
)
def get_run_patterns(
    request_id: str,
    run_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves methodology, dataset, model, and temporal patterns analyzed in a run."""
    repo = SynthesisRepository(db)
    return repo.get_patterns_by_run(run_id)


@router.get(
    "/{request_id}/synthesis/runs/{run_id}/candidate-gaps",
    response_model=List[CandidateResearchGapResponse],
    summary="Get Candidate Research Gaps for Run",
)
def get_candidate_gaps(
    request_id: str,
    run_id: str,
    category: Optional[str] = Query(None, description="Filter by gap category"),
    status: Optional[str] = Query(None, description="Filter by human review status"),
    db: Session = Depends(get_db),
):
    """Retrieves candidate research gaps generated in a run, with optional filtering."""
    review_service = SynthesisReviewService(db)
    repo = SynthesisRepository(db)
    gaps = repo.get_candidate_gaps_by_run(run_id, category=category, review_status=status)
    return [review_service.get_gap_with_provenance(g.id) for g in gaps]


@router.get(
    "/{request_id}/synthesis/candidate-gaps/{gap_id}",
    response_model=CandidateResearchGapResponse,
    summary="Get Candidate Research Gap Details & Provenance",
)
def get_candidate_gap_details(
    request_id: str,
    gap_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves a candidate gap with its full evidence links, exact passages, and review history."""
    review_service = SynthesisReviewService(db)
    gap = review_service.get_gap_with_provenance(gap_id)
    if not gap or gap["research_request_id"] != request_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate research gap not found.")
    return gap


@router.post(
    "/{request_id}/synthesis/candidate-gaps/{gap_id}/review",
    response_model=CandidateResearchGapResponse,
    summary="Submit Human Review for Candidate Gap",
)
def review_candidate_gap(
    request_id: str,
    gap_id: str,
    payload: HumanReviewRequest,
    db: Session = Depends(get_db),
):
    """Records a researcher review action (accept, reject, request_evidence, edit) on a candidate gap."""
    review_service = SynthesisReviewService(db)
    try:
        review_service.review_candidate_gap(gap_id, payload)
        return review_service.get_gap_with_provenance(gap_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/{request_id}/synthesis/history",
    summary="Compare Synthesis Runs",
)
def compare_runs_history(
    request_id: str,
    run_a_id: str = Query(..., description="Base run ID"),
    run_b_id: str = Query(..., description="Target run ID to compare"),
    db: Session = Depends(get_db),
):
    """Compares two synthesis runs to highlight differences in generated candidate gaps and themes."""
    review_service = SynthesisReviewService(db)
    try:
        return review_service.compare_synthesis_runs(run_a_id, run_b_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
