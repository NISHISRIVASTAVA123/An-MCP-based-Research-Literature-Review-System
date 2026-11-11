"""Academic Search Strategy Generator Service."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from backend.app.services.planner.keyword_expander import expand_keywords
from backend.app.services.planner.query_builder import generate_database_queries


class AbstractStrategyPlanner(ABC):
    """Abstract interface to allow deterministic or LLM-based planners in future phases."""

    @abstractmethod
    def generate(
        self,
        topic: str,
        objective: str,
        domain: str,
        research_questions: List[str],
        preferred_databases: List[str],
    ) -> Dict[str, Any]:
        pass


class DeterministicStrategyPlanner(AbstractStrategyPlanner):
    """Deterministic, reproducible academic strategy planner for Phase 1."""

    def generate(
        self,
        topic: str,
        objective: str,
        domain: str,
        research_questions: List[str],
        preferred_databases: List[str],
    ) -> Dict[str, Any]:
        # Expand keywords and extract concepts
        expansion = expand_keywords(topic, objective, domain, research_questions)

        # Generate database-specific queries
        db_queries = generate_database_queries(
            topic=topic,
            keywords=expansion["keywords"],
            query_combinations=expansion["query_combinations"],
            preferred_databases=preferred_databases,
        )

        return {
            "concepts": expansion["concepts"],
            "keywords": expansion["keywords"],
            "synonyms": expansion["synonyms"],
            "query_combinations": expansion["query_combinations"],
            "queries": db_queries,
        }


# Default strategy generator instance
strategy_planner = DeterministicStrategyPlanner()

