"""OpenAlex Academic Literature Retrieval Provider.

Official Documentation: https://docs.openalex.org/
OpenAlex indexes over 250M scientific works and provides open REST access.
"""

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


def reconstruct_openalex_abstract(inverted_index: Optional[Dict[str, List[int]]]) -> Optional[str]:
    """Reconstructs continuous text from OpenAlex's abstract_inverted_index format."""
    if not inverted_index:
        return None

    # Map word index to token
    index_word_pairs = []
    for word, positions in inverted_index.items():
        for pos in positions:
            index_word_pairs.append((pos, word))

    index_word_pairs.sort(key=lambda x: x[0])
    return " ".join([word for _, word in index_word_pairs])


class OpenAlexProvider(BaseAcademicProvider):
    """Adapter for OpenAlex Works API."""

    BASE_URL = "https://api.openalex.org/works"

    def __init__(self, timeout_seconds: float = settings.PROVIDER_TIMEOUT_SECONDS):
        super().__init__("openalex", timeout_seconds)
        self.mailto = settings.POLITE_EMAIL

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "User-Agent": f"AcademicLitReviewBot/1.0 (mailto:{self.mailto})",
            "Accept": "application/json",
        }
        return headers

    async def search(
        self,
        query: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        limit: int = 25,
    ) -> List[RawPaperRecord]:
        """Searches OpenAlex works with year filters and polite pool headers."""
        params: Dict[str, Any] = {
            "search": query,
            "per-page": min(limit, 50),
            "mailto": self.mailto,
        }

        # Build year filters
        filters = []
        if start_year and end_year:
            filters.append(f"publication_year:{start_year}-{end_year}")
        elif start_year:
            filters.append(f"publication_year:>{start_year - 1}")
        elif end_year:
            filters.append(f"publication_year:<{end_year + 1}")

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
                logger.warning(f"OpenAlex returned unexpected status {response.status_code}: {response.text[:200]}")
                return []

            data = response.json()
            results = data.get("results", [])

            records: List[RawPaperRecord] = []
            for item in results:
                record = self._parse_item(item)
                if record:
                    records.append(record)

            return records

        except httpx.TimeoutException as exc:
            logger.warning(f"OpenAlex request timed out after {self.timeout_seconds}s: {exc}")
            raise ProviderTimeoutError(self.provider_name, "Request timed out") from exc
        except (ProviderRateLimitError, ProviderUnavailableError):
            raise
        except Exception as exc:
            logger.error(f"Unexpected error querying OpenAlex: {exc}")
            raise ProviderUnavailableError(self.provider_name, str(exc)) from exc

    async def retrieve_by_doi(self, doi: str) -> Optional[RawPaperRecord]:
        """Retrieves specific work from OpenAlex via DOI."""
        clean_doi = doi.strip().replace("https://doi.org/", "").replace("http://doi.org/", "")
        url = f"https://api.openalex.org/works/https://doi.org/{clean_doi}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(url, params={"mailto": self.mailto}, headers=self._get_headers())

            if response.status_code == 200:
                return self._parse_item(response.json())
            return None
        except Exception as exc:
            logger.warning(f"Failed to retrieve OpenAlex DOI {clean_doi}: {exc}")
            return None

    def _parse_item(self, item: Dict[str, Any]) -> Optional[RawPaperRecord]:
        """Parses an OpenAlex work JSON object into RawPaperRecord."""
        title = item.get("display_name") or item.get("title")
        if not title:
            return None

        # Authors
        authors = []
        for authorship in item.get("authorships", []):
            author_obj = authorship.get("author", {})
            name = author_obj.get("display_name")
            if name:
                authors.append(name)

        # DOI
        raw_doi = item.get("doi")
        doi = None
        if raw_doi:
            doi = raw_doi.replace("https://doi.org/", "").strip()

        # Abstract
        abstract = reconstruct_openalex_abstract(item.get("abstract_inverted_index"))

        # Primary location / venue
        venue = None
        primary_loc = item.get("primary_location") or {}
        source = primary_loc.get("source") or {}
        if source:
            venue = source.get("display_name")

        # Open access / PDF
        pdf_url = None
        best_oa = item.get("best_oa_location") or {}
        if best_oa.get("pdf_url"):
            pdf_url = best_oa.get("pdf_url")
        elif primary_loc.get("pdf_url"):
            pdf_url = primary_loc.get("pdf_url")

        # Keywords / concepts
        keywords = []
        for c in item.get("concepts", []):
            c_name = c.get("display_name")
            if c_name:
                keywords.append(c_name)

        return RawPaperRecord(
            source_database=self.provider_name,
            external_id=item.get("id"),
            title=title.strip(),
            authors=authors,
            abstract=abstract,
            publication_year=item.get("publication_year"),
            publication_date=item.get("publication_date"),
            doi=doi,
            url=item.get("doi") or (primary_loc.get("landing_page_url") or item.get("id")),
            pdf_url=pdf_url,
            venue=venue,
            publication_type=item.get("type"),
            citation_count=item.get("cited_by_count", 0),
            keywords=keywords[:10],
            raw_metadata=item,
        )

