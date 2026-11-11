"""Crossref Academic Literature Retrieval Provider.

Official Documentation: https://api.crossref.org/
Crossref provides authoritative DOI registration metadata for over 150M records.
"""

import re
from typing import List, Optional, Dict, Any
import httpx
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.services.providers.base_provider import (
    BaseAcademicProvider,
    RawPaperRecord,
    ProviderUnavailableError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)


def strip_jats_xml(text: Optional[str]) -> Optional[str]:
    """Strips JATS XML markup tags commonly found in Crossref abstracts."""
    if not text:
        return None
    cleaned = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", cleaned).strip()


class CrossrefProvider(BaseAcademicProvider):
    """Adapter for Crossref REST API."""

    BASE_URL = "https://api.crossref.org/works"

    def __init__(self, timeout_seconds: float = settings.PROVIDER_TIMEOUT_SECONDS):
        super().__init__("crossref", timeout_seconds)
        self.mailto = settings.POLITE_EMAIL

    def _get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": f"AcademicLitReviewBot/1.0 (mailto:{self.mailto})",
            "Accept": "application/json",
        }

    async def search(
        self,
        query: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        limit: int = 25,
    ) -> List[RawPaperRecord]:
        """Searches Crossref works with publication date filters and polite mailto."""
        params: Dict[str, Any] = {
            "query": query,
            "rows": min(limit, 50),
            "mailto": self.mailto,
        }

        # Date filters
        filters = []
        if start_year and end_year:
            filters.append(f"from-pub-date:{start_year}-01-01,until-pub-date:{end_year}-12-31")
        elif start_year:
            filters.append(f"from-pub-date:{start_year}-01-01")
        elif end_year:
            filters.append(f"until-pub-date:{end_year}-12-31")

        if filters:
            params["filter"] = ",".join(filters)

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(self.BASE_URL, params=params, headers=self._get_headers())

            if response.status_code == 429:
                raise ProviderRateLimitError(self.provider_name, "Rate limit exceeded (HTTP 429)", 429)
            elif response.status_code >= 500:
                raise ProviderUnavailableError(self.provider_name, f"Service error (HTTP {response.status_code})", response.status_code)
            elif response.status_code != 200:
                logger.warning(f"Crossref returned status {response.status_code}: {response.text[:200]}")
                return []

            data = response.json()
            message = data.get("message", {})
            items = message.get("items", [])

            records: List[RawPaperRecord] = []
            for item in items:
                record = self._parse_item(item)
                if record:
                    records.append(record)

            return records

        except httpx.TimeoutException as exc:
            logger.warning(f"Crossref request timed out: {exc}")
            raise ProviderTimeoutError(self.provider_name, "Request timed out") from exc
        except (ProviderRateLimitError, ProviderUnavailableError):
            raise
        except Exception as exc:
            logger.error(f"Unexpected error querying Crossref: {exc}")
            raise ProviderUnavailableError(self.provider_name, str(exc)) from exc

    async def retrieve_by_doi(self, doi: str) -> Optional[RawPaperRecord]:
        """Retrieves exact metadata for a DOI from Crossref."""
        clean_doi = doi.strip().replace("https://doi.org/", "").replace("http://doi.org/", "")
        url = f"https://api.crossref.org/works/{clean_doi}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(url, params={"mailto": self.mailto}, headers=self._get_headers())

            if response.status_code == 200:
                item = response.json().get("message", {})
                return self._parse_item(item)
            return None
        except Exception as exc:
            logger.warning(f"Failed to retrieve Crossref DOI {clean_doi}: {exc}")
            return None

    def _parse_item(self, item: Dict[str, Any]) -> Optional[RawPaperRecord]:
        """Parses a Crossref item into a RawPaperRecord."""
        titles = item.get("title", [])
        title = titles[0] if titles else None
        if not title:
            return None

        # Authors
        authors = []
        for a in item.get("author", []):
            given = a.get("given", "").strip()
            family = a.get("family", "").strip()
            full_name = f"{given} {family}".strip() or a.get("name")
            if full_name:
                authors.append(full_name)

        # DOI
        doi = item.get("DOI")

        # Year and Date
        year = None
        date_str = None
        date_parts = None
        for date_key in ("published-print", "published-online", "issued", "created"):
            val = item.get(date_key, {})
            parts = val.get("date-parts", [])
            if parts and parts[0]:
                date_parts = parts[0]
                break

        if date_parts:
            year = date_parts[0]
            if len(date_parts) >= 2:
                date_str = f"{date_parts[0]:04d}-{date_parts[1]:02d}"
                if len(date_parts) >= 3:
                    date_str += f"-{date_parts[2]:02d}"
            else:
                date_str = f"{date_parts[0]:04d}"

        # Venue
        venues = item.get("container-title", [])
        venue = venues[0] if venues else None

        # Abstract (strip JATS XML tags)
        abstract = strip_jats_xml(item.get("abstract"))

        # Links & PDF
        url = item.get("URL") or (f"https://doi.org/{doi}" if doi else None)
        pdf_url = None
        for link in item.get("link", []):
            content_type = link.get("content-type", "")
            if "pdf" in content_type:
                pdf_url = link.get("URL")
                break

        return RawPaperRecord(
            source_database=self.provider_name,
            external_id=doi,
            title=title.strip(),
            authors=authors,
            abstract=abstract,
            publication_year=year,
            publication_date=date_str,
            doi=doi,
            url=url,
            pdf_url=pdf_url,
            venue=venue,
            publication_type=item.get("type"),
            citation_count=item.get("is-referenced-by-count", 0),
            keywords=[],
            raw_metadata=item,
        )

