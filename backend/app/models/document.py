"""Full-text Scientific Document Database Models.

Tracks downloaded, discovered, and user-uploaded scientific documents,
their extraction quality, page count, and layout-aware text sections.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, JSON, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.base import Base, generate_uuid, utc_now


class FulltextDocument(Base):
    """Full-text document linked to an academic paper."""

    __tablename__ = "fulltext_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    paper_id: Mapped[str] = mapped_column(String(64), ForeignKey("papers.id", ondelete="CASCADE"), nullable=False)

    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # open_access_url, arxiv_direct, user_upload
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    file_hash_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    mime_type: Mapped[str] = mapped_column(String(100), default="application/pdf", nullable=False)

    # Document extraction quality
    extraction_status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )  # success, partial, scanned_ocr_required, corrupt_unreadable, no_access, pending
    page_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Structured layout content: list of {page_number: int, sections: [...], text: str}
    extracted_sections: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    error_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    # Relationships
    paper: Mapped["Paper"] = relationship("Paper", back_populates="documents")

    __table_args__ = (
        Index("idx_fulltext_docs_paper", "paper_id"),
        Index("idx_fulltext_docs_status", "extraction_status"),
    )
