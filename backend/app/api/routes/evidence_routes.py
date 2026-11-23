"""API Routes for Structured Scientific Evidence and Passage Tracking (Phase 2)."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.services.persistence.database import get_db
from backend.app.services.extraction.extraction_service import EvidenceExtractionService
from backend.app.services.persistence.evidence_repository import EvidenceRepository
from backend.app.schemas.evidence import (
    EvidenceRecordResponse,
    EvidencePassageResponse,
    PassageUpdatePayload,
)

router = APIRouter(tags=["Evidence Extraction"])


@router.post(
    "/api/papers/{paper_id}/extract-evidence",
    response_model=EvidenceRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger structured evidence extraction on a paper",
)
async def extract_evidence(
    paper_id: str,
    backend: Optional[str] = Query(None, description="Extractor backend: auto, rule_based, mock"),
    db: Session = Depends(get_db),
):
    """Extracts research objective, methodology, datasets, metrics, findings, limitations, and future work."""
    service = EvidenceExtractionService(db)
    try:
        record = await service.extract_paper_evidence(paper_id, force_backend=backend)
        passages = service.evidence_repo.get_passages_by_paper(paper_id)
        return EvidenceRecordResponse(
            id=record.id,
            paper_id=record.paper_id,
            extraction_run_id=record.extraction_run_id,
            source_scope=record.extraction_run.source_scope if record.extraction_run else "abstract_only",
            extractor_backend=record.extraction_run.extractor_backend if record.extraction_run else "auto",
            research_objective=record.research_objective,
            methodology=record.methodology,
            datasets=record.datasets,
            evaluation_metrics=record.evaluation_metrics,
            findings=record.findings,
            limitations=record.limitations,
            future_work=record.future_work,
            contributions=record.contributions,
            uncertainties=record.uncertainties,
            is_human_edited=record.is_human_edited,
            human_notes=record.human_notes,
            passages=[
                EvidencePassageResponse(
                    id=p.id,
                    paper_id=p.paper_id,
                    category=p.category,
                    statement=p.statement,
                    verbatim_passage=p.verbatim_passage,
                    page_number=p.page_number,
                    section_heading=p.section_heading,
                    char_start=p.char_start,
                    char_end=p.char_end,
                    verification_status=p.verification_status,
                    user_notes=p.user_notes,
                    created_at=p.created_at,
                )
                for p in passages
            ],
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evidence extraction failed: {e}")


@router.get(
    "/api/papers/{paper_id}/evidence",
    response_model=Optional[EvidenceRecordResponse],
    summary="Get latest structured scientific evidence for a paper",
)
def get_paper_evidence(
    paper_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves latest structured scientific evidence and linked source passages."""
    repo = EvidenceRepository(db)
    record = repo.get_latest_evidence_by_paper(paper_id)
    if not record:
        return None

    passages = repo.get_passages_by_paper(paper_id)
    return EvidenceRecordResponse(
        id=record.id,
        paper_id=record.paper_id,
        extraction_run_id=record.extraction_run_id,
        source_scope=record.extraction_run.source_scope if record.extraction_run else "abstract_only",
        extractor_backend=record.extraction_run.extractor_backend if record.extraction_run else "auto",
        research_objective=record.research_objective,
        methodology=record.methodology,
        datasets=record.datasets,
        evaluation_metrics=record.evaluation_metrics,
        findings=record.findings,
        limitations=record.limitations,
        future_work=record.future_work,
        contributions=record.contributions,
        uncertainties=record.uncertainties,
        is_human_edited=record.is_human_edited,
        human_notes=record.human_notes,
        passages=[
            EvidencePassageResponse(
                id=p.id,
                paper_id=p.paper_id,
                category=p.category,
                statement=p.statement,
                verbatim_passage=p.verbatim_passage,
                page_number=p.page_number,
                section_heading=p.section_heading,
                char_start=p.char_start,
                char_end=p.char_end,
                verification_status=p.verification_status,
                user_notes=p.user_notes,
                created_at=p.created_at,
            )
            for p in passages
        ],
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.get(
    "/api/papers/{paper_id}/evidence-passages",
    response_model=List[EvidencePassageResponse],
    summary="Get verifiable evidence passages for a paper",
)
def get_evidence_passages(
    paper_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves all verbatim evidence passages linking claims to page and section pointers."""
    repo = EvidenceRepository(db)
    passages = repo.get_passages_by_paper(paper_id)
    return [
        EvidencePassageResponse(
            id=p.id,
            paper_id=p.paper_id,
            category=p.category,
            statement=p.statement,
            verbatim_passage=p.verbatim_passage,
            page_number=p.page_number,
            section_heading=p.section_heading,
            char_start=p.char_start,
            char_end=p.char_end,
            verification_status=p.verification_status,
            user_notes=p.user_notes,
            created_at=p.created_at,
        )
        for p in passages
    ]


@router.put(
    "/api/evidence/passages/{passage_id}",
    response_model=EvidencePassageResponse,
    summary="Update or verify an evidence passage",
)
def update_evidence_passage(
    passage_id: str,
    payload: PassageUpdatePayload,
    db: Session = Depends(get_db),
):
    """Allows user to verify, flag, or correct an extracted claim or verbatim passage."""
    repo = EvidenceRepository(db)
    updated = repo.update_passage(
        passage_id=passage_id,
        verification_status=payload.verification_status,
        statement=payload.statement,
        verbatim_passage=payload.verbatim_passage,
        user_notes=payload.user_notes,
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Passage {passage_id} not found")

    return EvidencePassageResponse(
        id=updated.id,
        paper_id=updated.paper_id,
        category=updated.category,
        statement=updated.statement,
        verbatim_passage=updated.verbatim_passage,
        page_number=updated.page_number,
        section_heading=updated.section_heading,
        char_start=updated.char_start,
        char_end=updated.char_end,
        verification_status=updated.verification_status,
        user_notes=updated.user_notes,
        created_at=updated.created_at,
    )

