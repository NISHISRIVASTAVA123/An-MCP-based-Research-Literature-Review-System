"""Full-Text Document Downloader.

Safely and legally attempts retrieval of permitted Open Access scientific papers
via academic provider URLs, arXiv direct PDF resolvers, and official open repositories.
Never bypasses paywalls or authentication boundaries.
"""

import os
import re
import hashlib
from typing import Optional, Tuple
import httpx
from backend.app.models.paper import Paper
from backend.app.core.config import settings
from backend.app.core.logging import logger

STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "storage", "pdfs")


class DocumentDownloader:
    """Legal open-access document retriever."""

    def __init__(self):
        os.makedirs(STORAGE_DIR, exist_ok=True)

    async def retrieve_paper_pdf(self, paper: Paper) -> Tuple[bool, Optional[str], Optional[bytes], str, Optional[str]]:
        """Attempts to obtain open-access PDF bytes from legitimate sources in priority order.

        Returns:
            Tuple of (success, source_type, file_bytes, message, source_url)
        """
        headers = {
            "User-Agent": f"AcademicLiteratureReview/1.0 (mailto:{settings.POLITE_EMAIL})",
            "Accept": "application/pdf,application/octet-stream;q=0.9,*/*;q=0.8",
        }

        # Priority 1: Direct Open Access PDF URL recorded in metadata
        if paper.pdf_url and paper.pdf_url.lower().endswith(".pdf"):
            logger.info(f"Attempting Priority 1 Open Access PDF retrieval for {paper.id}: {paper.pdf_url}")
            success, content = await self._fetch_pdf(paper.pdf_url, headers)
            if success:
                return True, "open_access_url", content, "Successfully retrieved from provider open-access URL", paper.pdf_url

        # Priority 2: arXiv Direct PDF Resolver
        arxiv_id = None
        for src in paper.sources:
            if src.source_database == "arxiv" and src.external_source_id:
                arxiv_id = src.external_source_id
                break

        if not arxiv_id and paper.url and "arxiv.org" in paper.url:
            match = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9]+\.[0-9]+(?:v[0-9]+)?)", paper.url)
            if match:
                arxiv_id = match.group(1)

        if arxiv_id:
            arxiv_pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            logger.info(f"Attempting Priority 2 arXiv PDF retrieval for {paper.id}: {arxiv_pdf_url}")
            success, content = await self._fetch_pdf(arxiv_pdf_url, headers)
            if success:
                return True, "arxiv_direct", content, "Successfully retrieved from arXiv open repository", arxiv_pdf_url

        # Priority 3: Fallback check on paper.pdf_url even without .pdf extension
        if paper.pdf_url and not paper.pdf_url.lower().endswith(".pdf"):
            logger.info(f"Attempting Priority 3 generic PDF URL for {paper.id}: {paper.pdf_url}")
            success, content = await self._fetch_pdf(paper.pdf_url, headers)
            if success:
                return True, "open_access_url", content, "Successfully retrieved from publisher open-access link", paper.pdf_url

        return False, "no_access", None, "No permitted open-access PDF found. Please upload a PDF manually if you have legitimate access.", None

    async def _fetch_pdf(self, url: str, headers: dict) -> Tuple[bool, Optional[bytes]]:
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    content = resp.content
                    # Validate PDF magic header
                    if content.startswith(b"%PDF-"):
                        return True, content
                    else:
                        logger.warning(f"URL {url} returned HTTP 200 but content is not a PDF (got {len(content)} bytes).")
                elif resp.status_code in (401, 403):
                    logger.info(f"URL {url} is restricted/paywalled (HTTP {resp.status_code}). Respecting access boundaries.")
                else:
                    logger.debug(f"URL {url} returned HTTP {resp.status_code}")
        except Exception as e:
            logger.warning(f"Failed to fetch PDF from {url}: {e}")
        return False, None

    def save_pdf(self, paper_id: str, file_bytes: bytes) -> Tuple[str, int, str]:
        """Saves PDF bytes to local disk storage and computes SHA-256 hash."""
        filename = f"{paper_id}.pdf"
        file_path = os.path.join(STORAGE_DIR, filename)
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        file_size = len(file_bytes)
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        return file_path, file_size, file_hash

