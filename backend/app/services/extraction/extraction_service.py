"""Structured Scientific Evidence Extraction Orchestration Service."""

import time
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.paper import Paper
from backend.app.models.evidence import ExtractionRun, EvidenceRecord, EvidencePassage
from backend.app.services.persistence.repositories import PaperRepository
from backend.app.services.persistence.document_repository import DocumentRepository
from backend.app.services.persistence.evidence_repository import EvidenceRepository
from backend.app.services.extraction.base_extractor import BaseEvidenceExtractor
from backend.app.services.extraction.rule_extractor import RuleBasedEvidenceExtractor
from backend.app.services.extraction.llm_extractor import LLMEvidenceExtractor
from backend.app.services.extraction.mock_extractor import MockEvidenceExtractor
from backend.app.schemas.evidence import StructuredEvidenceExtraction
from backend.app.core.logging import logger


class EvidenceExtractionService:
    """Orchestrates structured scientific evidence extraction on academic papers."""

    def __init__(self, db: Session, extractor: Optional[BaseEvidenceExtractor] = None):
        self.db = db
        self.paper_repo = PaperRepository(db)
        self.doc_repo = DocumentRepository(db)
        self.evidence_repo = EvidenceRepository(db)
        self.extractor = extractor or LLMEvidenceExtractor()

    async def extract_paper_evidence(
        self,
        paper_id: str,
        force_backend: Optional[str] = None,
    ) -> EvidenceRecord:
        """Extracts structured evidence from a paper, using full-text if accessible, or abstract."""
        paper = self.paper_repo.get_by_id(paper_id)
        if not paper:
            raise ValueError(f"Paper {paper_id} not found in database.")

        # Determine document availability
        doc = self.doc_repo.get_by_paper_id(paper_id)
        fulltext_sections = []
        document_id = None
        source_scope = "abstract_only"

        if doc and doc.extraction_status in ("success", "partial") and doc.extracted_sections:
            fulltext_sections = doc.extracted_sections
            document_id = doc.id
            source_scope = "full_text"

        # Determine backend
        active_extractor = self.extractor
        backend_name = "llm_groq_or_rule_fallback"
        if force_backend == "mock":
            active_extractor = MockEvidenceExtractor()
            backend_name = "mock"
        elif force_backend == "rule_based":
            active_extractor = RuleBasedEvidenceExtractor()
            backend_name = "rule_based"

        start_time = time.time()
        logger.info(f"Starting evidence extraction for paper '{paper.title}' (scope: {source_scope}, backend: {backend_name})")

        structured_data: StructuredEvidenceExtraction = await active_extractor.extract_evidence(
            paper_id=paper.id,
            title=paper.title,
            abstract=paper.abstract,
            fulltext_sections=fulltext_sections,
            source_scope=source_scope,
        )

        elapsed = time.time() - start_time

        # 1. Create Extraction Run
        run = self.evidence_repo.create_extraction_run(
            paper_id=paper.id,
            document_id=document_id,
            source_scope=source_scope,
            extractor_backend=backend_name,
            status=structured_data.extraction_status,
            execution_time_seconds=elapsed,
        )

        # 2. Create Canonical Evidence Record
        record = self.evidence_repo.create_evidence_record(
            extraction_run_id=run.id,
            paper_id=paper.id,
            research_objective=structured_data.research_objective.model_dump(),
            methodology={
                "items": [m.model_dump() for m in structured_data.methodologies],
            },
            datasets=[d.model_dump() for d in structured_data.datasets],
            evaluation_metrics=[m.model_dump() for m in structured_data.evaluation_metrics],
            findings=[f.model_dump() for f in structured_data.findings],
            limitations=[l.model_dump() for l in structured_data.limitations],
            future_work=[w.model_dump() for w in structured_data.future_work],
            contributions=structured_data.contributions,
            uncertainties=structured_data.uncertainties,
        )

        # 3. Create Granular Evidence Passages linking claims to exact page/sections
        # Objective passage
        obj = structured_data.research_objective
        if obj.supporting_passage or obj.problem_statement:
            self.evidence_repo.add_passage(
                evidence_record_id=record.id,
                paper_id=paper.id,
                category="objective",
                statement=obj.problem_statement,
                verbatim_passage=obj.supporting_passage,
                page_number=obj.page_number,
                section_heading=obj.section_heading,
            )

        # Methodologies
        for m in structured_data.methodologies:
            if m.supporting_passage or m.description:
                self.evidence_repo.add_passage(
                    evidence_record_id=record.id,
                    paper_id=paper.id,
                    category="methodology",
                    statement=f"{m.approach_name}: {m.description or ''}",
                    verbatim_passage=m.supporting_passage,
                    page_number=m.page_number,
                    section_heading=m.section_heading,
                )

        # Metrics
        for met in structured_data.evaluation_metrics:
            if met.supporting_passage or met.reported_value:
                self.evidence_repo.add_passage(
                    evidence_record_id=record.id,
                    paper_id=paper.id,
                    category="metric",
                    statement=f"{met.metric_name}: {met.reported_value} ({met.experimental_context or 'Reported'})",
                    verbatim_passage=met.supporting_passage,
                    page_number=met.page_number,
                    section_heading=met.section_heading,
                )

        # Findings
        for f in structured_data.findings:
            if f.supporting_passage or f.finding_statement:
                self.evidence_repo.add_passage(
                    evidence_record_id=record.id,
                    paper_id=paper.id,
                    category="finding",
                    statement=f.finding_statement,
                    verbatim_passage=f.supporting_passage,
                    page_number=f.page_number,
                    section_heading=f.section_heading,
                )

        # Limitations
        for lim in structured_data.limitations:
            if lim.supporting_passage or lim.limitation_text:
                self.evidence_repo.add_passage(
                    evidence_record_id=record.id,
                    paper_id=paper.id,
                    category="limitation",
                    statement=lim.limitation_text,
                    verbatim_passage=lim.supporting_passage,
                    page_number=lim.page_number,
                    section_heading=lim.section_heading,
                )

        # Future Work
        for fw in structured_data.future_work:
            if fw.supporting_passage or fw.direction_text:
                self.evidence_repo.add_passage(
                    evidence_record_id=record.id,
                    paper_id=paper.id,
                    category="future_work",
                    statement=fw.direction_text,
                    verbatim_passage=fw.supporting_passage,
                    page_number=fw.page_number,
                    section_heading=fw.section_heading,
                )

        self.db.commit()
        self.db.refresh(record)

        logger.info(f"Evidence extraction complete for {paper.id}: {len(record.passages)} verifiable passages tracked.")
        return record
