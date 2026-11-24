"""Staged Paper Screening Orchestration Service."""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.research_request import ResearchRequest
from backend.app.models.paper import Paper
from backend.app.models.screening import ScreeningRun, ScreeningDecision
from backend.app.services.persistence.repositories import ResearchRequestRepository, PaperRepository
from backend.app.services.persistence.screening_repository import ScreeningRepository
from backend.app.services.screening.criteria_evaluator import ScreeningCriteriaEvaluator
from backend.app.core.logging import logger


class ScreeningService:
    """Orchestrates staged academic paper screening runs."""

    def __init__(self, db: Session):
        self.db = db
        self.research_repo = ResearchRequestRepository(db)
        self.paper_repo = PaperRepository(db)
        self.screening_repo = ScreeningRepository(db)
        self.evaluator = ScreeningCriteriaEvaluator()

    def execute_screening_run(self, request_id: str) -> ScreeningRun:
        """Executes a complete reproducible screening batch on a research request's papers."""
        request = self.research_repo.get_by_id(request_id)
        if not request:
            raise ValueError(f"Research request {request_id} not found.")

        # Snapshot screening criteria for reproducibility
        criteria_snapshot = {
            "topic": request.topic,
            "objective": request.objective,
            "domain": request.domain,
            "research_questions": [q.question_text for q in request.questions],
            "start_year": request.start_year,
            "end_year": request.end_year,
            "publication_types": request.publication_types or [],
            "inclusion_criteria": request.inclusion_criteria or [],
            "exclusion_criteria": request.exclusion_criteria or [],
        }

        # Retrieve all canonical papers for this request
        papers = list(request.papers)
        total_papers = len(papers)
        if total_papers == 0:
            raise ValueError("No retrieved papers available to screen. Execute Phase 1 search first.")

        included_count = 0
        excluded_count = 0
        review_count = 0

        # Create screening run record
        run = self.screening_repo.create_run(
            request_id=request_id,
            criteria_snapshot=criteria_snapshot,
            total_papers=total_papers,
            included_count=0,
            excluded_count=0,
            review_needed_count=0,
        )

        for paper in papers:
            decision, reason, evaluated, satisfied, unsatisfied, missing, confidence = (
                self.evaluator.evaluate_paper(paper, request)
            )

            if decision == "included":
                included_count += 1
            elif decision == "excluded":
                excluded_count += 1
            else:
                review_count += 1

            self.screening_repo.add_decision(
                run_id=run.id,
                paper_id=paper.id,
                decision=decision,
                stage="metadata_abstract",
                reason=reason,
                criteria_evaluated=evaluated,
                criteria_satisfied=satisfied,
                criteria_unsatisfied=unsatisfied,
                missing_information=missing,
                confidence_score=confidence,
                screening_method="rule_based_staged",
            )

        # Update run aggregates
        run.included_count = included_count
        run.excluded_count = excluded_count
        run.review_needed_count = review_count

        self.db.commit()
        self.db.refresh(run)

        logger.info(
            f"Screening Run {run.run_number} complete for Request {request_id}: "
            f"{included_count} included, {excluded_count} excluded, {review_count} needs review."
        )
        return run

    def record_human_override(
        self,
        paper_id: str,
        decision: str,
        reviewer_notes: str,
    ) -> Optional[ScreeningDecision]:
        """Records a non-destructive human reviewer override for a paper's screening decision."""
        return self.screening_repo.update_human_override(
            paper_id=paper_id,
            new_decision=decision,
            reviewer_notes=reviewer_notes,
        )
