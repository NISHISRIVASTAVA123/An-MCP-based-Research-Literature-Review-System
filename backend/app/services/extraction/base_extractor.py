"""Base Abstract Extractor Interface."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from backend.app.schemas.evidence import StructuredEvidenceExtraction


class BaseEvidenceExtractor(ABC):
    """Abstract interface for structured scientific evidence extractors."""

    @abstractmethod
    async def extract_evidence(
        self,
        paper_id: str,
        title: str,
        abstract: Optional[str],
        fulltext_sections: List[Dict[str, Any]],
        source_scope: str,  # "full_text" or "abstract_only"
    ) -> StructuredEvidenceExtraction:
        """Extracts structured scientific evidence from paper content."""
        pass

