"""Pydantic Schemas for Full-text Documents and PDF Processing."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DocumentSection(BaseModel):
    """Layout-aware extracted section within a scientific paper page."""

    page_number: int
    heading: Optional[str] = None
    text: str
    char_count: int = 0


class DocumentStatusResponse(BaseModel):
    """Full-text processing and layout status of a paper."""

    paper_id: str
    has_document: bool
    document_id: Optional[str] = None
    source_type: Optional[str] = None  # open_access_url, arxiv_direct, user_upload
    file_size_bytes: int = 0
    page_count: int = 0
    extraction_status: str  # success, partial, scanned_ocr_required, corrupt_unreadable, no_access, pending
    section_headings: List[str] = Field(default_factory=list)
    total_characters_extracted: int = 0
    error_details: Optional[str] = None
    retrieved_at: Optional[datetime] = None


class DocumentRetrieveResponse(BaseModel):
    """Response after attempting automated permitted full-text retrieval."""

    paper_id: str
    success: bool
    document_id: Optional[str] = None
    source_type: str
    source_url: Optional[str] = None
    extraction_status: str
    page_count: int = 0
    message: str

