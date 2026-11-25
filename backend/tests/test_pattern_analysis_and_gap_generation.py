"""Tests for Pattern Analysis, Candidate Gap Generation, and Human Review Workflow (Phase 4).

Verifies empirical patterns, zero-fabrication gap formulation, reference validation against SQLite,
end-to-end evidence traceability, and researcher review lifecycle.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models.base import Base
from backend.app.models.research_request import ResearchRequest
from backend.app.models.paper import Paper
from backend.app.models.evidence import ExtractionRun, EvidenceRecord, EvidencePassage
from backend.app.models.graph import GraphNode, GraphEdge
from backend.app.services.persistence.synthesis_repository import SynthesisRepository
from backend.app.services.synthesis.pattern_analysis_service import PatternAnalysisService
from backend.app.services.synthesis.gap_generator import CandidateResearchGapGenerator
from backend.app.services.synthesis.review_service import SynthesisReviewService
from backend.app.schemas.synthesis import HumanReviewRequest


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


def test_pattern_analysis_frequencies_and_denominators(db_session):
    """Verifies that PatternAnalysisService computes correct frequencies, distributions, and denominators."""
    req = ResearchRequest(
        id="req-pattern-test",
        topic="Efficient Transformers",
        objective="Assess computational efficiency",
        domain="Computer Science",
        start_year=2019,
        end_year=2024,
    )
    p1 = Paper(id="p-pat-1", request_id=req.id, title="Linformer", normalized_title="linformer", publication_year=2020)
    p2 = Paper(id="p-pat-2", request_id=req.id, title="Performer", normalized_title="performer", publication_year=2021)
    db_session.add_all([req, p1, p2])
    db_session.commit()

    # Graph nodes & edges
    m_node = GraphNode(id="m-lin", request_id=req.id, node_type="METHOD", label="Linear Attention", normalized_label="Linear Attention", entity_key="METHOD:linear_attention")
    d_node = GraphNode(id="d-glue", request_id=req.id, node_type="DATASET", label="GLUE Benchmark", normalized_label="GLUE Benchmark", entity_key="DATASET:glue")
    pn1 = GraphNode(id="pn-1", request_id=req.id, node_type="PAPER", label=p1.title, normalized_label=p1.title, entity_key=f"PAPER:{p1.id}", source_paper_id=p1.id)
    pn2 = GraphNode(id="pn-2", request_id=req.id, node_type="PAPER", label=p2.title, normalized_label=p2.title, entity_key=f"PAPER:{p2.id}", source_paper_id=p2.id)

    e1 = GraphEdge(id="e1", request_id=req.id, source_node_id=pn1.id, target_node_id=m_node.id, relationship_type="USES_METHOD", edge_key=f"{pn1.id}:USES_METHOD:{m_node.id}")
    e2 = GraphEdge(id="e2", request_id=req.id, source_node_id=pn2.id, target_node_id=m_node.id, relationship_type="USES_METHOD", edge_key=f"{pn2.id}:USES_METHOD:{m_node.id}")
    e3 = GraphEdge(id="e3", request_id=req.id, source_node_id=pn1.id, target_node_id=d_node.id, relationship_type="USES_DATASET", edge_key=f"{pn1.id}:USES_DATASET:{d_node.id}")

    db_session.add_all([m_node, d_node, pn1, pn2, e1, e2, e3])
    db_session.commit()

    service = PatternAnalysisService(db_session)
    patterns = service.analyze_patterns(req.id)

    assert len(patterns) >= 2
    # Verify methodology pattern
    meth_pat = next(p for p in patterns if p["pattern_type"] == "methodology")
    assert meth_pat["observed_data"]["total_papers"] == 2
    assert "Linear Attention" in meth_pat["observed_data"]["method_frequencies"]
    assert meth_pat["observed_data"]["method_frequencies"]["Linear Attention"]["count"] == 2
    assert meth_pat["observed_data"]["method_frequencies"]["Linear Attention"]["percentage"] == 100.0

    # Verify temporal pattern
    time_pat = next(p for p in patterns if p["pattern_type"] == "publication_trend")
    assert time_pat["observed_data"]["year_distribution"][2020] == 1
    assert time_pat["observed_data"]["year_distribution"][2021] == 1


def test_candidate_research_gap_generation_and_provenance(db_session):
    """Verifies candidate gap generation, database reference validation, and end-to-end evidence provenance."""
    req = ResearchRequest(
        id="req-gap-test",
        topic="Neural Graph Reasoning",
        objective="Analyze reasoning capabilities",
        domain="Computer Science",
        start_year=2020,
        end_year=2024,
    )
    p1 = Paper(id="p-gap-1", request_id=req.id, title="Reasoning with Graph NNs", normalized_title="reasoning with graph nns", publication_year=2022)
    ex_rec = ExtractionRun(id="ex-gap-1", paper_id=p1.id, source_scope="abstract_only", extractor_backend="rule_based")
    ev_rec = EvidenceRecord(id="ev-gap-rec-1", extraction_run_id=ex_rec.id, paper_id=p1.id)
    pass1 = EvidencePassage(
        id="pass-gap-1",
        paper_id=p1.id,
        evidence_record_id=ev_rec.id,
        category="limitation",
        statement="Our model struggles to generalize to multi-hop queries beyond 3 hops.",
        verbatim_passage="Our model struggles to generalize to multi-hop queries beyond 3 hops.",
        page_number=6,
        section_heading="Experimental Limitations",
    )
    db_session.add_all([req, p1, ex_rec, ev_rec, pass1])
    db_session.commit()

    # Create Graph Node for Limitation grounded in pass1
    lim_node = GraphNode(
        id="node-lim-gap",
        request_id=req.id,
        node_type="LIMITATION",
        label="Generalization degrades on multi-hop reasoning beyond 3 hops",
        normalized_label="Generalization degrades on multi-hop reasoning beyond 3 hops",
        entity_key="LIMITATION:multihop_degrade",
        source_paper_id=p1.id,
        evidence_passage_id=pass1.id,
        properties={"origin": "author_reported"},
    )
    db_session.add(lim_node)
    db_session.commit()

    repo = SynthesisRepository(db_session)
    run = repo.create_synthesis_run(request_id=req.id, selected_paper_ids=[p1.id])

    gap_gen = CandidateResearchGapGenerator(db_session)
    gaps = gap_gen.generate_candidate_gaps(req.id, run.id, selected_paper_ids=[p1.id])

    assert len(gaps) >= 1
    gen_gap = gaps[0]
    assert gen_gap.category == "generalisation_gap"
    assert gen_gap.preliminary_confidence >= 0.70
    assert len(gen_gap.suggested_validation_queries) >= 1
    assert p1.id in gen_gap.supporting_paper_ids

    # Verify End-to-End Traceability via ReviewService
    review_service = SynthesisReviewService(db_session)
    detailed_gap = review_service.get_gap_with_provenance(gen_gap.id)

    assert detailed_gap is not None
    assert len(detailed_gap["evidence_links"]) >= 1
    link = detailed_gap["evidence_links"][0]
    assert link["paper_id"] == p1.id
    assert link["evidence_id"] == pass1.id
    assert "multi-hop" in link["exact_passage"]
    assert link["page_number"] == 6
    assert link["section_heading"] == "Experimental Limitations"


def test_candidate_gap_human_review_lifecycle(db_session):
    """Verifies that researchers can review, accept, edit, or reject candidate research gaps."""
    req = ResearchRequest(
        id="req-rev-test",
        topic="Robotics",
        objective="Assess RL methods",
        domain="Robotics",
        start_year=2020,
        end_year=2024,
    )
    p1 = Paper(id="p-rev-1", request_id=req.id, title="Sim-to-Real Transfer", normalized_title="sim-to-real transfer", publication_year=2023)
    db_session.add_all([req, p1])
    db_session.commit()

    repo = SynthesisRepository(db_session)
    run = repo.create_synthesis_run(request_id=req.id, selected_paper_ids=[p1.id])

    gap = repo.create_candidate_gap({
        "synthesis_run_id": run.id,
        "research_request_id": req.id,
        "title": "Sim-to-Real Dynamics Gap in Quadruped Locomotion",
        "description": "Friction coefficients in simulation do not accurately transfer to wet surfaces.",
        "category": "deployment_gap",
        "research_domain": "Robotics",
        "rationale": "Empirical reality gap noted across trials.",
        "observed_pattern": "Robot slips on real surfaces.",
        "supporting_paper_ids": [p1.id],
        "confidence_explanation": "Directly observed in trials.",
        "generation_status": "evidence_grounded",
        "human_review_status": "pending_review",
    })

    review_service = SynthesisReviewService(db_session)

    # 1. Edit Gap Title & Category
    edit_req = HumanReviewRequest(
        reviewer_reference="Senior Roboticist",
        review_action="edit",
        revised_title="Non-Linear Friction Discrepancy in Sim-to-Real Quadruped Locomotion",
        revised_category="empirical_gap",
        reviewer_comment="Refined title to emphasize specific friction modeling discrepancy.",
    )
    edited_gap = review_service.review_candidate_gap(gap.id, edit_req)

    assert edited_gap.title == "Non-Linear Friction Discrepancy in Sim-to-Real Quadruped Locomotion"
    assert edited_gap.category == "empirical_gap"
    assert edited_gap.human_review_status == "edited_by_reviewer"

    # 2. Accept for Further Investigation
    accept_req = HumanReviewRequest(
        reviewer_reference="Lab PI",
        review_action="accept",
        reviewer_comment="Approved for Phase 5 explicit counterevidence retrieval.",
    )
    accepted_gap = review_service.review_candidate_gap(gap.id, accept_req)

    assert accepted_gap.human_review_status == "accepted_for_further_investigation"

    # Verify review audit history has 2 records
    audit = repo.get_review_records_by_gap(gap.id)
    assert len(audit) == 2
    assert audit[0].review_action == "accept"
    assert audit[1].review_action == "edit"
