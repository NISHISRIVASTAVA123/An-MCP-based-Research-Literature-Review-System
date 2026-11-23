"""Pydantic Schemas for Structured Scientific Evidence and Passage Tracking."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# --- Evidence Sub-models ---

class EvidencePassageResponse(BaseModel):
    """Verifiable source passage linking an extracted statement to verbatim paper text."""

    id: str
    paper_id: str
    category: str  # objective, methodology, dataset, metric, finding, limitation, future_work
    statement: str
    verbatim_passage: Optional[str] = None
    page_number: Optional[int] = None
    section_heading: Optional[str] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    verification_status: str  # machine_extracted, user_verified, flagged_incorrect, unsupported_needs_review
    user_notes: Optional[str] = None
    created_at: datetime


class ResearchObjectiveItem(BaseModel):
    """Extracted research objective and problem formulation."""

    problem_statement: str
    motivation: Optional[str] = None
    significance: Optional[str] = None
    supporting_passage: Optional[str] = None
    page_number: Optional[int] = None
    section_heading: Optional[str] = None


class MethodologyItem(BaseModel):
    """Extracted scientific methodology, architecture, and baseline comparator."""

    approach_name: str
    approach_type: str  # algorithm, model_architecture, framework, theoretical, empirical
    description: Optional[str] = None
    baselines_compared: List[str] = Field(default_factory=list)
    experimental_setup: Optional[str] = None
    supporting_passage: Optional[str] = None
    page_number: Optional[int] = None
    section_heading: Optional[str] = None


class DatasetItem(BaseModel):
    """Extracted dataset details with explicit statistics."""

    dataset_name: str
    source_or_origin: Optional[str] = None
    reported_sample_size: Optional[str] = None
    train_test_split: Optional[str] = None
    modality: Optional[str] = None  # text, tabular, image, graph, multimodal
    supporting_passage: Optional[str] = None
    page_number: Optional[int] = None
    section_heading: Optional[str] = None


class EvaluationMetricItem(BaseModel):
    """Extracted experimental metric and reported quantitative value."""

    metric_name: str  # Accuracy, F1, Recall, Precision, AUC, Latency, etc.
    reported_value: str
    comparator_baseline_value: Optional[str] = None
    experimental_context: Optional[str] = None
    supporting_passage: Optional[str] = None
    page_number: Optional[int] = None
    section_heading: Optional[str] = None


class FindingItem(BaseModel):
    """Extracted scientific finding and reported result."""

    finding_statement: str
    percentage_gain_or_delta: Optional[str] = None
    is_statistically_tested: Optional[bool] = None
    supporting_passage: Optional[str] = None
    page_number: Optional[int] = None
    section_heading: Optional[str] = None


class LimitationItem(BaseModel):
    """Extracted limitation (strictly distinguishing author-reported vs system-inferred)."""

    limitation_text: str
    limitation_type: str = "author_reported"  # author_reported vs system_inferred
    aspect: Optional[str] = None  # dataset_size, generalization, computational_cost, interpretability, adversarial
    supporting_passage: Optional[str] = None
    page_number: Optional[int] = None
    section_heading: Optional[str] = None


class FutureWorkItem(BaseModel):
    """Extracted future research direction proposed by authors."""

    direction_text: str
    potential_impact: Optional[str] = None
    supporting_passage: Optional[str] = None
    page_number: Optional[int] = None
    section_heading: Optional[str] = None


# --- Structured Extraction Schema (Validated against LLM/Extractor outputs) ---

class StructuredEvidenceExtraction(BaseModel):
    """Complete structured scientific evidence extracted from a paper."""

    paper_id: str
    source_scope: str = "full_text"  # full_text or abstract_only
    extraction_status: str = "completed"

    research_objective: ResearchObjectiveItem
    methodologies: List[MethodologyItem] = Field(default_factory=list)
    datasets: List[DatasetItem] = Field(default_factory=list)
    evaluation_metrics: List[EvaluationMetricItem] = Field(default_factory=list)
    findings: List[FindingItem] = Field(default_factory=list)
    limitations: List[LimitationItem] = Field(default_factory=list)
    future_work: List[FutureWorkItem] = Field(default_factory=list)
    contributions: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)


# --- API Responses ---

class EvidenceRecordResponse(BaseModel):
    """Structured evidence response for a paper."""

    id: str
    paper_id: str
    extraction_run_id: str
    source_scope: str  # full_text or abstract_only
    extractor_backend: str

    research_objective: Dict[str, Any]
    methodology: Dict[str, Any]
    datasets: List[Dict[str, Any]]
    evaluation_metrics: List[Dict[str, Any]]
    findings: List[Dict[str, Any]]
    limitations: List[Dict[str, Any]]
    future_work: List[Dict[str, Any]]
    contributions: List[str]
    uncertainties: List[str]

    is_human_edited: bool = False
    human_notes: Optional[str] = None
    passages: List[EvidencePassageResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class PassageUpdatePayload(BaseModel):
    """Payload to record human verification, flagging, or correction on an evidence passage."""

    verification_status: str = Field(..., pattern="^(machine_extracted|user_verified|flagged_incorrect|unsupported_needs_review)$")
    statement: Optional[str] = None
    verbatim_passage: Optional[str] = None
    user_notes: Optional[str] = None

