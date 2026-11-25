"""Tests for Synthesis Data Layer and Evidence Retrieval Service (Phase 4).

Verifies persistence of SynthesisRun, LiteratureTheme, LiteraturePattern, CandidateResearchGap,
GapEvidenceLink, HumanReviewRecord, and strict screening exclusion filtering.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models.base import Base
from backend.app.models.research_request import ResearchRequest, ResearchQuestion
from backend.app.models.paper import Paper
from backend.app.models.screening import ScreeningRun, ScreeningDecision
from backend.app.models.evidence import EvidenceRecord, EvidencePassage
from backend.app.models.graph import GraphNode, GraphEdge
from backend.app.models.synthesis import (
    SynthesisRun,
    LiteratureTheme,
    LiteraturePattern,
    CandidateResearchGap,
    GapEvidenceLink,
    HumanReviewRecord,
)
from backend.app.services.persistence.synthesis_repository import SynthesisRepository
from backend.app.services.synthesis.evidence_retrieval_service import EvidenceRetrievalService


@pytest.fixture
def db_session():
    """In-memory SQLite test database session fixture."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


def test_synthesis_run_and_sub_entities_persistence(db_session):
    """Verifies relational persistence and cascade of SynthesisRun, Themes, Patterns, Gaps, and Links."""
    # 1. Setup Request and Paper
    req = ResearchRequest(
        id="req-test-synthesis-1",
        topic="Graph Neural Networks in Drug Discovery",
        objective="Assess binding affinity prediction accuracy",
        domain="Bioinformatics",
        start_year=2020,
        end_year=2024,
    )
    p1 = Paper(
        id="paper-synth-1",
        request_id=req.id,
        title="GNNs for Molecular Property Prediction",
        normalized_title="gnns for molecular property prediction",
        authors=["Alice Smith", "Bob Jones"],
        publication_year=2023,
    )
    p2 = Paper(
        id="paper-synth-2",
        request_id=req.id,
        title="Scalable Graph Transformers",
        normalized_title="scalable graph transformers",
        authors=["Charlie Brown"],
        publication_year=2024,
    )
    db_session.add_all([req, p1, p2])
    db_session.commit()

    repo = SynthesisRepository(db_session)

    # 2. Create SynthesisRun
    run = repo.create_synthesis_run(
        request_id=req.id,
        selected_paper_ids=[p1.id, p2.id],
        synthesis_configuration={"cluster_threshold": 0.7},
        prompt_version="v1.0-academic",
        model_provider="rule_deterministic",
        model_name="deterministic-engine",
        evidence_graph_version="graph-snapshot-01",
    )
    assert run.id is not None
    assert run.run_number == 1
    assert run.status == "pending"
    assert len(run.selected_paper_ids) == 2

    # 3. Create Themes
    themes = repo.create_literature_themes(
        run.id,
        [
            {
                "name": "Graph Transformer Methodologies",
                "description": "Studies evaluating graph transformers for molecular graphs",
                "theme_category": "methodological",
                "related_concepts": ["Graph Transformer", "Self-Attention"],
                "associated_paper_ids": [p1.id, p2.id],
                "frequency": 2,
                "confidence": 0.88,
            }
        ],
    )
    assert len(themes) == 1
    assert themes[0].name == "Graph Transformer Methodologies"

    # 4. Create Patterns
    patterns = repo.create_literature_patterns(
        run.id,
        [
            {
                "pattern_type": "methodology",
                "description": "Prevalence of GNN architectures",
                "observed_data": {"Transformer": 2},
                "related_paper_ids": [p1.id, p2.id],
                "interpretation": "GNNs are standard in both retrieved studies",
                "confidence": 0.85,
            }
        ],
    )
    assert len(patterns) == 1
    assert patterns[0].pattern_type == "methodology"

    # 5. Create Candidate Gap
    gap = repo.create_candidate_gap({
        "synthesis_run_id": run.id,
        "research_request_id": req.id,
        "title": "Low Data Regimes in Molecular Graph Benchmarks",
        "description": "Models exhibit high variance when training on sparse bioactivity datasets",
        "category": "empirical_gap",
        "research_domain": "Bioinformatics",
        "related_research_questions": ["How do few-shot adapters perform on sparse bioassays?"],
        "rationale": "High variance noted across papers under low data support.",
        "observed_pattern": "Performance drops 35% on assays with < 100 samples.",
        "scope": "Retrieved 2 papers",
        "preliminary_confidence": 0.82,
        "confidence_explanation": "Explicitly reported in paper-synth-1 and paper-synth-2.",
        "assumptions": ["Assay size reflects operational clinical constraints."],
        "known_limitations": ["Small test corpus."],
        "potential_counterexamples": [],
        "unresolved_questions": [],
        "suggested_validation_queries": ["few-shot molecular bioactivity GNN benchmark"],
        "supporting_paper_ids": [p1.id, p2.id],
        "supporting_claim_ids": [],
        "supporting_finding_ids": [],
        "supporting_limitation_ids": [],
        "supporting_evidence_ids": [],
        "generation_status": "evidence_grounded",
        "human_review_status": "pending_review",
    })
    assert gap.id is not None
    assert gap.category == "empirical_gap"

    # 6. Create Evidence Link
    links = repo.create_gap_evidence_links([
        {
            "candidate_gap_id": gap.id,
            "paper_id": p1.id,
            "relationship_type": "reports_limitation",
            "contribution_explanation": "Authors cite severe drop on sparse data.",
            "relevance_score": 0.92,
        }
    ])
    assert len(links) == 1
    assert links[0].candidate_gap_id == gap.id

    # 7. Add Human Review Record
    review = repo.add_human_review_record(
        gap_id=gap.id,
        reviewer_reference="Senior PI",
        review_action="accept",
        original_value={"status": "pending_review"},
        revised_value={"status": "accepted_for_further_investigation"},
        reviewer_comment="High priority gap for Phase 5 counterevidence validation.",
    )
    assert review.id is not None
    assert review.review_action == "accept"

    # Verify gap status updated
    updated_gap = repo.get_candidate_gap(gap.id)
    assert updated_gap.human_review_status == "accepted_for_further_investigation"


def test_evidence_retrieval_service_screening_exclusion(db_session):
    """Verifies that EvidenceRetrievalService strictly omits screened-out / excluded papers."""
    req = ResearchRequest(
        id="req-screening-gate",
        topic="Protein Folding Prediction",
        objective="Analyze modern deep learning approaches",
        domain="Bioinformatics",
        start_year=2015,
        end_year=2024,
    )
    p_included = Paper(
        id="p-included-1",
        request_id=req.id,
        title="AlphaFold2 Validation Study",
        normalized_title="alphafold2 validation study",
        publication_year=2021,
    )
    p_excluded = Paper(
        id="p-excluded-1",
        request_id=req.id,
        title="Unrelated Social Network Analysis",
        normalized_title="unrelated social network analysis",
        publication_year=2015,
    )
    db_session.add_all([req, p_included, p_excluded])
    db_session.commit()

    # Screening run with 1 included, 1 excluded
    s_run = ScreeningRun(
        id="screen-run-1",
        request_id=req.id,
        total_papers=2,
        included_count=1,
        excluded_count=1,
    )
    dec_inc = ScreeningDecision(
        id="dec-1",
        run_id=s_run.id,
        paper_id=p_included.id,
        decision="included",
        reason="Relevant topic",
        confidence_score=0.95,
    )
    dec_exc = ScreeningDecision(
        id="dec-2",
        run_id=s_run.id,
        paper_id=p_excluded.id,
        decision="excluded",
        reason="Out of domain",
        confidence_score=0.99,
    )
    db_session.add_all([s_run, dec_inc, dec_exc])
    db_session.commit()

    retrieval = EvidenceRetrievalService(db_session)
    eligible = retrieval.get_eligible_papers_for_request(req.id)

    assert len(eligible) == 1
    assert eligible[0].id == p_included.id
    assert p_excluded.id not in [p.id for p in eligible]

    status_map = retrieval.get_paper_screening_status_map(req.id)
    assert status_map[p_included.id] == "included"
    assert status_map[p_excluded.id] == "excluded"
