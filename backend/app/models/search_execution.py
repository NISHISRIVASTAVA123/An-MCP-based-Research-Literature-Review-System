"""Search Execution History Database Model."""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, JSON, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, generate_uuid, utc_now


class SearchExecution(Base):
    """Historical record of an executed literature retrieval run."""

    __tablename__ = "search_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    request_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_requests.id", ondelete="CASCADE"), nullable=False)

    executed_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    status: Mapped[str] = mapped_column(String(50), default="completed", nullable=False)  # completed, partial_failure, failed
    total_raw_retrieved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_unique_papers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_duplicates_removed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    provider_statuses: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    queries_executed: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    # Relationships
    request: Mapped["ResearchRequest"] = relationship("ResearchRequest", back_populates="executions")

