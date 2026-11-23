"""Screening Database Models.

Stores batches of automated screening executions, screening criteria snapshots,
individual paper decisions, and non-destructive human overrides with audit trail.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Text, JSON, DateTime, ForeignKey, Boolean, Float, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, generate_uuid, utc_now


class ScreeningRun(Base):
    """Represents a screening execution batch for a research request."""

    __tablename__ = "screening_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    request_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_requests.id", ondelete="CASCADE"), nullable=False)
    run_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    criteria_snapshot: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    total_papers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    included_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    excluded_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    review_needed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    executed_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    request: Mapped["ResearchRequest"] = relationship("ResearchRequest", back_populates="screening_runs")
    decisions: Mapped[List["ScreeningDecision"]] = relationship(
        "ScreeningDecision", back_populates="run", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_screening_runs_request", "request_id", "run_number"),
    )


class ScreeningDecision(Base):
    """Individual screening decision for a paper within a screening run."""

    __tablename__ = "screening_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("screening_runs.id", ondelete="CASCADE"), nullable=False)
    paper_id: Mapped[str] = mapped_column(String(64), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)

    decision: Mapped[str] = mapped_column(String(30), nullable=False)  # included, excluded, needs_human_review
    stage: Mapped[str] = mapped_column(String(30), default="metadata_abstract", nullable=False)  # metadata_abstract, full_text, human_override
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    criteria_evaluated: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    criteria_satisfied: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    criteria_unsatisfied: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    missing_information: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    screening_method: Mapped[str] = mapped_column(String(50), default="rule_based", nullable=False)

    # Non-destructive human override audit trail
    is_human_override: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    original_decision: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    run: Mapped["ScreeningRun"] = relationship("ScreeningRun", back_populates="decisions")
    paper: Mapped["Paper"] = relationship("Paper", back_populates="screening_decisions")

    __table_args__ = (
        Index("idx_screening_decisions_run_paper", "run_id", "paper_id"),
        Index("idx_screening_decisions_decision", "decision"),
    )
