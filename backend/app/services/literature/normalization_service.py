"""Metadata Normalization Service.

Converts heterogeneous raw academic records from OpenAlex, Semantic Scholar,
Crossref, and arXiv into a unified canonical research paper model.
"""

import hashlib
import re
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from backend.app.services.providers.base_provider import RawPaperRecord


def normalize_title(title: str) -> str:
    """Produces standardized title string for reliable duplicate matching."""
    if not title:
        return ""
    # Lowercase, remove all non-alphanumeric chars except space, collapse spaces
    cleaned = re.sub(r"[^\w\s]", "", title.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def normalize_doi(doi: Optional[str]) -> Optional[str]:
    """Cleans and standardizes DOI string."""
    if not doi:
        return None
    cleaned = doi.strip().lower()
    for prefix in (
        "https://doi.org/",
        "http://doi.org/",
        "https://dx.doi.org/",
        "http://dx.doi.org/",
        "doi:",
    ):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
    return cleaned.strip() or None


class NormalizedSource(BaseModel):
    source_database: str
    external_source_id: Optional[str] = None
    source_url: Optional[str] = None
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)


class NormalizedPaper(BaseModel):
    """Unified academic paper schema."""

    id: str  # Deterministic identifier
    title: str
    normalized_title: str
    authors: List[str] = Field(default_factory=list)
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

    # Availability indicators
    has_abstract: bool = False
    has_pdf: bool = False
    has_doi: bool = False
    is_open_access: bool = False

    sources: List[NormalizedSource] = Field(default_factory=list)


def generate_paper_id(doi: Optional[str], normalized_title: str, year: Optional[int]) -> str:
    """Generates a stable, reproducible hash identifier for an academic paper."""
    if doi:
        return "doi_" + hashlib.sha256(doi.encode("utf-8")).hexdigest()[:24]
    base = f"{normalized_title}_{year or 'unknown'}"
    return "paper_" + hashlib.sha256(base.encode("utf-8")).hexdigest()[:24]


class NormalizationService:
    """Transforms raw records into canonical NormalizedPaper instances."""

    @staticmethod
    def normalize_record(raw: RawPaperRecord) -> NormalizedPaper:
        clean_doi = normalize_doi(raw.doi)
        clean_norm_title = normalize_title(raw.title)
        paper_id = generate_paper_id(clean_doi, clean_norm_title, raw.publication_year)

        # Validate abstract: empty or meaningless string counts as None
        abstract = raw.abstract.strip() if raw.abstract and len(raw.abstract.strip()) > 15 else None
        has_abstract = abstract is not None

        # Clean author names
        authors = [re.sub(r"\s+", " ", a).strip() for a in raw.authors if a and len(a.strip()) > 1]

        # PDF and Open Access determination
        has_pdf = bool(raw.pdf_url)
        is_open_access = has_pdf or (raw.source_database == "arxiv")

        source = NormalizedSource(
            source_database=raw.source_database,
            external_source_id=raw.external_id,
            source_url=raw.url,
            raw_metadata=raw.raw_metadata,
        )

        return NormalizedPaper(
            id=paper_id,
            title=raw.title.strip(),
            normalized_title=clean_norm_title,
            authors=authors,
            abstract=abstract,
            publication_year=raw.publication_year,
            publication_date=raw.publication_date,
            doi=clean_doi,
            url=raw.url,
            pdf_url=raw.pdf_url,
            venue=raw.venue.strip() if raw.venue else None,
            publication_type=raw.publication_type,
            keywords=raw.keywords,
            citation_count=raw.citation_count or 0,
            has_abstract=has_abstract,
            has_pdf=has_pdf,
            has_doi=clean_doi is not None,
            is_open_access=is_open_access,
            sources=[source],
        )

    def normalize_records(self, raw_records: List[RawPaperRecord]) -> List[NormalizedPaper]:
        """Normalizes a batch of raw records."""
        return [self.normalize_record(r) for r in raw_records]

