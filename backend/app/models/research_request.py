"""Research Request and Research Question Database Models."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, generate_uuid, utc_now


class ResearchRequest(Base):
    """Represents a user's scientific literature review request."""

    __tablename__ = "research_requests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str] = mapped_column(String(200), nullable=False)
    start_year: Mapped[int] = mapped_column(Integer, nullable=False)
    end_year: Mapped[int] = mapped_column(Integer, nullable=False)
    max_papers: Mapped[int] = mapped_column(Integer, default=25, nullable=False)
    citation_style: Mapped[str] = mapped_column(String(50), default="IEEE", nullable=False)

    # Optional fields stored as structured JSON
    inclusion_criteria: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    exclusion_criteria: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    preferred_databases: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    publication_types: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    specific_dois: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    questions: Mapped[List["ResearchQuestion"]] = relationship(
        "ResearchQuestion", back_populates="request", cascade="all, delete-orphan", order_by="ResearchQuestion.order_index"
    )
    strategy: Mapped[Optional["SearchStrategy"]] = relationship(
        "SearchStrategy", back_populates="request", uselist=False, cascade="all, delete-orphan"
    )
    executions: Mapped[List["SearchExecution"]] = relationship(
        "SearchExecution", back_populates="request", cascade="all, delete-orphan", order_by="desc(SearchExecution.executed_at)"
    )
    papers: Mapped[List["Paper"]] = relationship(
        "Paper", back_populates="request", cascade="all, delete-orphan"
    )


class ResearchQuestion(Base):
    """Individual research question attached to a research request."""

    __tablename__ = "research_questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    request_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_requests.id", ondelete="CASCADE"), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    request: Mapped["ResearchRequest"] = relationship("ResearchRequest", back_populates="questions")

