"""Pydantic schemas for Research Requests and Questions."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class ResearchQuestionBase(BaseModel):
    """Base schema for research questions."""
    question_text: str = Field(..., min_length=5, max_length=1000, description="The research question to be investigated")
    order_index: int = Field(0, description="Display order index")


class ResearchQuestionCreate(ResearchQuestionBase):
    pass


class ResearchQuestionResponse(ResearchQuestionBase):
    id: str
    request_id: str

    model_config = {"from_attributes": True}


class ResearchRequestBase(BaseModel):
    """Base schema for research requests with rigorous academic validations."""

    topic: str = Field(..., min_length=3, max_length=500, description="Academic research topic")
    objective: str = Field(..., min_length=10, max_length=5000, description="Primary research objective and scope")
    domain: str = Field(..., min_length=2, max_length=200, description="Scientific or computing domain")
    start_year: int = Field(2015, ge=1900, le=2030, description="Starting publication year")
    end_year: int = Field(2026, ge=1900, le=2030, description="Ending publication year")
    max_papers: int = Field(25, ge=1, le=200, description="Maximum papers to retrieve per search")
    citation_style: str = Field("IEEE", description="Citation formatting style (IEEE, APA, Harvard, etc.)")

    # Optional scope configuration
    inclusion_criteria: List[str] = Field(default_factory=list, description="Explicit inclusion criteria")
    exclusion_criteria: List[str] = Field(default_factory=list, description="Explicit exclusion criteria")
    preferred_databases: List[str] = Field(
        default_factory=lambda: ["openalex", "semantic_scholar", "crossref", "arxiv"],
        description="Target academic databases"
    )
    publication_types: List[str] = Field(
        default_factory=lambda: ["journal", "conference", "review", "preprint"],
        description="Accepted publication types"
    )
    specific_dois: List[str] = Field(default_factory=list, description="Specific DOIs or paper identifiers to include")

    @field_validator("topic")
    @classmethod
    def validate_topic_non_empty(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Research topic cannot be empty or purely whitespace.")
        return clean

    @field_validator("objective")
    @classmethod
    def validate_objective_non_empty(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Research objective cannot be empty or purely whitespace.")
        return clean

    @model_validator(mode="after")
    def validate_years_and_scope(self) -> "ResearchRequestBase":
        if self.start_year > self.end_year:
            raise ValueError(
                f"Publication start year ({self.start_year}) cannot be later than end year ({self.end_year})."
            )
        return self


class ResearchRequestCreate(ResearchRequestBase):
    """Payload to create a new research review request."""
    research_questions: List[str] = Field(
        default_factory=list,
        description="List of specific research questions exploring the topic"
    )


class ResearchRequestUpdate(BaseModel):
    """Payload to update an existing research request."""
    topic: Optional[str] = None
    objective: Optional[str] = None
    domain: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    max_papers: Optional[int] = None
    citation_style: Optional[str] = None
    inclusion_criteria: Optional[List[str]] = None
    exclusion_criteria: Optional[List[str]] = None
    preferred_databases: Optional[List[str]] = None
    publication_types: Optional[List[str]] = None
    specific_dois: Optional[List[str]] = None
    research_questions: Optional[List[str]] = None


class ResearchRequestResponse(ResearchRequestBase):
    """Complete research request response including questions and timestamps."""
    id: str
    created_at: datetime
    updated_at: datetime
    questions: List[ResearchQuestionResponse] = Field(default_factory=list)
    has_strategy: bool = False
    has_retrieved_papers: bool = False
    total_papers_count: int = 0

    model_config = {"from_attributes": True}


class ResearchRequestSummary(BaseModel):
    """Lightweight summary of research request for listing history."""
    id: str
    topic: str
    objective: str
    domain: str
    start_year: int
    end_year: int
    max_papers: int
    created_at: datetime
    updated_at: datetime
    total_papers: int = 0
    total_questions: int = 0
    has_strategy: bool = False

    model_config = {"from_attributes": True}

