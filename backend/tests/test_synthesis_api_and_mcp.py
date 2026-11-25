"""Tests for Literature Synthesis REST APIs and MCP Tools (Phase 4).

Verifies HTTP endpoints for synthesis orchestration, comparison matrix exports,
research themes, empirical patterns, candidate gap reviews, and registered MCP tools.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.main import app
from backend.app.services.persistence.database import get_db
from backend.app.models.base import Base
from backend.app.models.research_request import ResearchRequest
from backend.app.models.paper import Paper
from backend.app.models.evidence import ExtractionRun, EvidenceRecord, EvidencePassage
from backend.app.models.screening import ScreeningRun, ScreeningDecision
from backend.app.models.graph import GraphNode, GraphEdge
from backend.app.services.mcp.tools import (
    tool_generate_literature_synthesis,
    tool_get_literature_synthesis,
    tool_get_paper_comparison_matrix,
    tool_identify_research_themes,
    tool_analyze_methodology_trends,
    tool_analyze_dataset_trends,
    tool_analyze_research_trends,
    tool_generate_candidate_research_gaps,
    tool_get_candidate_gap_details,
    tool_get_candidate_gap_evidence,
    tool_update_candidate_gap_review,
    tool_get_synthesis_history,
)
from backend.tests.conftest import TestingSessionLocal, test_engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_data():
    """Seeds test database with research request, screened papers, and evidence graph nodes."""
    db = TestingSessionLocal()
    # Ensure fresh tables on shared test database
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    req = ResearchRequest(
        id="req-api-synth-1",
        topic="Reinforcement Learning for Autonomous Driving",
        objective="Analyze safety constraints and sample efficiency",
        domain="Artificial Intelligence",
        start_year=2020,
        end_year=2024,
    )
    p1 = Paper(
        id="p-api-1",
        request_id=req.id,
        title="Safe Policy Optimization via Barrier Functions",
        normalized_title="safe policy optimization via barrier functions",
        authors=["John Doe", "Jane Roe"],
        publication_year=2022,
        venue="ICRA",
    )
    p2 = Paper(
        id="p-api-2",
        request_id=req.id,
        title="Model-Based RL for Urban Navigation",
        normalized_title="model-based rl for urban navigation",
        authors=["Alan Turing", "Ada Lovelace"],
        publication_year=2023,
        venue="CoRL",
    )
    db.add_all([req, p1, p2])
    db.commit()

    # Screening Run: both included
    s_run = ScreeningRun(id="s-run-api", request_id=req.id, total_papers=2, included_count=2)
    d1 = ScreeningDecision(id="d-api-1", run_id=s_run.id, paper_id=p1.id, decision="included", reason="In scope", confidence_score=0.9)
    d2 = ScreeningDecision(id="d-api-2", run_id=s_run.id, paper_id=p2.id, decision="included", reason="In scope", confidence_score=0.9)
    db.add_all([s_run, d1, d2])

    # Structured Evidence & Passages
    ex1 = ExtractionRun(id="ex-api-1", paper_id=p1.id, source_scope="abstract_only", extractor_backend="rule_based")
    ev1 = EvidenceRecord(
        id="ev-api-1",
        extraction_run_id=ex1.id,
        paper_id=p1.id,
        research_objective={"objective_text": "Safe autonomous navigation"},
        methodology={
            "items": [{"method_name": "Control Barrier Functions"}],
            "models": [{"model_name": "PPO"}],
        },
        datasets=[{"dataset_name": "CARLA Simulator"}],
        evaluation_metrics=[{"metric_name": "Collision Rate"}],
        limitations=[{"limitation_text": "Severe computational latency in dense traffic scenarios."}],
    )
    pass1 = EvidencePassage(
        id="pass-api-1",
        paper_id=p1.id,
        evidence_record_id=ev1.id,
        category="limitation",
        statement="Barrier evaluation introduces 85ms overhead per planning step.",
        verbatim_passage="Barrier evaluation introduces 85ms overhead per planning step.",
        page_number=5,
        section_heading="Computational Complexity",
    )

    ex2 = ExtractionRun(id="ex-api-2", paper_id=p2.id, source_scope="abstract_only", extractor_backend="rule_based")
    ev2 = EvidenceRecord(
        id="ev-api-2",
        extraction_run_id=ex2.id,
        paper_id=p2.id,
        research_objective={"objective_text": "Model-based urban navigation"},
        methodology={
            "items": [{"method_name": "World Models"}],
            "models": [{"model_name": "DreamerV3"}],
        },
        datasets=[{"dataset_name": "CARLA Simulator"}],
        evaluation_metrics=[{"metric_name": "Collision Rate"}],
        limitations=[{"limitation_text": "Generalization fails on unmapped intersection topologies."}],
    )
    pass2 = EvidencePassage(
        id="pass-api-2",
        paper_id=p2.id,
        evidence_record_id=ev2.id,
        category="limitation",
        statement="Policy fails when encountering roundabouts not seen in training.",
        verbatim_passage="Policy fails when encountering roundabouts not seen in training.",
        page_number=8,
        section_heading="Generalization Failure Modes",
    )
    db.add_all([ex1, ex2, ev1, pass1, ev2, pass2])

    # Graph Nodes and Edges
    m1 = GraphNode(id="gn-m1", request_id=req.id, node_type="METHOD", label="Control Barrier Functions", normalized_label="Control Barrier Functions", entity_key="METHOD:cbf")
    m2 = GraphNode(id="gn-m2", request_id=req.id, node_type="METHOD", label="World Models", normalized_label="World Models", entity_key="METHOD:world_models")
    d_carla = GraphNode(id="gn-d1", request_id=req.id, node_type="DATASET", label="CARLA Simulator", normalized_label="CARLA Simulator", entity_key="DATASET:carla")
    pn1 = GraphNode(id="gn-p1", request_id=req.id, node_type="PAPER", label=p1.title, normalized_label=p1.title, entity_key=f"PAPER:{p1.id}", source_paper_id=p1.id)
    pn2 = GraphNode(id="gn-p2", request_id=req.id, node_type="PAPER", label=p2.title, normalized_label=p2.title, entity_key=f"PAPER:{p2.id}", source_paper_id=p2.id)

    lim1 = GraphNode(
        id="gn-lim1", request_id=req.id, node_type="LIMITATION",
        label="Severe computational latency in dense traffic scenarios",
        normalized_label="Severe computational latency in dense traffic scenarios",
        entity_key="LIMITATION:latency", source_paper_id=p1.id, evidence_passage_id=pass1.id
    )
    lim2 = GraphNode(
        id="gn-lim2", request_id=req.id, node_type="LIMITATION",
        label="Generalization fails on unmapped intersection topologies",
        normalized_label="Generalization fails on unmapped intersection topologies",
        entity_key="LIMITATION:unmapped_topo", source_paper_id=p2.id, evidence_passage_id=pass2.id
    )

    e_m1 = GraphEdge(id="ge-1", request_id=req.id, source_node_id=pn1.id, target_node_id=m1.id, relationship_type="USES_METHOD", edge_key=f"{pn1.id}:USES_METHOD:{m1.id}")
    e_m2 = GraphEdge(id="ge-2", request_id=req.id, source_node_id=pn2.id, target_node_id=m2.id, relationship_type="USES_METHOD", edge_key=f"{pn2.id}:USES_METHOD:{m2.id}")
    e_d1 = GraphEdge(id="ge-3", request_id=req.id, source_node_id=pn1.id, target_node_id=d_carla.id, relationship_type="USES_DATASET", edge_key=f"{pn1.id}:USES_DATASET:{d_carla.id}")
    e_d2 = GraphEdge(id="ge-4", request_id=req.id, source_node_id=pn2.id, target_node_id=d_carla.id, relationship_type="USES_DATASET", edge_key=f"{pn2.id}:USES_DATASET:{d_carla.id}")

    db.add_all([m1, m2, d_carla, pn1, pn2, lim1, lim2, e_m1, e_m2, e_d1, e_d2])
    db.commit()
    db.close()


def test_synthesis_rest_api_lifecycle():
    """Tests the full REST API lifecycle from run trigger to comparison matrix and review."""
    req_id = "req-api-synth-1"

    # 1. Trigger synthesis run
    post_res = client.post(f"/api/research-requests/{req_id}/synthesis/runs", json={})
    assert post_res.status_code in [200, 201]
    run_data = post_res.json()
    assert run_data["status"] == "completed"
    assert run_data["run_number"] == 1
    run_id = run_data["id"]

    # 2. Get overview stats
    stats_res = client.get(f"/api/research-requests/{req_id}/synthesis/overview")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_eligible_papers"] == 2
    assert stats["total_candidate_gaps"] >= 1

    # 3. Get comparison matrix (JSON)
    matrix_res = client.get(f"/api/research-requests/{req_id}/synthesis/comparison")
    assert matrix_res.status_code == 200
    matrix = matrix_res.json()
    assert matrix["total_papers"] == 2
    assert len(matrix["rows"]) == 2

    # 4. Get comparison matrix (CSV)
    csv_res = client.get(f"/api/research-requests/{req_id}/synthesis/comparison?export_format=csv")
    assert csv_res.status_code == 200
    assert "Safe Policy Optimization" in csv_res.text
    assert "CARLA Simulator" in csv_res.text

    # 5. Get Themes
    themes_res = client.get(f"/api/research-requests/{req_id}/synthesis/runs/{run_id}/themes")
    assert themes_res.status_code == 200
    themes = themes_res.json()
    assert len(themes) >= 1

    # 6. Get Patterns
    pat_res = client.get(f"/api/research-requests/{req_id}/synthesis/runs/{run_id}/patterns")
    assert pat_res.status_code == 200
    patterns = pat_res.json()
    assert len(patterns) >= 1

    # 7. Get Candidate Gaps
    gaps_res = client.get(f"/api/research-requests/{req_id}/synthesis/runs/{run_id}/candidate-gaps")
    assert gaps_res.status_code == 200
    gaps = gaps_res.json()
    assert len(gaps) >= 1
    first_gap = gaps[0]
    gap_id = first_gap["id"]

    # 8. Submit Human Review
    review_res = client.post(
        f"/api/research-requests/{req_id}/synthesis/candidate-gaps/{gap_id}/review",
        json={
            "reviewer_reference": "Senior Safety Engineer",
            "review_action": "accept",
            "reviewer_comment": "Crucial gap for physical vehicle trials.",
        },
    )
    assert review_res.status_code == 200
    reviewed_gap = review_res.json()
    assert reviewed_gap["human_review_status"] == "accepted_for_further_investigation"


def test_phase4_mcp_tools_execution():
    """Tests that all 12 Phase 4 MCP tools execute and return valid structured outputs."""
    req_id = "req-api-synth-1"
    db = TestingSessionLocal()
    try:
        # 1. tool_generate_literature_synthesis
        gen_out = tool_generate_literature_synthesis(req_id, db=db)
        assert "run_id" in gen_out
        assert gen_out["status"] == "completed"

        # 2. tool_get_literature_synthesis
        synth_out = tool_get_literature_synthesis(req_id, db=db)
        assert synth_out["status"] == "completed"
        assert "summary_narrative" in synth_out

        # 3. tool_get_paper_comparison_matrix
        mat_out = tool_get_paper_comparison_matrix(req_id, db=db)
        assert mat_out["total_papers"] == 2
        assert len(mat_out["rows"]) == 2

        # 4. tool_identify_research_themes
        thm_out = tool_identify_research_themes(req_id, db=db)
        assert isinstance(thm_out, list)
        assert len(thm_out) >= 1

        # 5. tool_analyze_methodology_trends
        meth_out = tool_analyze_methodology_trends(req_id, db=db)
        assert meth_out["pattern_type"] == "methodology"

        # 6. tool_analyze_dataset_trends
        ds_out = tool_analyze_dataset_trends(req_id, db=db)
        assert ds_out["pattern_type"] == "dataset"

        # 7. tool_analyze_research_trends
        trends_out = tool_analyze_research_trends(req_id, db=db)
        assert isinstance(trends_out, list)
        assert len(trends_out) >= 3

        # 8. tool_generate_candidate_research_gaps
        gaps_out = tool_generate_candidate_research_gaps(req_id, db=db)
        assert isinstance(gaps_out, list)
        assert len(gaps_out) >= 1
        gap_id = gaps_out[0]["id"]

        # 9. tool_get_candidate_gap_details
        det_out = tool_get_candidate_gap_details(gap_id, db=db)
        assert det_out["id"] == gap_id
        assert "rationale" in det_out

        # 10. tool_get_candidate_gap_evidence
        ev_links = tool_get_candidate_gap_evidence(gap_id, db=db)
        assert isinstance(ev_links, list)

        # 11. tool_update_candidate_gap_review
        rev_out = tool_update_candidate_gap_review(
            gap_id, action="accept", reviewer="mcp-agent", comment="Auto-accepted", db=db
        )
        assert rev_out["human_review_status"] == "accepted_for_further_investigation"

        # 12. tool_get_synthesis_history
        hist_out = tool_get_synthesis_history(req_id, db=db)
        assert isinstance(hist_out, list)
        assert len(hist_out) >= 1
    finally:
        db.close()
