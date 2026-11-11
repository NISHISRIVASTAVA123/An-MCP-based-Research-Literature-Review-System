"""Search Strategy Database Models."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Text, JSON, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, generate_uuid, utc_now


class SearchStrategy(Base):
    """Generated literature search strategy for a research request."""

    __tablename__ = "search_strategies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    request_id: Mapped[str] = mapped_column(String(36), ForeignKey("research_requests.id", ondelete="CASCADE"), unique=True, nullable=False)

    # Decomposed strategy components
    concepts: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    keywords: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    synonyms: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    query_combinations: Mapped[list] = mapped_column(JSON, default=list, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    request: Mapped["ResearchRequest"] = relationship("ResearchRequest", back_populates="strategy")
    queries: Mapped[List["StrategyQuery"]] = relationship(
        "StrategyQuery", back_populates="strategy", cascade="all, delete-orphan", order_by="StrategyQuery.order_index"
    )


class StrategyQuery(Base):
    """Database-specific executable query instance."""

    __tablename__ = "strategy_queries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    strategy_id: Mapped[str] = mapped_column(String(36), ForeignKey("search_strategies.id", ondelete="CASCADE"), nullable=False)
    target_database: Mapped[str] = mapped_column(String(50), nullable=False)  # openalex, semantic_scholar, crossref, arxiv
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    strategy: Mapped["SearchStrategy"] = relationship("SearchStrategy", back_populates="queries")

