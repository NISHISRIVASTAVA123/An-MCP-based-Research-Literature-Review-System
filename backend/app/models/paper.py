"""Normalized Paper and Provenance Database Models."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Text, JSON, DateTime, ForeignKey, Boolean, Float, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, generate_uuid, utc_now


class Paper(Base):
    """Canonical normalized academic research paper."""

    __tablename__ = "papers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # Hash or UUID
    request_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_requests.id", ondelete="CASCADE"), nullable=False)

    title: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_title: Mapped[str] = mapped_column(String(500), index=True, nullable=False)
    authors: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    abstract: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    publication_year: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    publication_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    doi: Mapped[Optional[str]] = mapped_column(String(200), index=True, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pdf_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    venue: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    publication_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    keywords: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    citation_count: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True)

    # Boolean metadata availability indicators
    has_abstract: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_pdf: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_doi: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_open_access: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    request: Mapped["ResearchRequest"] = relationship("ResearchRequest", back_populates="papers")
    sources: Mapped[List["PaperSource"]] = relationship(
        "PaperSource", back_populates="paper", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_papers_request_year", "request_id", "publication_year"),
    )


class PaperSource(Base):
    """Provenance tracking for a paper retrieved from a specific provider."""

    __tablename__ = "paper_sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    paper_id: Mapped[str] = mapped_column(String(64), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)
    source_database: Mapped[str] = mapped_column(String(50), nullable=False)  # openalex, semantic_scholar, crossref, arxiv
    external_source_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    paper: Mapped["Paper"] = relationship("Paper", back_populates="sources")

