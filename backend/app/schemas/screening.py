"""Pydantic Schemas for Paper Screening."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ScreeningCriteriaSnapshot(BaseModel):
    """Snapshot of screening criteria used during a run."""

    topic: str
    objective: str
    research_questions: List[str] = Field(default_factory=list)
    start_year: int
    end_year: int
    publication_types: List[str] = Field(default_factory=list)
    inclusion_criteria: List[str] = Field(default_factory=list)
    exclusion_criteria: List[str] = Field(default_factory=list)


class ScreeningDecisionResponse(BaseModel):
    """Screening decision for an individual paper."""

    id: str
    run_id: str
    paper_id: str
    paper_title: Optional[str] = None
    paper_authors: List[str] = Field(default_factory=list)
    paper_year: Optional[int] = None
    paper_venue: Optional[str] = None
    has_abstract: bool = False
    has_pdf: bool = False

    decision: str  # included, excluded, needs_human_review
    stage: str  # metadata_abstract, full_text, human_override
    reason: str
    criteria_evaluated: List[str] = Field(default_factory=list)
    criteria_satisfied: List[str] = Field(default_factory=list)
    criteria_unsatisfied: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    confidence_score: Optional[float] = None
    screening_method: str = "rule_based"

    is_human_override: bool = False
    original_decision: Optional[str] = None
    reviewer_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime


class ScreeningRunResponse(BaseModel):
    """Screening run execution summary."""

    id: str
    request_id: str
    run_number: int
    criteria_snapshot: Dict[str, Any]
    total_papers: int
    included_count: int
    excluded_count: int
    review_needed_count: int
    executed_at: datetime


class ScreeningRunDetailResponse(ScreeningRunResponse):
    """Screening run response including individual paper decisions."""

    decisions: List[ScreeningDecisionResponse] = Field(default_factory=list)


class HumanOverrideRequest(BaseModel):
    """Payload to manually override an automated screening decision."""

    decision: str = Field(..., pattern="^(included|excluded|needs_human_review)$")
    reviewer_notes: str = Field(..., min_length=3, description="Justification for manual decision change")

