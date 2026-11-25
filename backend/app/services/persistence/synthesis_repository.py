"""Synthesis Repository (Phase 4).

Provides persistent data access, CRUD operations, and transaction management
for synthesis runs, research themes, empirical patterns, candidate research gaps,
evidence links, and human reviews.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import Session, joinedload
from backend.app.models.synthesis import (
    SynthesisRun,
    LiteratureTheme,
    LiteraturePattern,
    CandidateResearchGap,
    GapEvidenceLink,
    HumanReviewRecord,
)
from backend.app.models.base import utc_now


class SynthesisRepository:
    """Repository handling persistence for all Phase 4 synthesis and candidate gap models."""

    def __init__(self, db: Session):
        self.db = db

    def create_synthesis_run(
        self,
        request_id: str,
        selected_paper_ids: List[str],
        synthesis_configuration: Optional[Dict[str, Any]] = None,
        prompt_version: str = "v1.0-academic",
        model_provider: str = "rule_deterministic",
        model_name: str = "deterministic-engine",
        evidence_graph_version: Optional[str] = None,
    ) -> SynthesisRun:
        """Initializes a new versioned synthesis run."""
        # Calculate run number
        count_stmt = select(func.count(SynthesisRun.id)).where(SynthesisRun.research_request_id == request_id)
        current_count = self.db.scalar(count_stmt) or 0
        run_number = current_count + 1

        run = SynthesisRun(
            research_request_id=request_id,
            run_number=run_number,
            status="pending",
            selected_paper_ids=selected_paper_ids,
            evidence_graph_version=evidence_graph_version,
            synthesis_configuration=synthesis_configuration or {},
            prompt_version=prompt_version,
            model_provider=model_provider,
            model_name=model_name,
            summary_narrative={},
            execution_started_at=utc_now(),
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def update_synthesis_run_status(
        self,
        run_id: str,
        status: str,
        error_details: Optional[str] = None,
        summary_narrative: Optional[Dict[str, Any]] = None,
    ) -> Optional[SynthesisRun]:
        """Updates status, execution completion, and narrative summary of a run."""
        run = self.get_synthesis_run(run_id)
        if not run:
            return None

        run.status = status
        if error_details:
            run.error_details = error_details
        if summary_narrative is not None:
            run.summary_narrative = summary_narrative
        if status in ("completed", "failed", "cancelled", "partially_completed"):
            run.execution_completed_at = utc_now()

        run.updated_at = utc_now()
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_synthesis_run(self, run_id: str) -> Optional[SynthesisRun]:
        """Retrieves a single synthesis run by ID."""
        return self.db.scalar(select(SynthesisRun).where(SynthesisRun.id == run_id))

    def get_synthesis_runs_by_request(self, request_id: str) -> List[SynthesisRun]:
        """Lists all synthesis runs for a research request, sorted newest first."""
        stmt = (
            select(SynthesisRun)
            .where(SynthesisRun.research_request_id == request_id)
            .order_by(desc(SynthesisRun.created_at))
        )
        return list(self.db.scalars(stmt).all())

    def get_latest_synthesis_run(self, request_id: str) -> Optional[SynthesisRun]:
        """Retrieves the most recent synthesis run for a request."""
        stmt = (
            select(SynthesisRun)
            .where(SynthesisRun.research_request_id == request_id)
            .order_by(desc(SynthesisRun.created_at))
            .limit(1)
        )
        return self.db.scalar(stmt)

    # --- Themes ---

    def create_literature_themes(
        self, run_id: str, themes_data: List[Dict[str, Any]]
    ) -> List[LiteratureTheme]:
        """Bulk inserts identified literature themes for a run."""
        created = []
        for t in themes_data:
            theme = LiteratureTheme(
                synthesis_run_id=run_id,
                name=t["name"],
                description=t["description"],
                theme_category=t.get("theme_category", "methodological"),
                related_concepts=t.get("related_concepts", []),
                associated_paper_ids=t.get("associated_paper_ids", []),
                supporting_claim_ids=t.get("supporting_claim_ids", []),
                supporting_evidence_ids=t.get("supporting_evidence_ids", []),
                frequency=t.get("frequency", len(t.get("associated_paper_ids", []))),
                confidence=t.get("confidence", 0.8),
                confidence_explanation=t.get("confidence_explanation"),
                known_limitations=t.get("known_limitations"),
            )
            self.db.add(theme)
            created.append(theme)
        self.db.commit()
        return created

    def get_themes_by_run(self, run_id: str) -> List[LiteratureTheme]:
        """Retrieves all themes identified in a run."""
        stmt = (
            select(LiteratureTheme)
            .where(LiteratureTheme.synthesis_run_id == run_id)
            .order_by(desc(LiteratureTheme.frequency))
        )
        return list(self.db.scalars(stmt).all())

    # --- Patterns ---

    def create_literature_patterns(
        self, run_id: str, patterns_data: List[Dict[str, Any]]
    ) -> List[LiteraturePattern]:
        """Bulk inserts analyzed empirical and methodological patterns."""
        created = []
        for p in patterns_data:
            pat = LiteraturePattern(
                synthesis_run_id=run_id,
                pattern_type=p["pattern_type"],
                description=p["description"],
                observed_data=p.get("observed_data", {}),
                related_paper_ids=p.get("related_paper_ids", []),
                related_evidence_ids=p.get("related_evidence_ids", []),
                interpretation=p["interpretation"],
                confidence=p.get("confidence", 0.75),
                limitations=p.get("limitations"),
            )
            self.db.add(pat)
            created.append(pat)
        self.db.commit()
        return created

    def get_patterns_by_run(self, run_id: str) -> List[LiteraturePattern]:
        """Retrieves all patterns analyzed in a run."""
        stmt = (
            select(LiteraturePattern)
            .where(LiteraturePattern.synthesis_run_id == run_id)
            .order_by(LiteraturePattern.pattern_type.asc())
        )
        return list(self.db.scalars(stmt).all())

    # --- Candidate Research Gaps ---

    def create_candidate_gap(self, gap_data: Dict[str, Any]) -> CandidateResearchGap:
        """Persists a new candidate research gap."""
        gap = CandidateResearchGap(
            synthesis_run_id=gap_data["synthesis_run_id"],
            research_request_id=gap_data["research_request_id"],
            title=gap_data["title"],
            description=gap_data["description"],
            category=gap_data.get("category", "unclassified"),
            research_domain=gap_data.get("research_domain", "Computer Science"),
            related_research_questions=gap_data.get("related_research_questions", []),
            rationale=gap_data["rationale"],
            observed_pattern=gap_data["observed_pattern"],
            scope=gap_data.get("scope", "retrieved_corpus_subset"),
            preliminary_confidence=gap_data.get("preliminary_confidence", 0.7),
            confidence_explanation=gap_data.get("confidence_explanation", ""),
            assumptions=gap_data.get("assumptions", []),
            known_limitations=gap_data.get("known_limitations", []),
            potential_counterexamples=gap_data.get("potential_counterexamples", []),
            unresolved_questions=gap_data.get("unresolved_questions", []),
            suggested_validation_queries=gap_data.get("suggested_validation_queries", []),
            supporting_paper_ids=gap_data.get("supporting_paper_ids", []),
            supporting_claim_ids=gap_data.get("supporting_claim_ids", []),
            supporting_finding_ids=gap_data.get("supporting_finding_ids", []),
            supporting_limitation_ids=gap_data.get("supporting_limitation_ids", []),
            supporting_evidence_ids=gap_data.get("supporting_evidence_ids", []),
            generation_status=gap_data.get("generation_status", "provisional"),
            human_review_status=gap_data.get("human_review_status", "pending_review"),
        )
        self.db.add(gap)
        self.db.commit()
        self.db.refresh(gap)
        return gap

    def get_candidate_gap(self, gap_id: str) -> Optional[CandidateResearchGap]:
        """Retrieves a single candidate research gap with evidence links and review history."""
        stmt = (
            select(CandidateResearchGap)
            .options(
                joinedload(CandidateResearchGap.evidence_links),
                joinedload(CandidateResearchGap.review_records),
            )
            .where(CandidateResearchGap.id == gap_id)
        )
        return self.db.scalar(stmt)

    def get_candidate_gaps_by_run(
        self,
        run_id: str,
        category: Optional[str] = None,
        review_status: Optional[str] = None,
    ) -> List[CandidateResearchGap]:
        """Lists candidate gaps for a run, with optional filtering."""
        conditions = [CandidateResearchGap.synthesis_run_id == run_id]
        if category:
            conditions.append(CandidateResearchGap.category == category)
        if review_status:
            conditions.append(CandidateResearchGap.human_review_status == review_status)

        stmt = (
            select(CandidateResearchGap)
            .options(joinedload(CandidateResearchGap.evidence_links))
            .where(and_(*conditions))
            .order_by(desc(CandidateResearchGap.preliminary_confidence))
        )
        return list(self.db.scalars(stmt).unique().all())

    def get_candidate_gaps_by_request(
        self,
        request_id: str,
        category: Optional[str] = None,
        review_status: Optional[str] = None,
    ) -> List[CandidateResearchGap]:
        """Lists all candidate gaps across runs for a research request."""
        conditions = [CandidateResearchGap.research_request_id == request_id]
        if category:
            conditions.append(CandidateResearchGap.category == category)
        if review_status:
            conditions.append(CandidateResearchGap.human_review_status == review_status)

        stmt = (
            select(CandidateResearchGap)
            .options(joinedload(CandidateResearchGap.evidence_links))
            .where(and_(*conditions))
            .order_by(desc(CandidateResearchGap.created_at))
        )
        return list(self.db.scalars(stmt).unique().all())

    # --- Evidence Links ---

    def create_gap_evidence_links(self, links_data: List[Dict[str, Any]]) -> List[GapEvidenceLink]:
        """Creates explicit grounding links between a candidate gap and supporting evidence."""
        created = []
        for l in links_data:
            link = GapEvidenceLink(
                candidate_gap_id=l["candidate_gap_id"],
                evidence_id=l.get("evidence_id"),
                claim_id=l.get("claim_id"),
                paper_id=l["paper_id"],
                relationship_type=l.get("relationship_type", "supports_rationale"),
                contribution_explanation=l.get("contribution_explanation", "Direct evidence"),
                relevance_score=l.get("relevance_score", 1.0),
            )
            self.db.add(link)
            created.append(link)
        self.db.commit()
        return created

    def get_gap_evidence_links(self, gap_id: str) -> List[GapEvidenceLink]:
        """Retrieves all evidence links for a candidate research gap."""
        stmt = (
            select(GapEvidenceLink)
            .where(GapEvidenceLink.candidate_gap_id == gap_id)
            .order_by(desc(GapEvidenceLink.relevance_score))
        )
        return list(self.db.scalars(stmt).all())

    # --- Human Reviews ---

    def add_human_review_record(
        self,
        gap_id: str,
        reviewer_reference: str,
        review_action: str,
        original_value: Dict[str, Any],
        revised_value: Dict[str, Any],
        reviewer_comment: Optional[str] = None,
    ) -> HumanReviewRecord:
        """Records a human review decision and updates candidate gap status."""
        gap = self.get_candidate_gap(gap_id)
        if not gap:
            raise ValueError(f"CandidateResearchGap '{gap_id}' not found.")

        # Map action to gap review status
        if review_action == "accept":
            gap.human_review_status = "accepted_for_further_investigation"
        elif review_action == "reject":
            gap.human_review_status = "rejected"
        elif review_action == "request_evidence":
            gap.human_review_status = "requires_more_evidence"
        elif review_action == "edit":
            gap.human_review_status = "edited_by_reviewer"
            if revised_value.get("title"):
                gap.title = revised_value["title"]
            if revised_value.get("description"):
                gap.description = revised_value["description"]
            if revised_value.get("category"):
                gap.category = revised_value["category"]

        gap.updated_at = utc_now()

        review = HumanReviewRecord(
            candidate_gap_id=gap_id,
            reviewer_reference=reviewer_reference,
            review_action=review_action,
            original_value=original_value,
            revised_value=revised_value,
            reviewer_comment=reviewer_comment,
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review

    def get_review_records_by_gap(self, gap_id: str) -> List[HumanReviewRecord]:
        """Retrieves the review audit history for a candidate gap."""
        stmt = (
            select(HumanReviewRecord)
            .where(HumanReviewRecord.candidate_gap_id == gap_id)
            .order_by(desc(HumanReviewRecord.created_at))
        )
        return list(self.db.scalars(stmt).all())
