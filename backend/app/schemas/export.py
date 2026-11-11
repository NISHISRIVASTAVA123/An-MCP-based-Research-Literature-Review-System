"""Pydantic schemas for Export Operations."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ExportRecord(BaseModel):
    paper_id: str
    title: str
    authors: str
    publication_year: Optional[int] = None
    publication_date: Optional[str] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    citation_count: Optional[int] = 0
    has_abstract: bool
    abstract: Optional[str] = None
    source_databases: str
    external_ids: str
    retrieval_timestamp: str
    search_topic: str


class ExportResponse(BaseModel):
    format: str
    total_records: int
    data: Any

