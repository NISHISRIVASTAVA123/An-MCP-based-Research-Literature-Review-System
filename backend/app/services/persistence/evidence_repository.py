"""Evidence database repository."""

from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from backend.app.models.evidence import ExtractionRun, EvidenceRecord, EvidencePassage


class EvidenceRepository:
    """Repository handling persistence for structured scientific evidence."""

    def __init__(self, db: Session):
        self.db = db

    def create_extraction_run(
        self,
        paper_id: str,
        document_id: Optional[str],
        source_scope: str,
        extractor_backend: str,
        status: str = "completed",
        execution_time_seconds: float = 0.0,
    ) -> ExtractionRun:
        run = ExtractionRun(
            paper_id=paper_id,
            document_id=document_id,
            source_scope=source_scope,
            extractor_backend=extractor_backend,
            status=status,
            execution_time_seconds=execution_time_seconds,
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_runs_by_paper(self, paper_id: str) -> List[ExtractionRun]:
        stmt = (
            select(ExtractionRun)
            .where(ExtractionRun.paper_id == paper_id)
            .order_by(desc(ExtractionRun.created_at))
        )
        return list(self.db.scalars(stmt).all())

    def create_evidence_record(
        self,
        extraction_run_id: str,
        paper_id: str,
        research_objective: dict,
        methodology: dict,
        datasets: list,
        evaluation_metrics: list,
        findings: list,
        limitations: list,
        future_work: list,
        contributions: list,
        uncertainties: list,
    ) -> EvidenceRecord:
        record = EvidenceRecord(
            extraction_run_id=extraction_run_id,
            paper_id=paper_id,
            research_objective=research_objective,
            methodology=methodology,
            datasets=datasets,
            evaluation_metrics=evaluation_metrics,
            findings=findings,
            limitations=limitations,
            future_work=future_work,
            contributions=contributions,
            uncertainties=uncertainties,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def add_passage(
        self,
        evidence_record_id: str,
        paper_id: str,
        category: str,
        statement: str,
        verbatim_passage: Optional[str] = None,
        page_number: Optional[int] = None,
        section_heading: Optional[str] = None,
        char_start: Optional[int] = None,
        char_end: Optional[int] = None,
        verification_status: str = "machine_extracted",
    ) -> EvidencePassage:
        passage = EvidencePassage(
            evidence_record_id=evidence_record_id,
            paper_id=paper_id,
            category=category,
            statement=statement,
            verbatim_passage=verbatim_passage,
            page_number=page_number,
            section_heading=section_heading,
            char_start=char_start,
            char_end=char_end,
            verification_status=verification_status,
        )
        self.db.add(passage)
        return passage

    def get_latest_evidence_by_paper(self, paper_id: str) -> Optional[EvidenceRecord]:
        stmt = (
            select(EvidenceRecord)
            .where(EvidenceRecord.paper_id == paper_id)
            .order_by(desc(EvidenceRecord.created_at))
            .limit(1)
        )
        return self.db.scalars(stmt).first()

    def get_passages_by_paper(self, paper_id: str) -> List[EvidencePassage]:
        stmt = (
            select(EvidencePassage)
            .where(EvidencePassage.paper_id == paper_id)
            .order_by(EvidencePassage.category.asc(), EvidencePassage.page_number.asc())
        )
        return list(self.db.scalars(stmt).all())

    def update_passage(
        self,
        passage_id: str,
        verification_status: str,
        statement: Optional[str] = None,
        verbatim_passage: Optional[str] = None,
        user_notes: Optional[str] = None,
    ) -> Optional[EvidencePassage]:
        stmt = select(EvidencePassage).where(EvidencePassage.id == passage_id)
        passage = self.db.scalars(stmt).first()
        if not passage:
            return None

        passage.verification_status = verification_status
        if statement is not None:
            passage.statement = statement
        if verbatim_passage is not None:
            passage.verbatim_passage = verbatim_passage
        if user_notes is not None:
            passage.user_notes = user_notes

        self.db.commit()
        self.db.refresh(passage)
        return passage

