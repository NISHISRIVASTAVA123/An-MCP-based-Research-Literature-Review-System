"""Structured Scientific Evidence Database Models.

Stores extraction runs, structured scientific findings, datasets,
evaluation metrics, author-reported limitations, and verifiable source passages.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Text, JSON, DateTime, ForeignKey, Boolean, Float, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, generate_uuid, utc_now


class ExtractionRun(Base):
    """Execution run for structured evidence extraction on a paper."""

    __tablename__ = "extraction_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    paper_id: Mapped[str] = mapped_column(String(64), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    document_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("fulltext_documents.id", ondelete="SET NULL"), nullable=True)

    source_scope: Mapped[str] = mapped_column(String(30), nullable=False)  # full_text, abstract_only
    extractor_backend: Mapped[str] = mapped_column(String(50), nullable=False)  # groq, openai, ollama, rule_based, mock
    status: Mapped[str] = mapped_column(String(30), default="completed", nullable=False)  # completed, failed, requires_review
    execution_time_seconds: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    paper: Mapped["Paper"] = relationship("Paper", back_populates="extraction_runs")
    document: Mapped[Optional["FulltextDocument"]] = relationship("FulltextDocument")
    evidence_records: Mapped[List["EvidenceRecord"]] = relationship(
        "EvidenceRecord", back_populates="extraction_run", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_extraction_runs_paper", "paper_id"),
    )


class EvidenceRecord(Base):
    """Canonical structured scientific evidence record extracted from a paper."""

    __tablename__ = "evidence_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    extraction_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("extraction_runs.id", ondelete="CASCADE"), nullable=False)
    paper_id: Mapped[str] = mapped_column(String(64), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)

    # Core Scientific Dimensions (Stored as validated JSON structures)
    research_objective: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    methodology: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    datasets: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    evaluation_metrics: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    findings: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    limitations: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    future_work: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    contributions: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    uncertainties: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    is_human_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    human_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    extraction_run: Mapped["ExtractionRun"] = relationship("ExtractionRun", back_populates="evidence_records")
    paper: Mapped["Paper"] = relationship("Paper", back_populates="evidence_records")
    passages: Mapped[List["EvidencePassage"]] = relationship(
        "EvidencePassage", back_populates="evidence_record", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_evidence_records_paper", "paper_id"),
    )


class EvidencePassage(Base):
    """Verifiable source passage linking an extracted statement to exact paper text."""

    __tablename__ = "evidence_passages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    evidence_record_id: Mapped[str] = mapped_column(String(36), ForeignKey("evidence_records.id", ondelete="CASCADE"), nullable=False)
    paper_id: Mapped[str] = mapped_column(String(64), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)

    category: Mapped[str] = mapped_column(String(50), nullable=False)  # objective, methodology, dataset, metric, finding, limitation, future_work
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    verbatim_passage: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    section_heading: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    char_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    char_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    verification_status: Mapped[str] = mapped_column(
        String(30), default="machine_extracted", nullable=False
    )  # machine_extracted, user_verified, flagged_incorrect, unsupported_needs_review
    user_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    evidence_record: Mapped["EvidenceRecord"] = relationship("EvidenceRecord", back_populates="passages")
    paper: Mapped["Paper"] = relationship("Paper")

    __table_args__ = (
        Index("idx_evidence_passages_paper_cat", "paper_id", "category"),
        Index("idx_evidence_passages_status", "verification_status"),
    )
