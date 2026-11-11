"""Semantic Scholar Academic Literature Retrieval Provider.

Official Documentation: https://api.semanticscholar.org/api-docs/
Provides academic graph access covering over 200M publications.
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


class SemanticScholarProvider(BaseAcademicProvider):
    """Adapter for Semantic Scholar Academic Graph API."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

    def __init__(self, timeout_seconds: float = settings.PROVIDER_TIMEOUT_SECONDS):
        super().__init__("semantic_scholar", timeout_seconds)
        self.api_key = settings.SEMANTIC_SCHOLAR_API_KEY

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "User-Agent": f"AcademicLitReviewBot/1.0 ({settings.POLITE_EMAIL})",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    async def search(
        self,
        query: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        limit: int = 25,
    ) -> List[RawPaperRecord]:
        """Searches Semantic Scholar graph API with requested fields and year filters."""
        params: Dict[str, Any] = {
            "query": query,
            "limit": min(limit, 50),
            "fields": (
                "title,authors,year,publicationDate,venue,abstract,citationCount,"
                "url,externalIds,openAccessPdf,publicationTypes"
            ),
        }

        if start_year and end_year:
            params["year"] = f"{start_year}-{end_year}"
        elif start_year:
            params["year"] = f"{start_year}-"
        elif end_year:
            params["year"] = f"-{end_year}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(self.BASE_URL, params=params, headers=self._get_headers())

            if response.status_code == 429:
                logger.warning("Semantic Scholar rate limit hit (HTTP 429).")
                raise ProviderRateLimitError(self.provider_name, "Rate limit exceeded (HTTP 429)", 429)
            elif response.status_code >= 500:
                raise ProviderUnavailableError(self.provider_name, f"Service error (HTTP {response.status_code})", response.status_code)
            elif response.status_code != 200:
                logger.warning(f"Semantic Scholar returned unexpected status {response.status_code}: {response.text[:200]}")
                return []

            data = response.json()
            results = data.get("data", [])

            records: List[RawPaperRecord] = []
            for item in results:
                record = self._parse_item(item)
                if record:
                    records.append(record)

            return records

        except httpx.TimeoutException as exc:
            logger.warning(f"Semantic Scholar request timed out: {exc}")
            raise ProviderTimeoutError(self.provider_name, "Request timed out") from exc
        except (ProviderRateLimitError, ProviderUnavailableError):
            raise
        except Exception as exc:
            logger.error(f"Unexpected error querying Semantic Scholar: {exc}")
            raise ProviderUnavailableError(self.provider_name, str(exc)) from exc

    async def retrieve_by_doi(self, doi: str) -> Optional[RawPaperRecord]:
        """Retrieves paper from Semantic Scholar by DOI."""
        clean_doi = doi.strip().replace("https://doi.org/", "").replace("http://doi.org/", "")
        url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{clean_doi}"
        params = {
            "fields": (
                "title,authors,year,publicationDate,venue,abstract,citationCount,"
                "url,externalIds,openAccessPdf,publicationTypes"
            )
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(url, params=params, headers=self._get_headers())

            if response.status_code == 200:
                return self._parse_item(response.json())
            return None
        except Exception as exc:
            logger.warning(f"Failed to retrieve Semantic Scholar DOI {clean_doi}: {exc}")
            return None

    def _parse_item(self, item: Dict[str, Any]) -> Optional[RawPaperRecord]:
        """Parses Semantic Scholar JSON object into RawPaperRecord."""
        title = item.get("title")
        if not title:
            return None

        # Authors
        authors = [a.get("name") for a in item.get("authors", []) if a.get("name")]

        # External IDs (DOI, ArXiv, PubMed)
        external_ids = item.get("externalIds") or {}
        doi = external_ids.get("DOI")

        # Open access PDF
        pdf_url = None
        oa_obj = item.get("openAccessPdf")
        if oa_obj and isinstance(oa_obj, dict):
            pdf_url = oa_obj.get("url")

        # Publication types
        pub_types = item.get("publicationTypes") or []
        pub_type_str = ", ".join(pub_types) if pub_types else None

        return RawPaperRecord(
            source_database=self.provider_name,
            external_id=item.get("paperId"),
            title=title.strip(),
            authors=authors,
            abstract=item.get("abstract"),
            publication_year=item.get("year"),
            publication_date=item.get("publicationDate"),
            doi=doi,
            url=item.get("url") or (f"https://doi.org/{doi}" if doi else None),
            pdf_url=pdf_url,
            venue=item.get("venue"),
            publication_type=pub_type_str,
            citation_count=item.get("citationCount", 0),
            keywords=[],
            raw_metadata=item,
        )

