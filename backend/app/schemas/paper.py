"""Pydantic schemas for Academic Research Papers and Sources."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class PaperSourceResponse(BaseModel):
    id: str
    paper_id: str
    source_database: str
    external_source_id: Optional[str] = None
    source_url: Optional[str] = None
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)
    retrieved_at: datetime

    model_config = {"from_attributes": True}


class PaperResponse(BaseModel):
    id: str
    request_id: str
    title: str
    normalized_title: str
    authors: List[Any] = Field(default_factory=list)
    abstract: Optional[str] = None
    publication_year: Optional[int] = None
    publication_date: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    venue: Optional[str] = None
    publication_type: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    citation_count: Optional[int] = 0
    has_abstract: bool
    has_pdf: bool
    has_doi: bool
    is_open_access: bool
    created_at: datetime
    sources: List[PaperSourceResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class PaperListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[PaperResponse]

