"""Persistence repository for Counterevidence Retrieval & Assessment (Phase 5)."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, and_

from backend.app.models.counterevidence import (
    CounterevidenceSearchRun,
    CounterevidenceClaim,
    CounterevidenceSearchQuery,
    CounterevidencePublication,
    CounterevidenceAssessment,
    CounterevidenceEvidence,
    CounterevidenceProfile,
)
from backend.app.models.paper import Paper
from backend.app.models.synthesis import CandidateResearchGap
from backend.app.models.base import utc_now


class CounterevidenceRepository:
    """Manages transactional database operations for Phase 5 counterevidence entities."""

    def __init__(self, db: Session):
        self.db = db

    # ==========================================
    # 1. Search Run Operations
    # ==========================================

    def create_search_run(
        self,
        research_request_id: str,
        candidate_gap_id: Optional[str] = None,
        initiated_by: str = "researcher",
        configuration_snapshot: Optional[Dict[str, Any]] = None,
    ) -> CounterevidenceSearchRun:
        # Determine next run number
        stmt = (
            select(CounterevidenceSearchRun.run_number)
            .where(CounterevidenceSearchRun.research_request_id == research_request_id)
            .order_by(desc(CounterevidenceSearchRun.run_number))
            .limit(1)
        )
        last_num = self.db.execute(stmt).scalar_one_or_none() or 0
        run_number = last_num + 1

        run = CounterevidenceSearchRun(
            research_request_id=research_request_id,
            candidate_gap_id=candidate_gap_id,
            run_number=run_number,
            status="pending",
            initiated_by=initiated_by,
            configuration_snapshot=configuration_snapshot or {},
            started_at=utc_now(),
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_search_run(self, run_id: str) -> Optional[CounterevidenceSearchRun]:
        return self.db.execute(
            select(CounterevidenceSearchRun).where(CounterevidenceSearchRun.id == run_id)
        ).scalar_one_or_none()

    def get_runs_by_request(self, research_request_id: str) -> List[CounterevidenceSearchRun]:
        return list(
            self.db.execute(
                select(CounterevidenceSearchRun)
                .where(CounterevidenceSearchRun.research_request_id == research_request_id)
                .order_by(desc(CounterevidenceSearchRun.created_at))
            ).scalars().all()
        )

    def get_latest_run_for_gap(self, candidate_gap_id: str) -> Optional[CounterevidenceSearchRun]:
        return self.db.execute(
            select(CounterevidenceSearchRun)
            .where(CounterevidenceSearchRun.candidate_gap_id == candidate_gap_id)
            .order_by(desc(CounterevidenceSearchRun.created_at))
            .limit(1)
        ).scalar_one_or_none()

    def update_run_status(
        self,
        run_id: str,
        status: str,
        error_message: Optional[str] = None,
        claims_count: Optional[int] = None,
        queries_count: Optional[int] = None,
        pubs_count: Optional[int] = None,
        new_count: Optional[int] = None,
    ) -> Optional[CounterevidenceSearchRun]:
        run = self.get_search_run(run_id)
        if not run:
            return None
        run.status = status
        if error_message is not None:
            run.error_message = error_message
        if claims_count is not None:
            run.total_claims_decomposed = claims_count
        if queries_count is not None:
            run.total_queries_executed = queries_count
        if pubs_count is not None:
            run.total_publications_found = pubs_count
        if new_count is not None:
            run.newly_discovered_count = new_count
        if status in ("completed", "failed", "cancelled"):
            run.completed_at = utc_now()
        self.db.commit()
        self.db.refresh(run)
        return run

    # ==========================================
    # 2. Decomposed Claim Operations
    # ==========================================

    def save_claim(
        self,
        candidate_gap_id: str,
        claim_text: str,
        claim_type: str = "unexplored_problem",
        original_gap_statement: Optional[str] = None,
        generated_keywords: Optional[List[str]] = None,
        assumptions_investigated: Optional[List[str]] = None,
        order_index: int = 0,
    ) -> CounterevidenceClaim:
        claim = CounterevidenceClaim(
            candidate_gap_id=candidate_gap_id,
            claim_text=claim_text,
            claim_type=claim_type,
            original_gap_statement=original_gap_statement,
            generated_keywords=generated_keywords or [],
            assumptions_investigated=assumptions_investigated or [],
            order_index=order_index,
        )
        self.db.add(claim)
        self.db.commit()
        self.db.refresh(claim)
        return claim

    def get_claims_by_gap(self, candidate_gap_id: str) -> List[CounterevidenceClaim]:
        return list(
            self.db.execute(
                select(CounterevidenceClaim)
                .where(CounterevidenceClaim.candidate_gap_id == candidate_gap_id)
                .order_by(CounterevidenceClaim.order_index)
            ).scalars().all()
        )

    # ==========================================
    # 3. Search Query Operations
    # ==========================================

    def save_query(
        self,
        search_run_id: str,
        candidate_gap_id: str,
        query_text: str,
        query_type: str,
        search_rationale: str,
        source_database: str,
        claim_id: Optional[str] = None,
    ) -> CounterevidenceSearchQuery:
        query = CounterevidenceSearchQuery(
            search_run_id=search_run_id,
            candidate_gap_id=candidate_gap_id,
            claim_id=claim_id,
            query_text=query_text,
            query_type=query_type,
            search_rationale=search_rationale,
            source_database=source_database,
            execution_status="pending",
        )
        self.db.add(query)
        self.db.commit()
        self.db.refresh(query)
        return query

    def update_query_execution(
        self,
        query_id: str,
        status: str,
        results_count: int = 0,
        error_message: Optional[str] = None,
    ) -> Optional[CounterevidenceSearchQuery]:
        stmt = select(CounterevidenceSearchQuery).where(CounterevidenceSearchQuery.id == query_id)
        q = self.db.execute(stmt).scalar_one_or_none()
        if not q:
            return None
        q.execution_status = status
        q.results_count = results_count
        q.error_message = error_message
        q.executed_at = utc_now()
        self.db.commit()
        self.db.refresh(q)
        return q

    def get_queries_by_gap(self, candidate_gap_id: str) -> List[CounterevidenceSearchQuery]:
        return list(
            self.db.execute(
                select(CounterevidenceSearchQuery)
                .where(CounterevidenceSearchQuery.candidate_gap_id == candidate_gap_id)
                .order_by(desc(CounterevidenceSearchQuery.executed_at))
            ).scalars().all()
        )

    # ==========================================
    # 4. Publication Discovery Operations
    # ==========================================

    def record_publication(
        self,
        candidate_gap_id: str,
        search_run_id: str,
        paper_id: str,
        discovery_source: str,
        discovery_query_id: Optional[str] = None,
        is_newly_discovered: bool = True,
        discovery_tag: str = "counterevidence_discovered",
    ) -> CounterevidencePublication:
        # Check if already recorded for this gap
        stmt = select(CounterevidencePublication).where(
            and_(
                CounterevidencePublication.candidate_gap_id == candidate_gap_id,
                CounterevidencePublication.paper_id == paper_id,
            )
        )
        existing = self.db.execute(stmt).scalar_one_or_none()
        if existing:
            return existing

        pub = CounterevidencePublication(
            candidate_gap_id=candidate_gap_id,
            search_run_id=search_run_id,
            paper_id=paper_id,
            discovery_query_id=discovery_query_id,
            discovery_source=discovery_source,
            is_newly_discovered=is_newly_discovered,
            discovery_tag=discovery_tag,
            screening_status="unscreened",
            retrieved_at=utc_now(),
        )
        self.db.add(pub)
        self.db.commit()
        self.db.refresh(pub)
        return pub

    def get_publications_by_gap(self, candidate_gap_id: str) -> List[CounterevidencePublication]:
        return list(
            self.db.execute(
                select(CounterevidencePublication)
                .where(CounterevidencePublication.candidate_gap_id == candidate_gap_id)
                .order_by(desc(CounterevidencePublication.retrieved_at))
            ).scalars().all()
        )

    # ==========================================
    # 5. Assessment Operations
    # ==========================================

    def save_assessment(
        self,
        candidate_gap_id: str,
        paper_id: str,
        relevance_classification: str,
        impact_classification: str,
        explanation: str,
        actual_contribution_identified: str,
        research_problem_addressed: str,
        claim_id: Optional[str] = None,
        search_run_id: Optional[str] = None,
        relevant_methodology: Optional[str] = None,
        evidence_level: str = "level_3_metadata_only",
        is_abstract_based: bool = True,
        confidence_indicator: float = 0.7,
        assessment_method: str = "rule_deterministic",
        verification_status: str = "needs_verification",
    ) -> CounterevidenceAssessment:
        stmt = select(CounterevidenceAssessment).where(
            and_(
                CounterevidenceAssessment.candidate_gap_id == candidate_gap_id,
                CounterevidenceAssessment.paper_id == paper_id,
            )
        )
        existing = self.db.execute(stmt).scalar_one_or_none()
        if existing:
            # Update fields non-destructively
            existing.relevance_classification = relevance_classification
            existing.impact_classification = impact_classification
            existing.explanation = explanation
            existing.actual_contribution_identified = actual_contribution_identified
            existing.research_problem_addressed = research_problem_addressed
            existing.relevant_methodology = relevant_methodology
            existing.evidence_level = evidence_level
            existing.is_abstract_based = is_abstract_based
            existing.confidence_indicator = confidence_indicator
            existing.assessment_method = assessment_method
            existing.verification_status = verification_status
            existing.updated_at = utc_now()
            self.db.commit()
            self.db.refresh(existing)
            return existing

        assessment = CounterevidenceAssessment(
            candidate_gap_id=candidate_gap_id,
            paper_id=paper_id,
            claim_id=claim_id,
            search_run_id=search_run_id,
            relevance_classification=relevance_classification,
            impact_classification=impact_classification,
            explanation=explanation,
            actual_contribution_identified=actual_contribution_identified,
            research_problem_addressed=research_problem_addressed,
            relevant_methodology=relevant_methodology,
            evidence_level=evidence_level,
            is_abstract_based=is_abstract_based,
            confidence_indicator=confidence_indicator,
            assessment_method=assessment_method,
            verification_status=verification_status,
            human_review_status="pending_review",
            original_automated_classification=relevance_classification,
        )
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        return assessment

    def get_assessments_by_gap(self, candidate_gap_id: str) -> List[CounterevidenceAssessment]:
        return list(
            self.db.execute(
                select(CounterevidenceAssessment)
                .where(CounterevidenceAssessment.candidate_gap_id == candidate_gap_id)
                .order_by(desc(CounterevidenceAssessment.created_at))
            ).scalars().all()
        )

    def get_assessment_by_id(self, assessment_id: str) -> Optional[CounterevidenceAssessment]:
        return self.db.execute(
            select(CounterevidenceAssessment).where(CounterevidenceAssessment.id == assessment_id)
        ).scalar_one_or_none()

    def update_assessment_review(
        self,
        assessment_id: str,
        relevance_classification: str,
        reviewer_reference: str,
        reviewer_notes: str,
        impact_classification: Optional[str] = None,
    ) -> Optional[CounterevidenceAssessment]:
        assess = self.get_assessment_by_id(assessment_id)
        if not assess:
            return None
        # Preserve original automated classification if not yet preserved
        if not assess.original_automated_classification:
            assess.original_automated_classification = assess.relevance_classification
        assess.relevance_classification = relevance_classification
        if impact_classification:
            assess.impact_classification = impact_classification
        assess.human_review_status = "corrected" if relevance_classification != assess.original_automated_classification else "confirmed"
        assess.reviewer_reference = reviewer_reference
        assess.reviewer_notes = reviewer_notes
        assess.verification_status = "human_verified"
        assess.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(assess)
        return assess

    # ==========================================
    # 6. Evidence Ground Truth Items
    # ==========================================

    def save_evidence_item(
        self,
        assessment_id: str,
        candidate_gap_id: str,
        paper_id: str,
        verbatim_passage: str,
        evidence_summary: str,
        source_reference: str,
        page_number: Optional[int] = None,
        section_heading: Optional[str] = None,
        evidence_passage_id: Optional[str] = None,
        evidence_type: str = "finding",
        is_verbatim_quote: bool = True,
        verification_status: str = "source_supported",
    ) -> CounterevidenceEvidence:
        item = CounterevidenceEvidence(
            assessment_id=assessment_id,
            candidate_gap_id=candidate_gap_id,
            paper_id=paper_id,
            evidence_passage_id=evidence_passage_id,
            verbatim_passage=verbatim_passage,
            page_number=page_number,
            section_heading=section_heading,
            evidence_summary=evidence_summary,
            evidence_type=evidence_type,
            source_reference=source_reference,
            is_verbatim_quote=is_verbatim_quote,
            verification_status=verification_status,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def get_evidence_items_by_gap(self, candidate_gap_id: str) -> List[CounterevidenceEvidence]:
        return list(
            self.db.execute(
                select(CounterevidenceEvidence)
                .where(CounterevidenceEvidence.candidate_gap_id == candidate_gap_id)
                .order_by(desc(CounterevidenceEvidence.created_at))
            ).scalars().all()
        )

    # ==========================================
    # 7. Counterevidence Profile Operations
    # ==========================================

    def save_profile(
        self,
        candidate_gap_id: str,
        search_run_id: str,
        total_retrieved: int,
        previously_reviewed_count: int,
        newly_discovered_count: int,
        direct_counterevidence_count: int,
        partial_counterevidence_count: int,
        related_evidence_count: int,
        irrelevant_count: int,
        inconclusive_count: int,
        impact_assessment: str,
        executive_summary: str,
        remaining_unresolved_claims: Optional[List[str]] = None,
        search_limitations: Optional[List[str]] = None,
        fulltext_availability_limitations: Optional[List[str]] = None,
        verification_status: str = "verified_traceable",
    ) -> CounterevidenceProfile:
        stmt = select(CounterevidenceProfile).where(
            CounterevidenceProfile.candidate_gap_id == candidate_gap_id
        )
        existing = self.db.execute(stmt).scalar_one_or_none()
        if existing:
            existing.search_run_id = search_run_id
            existing.total_retrieved = total_retrieved
            existing.previously_reviewed_count = previously_reviewed_count
            existing.newly_discovered_count = newly_discovered_count
            existing.direct_counterevidence_count = direct_counterevidence_count
            existing.partial_counterevidence_count = partial_counterevidence_count
            existing.related_evidence_count = related_evidence_count
            existing.irrelevant_count = irrelevant_count
            existing.inconclusive_count = inconclusive_count
            existing.impact_assessment = impact_assessment
            existing.executive_summary = executive_summary
            existing.remaining_unresolved_claims = remaining_unresolved_claims or []
            existing.search_limitations = search_limitations or []
            existing.fulltext_availability_limitations = fulltext_availability_limitations or []
            existing.verification_status = verification_status
            existing.updated_at = utc_now()
            self.db.commit()
            self.db.refresh(existing)
            return existing

        profile = CounterevidenceProfile(
            candidate_gap_id=candidate_gap_id,
            search_run_id=search_run_id,
            total_retrieved=total_retrieved,
            previously_reviewed_count=previously_reviewed_count,
            newly_discovered_count=newly_discovered_count,
            direct_counterevidence_count=direct_counterevidence_count,
            partial_counterevidence_count=partial_counterevidence_count,
            related_evidence_count=related_evidence_count,
            irrelevant_count=irrelevant_count,
            inconclusive_count=inconclusive_count,
            impact_assessment=impact_assessment,
            executive_summary=executive_summary,
            remaining_unresolved_claims=remaining_unresolved_claims or [],
            search_limitations=search_limitations or [],
            fulltext_availability_limitations=fulltext_availability_limitations or [],
            verification_status=verification_status,
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def get_profile_by_gap(self, candidate_gap_id: str) -> Optional[CounterevidenceProfile]:
        return self.db.execute(
            select(CounterevidenceProfile).where(
                CounterevidenceProfile.candidate_gap_id == candidate_gap_id
            )
        ).scalar_one_or_none()
