"""Pydantic Schemas for Literature Synthesis & Candidate Research-Gap Generation (Phase 4).

Type definitions for synthesis runs, comparison matrix, research themes,
empirical patterns, candidate research gaps, evidence links, and human reviews.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class SynthesisRunCreate(BaseModel):
    """Payload to initiate a new literature synthesis run."""

    selected_paper_ids: Optional[List[str]] = Field(
        None, description="Specific paper IDs to include; if None, all eligible screened papers are used."
    )
    synthesis_configuration: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Configuration parameters for clustering, trend analysis, and gap generation."
    )
    prompt_version: Optional[str] = Field("v1.0-academic", description="Version tag of synthesis prompts.")
    model_provider: Optional[str] = Field("rule_deterministic", description="Model backend: rule_deterministic, groq, openai, ollama.")
    model_name: Optional[str] = Field("deterministic-engine", description="Model identifier.")


class LiteratureThemeResponse(BaseModel):
    """A recurring scientific research theme grouped across literature."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    synthesis_run_id: str
    name: str
    description: str
    theme_category: str
    related_concepts: List[str] = Field(default_factory=list)
    associated_paper_ids: List[str] = Field(default_factory=list)
    supporting_claim_ids: List[str] = Field(default_factory=list)
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    frequency: int
    confidence: float
    confidence_explanation: Optional[str] = None
    known_limitations: Optional[str] = None
    created_at: datetime


class LiteraturePatternResponse(BaseModel):
    """An observed pattern across methodologies, datasets, models, metrics, or years."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    synthesis_run_id: str
    pattern_type: str
    description: str
    observed_data: Dict[str, Any] = Field(default_factory=dict)
    related_paper_ids: List[str] = Field(default_factory=list)
    related_evidence_ids: List[str] = Field(default_factory=list)
    interpretation: str
    confidence: float
    limitations: Optional[str] = None
    created_at: datetime


class GapEvidenceLinkResponse(BaseModel):
    """Explicit mapping from a candidate gap to its supporting evidence passage."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    candidate_gap_id: str
    evidence_id: Optional[str] = None
    claim_id: Optional[str] = None
    paper_id: str
    paper_title: Optional[str] = None
    relationship_type: str
    contribution_explanation: str
    relevance_score: float
    exact_passage: Optional[str] = None
    section_heading: Optional[str] = None
    page_number: Optional[int] = None
    created_at: datetime


class HumanReviewRecordResponse(BaseModel):
    """Audit log of human review decisions on candidate research gaps."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    candidate_gap_id: str
    reviewer_reference: str
    review_action: str
    original_value: Dict[str, Any] = Field(default_factory=dict)
    revised_value: Dict[str, Any] = Field(default_factory=dict)
    reviewer_comment: Optional[str] = None
    created_at: datetime


class CandidateResearchGapResponse(BaseModel):
    """Structured candidate research gap with evidence provenance and review state."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    synthesis_run_id: str
    research_request_id: str
    title: str
    description: str
    category: str
    research_domain: str
    related_research_questions: List[str] = Field(default_factory=list)
    rationale: str
    observed_pattern: str
    scope: str
    preliminary_confidence: float
    confidence_explanation: str
    assumptions: List[str] = Field(default_factory=list)
    known_limitations: List[str] = Field(default_factory=list)
    potential_counterexamples: List[str] = Field(default_factory=list)
    unresolved_questions: List[str] = Field(default_factory=list)
    suggested_validation_queries: List[str] = Field(default_factory=list)
    supporting_paper_ids: List[str] = Field(default_factory=list)
    supporting_claim_ids: List[str] = Field(default_factory=list)
    supporting_finding_ids: List[str] = Field(default_factory=list)
    supporting_limitation_ids: List[str] = Field(default_factory=list)
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    generation_status: str
    human_review_status: str
    created_at: datetime
    updated_at: datetime

    evidence_links: Optional[List[GapEvidenceLinkResponse]] = None
    review_records: Optional[List[HumanReviewRecordResponse]] = None


class SynthesisRunResponse(BaseModel):
    """Detailed summary of a completed or active synthesis run."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    research_request_id: str
    run_number: int
    status: str
    selected_paper_ids: List[str] = Field(default_factory=list)
    evidence_graph_version: Optional[str] = None
    synthesis_configuration: Dict[str, Any] = Field(default_factory=dict)
    prompt_version: Optional[str] = None
    model_provider: Optional[str] = None
    model_name: Optional[str] = None
    summary_narrative: Dict[str, Any] = Field(default_factory=dict)
    execution_started_at: Optional[datetime] = None
    execution_completed_at: Optional[datetime] = None
    error_details: Optional[str] = None
    theme_count: int = 0
    pattern_count: int = 0
    gap_count: int = 0
    created_at: datetime
    updated_at: datetime


class PaperComparisonRow(BaseModel):
    """Extracted comparative dimensions for a single academic paper."""

    paper_id: str
    title: str
    authors: List[str] = Field(default_factory=list)
    year: Optional[int] = None
    venue: Optional[str] = None
    research_objectives: List[str] = Field(default_factory=list)
    research_questions: List[str] = Field(default_factory=list)
    methodologies: List[str] = Field(default_factory=list)
    models: List[str] = Field(default_factory=list)
    datasets: List[str] = Field(default_factory=list)
    metrics: List[str] = Field(default_factory=list)
    experimental_setup: Optional[str] = "Not reported"
    main_findings: List[str] = Field(default_factory=list)
    reported_limitations: List[str] = Field(default_factory=list)
    future_directions: List[str] = Field(default_factory=list)
    evidence_count: int = 0


class PaperComparisonMatrixResponse(BaseModel):
    """Dynamic multi-paper comparative matrix."""

    request_id: str
    total_papers: int
    columns: List[str]
    rows: List[PaperComparisonRow]


class HumanReviewRequest(BaseModel):
    """Payload to review or revise a candidate research gap."""

    reviewer_reference: str = Field("researcher", description="Identity or handle of the reviewer.")
    review_action: str = Field(
        ..., description="Action: accept, reject, request_evidence, edit."
    )
    revised_title: Optional[str] = Field(None, description="Updated title if action is edit.")
    revised_description: Optional[str] = Field(None, description="Updated description if action is edit.")
    revised_category: Optional[str] = Field(None, description="Updated category if action is edit.")
    reviewer_comment: Optional[str] = Field(None, description="Reviewer feedback or rationale.")


class SynthesisOverviewStats(BaseModel):
    """High-level KPI statistics for the Literature Synthesis dashboard."""

    request_id: str
    total_eligible_papers: int
    latest_run_id: Optional[str] = None
    latest_run_status: Optional[str] = None
    total_themes: int = 0
    total_patterns: int = 0
    total_candidate_gaps: int = 0
    gaps_by_category: Dict[str, int] = Field(default_factory=dict)
    gaps_by_review_status: Dict[str, int] = Field(default_factory=dict)
    evidence_grounding_rate: float = 1.0
