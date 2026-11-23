"""Models package initialization."""

from backend.app.models.base import Base
from backend.app.models.research_request import ResearchRequest, ResearchQuestion
from backend.app.models.search_strategy import SearchStrategy, StrategyQuery
from backend.app.models.paper import Paper, PaperSource
from backend.app.models.search_execution import SearchExecution
from backend.app.models.screening import ScreeningRun, ScreeningDecision
from backend.app.models.document import FulltextDocument
from backend.app.models.evidence import ExtractionRun, EvidenceRecord, EvidencePassage

__all__ = [
    "Base",
    "ResearchRequest",
    "ResearchQuestion",
    "SearchStrategy",
    "StrategyQuery",
    "Paper",
    "PaperSource",
    "SearchExecution",
    "ScreeningRun",
    "ScreeningDecision",
    "FulltextDocument",
    "ExtractionRun",
    "EvidenceRecord",
    "EvidencePassage",
]
