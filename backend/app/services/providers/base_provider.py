"""Base Academic Provider Interfaces and Models.

Defines the contract for all academic database adapters and standardizes
raw provider outputs and error classifications.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RawPaperRecord(BaseModel):
    """Raw standardized container for unnormalized provider data."""

    source_database: str = Field(..., description="Provider name: openalex, semantic_scholar, crossref, arxiv")
    external_id: Optional[str] = Field(None, description="Provider-specific identifier")
    title: str = Field(..., description="Paper title as returned by the API")
    authors: List[str] = Field(default_factory=list, description="Author names")
    abstract: Optional[str] = Field(None, description="Paper abstract text, if available")
    publication_year: Optional[int] = Field(None, description="Year of publication")
    publication_date: Optional[str] = Field(None, description="ISO publication date if available")
    doi: Optional[str] = Field(None, description="Digital Object Identifier")
    url: Optional[str] = Field(None, description="Canonical publication URL")
    pdf_url: Optional[str] = Field(None, description="Direct link to open access PDF if available")
    venue: Optional[str] = Field(None, description="Journal, conference, or repository venue")
    publication_type: Optional[str] = Field(None, description="Article, conference paper, preprint, etc.")
    citation_count: Optional[int] = Field(None, description="Total citations if provided")
    keywords: List[str] = Field(default_factory=list, description="Keywords or classifications")
    raw_metadata: Dict[str, Any] = Field(default_factory=dict, description="Complete unaltered provider response object")


class AcademicProviderException(Exception):
    """Base exception for provider failures."""
    def __init__(self, provider: str, message: str, status_code: Optional[int] = None):
        super().__init__(f"[{provider.upper()}] {message}")
        self.provider = provider
        self.status_code = status_code


class ProviderUnavailableError(AcademicProviderException):
    """Provider API returned 5xx or is temporarily unreachable."""
    pass


class ProviderRateLimitError(AcademicProviderException):
    """Provider rate limits exceeded (HTTP 429)."""
    pass


class ProviderTimeoutError(AcademicProviderException):
    """Request exceeded configured timeout."""
    pass


class BaseAcademicProvider(ABC):
    """Abstract Base Class for all academic retrieval adapters."""

    def __init__(self, provider_name: str, timeout_seconds: float = 15.0):
        self.provider_name = provider_name
        self.timeout_seconds = timeout_seconds

    @abstractmethod
    async def search(
        self,
        query: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        limit: int = 25,
    ) -> List[RawPaperRecord]:
        """Executes academic literature search against provider API."""
        pass

    @abstractmethod
    async def retrieve_by_doi(self, doi: str) -> Optional[RawPaperRecord]:
        """Retrieves single work metadata via DOI."""
        pass

