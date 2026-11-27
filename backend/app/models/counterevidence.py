"""Counterevidence Database Models (Phase 5).

Stores counterevidence search runs, decomposed gap claims, generated counter-queries,
discovered counterevidence publications, claim-level relevance assessments,
passage ground-truth linkages, and structured counterevidence gap profiles.
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


class CounterevidenceSearchRun(Base):
    """Represents an execution run of the counterevidence retrieval pipeline."""

    __tablename__ = "counterevidence_search_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    research_request_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("research_requests.id", ondelete="CASCADE"), nullable=False
    )
    candidate_gap_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("candidate_research_gaps.id", ondelete="CASCADE"), nullable=True
    )
    run_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )  # pending, decomposing_claims, generating_queries, searching_databases, processing_publications, assessing_relevance, extracting_evidence, generating_profile, completed, failed, cancelled

    initiated_by: Mapped[str] = mapped_column(String(50), default="researcher", nullable=False)
    configuration_snapshot: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    
    total_claims_decomposed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_queries_executed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_publications_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    newly_discovered_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=utc_now, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    queries: Mapped[List["CounterevidenceSearchQuery"]] = relationship(
        "CounterevidenceSearchQuery", back_populates="search_run", cascade="all, delete-orphan"
    )
    publications: Mapped[List["CounterevidencePublication"]] = relationship(
        "CounterevidencePublication", back_populates="search_run", cascade="all, delete-orphan"
    )
    profiles: Mapped[List["CounterevidenceProfile"]] = relationship(
        "CounterevidenceProfile", back_populates="search_run", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_counter_runs_request", "research_request_id"),
        Index("idx_counter_runs_gap", "candidate_gap_id"),
        Index("idx_counter_runs_status", "status"),
    )


class CounterevidenceClaim(Base):
    """Represents an independently searchable empirical claim decomposed from a candidate gap."""

    __tablename__ = "counterevidence_claims"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    candidate_gap_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("candidate_research_gaps.id", ondelete="CASCADE"), nullable=False
    )
    claim_text: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[str] = mapped_column(
        String(80), default="unexplored_problem", nullable=False
    )  # unexplored_problem, missing_methodology, missing_dataset, missing_evaluation, untested_assumption, generalizability_constraint

    original_gap_statement: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generated_keywords: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    assumptions_investigated: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    queries: Mapped[List["CounterevidenceSearchQuery"]] = relationship(
        "CounterevidenceSearchQuery", back_populates="claim", cascade="all, delete-orphan"
    )
    assessments: Mapped[List["CounterevidenceAssessment"]] = relationship(
        "CounterevidenceAssessment", back_populates="claim"
    )

    __table_args__ = (
        Index("idx_counter_claims_gap", "candidate_gap_id"),
        Index("idx_counter_claims_type", "claim_type"),
    )


class CounterevidenceSearchQuery(Base):
    """Represents an academic query targeted at retrieving contradictory/challenging publications."""

    __tablename__ = "counterevidence_search_queries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    search_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("counterevidence_search_runs.id", ondelete="CASCADE"), nullable=False
    )
    candidate_gap_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("candidate_research_gaps.id", ondelete="CASCADE"), nullable=False
    )
    claim_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("counterevidence_claims.id", ondelete="SET NULL"), nullable=True
    )

    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    query_type: Mapped[str] = mapped_column(
        String(80), default="direct_counter", nullable=False
    )  # direct_counter, synonym_expansion, methodology_application, newer_publications, alternative_terminology, implementation_evidence
    
    search_rationale: Mapped[str] = mapped_column(Text, nullable=False)
    source_database: Mapped[str] = mapped_column(String(50), nullable=False)  # openalex, semantic_scholar, crossref, arxiv
    
    execution_status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )  # pending, success, rate_limited, failed, empty_results
    results_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=utc_now, nullable=True)

    # Relationships
    search_run: Mapped["CounterevidenceSearchRun"] = relationship(
        "CounterevidenceSearchRun", back_populates="queries"
    )
    claim: Mapped[Optional["CounterevidenceClaim"]] = relationship(
        "CounterevidenceClaim", back_populates="queries"
    )

    __table_args__ = (
        Index("idx_counter_queries_run", "search_run_id"),
        Index("idx_counter_queries_gap", "candidate_gap_id"),
        Index("idx_counter_queries_claim", "claim_id"),
        Index("idx_counter_queries_database", "source_database"),
    )


class CounterevidencePublication(Base):
    """Tracks a publication discovered specifically through counterevidence retrieval."""

    __tablename__ = "counterevidence_publications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    candidate_gap_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("candidate_research_gaps.id", ondelete="CASCADE"), nullable=False
    )
    search_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("counterevidence_search_runs.id", ondelete="CASCADE"), nullable=False
    )
    paper_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False
    )
    discovery_query_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("counterevidence_search_queries.id", ondelete="SET NULL"), nullable=True
    )

    discovery_source: Mapped[str] = mapped_column(String(50), nullable=False)
    is_newly_discovered: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    discovery_tag: Mapped[str] = mapped_column(String(60), default="counterevidence_discovered", nullable=False)
    
    screening_status: Mapped[str] = mapped_column(
        String(50), default="unscreened", nullable=False
    )  # unscreened, screened_included, screened_excluded, screened_needs_review
    
    retrieved_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    search_run: Mapped["CounterevidenceSearchRun"] = relationship(
        "CounterevidenceSearchRun", back_populates="publications"
    )
    paper: Mapped["Paper"] = relationship("Paper")

    __table_args__ = (
        Index("idx_counter_pubs_gap", "candidate_gap_id"),
        Index("idx_counter_pubs_run", "search_run_id"),
        Index("idx_counter_pubs_paper", "paper_id"),
        Index("idx_counter_pubs_tag", "discovery_tag"),
    )


class CounterevidenceAssessment(Base):
    """Structured assessment evaluating whether a publication disproves or qualifies a candidate gap."""

    __tablename__ = "counterevidence_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    candidate_gap_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("candidate_research_gaps.id", ondelete="CASCADE"), nullable=False
    )
    paper_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False
    )
    claim_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("counterevidence_claims.id", ondelete="SET NULL"), nullable=True
    )
    search_run_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("counterevidence_search_runs.id", ondelete="SET NULL"), nullable=True
    )

    relevance_classification: Mapped[str] = mapped_column(
        String(60), default="insufficient_information", nullable=False
    )  # direct_counterevidence, partial_counterevidence, related_evidence, not_relevant, insufficient_information

    impact_classification: Mapped[str] = mapped_column(
        String(60), default="inconclusive", nullable=False
    )  # strongly_challenged, partially_challenged, weakly_challenged, no_counterevidence_retrieved, inconclusive

    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    actual_contribution_identified: Mapped[str] = mapped_column(Text, nullable=False)
    research_problem_addressed: Mapped[str] = mapped_column(Text, nullable=False)
    relevant_methodology: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    evidence_level: Mapped[str] = mapped_column(
        String(60), default="level_3_metadata_only", nullable=False
    )  # level_1_fulltext_passage, level_2_abstract_supported, level_3_metadata_only, level_4_model_inference
    is_abstract_based: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    confidence_indicator: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    assessment_method: Mapped[str] = mapped_column(String(50), default="rule_deterministic", nullable=False)
    model_version: Mapped[Optional[str]] = mapped_column(String(50), default="v1.0-counterevidence", nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(50), default="v1.0-academic", nullable=True)

    verification_status: Mapped[str] = mapped_column(
        String(50), default="needs_verification", nullable=False
    )  # source_supported, abstract_supported, metadata_only, needs_verification, human_verified, rejected_by_reviewer, unavailable
    
    human_review_status: Mapped[str] = mapped_column(
        String(50), default="pending_review", nullable=False
    )  # pending_review, confirmed, corrected, flagged
    reviewer_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    original_automated_classification: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    claim: Mapped[Optional["CounterevidenceClaim"]] = relationship(
        "CounterevidenceClaim", back_populates="assessments"
    )
    paper: Mapped["Paper"] = relationship("Paper")
    evidence_items: Mapped[List["CounterevidenceEvidence"]] = relationship(
        "CounterevidenceEvidence", back_populates="assessment", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_counter_assess_gap", "candidate_gap_id"),
        Index("idx_counter_assess_paper", "paper_id"),
        Index("idx_counter_assess_relevance", "relevance_classification"),
        Index("idx_counter_assess_level", "evidence_level"),
    )


class CounterevidenceEvidence(Base):
    """Detailed passage-level ground truth supporting a counterevidence assessment."""

    __tablename__ = "counterevidence_evidence_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    assessment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("counterevidence_assessments.id", ondelete="CASCADE"), nullable=False
    )
    candidate_gap_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("candidate_research_gaps.id", ondelete="CASCADE"), nullable=False
    )
    paper_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False
    )
    evidence_passage_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("evidence_passages.id", ondelete="SET NULL"), nullable=True
    )

    verbatim_passage: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    section_heading: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    evidence_summary: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_type: Mapped[str] = mapped_column(
        String(80), default="finding", nullable=False
    )  # methodology, experimental_result, finding, limitation_refutation, alternative_solution
    source_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    is_verbatim_quote: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    verification_status: Mapped[str] = mapped_column(
        String(50), default="source_supported", nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    assessment: Mapped["CounterevidenceAssessment"] = relationship(
        "CounterevidenceAssessment", back_populates="evidence_items"
    )

    __table_args__ = (
        Index("idx_counter_ev_assess", "assessment_id"),
        Index("idx_counter_ev_gap", "candidate_gap_id"),
        Index("idx_counter_ev_paper", "paper_id"),
    )


class CounterevidenceProfile(Base):
    """Aggregated counterevidence profile summarizing the state and impact of challenging evidence on a gap."""

    __tablename__ = "counterevidence_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    candidate_gap_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("candidate_research_gaps.id", ondelete="CASCADE"), nullable=False
    )
    search_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("counterevidence_search_runs.id", ondelete="CASCADE"), nullable=False
    )

    total_retrieved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    previously_reviewed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    newly_discovered_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    direct_counterevidence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    partial_counterevidence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    related_evidence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    irrelevant_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    inconclusive_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    impact_assessment: Mapped[str] = mapped_column(
        String(60), default="inconclusive", nullable=False
    )  # strongly_challenged, partially_challenged, weakly_challenged, no_counterevidence_retrieved, inconclusive

    executive_summary: Mapped[str] = mapped_column(Text, nullable=False)
    remaining_unresolved_claims: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    search_limitations: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    fulltext_availability_limitations: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    verification_status: Mapped[str] = mapped_column(String(50), default="verified_traceable", nullable=False)

    generated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    search_run: Mapped["CounterevidenceSearchRun"] = relationship(
        "CounterevidenceSearchRun", back_populates="profiles"
    )
    candidate_gap: Mapped["CandidateResearchGap"] = relationship("CandidateResearchGap")

    __table_args__ = (
        Index("idx_counter_prof_gap", "candidate_gap_id"),
        Index("idx_counter_prof_run", "search_run_id"),
        Index("idx_counter_prof_impact", "impact_assessment"),
    )
