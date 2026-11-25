"""Synthesis Database Models (Phase 4).

Stores versioned literature synthesis runs, paper comparison records,
discovered research themes, empirical patterns, candidate research gaps,
explicit evidence links, and human review audit histories.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import (
    String,
    Integer,
    Text,
    JSON,
    DateTime,
    ForeignKey,
    Boolean,
    Float,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, generate_uuid, utc_now


class SynthesisRun(Base):
    """Represents a versioned execution run of the literature synthesis pipeline."""

    __tablename__ = "synthesis_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    research_request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("research_requests.id", ondelete="CASCADE"), nullable=False
    )
    run_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )  # pending, retrieving_evidence, building_comparison, identifying_themes, analysing_patterns, generating_synthesis, generating_candidate_gaps, completed, partially_completed, failed, cancelled

    selected_paper_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    evidence_graph_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    synthesis_configuration: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    prompt_version: Mapped[Optional[str]] = mapped_column(String(50), default="v1.0-academic", nullable=True)
    model_provider: Mapped[Optional[str]] = mapped_column(String(50), default="rule_deterministic", nullable=True)
    model_name: Mapped[Optional[str]] = mapped_column(String(100), default="deterministic-engine", nullable=True)

    summary_narrative: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    execution_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    execution_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    themes: Mapped[List["LiteratureTheme"]] = relationship(
        "LiteratureTheme", back_populates="synthesis_run", cascade="all, delete-orphan"
    )
    patterns: Mapped[List["LiteraturePattern"]] = relationship(
        "LiteraturePattern", back_populates="synthesis_run", cascade="all, delete-orphan"
    )
    candidate_gaps: Mapped[List["CandidateResearchGap"]] = relationship(
        "CandidateResearchGap", back_populates="synthesis_run", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_synthesis_runs_request", "research_request_id"),
        Index("idx_synthesis_runs_status", "status"),
    )


class LiteratureTheme(Base):
    """Represents a recurring research theme grouped across retrieved literature."""

    __tablename__ = "literature_themes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    synthesis_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("synthesis_runs.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    theme_category: Mapped[str] = mapped_column(
        String(100), default="methodological", nullable=False
    )  # methodological, empirical, application, theoretical, evaluation

    related_concepts: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    associated_paper_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    supporting_claim_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    supporting_evidence_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    frequency: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)
    confidence_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    known_limitations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    synthesis_run: Mapped["SynthesisRun"] = relationship("SynthesisRun", back_populates="themes")

    __table_args__ = (
        Index("idx_lit_themes_run", "synthesis_run_id"),
        Index("idx_lit_themes_category", "theme_category"),
    )


class LiteraturePattern(Base):
    """Represents an observed trend or pattern in methodologies, datasets, models, or evaluations."""

    __tablename__ = "literature_patterns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    synthesis_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("synthesis_runs.id", ondelete="CASCADE"), nullable=False
    )
    pattern_type: Mapped[str] = mapped_column(
        String(80), nullable=False
    )  # methodology, dataset, model, evaluation, cross_limitation, publication_trend
    description: Mapped[str] = mapped_column(Text, nullable=False)
    observed_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    related_paper_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    related_evidence_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    interpretation: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.75, nullable=False)
    limitations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    synthesis_run: Mapped["SynthesisRun"] = relationship("SynthesisRun", back_populates="patterns")

    __table_args__ = (
        Index("idx_lit_patterns_run", "synthesis_run_id"),
        Index("idx_lit_patterns_type", "pattern_type"),
    )


class CandidateResearchGap(Base):
    """Represents an evidence-backed candidate research gap hypothesis."""

    __tablename__ = "candidate_research_gaps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    synthesis_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("synthesis_runs.id", ondelete="CASCADE"), nullable=False
    )
    research_request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("research_requests.id", ondelete="CASCADE"), nullable=False
    )

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(80), default="unclassified", nullable=False
    )  # methodological_gap, empirical_gap, dataset_or_benchmark_gap, evaluation_gap, generalisation_gap, reproducibility_gap, theoretical_gap, deployment_gap, interdisciplinary_gap, unclassified

    research_domain: Mapped[str] = mapped_column(String(150), default="Computer Science", nullable=False)
    related_research_questions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    observed_pattern: Mapped[str] = mapped_column(Text, nullable=False)
    scope: Mapped[str] = mapped_column(String(200), default="retrieved_corpus_subset", nullable=False)

    preliminary_confidence: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    confidence_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    assumptions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    known_limitations: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    potential_counterexamples: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    unresolved_questions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    suggested_validation_queries: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    supporting_paper_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    supporting_claim_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    supporting_finding_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    supporting_limitation_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    supporting_evidence_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    generation_status: Mapped[str] = mapped_column(
        String(50), default="provisional", nullable=False
    )  # provisional, evidence_grounded, weak_evidence, flagged
    human_review_status: Mapped[str] = mapped_column(
        String(50), default="pending_review", nullable=False
    )  # pending_review, accepted_for_further_investigation, rejected, requires_more_evidence, edited_by_reviewer

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    synthesis_run: Mapped["SynthesisRun"] = relationship("SynthesisRun", back_populates="candidate_gaps")
    evidence_links: Mapped[List["GapEvidenceLink"]] = relationship(
        "GapEvidenceLink", back_populates="candidate_gap", cascade="all, delete-orphan"
    )
    review_records: Mapped[List["HumanReviewRecord"]] = relationship(
        "HumanReviewRecord", back_populates="candidate_gap", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_gaps_run", "synthesis_run_id"),
        Index("idx_gaps_request", "research_request_id"),
        Index("idx_gaps_category", "category"),
        Index("idx_gaps_review_status", "human_review_status"),
    )


class GapEvidenceLink(Base):
    """Explicit relationship mapping a candidate research gap to a supporting evidence passage or claim."""

    __tablename__ = "gap_evidence_links"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    candidate_gap_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("candidate_research_gaps.id", ondelete="CASCADE"), nullable=False
    )
    evidence_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("evidence_passages.id", ondelete="SET NULL"), nullable=True
    )
    claim_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    paper_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False
    )

    relationship_type: Mapped[str] = mapped_column(
        String(60), default="supports_rationale", nullable=False
    )  # supports_rationale, demonstrates_pattern, reports_limitation, reports_future_direction, provides_context
    contribution_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    candidate_gap: Mapped["CandidateResearchGap"] = relationship(
        "CandidateResearchGap", back_populates="evidence_links"
    )

    __table_args__ = (
        Index("idx_gap_ev_links_gap", "candidate_gap_id"),
        Index("idx_gap_ev_links_paper", "paper_id"),
        Index("idx_gap_ev_links_evidence", "evidence_id"),
    )


class HumanReviewRecord(Base):
    """Audit record capturing human review decisions and revisions on candidate research gaps."""

    __tablename__ = "human_review_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    candidate_gap_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("candidate_research_gaps.id", ondelete="CASCADE"), nullable=False
    )
    reviewer_reference: Mapped[str] = mapped_column(String(100), default="researcher", nullable=False)
    review_action: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # accept, reject, request_evidence, edit

    original_value: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    revised_value: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    reviewer_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    candidate_gap: Mapped["CandidateResearchGap"] = relationship(
        "CandidateResearchGap", back_populates="review_records"
    )

    __table_args__ = (
        Index("idx_human_reviews_gap", "candidate_gap_id"),
        Index("idx_human_reviews_action", "review_action"),
    )
