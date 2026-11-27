"""Pydantic Schemas for Counterevidence Retrieval & Assessment (Phase 5)."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CounterevidenceClaimBase(BaseModel):
    claim_text: str
    claim_type: str = "unexplored_problem"
    original_gap_statement: Optional[str] = None
    generated_keywords: List[str] = Field(default_factory=list)
    assumptions_investigated: List[str] = Field(default_factory=list)
    order_index: int = 0


class CounterevidenceClaimResponse(CounterevidenceClaimBase):
    id: str
    candidate_gap_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class CounterevidenceQueryBase(BaseModel):
    query_text: str
    query_type: str = "direct_counter"
    search_rationale: str
    source_database: str
    execution_status: str = "pending"
    results_count: int = 0
    error_message: Optional[str] = None


class CounterevidenceQueryResponse(CounterevidenceQueryBase):
    id: str
    search_run_id: str
    candidate_gap_id: str
    claim_id: Optional[str] = None
    executed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CounterevidencePublicationResponse(BaseModel):
    id: str
    candidate_gap_id: str
    search_run_id: str
    paper_id: str
    discovery_query_id: Optional[str] = None
    discovery_source: str
    is_newly_discovered: bool
    discovery_tag: str = "counterevidence_discovered"
    screening_status: str = "unscreened"
    retrieved_at: datetime

    # Embedded paper details for frontend display
    title: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    publication_year: Optional[int] = None
    doi: Optional[str] = None
    venue: Optional[str] = None
    has_abstract: bool = False
    has_pdf: bool = False
    source_database: Optional[str] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None

    class Config:
        from_attributes = True


class CounterevidenceEvidenceItemResponse(BaseModel):
    id: str
    assessment_id: str
    candidate_gap_id: str
    paper_id: str
    evidence_passage_id: Optional[str] = None
    verbatim_passage: str
    page_number: Optional[int] = None
    section_heading: Optional[str] = None
    evidence_summary: str
    evidence_type: str
    source_reference: str
    is_verbatim_quote: bool = True
    verification_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class CounterevidenceAssessmentBase(BaseModel):
    relevance_classification: str
    impact_classification: str
    explanation: str
    actual_contribution_identified: str
    research_problem_addressed: str
    relevant_methodology: Optional[str] = None
    evidence_level: str = "level_3_metadata_only"
    is_abstract_based: bool = True
    confidence_indicator: float = 0.7
    assessment_method: str = "rule_deterministic"
    verification_status: str = "needs_verification"


class CounterevidenceAssessmentResponse(CounterevidenceAssessmentBase):
    id: str
    candidate_gap_id: str
    paper_id: str
    claim_id: Optional[str] = None
    search_run_id: Optional[str] = None
    model_version: Optional[str] = None
    prompt_version: Optional[str] = None
    human_review_status: str
    reviewer_reference: Optional[str] = None
    reviewer_notes: Optional[str] = None
    original_automated_classification: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Embedded evidence items & paper metadata
    paper_title: Optional[str] = None
    paper_authors: List[str] = Field(default_factory=list)
    paper_year: Optional[int] = None
    paper_doi: Optional[str] = None
    evidence_items: List[CounterevidenceEvidenceItemResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class CounterevidenceAssessmentReviewRequest(BaseModel):
    reviewer_reference: str = "lead_researcher"
    relevance_classification: Optional[str] = None
    override_relevance: Optional[str] = None
    impact_classification: Optional[str] = None
    reviewer_notes: Optional[str] = ""


class CounterevidenceProfileResponse(BaseModel):
    id: str
    candidate_gap_id: str
    search_run_id: str
    total_retrieved: int
    previously_reviewed_count: int
    newly_discovered_count: int
    direct_counterevidence_count: int
    partial_counterevidence_count: int
    related_evidence_count: int
    irrelevant_count: int
    inconclusive_count: int
    impact_assessment: str
    executive_summary: str
    remaining_unresolved_claims: List[str] = Field(default_factory=list)
    search_limitations: List[str] = Field(default_factory=list)
    fulltext_availability_limitations: List[str] = Field(default_factory=list)
    verification_status: str
    generated_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CounterevidenceSearchRunResponse(BaseModel):
    id: str
    research_request_id: str
    candidate_gap_id: Optional[str] = None
    run_number: int
    status: str
    initiated_by: str
    configuration_snapshot: Dict[str, Any] = Field(default_factory=dict)
    total_claims_decomposed: int
    total_queries_executed: int
    total_publications_found: int
    newly_discovered_count: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SearchRunCreateRequest(BaseModel):
    candidate_gap_id: Optional[str] = None
    databases: Optional[List[str]] = None
    max_results_per_query: int = 10
    auto_extract_evidence: bool = True
    initiated_by: str = "researcher"
