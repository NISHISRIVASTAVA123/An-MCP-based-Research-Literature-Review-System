"""arXiv Academic Literature Retrieval Provider.

Official Documentation: https://info.arxiv.org/help/api/index.html
Provides open access to scientific preprints across Computer Science, Physics,
Mathematics, Quantitative Biology, and Statistics.
"""

import re
import xml.etree.ElementTree as ET
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

ATOM_NS = "{http://www.w3.org/2005/Atom}"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"


class ArxivProvider(BaseAcademicProvider):
    """Adapter for arXiv Atom XML API."""

    BASE_URL = "https://export.arxiv.org/api/query"

    def __init__(self, timeout_seconds: float = settings.PROVIDER_TIMEOUT_SECONDS):
        super().__init__("arxiv", timeout_seconds)

    def _get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": f"AcademicLitReviewBot/1.0 ({settings.POLITE_EMAIL})",
        }

    async def search(
        self,
        query: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        limit: int = 25,
    ) -> List[RawPaperRecord]:
        """Searches arXiv preprint repository and parses Atom XML feed."""
        clean_query = query.strip()
        if not (clean_query.startswith("all:") or clean_query.startswith("ti:") or clean_query.startswith("abs:")):
            if " " in clean_query and not (clean_query.startswith('"') and clean_query.endswith('"')):
                clean_query = f'all:"{clean_query}"'
            else:
                clean_query = f"all:{clean_query}"

        params: Dict[str, Any] = {
            "search_query": clean_query,
            "start": 0,
            "max_results": min(limit * 2, 100),  # Fetch extra to accommodate client-side year filtering
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(self.BASE_URL, params=params, headers=self._get_headers())

            if response.status_code == 429:
                raise ProviderRateLimitError(self.provider_name, "Rate limit exceeded (HTTP 429)", 429)
            elif response.status_code >= 500:
                raise ProviderUnavailableError(self.provider_name, f"Service error (HTTP {response.status_code})", response.status_code)
            elif response.status_code != 200:
                logger.warning(f"arXiv returned status {response.status_code}: {response.text[:200]}")
                return []

            return self._parse_feed(response.text, start_year, end_year)

        except httpx.TimeoutException as exc:
            logger.warning(f"arXiv request timed out: {exc}")
            raise ProviderTimeoutError(self.provider_name, "Request timed out") from exc
        except (ProviderRateLimitError, ProviderUnavailableError):
            raise
        except Exception as exc:
            logger.error(f"Unexpected error querying arXiv: {exc}")
            raise ProviderUnavailableError(self.provider_name, str(exc)) from exc

    async def retrieve_by_doi(self, doi: str) -> Optional[RawPaperRecord]:
        """Searches arXiv for a specific DOI."""
        clean_doi = doi.strip().replace("https://doi.org/", "").replace("http://doi.org/", "")
        query = f'doi:"{clean_doi}"'
        params = {"search_query": query, "max_results": 1}

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(self.BASE_URL, params=params, headers=self._get_headers())

            if response.status_code == 200:
                results = self._parse_feed(response.text)
                return results[0] if results else None
            return None
        except Exception as exc:
            logger.warning(f"Failed to query arXiv for DOI {clean_doi}: {exc}")
            return None

    def _parse_feed(
        self, xml_text: str, start_year: Optional[int] = None, end_year: Optional[int] = None
    ) -> List[RawPaperRecord]:
        """Parses Atom XML response and extracts paper metadata."""
        records: List[RawPaperRecord] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.error(f"Failed to parse arXiv Atom XML: {e}")
            return []

        for entry in root.findall(f"{ATOM_NS}entry"):
            title_elem = entry.find(f"{ATOM_NS}title")
            if title_elem is None or not title_elem.text:
                continue
            title = re.sub(r"\s+", " ", title_elem.text).strip()

            # Authors
            authors = []
            for author_elem in entry.findall(f"{ATOM_NS}author"):
                name_elem = author_elem.find(f"{ATOM_NS}name")
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text.strip())

            # Abstract / summary
            summary_elem = entry.find(f"{ATOM_NS}summary")
            abstract = re.sub(r"\s+", " ", summary_elem.text).strip() if summary_elem is not None and summary_elem.text else None

            # Dates
            published_elem = entry.find(f"{ATOM_NS}published")
            pub_date = published_elem.text.strip() if published_elem is not None and published_elem.text else None
            year = int(pub_date[:4]) if pub_date and len(pub_date) >= 4 else None

            # Check year filter
            if start_year and year and year < start_year:
                continue
            if end_year and year and year > end_year:
                continue

            # Identifier & Links
            id_elem = entry.find(f"{ATOM_NS}id")
            raw_id = id_elem.text.strip() if id_elem is not None and id_elem.text else None

            # Clean arxiv id
            external_id = raw_id
            if raw_id and "arxiv.org/abs/" in raw_id:
                external_id = raw_id.split("arxiv.org/abs/")[-1]

            url = raw_id
            pdf_url = None
            for link_elem in entry.findall(f"{ATOM_NS}link"):
                link_type = link_elem.attrib.get("type", "")
                link_title = link_elem.attrib.get("title", "")
                if "pdf" in link_type or link_title == "pdf":
                    pdf_url = link_elem.attrib.get("href")

            # DOI
            doi_elem = entry.find(f"{ARXIV_NS}doi")
            doi = doi_elem.text.strip() if doi_elem is not None and doi_elem.text else None

            # Primary Category / Venue
            cat_elem = entry.find(f"{ARXIV_NS}primary_category")
            category = cat_elem.attrib.get("term") if cat_elem is not None else "arXiv"
            venue = f"arXiv ({category})"

            records.append(
                RawPaperRecord(
                    source_database=self.provider_name,
                    external_id=external_id,
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    publication_year=year,
                    publication_date=pub_date[:10] if pub_date else None,
                    doi=doi,
                    url=url,
                    pdf_url=pdf_url,
                    venue=venue,
                    publication_type="preprint",
                    citation_count=0,
                    keywords=[category],
                    raw_metadata={"raw_arxiv_id": raw_id, "category": category},
                )
            )

        return records

