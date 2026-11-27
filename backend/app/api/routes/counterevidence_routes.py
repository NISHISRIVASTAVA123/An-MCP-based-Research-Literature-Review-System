"""API routes for Phase 5: Explicit Counterevidence Retrieval & Evidence Traceability."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.services.persistence.database import get_db
from backend.app.services.persistence.counterevidence_repository import CounterevidenceRepository
from backend.app.services.counterevidence.counterevidence_orchestrator import CounterevidenceOrchestrator
from backend.app.services.counterevidence.profile_aggregator import CounterevidenceProfileAggregator
from backend.app.models.paper import Paper
from backend.app.models.synthesis import CandidateResearchGap
from backend.app.models.counterevidence import CounterevidenceSearchRun
from backend.app.schemas.counterevidence import (
    CounterevidenceSearchRunResponse,
    SearchRunCreateRequest,
    CounterevidenceClaimResponse,
    CounterevidenceQueryResponse,
    CounterevidencePublicationResponse,
    CounterevidenceAssessmentResponse,
    CounterevidenceAssessmentReviewRequest,
    CounterevidenceEvidenceItemResponse,
    CounterevidenceProfileResponse,
)

router = APIRouter(prefix="/api", tags=["Counterevidence Retrieval & Assessment"])


# ==========================================
# 1. Counterevidence Search Triggers
# ==========================================

@router.post(
    "/research-requests/{request_id}/gaps/{gap_id}/counterevidence/search",
    response_model=CounterevidenceProfileResponse,
    summary="Trigger counterevidence search & assessment for a single candidate gap",
)
async def search_counterevidence_for_gap(
    request_id: str,
    gap_id: str,
    payload: Optional[SearchRunCreateRequest] = None,
    db: Session = Depends(get_db),
):
    orchestrator = CounterevidenceOrchestrator(db)
    databases = payload.databases if payload else None
    max_results = payload.max_results_per_query if payload else 10

    try:
        await orchestrator.execute_search_for_gap(
            candidate_gap_id=gap_id,
            research_request_id=request_id,
            databases=databases,
            max_results_per_query=max_results,
        )
        repo = CounterevidenceRepository(db)
        profile = repo.get_profile_by_gap(gap_id)
        if not profile:
            raise HTTPException(status_code=500, detail="Failed to synthesize counterevidence profile.")
        return profile
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Counterevidence search failed: {str(e)}")


@router.post(
    "/research-requests/{request_id}/counterevidence/search-all",
    summary="Trigger counterevidence search across all candidate gaps in a research request",
)
async def search_counterevidence_for_all_gaps(
    request_id: str,
    payload: Optional[SearchRunCreateRequest] = None,
    db: Session = Depends(get_db),
):
    orchestrator = CounterevidenceOrchestrator(db)
    databases = payload.databases if payload else None
    max_results = payload.max_results_per_query if payload else 10

    try:
        results = await orchestrator.execute_search_for_all_gaps(
            research_request_id=request_id,
            databases=databases,
            max_results_per_query=max_results,
        )
        return {
            "research_request_id": request_id,
            "processed_gaps_count": len(results),
            "results": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch counterevidence search failed: {str(e)}")


@router.get(
    "/research-requests/{request_id}/counterevidence/runs",
    response_model=List[CounterevidenceSearchRunResponse],
    summary="List past counterevidence search runs for a research request",
)
def get_counterevidence_runs(
    request_id: str,
    db: Session = Depends(get_db),
):
    repo = CounterevidenceRepository(db)
    return repo.get_runs_by_request(request_id)


@router.get(
    "/counterevidence/runs/{run_id}",
    response_model=CounterevidenceSearchRunResponse,
    summary="Get counterevidence search run details and status",
)
def get_counterevidence_run(
    run_id: str,
    db: Session = Depends(get_db),
):
    repo = CounterevidenceRepository(db)
    run = repo.get_search_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Search run '{run_id}' not found.")
    return run


# ==========================================
# 2. Decomposed Claims & Queries
# ==========================================

@router.get(
    "/gaps/{gap_id}/counterevidence/claims",
    response_model=List[CounterevidenceClaimResponse],
    summary="Get independently searchable claims decomposed from a candidate gap",
)
def get_gap_counterevidence_claims(
    gap_id: str,
    db: Session = Depends(get_db),
):
    repo = CounterevidenceRepository(db)
    return repo.get_claims_by_gap(gap_id)


@router.get(
    "/gaps/{gap_id}/counterevidence/queries",
    response_model=List[CounterevidenceQueryResponse],
    summary="Get generated counterevidence queries for a candidate gap",
)
def get_gap_counterevidence_queries(
    gap_id: str,
    db: Session = Depends(get_db),
):
    repo = CounterevidenceRepository(db)
    return repo.get_queries_by_gap(gap_id)


# ==========================================
# 3. Discovered Publications
# ==========================================

@router.get(
    "/gaps/{gap_id}/counterevidence/publications",
    response_model=List[CounterevidencePublicationResponse],
    summary="Get publications discovered specifically through counterevidence retrieval",
)
def get_gap_counterevidence_publications(
    gap_id: str,
    db: Session = Depends(get_db),
):
    repo = CounterevidenceRepository(db)
    pubs = repo.get_publications_by_gap(gap_id)
    results = []
    for p in pubs:
        resp = CounterevidencePublicationResponse.from_orm(p)
        if p.paper:
            resp.title = p.paper.title
            resp.authors = p.paper.authors or []
            resp.publication_year = p.paper.publication_year
            resp.doi = p.paper.doi
            resp.venue = p.paper.venue
            resp.has_abstract = p.paper.has_abstract
            resp.has_pdf = p.paper.has_pdf
            resp.url = p.paper.url
            resp.pdf_url = p.paper.pdf_url
            if p.paper.sources and len(p.paper.sources) > 0:
                resp.source_database = p.paper.sources[0].source_database
        results.append(resp)
    return results


# ==========================================
# 4. Relevance Assessments & Human Review
# ==========================================

@router.get(
    "/gaps/{gap_id}/counterevidence/assessments",
    response_model=List[CounterevidenceAssessmentResponse],
    summary="Get structured relevance assessments for a candidate gap",
)
def get_gap_counterevidence_assessments(
    gap_id: str,
    relevance: Optional[str] = Query(None, description="Filter by classification"),
    db: Session = Depends(get_db),
):
    repo = CounterevidenceRepository(db)
    assessments = repo.get_assessments_by_gap(gap_id)
    if relevance:
        assessments = [a for a in assessments if a.relevance_classification == relevance]

    results = []
    for a in assessments:
        resp = CounterevidenceAssessmentResponse.from_orm(a)
        if a.paper:
            resp.paper_title = a.paper.title
            resp.paper_authors = a.paper.authors or []
            resp.paper_year = a.paper.publication_year
            resp.paper_doi = a.paper.doi
        resp.evidence_items = [
            CounterevidenceEvidenceItemResponse.from_orm(ev) for ev in (a.evidence_items or [])
        ]
        results.append(resp)
    return results


@router.put(
    "/counterevidence/assessments/{assessment_id}",
    response_model=CounterevidenceAssessmentResponse,
    summary="Record human researcher review or override on a counterevidence assessment",
)
def review_counterevidence_assessment(
    assessment_id: str,
    payload: CounterevidenceAssessmentReviewRequest,
    db: Session = Depends(get_db),
):
    repo = CounterevidenceRepository(db)
    target_rel = payload.relevance_classification or payload.override_relevance or "partial_counterevidence"
    updated = repo.update_assessment_review(
        assessment_id=assessment_id,
        relevance_classification=target_rel,
        reviewer_reference=payload.reviewer_reference,
        reviewer_notes=payload.reviewer_notes or "",
        impact_classification=payload.impact_classification,
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Assessment '{assessment_id}' not found.")

    # Re-aggregate profile to reflect human correction
    aggregator = CounterevidenceProfileAggregator(db)
    if updated.search_run_id:
        aggregator.aggregate_profile_for_gap(updated.candidate_gap_id, updated.search_run_id)

    resp = CounterevidenceAssessmentResponse.from_orm(updated)
    if updated.paper:
        resp.paper_title = updated.paper.title
        resp.paper_authors = updated.paper.authors or []
        resp.paper_year = updated.paper.publication_year
        resp.paper_doi = updated.paper.doi
    resp.evidence_items = [
        CounterevidenceEvidenceItemResponse.from_orm(ev) for ev in (updated.evidence_items or [])
    ]
    return resp


# ==========================================
# 5. Evidence Passages & Gap Profiles
# ==========================================

@router.get(
    "/gaps/{gap_id}/counterevidence/evidence",
    response_model=List[CounterevidenceEvidenceItemResponse],
    summary="Get inspectable verbatim source passages supporting counterevidence assessments",
)
def get_gap_counterevidence_evidence_items(
    gap_id: str,
    db: Session = Depends(get_db),
):
    repo = CounterevidenceRepository(db)
    items = repo.get_evidence_items_by_gap(gap_id)
    return [CounterevidenceEvidenceItemResponse.from_orm(it) for it in items]


@router.get(
    "/gaps/{gap_id}/counterevidence/profile",
    response_model=CounterevidenceProfileResponse,
    summary="Get the aggregated counterevidence profile and impact classification for a gap",
)
def get_gap_counterevidence_profile(
    gap_id: str,
    db: Session = Depends(get_db),
):
    repo = CounterevidenceRepository(db)
    profile = repo.get_profile_by_gap(gap_id)
    if not profile:
        raise HTTPException(
            status_code=404,
            detail=f"Counterevidence profile for candidate gap '{gap_id}' has not been generated yet.",
        )
    return profile


# Convenient aliases for direct gap routes
@router.post(
    "/counterevidence/gaps/{gap_id}/search",
    response_model=CounterevidenceProfileResponse,
    summary="Trigger counterevidence search & assessment for a single candidate gap (shorthand)",
)
async def search_counterevidence_for_gap_shorthand(
    gap_id: str,
    payload: Optional[SearchRunCreateRequest] = None,
    db: Session = Depends(get_db),
):
    stmt = select(CandidateResearchGap).where(CandidateResearchGap.id == gap_id)
    gap = db.execute(stmt).scalar_one_or_none()
    if not gap:
        raise HTTPException(status_code=404, detail=f"Candidate gap '{gap_id}' not found.")
    return await search_counterevidence_for_gap(
        request_id=gap.research_request_id,
        gap_id=gap_id,
        payload=payload,
        db=db,
    )


@router.get(
    "/counterevidence/gaps/{gap_id}/claims",
    response_model=List[CounterevidenceClaimResponse],
    summary="Get claims (shorthand)",
)
def get_gap_counterevidence_claims_shorthand(gap_id: str, db: Session = Depends(get_db)):
    return get_gap_counterevidence_claims(gap_id, db)


@router.get(
    "/counterevidence/gaps/{gap_id}/queries",
    response_model=List[CounterevidenceQueryResponse],
    summary="Get queries (shorthand)",
)
def get_gap_counterevidence_queries_shorthand(gap_id: str, db: Session = Depends(get_db)):
    return get_gap_counterevidence_queries(gap_id, db)


@router.get(
    "/counterevidence/gaps/{gap_id}/publications",
    response_model=List[CounterevidencePublicationResponse],
    summary="Get publications (shorthand)",
)
def get_gap_counterevidence_publications_shorthand(gap_id: str, db: Session = Depends(get_db)):
    return get_gap_counterevidence_publications(gap_id, db)


@router.get(
    "/counterevidence/gaps/{gap_id}/assessments",
    response_model=List[CounterevidenceAssessmentResponse],
    summary="Get assessments (shorthand)",
)
def get_gap_counterevidence_assessments_shorthand(
    gap_id: str,
    relevance: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    return get_gap_counterevidence_assessments(gap_id, relevance, db)


@router.post(
    "/counterevidence/assessments/{assessment_id}/review",
    response_model=CounterevidenceAssessmentResponse,
    summary="Review assessment (shorthand)",
)
def review_counterevidence_assessment_post(
    assessment_id: str,
    payload: CounterevidenceAssessmentReviewRequest,
    db: Session = Depends(get_db),
):
    return review_counterevidence_assessment(assessment_id, payload, db)


@router.get(
    "/counterevidence/gaps/{gap_id}/evidence",
    response_model=List[CounterevidenceEvidenceItemResponse],
    summary="Get evidence passages (shorthand)",
)
def get_gap_counterevidence_evidence_shorthand(gap_id: str, db: Session = Depends(get_db)):
    return get_gap_counterevidence_evidence_items(gap_id, db)


@router.get(
    "/counterevidence/gaps/{gap_id}/profile",
    response_model=CounterevidenceProfileResponse,
    summary="Get profile (shorthand)",
)
def get_gap_counterevidence_profile_shorthand(gap_id: str, db: Session = Depends(get_db)):
    return get_gap_counterevidence_profile(gap_id, db)


@router.post(
    "/gaps/{gap_id}/counterevidence/rebuild-profile",
    response_model=CounterevidenceProfileResponse,
    summary="Recompute and re-aggregate counterevidence profile for a candidate gap",
)
@router.post(
    "/counterevidence/gaps/{gap_id}/profile/rebuild",
    response_model=CounterevidenceProfileResponse,
    summary="Rebuild profile (shorthand)",
)
def rebuild_gap_counterevidence_profile(gap_id: str, db: Session = Depends(get_db)):
    repo = CounterevidenceRepository(db)
    run = repo.get_latest_run_for_gap(gap_id)
    if not run:
        raise HTTPException(
            status_code=400,
            detail="Cannot rebuild profile: no counterevidence search run exists for this gap.",
        )
    aggregator = CounterevidenceProfileAggregator(db)
    return aggregator.aggregate_profile_for_gap(gap_id, run.id)


@router.get(
    "/counterevidence/runs",
    response_model=List[CounterevidenceSearchRunResponse],
    summary="List all counterevidence search runs",
)
def list_all_counterevidence_runs(db: Session = Depends(get_db)):
    stmt = select(CounterevidenceSearchRun).order_by(CounterevidenceSearchRun.created_at.desc()).limit(50)
    return list(db.execute(stmt).scalars().all())
