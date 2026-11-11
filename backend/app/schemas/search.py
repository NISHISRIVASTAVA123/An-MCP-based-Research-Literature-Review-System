"""Pydantic schemas for Search Strategies and Search Executions."""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class StrategyQueryBase(BaseModel):
    target_database: str = Field(..., description="Target academic database identifier (openalex, semantic_scholar, crossref, arxiv)")
    query_text: str = Field(..., min_length=2, description="Database-specific formatted search query string")
    is_enabled: bool = Field(True, description="Whether this query is active for retrieval")
    order_index: int = Field(0, description="Execution order")


class StrategyQueryUpdate(BaseModel):
    id: Optional[str] = None
    target_database: str
    query_text: str
    is_enabled: bool = True
    order_index: int = 0


class StrategyQueryResponse(StrategyQueryBase):
    id: str
    strategy_id: str

    model_config = {"from_attributes": True}


class SearchStrategyResponse(BaseModel):
    id: str
    request_id: str
    concepts: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    synonyms: Dict[str, List[str]] = Field(default_factory=dict)
    query_combinations: List[str] = Field(default_factory=list)
    queries: List[StrategyQueryResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SearchStrategyUpdate(BaseModel):
    concepts: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    synonyms: Optional[Dict[str, List[str]]] = None
    query_combinations: Optional[List[str]] = None
    queries: Optional[List[StrategyQueryUpdate]] = None


class SearchExecutionSummary(BaseModel):
    id: str
    request_id: str
    executed_at: datetime
    status: str
    total_raw_retrieved: int
    total_unique_papers: int
    total_duplicates_removed: int
    provider_statuses: Dict[str, Any]
    queries_executed: List[str]

    model_config = {"from_attributes": True}


class SearchExecutionRequest(BaseModel):
    """Optional execution overrides."""
    override_queries: Optional[List[StrategyQueryUpdate]] = None
    override_databases: Optional[List[str]] = None
    max_papers_per_provider: Optional[int] = None

