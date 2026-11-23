"""Screening database repository."""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from backend.app.models.screening import ScreeningRun, ScreeningDecision
from backend.app.models.paper import Paper


class ScreeningRepository:
    """Repository handling persistence for screening runs and decisions."""

    def __init__(self, db: Session):
        self.db = db

    def get_latest_run(self, request_id: str) -> Optional[ScreeningRun]:
        stmt = (
            select(ScreeningRun)
            .where(ScreeningRun.request_id == request_id)
            .order_by(desc(ScreeningRun.run_number))
            .limit(1)
        )
        return self.db.scalars(stmt).first()

    def get_runs_by_request(self, request_id: str) -> List[ScreeningRun]:
        stmt = (
            select(ScreeningRun)
            .where(ScreeningRun.request_id == request_id)
            .order_by(desc(ScreeningRun.run_number))
        )
        return list(self.db.scalars(stmt).all())

    def create_run(
        self,
        request_id: str,
        criteria_snapshot: dict,
        total_papers: int,
        included_count: int,
        excluded_count: int,
        review_needed_count: int,
    ) -> ScreeningRun:
        latest = self.get_latest_run(request_id)
        next_run_num = (latest.run_number + 1) if latest else 1

        run = ScreeningRun(
            request_id=request_id,
            run_number=next_run_num,
            criteria_snapshot=criteria_snapshot,
            total_papers=total_papers,
            included_count=included_count,
            excluded_count=excluded_count,
            review_needed_count=review_needed_count,
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def add_decision(
        self,
        run_id: str,
        paper_id: str,
        decision: str,
        stage: str,
        reason: str,
        criteria_evaluated: list,
        criteria_satisfied: list,
        criteria_unsatisfied: list,
        missing_information: list,
        confidence_score: Optional[float] = None,
        screening_method: str = "rule_based",
    ) -> ScreeningDecision:
        dec = ScreeningDecision(
            run_id=run_id,
            paper_id=paper_id,
            decision=decision,
            stage=stage,
            reason=reason,
            criteria_evaluated=criteria_evaluated,
            criteria_satisfied=criteria_satisfied,
            criteria_unsatisfied=criteria_unsatisfied,
            missing_information=missing_information,
            confidence_score=confidence_score,
            screening_method=screening_method,
        )
        self.db.add(dec)
        return dec

    def get_decisions_for_run(
        self,
        run_id: str,
        decision_filter: Optional[str] = None,
    ) -> List[ScreeningDecision]:
        stmt = select(ScreeningDecision).where(ScreeningDecision.run_id == run_id)
        if decision_filter:
            stmt = stmt.where(ScreeningDecision.decision == decision_filter)
        stmt = stmt.order_by(ScreeningDecision.created_at.asc())
        return list(self.db.scalars(stmt).all())

    def get_decision_by_paper(self, paper_id: str) -> Optional[ScreeningDecision]:
        stmt = (
            select(ScreeningDecision)
            .where(ScreeningDecision.paper_id == paper_id)
            .order_by(desc(ScreeningDecision.created_at))
            .limit(1)
        )
        return self.db.scalars(stmt).first()

    def update_human_override(
        self,
        paper_id: str,
        new_decision: str,
        reviewer_notes: str,
    ) -> Optional[ScreeningDecision]:
        decision = self.get_decision_by_paper(paper_id)
        if not decision:
            return None

        # Non-destructive: preserve original decision
        if not decision.is_human_override:
            decision.original_decision = decision.decision

        decision.is_human_override = True
        decision.decision = new_decision
        decision.stage = "human_override"
        decision.reviewer_notes = reviewer_notes
        decision.reviewed_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(decision)
        return decision

