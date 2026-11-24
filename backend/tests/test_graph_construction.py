"""Integration Tests for Evidence Graph Construction Pipeline (Phase 3)."""

import uuid
import pytest
from backend.tests.conftest import TestingSessionLocal
from backend.app.models.research_request import ResearchRequest, ResearchQuestion
from backend.app.models.paper import Paper
from backend.app.models.screening import ScreeningRun, ScreeningDecision
from backend.app.models.evidence import ExtractionRun, EvidenceRecord, EvidencePassage
from backend.app.services.graph.graph_builder import EvidenceGraphBuilder
from backend.app.services.persistence.graph_repository import GraphRepository
from backend.app.services.graph.graph_validation_service import GraphValidationService


def create_test_research_context(db):
    uid = uuid.uuid4().hex[:8]
    req_id = f"test-req-{uid}"

    req = ResearchRequest(
        id=req_id,
        topic="Explainable AI for Fake News Detection",
        objective="Assess interpretability techniques for detecting misinformation",
        domain="Artificial Intelligence",
        start_year=2020,
        end_year=2025,
    )
    db.add(req)

    q1 = ResearchQuestion(
        id=f"q1-{uid}",
        request_id=req_id,
        question_text="What attribution methods are most reliable?",
        order_index=1,
    )
    db.add(q1)

    # Paper 1: Included
    p1 = Paper(
        id=f"p1-{uid}",
        request_id=req_id,
        title="Towards Interpretable Misinformation Detection with SHAP and BERT",
        normalized_title="towards interpretable misinformation detection with shap and bert",
        authors=["Alice Smith", "Bob Jones"],
        publication_year=2022,
        venue="ACL",
        publication_type="proceedings-article",
        has_abstract=True,
    )

    # Paper 2: Excluded
    p2 = Paper(
        id=f"p2-{uid}",
        request_id=req_id,
        title="Seismic Wave Propagation in Crystalline Rock Formations",
        normalized_title="seismic wave propagation in crystalline rock formations",
        authors=["Charlie Rock"],
        publication_year=2021,
        venue="Geophysics",
        publication_type="journal-article",
    )
    db.add_all([p1, p2])
    db.commit()

    # Screening Run
    screening_run = ScreeningRun(
        id=f"srun-{uid}",
        request_id=req_id,
        run_number=1,
        total_papers=2,
        included_count=1,
        excluded_count=1,
        review_needed_count=0,
    )
    db.add(screening_run)

    dec1 = ScreeningDecision(
        id=f"dec1-{uid}",
        run_id=screening_run.id,
        paper_id=p1.id,
        decision="included",
        stage="metadata_abstract",
        reason="Aligned with topic and objectives.",
    )
    dec2 = ScreeningDecision(
        id=f"dec2-{uid}",
        run_id=screening_run.id,
        paper_id=p2.id,
        decision="excluded",
        stage="metadata_abstract",
        reason="Thematically irrelevant.",
    )
    db.add_all([dec1, dec2])

    # Structured Evidence for Paper 1
    ext_run = ExtractionRun(
        id=f"ext-{uid}",
        paper_id=p1.id,
        source_scope="abstract_only",
        extractor_backend="rule_based",
        status="completed",
    )
    db.add(ext_run)

    ev_record = EvidenceRecord(
        id=f"ev-{uid}",
        extraction_run_id=ext_run.id,
        paper_id=p1.id,
        research_objective={"problem_statement": "Interpretable fake news detection"},
        methodology=[
            {"approach_name": "SHAP", "model_architecture": "BERT"},
            {"approach_name": "Attention Mechanism"},
        ],
        datasets=[{"dataset_name": "LIAR", "sample_size": "12,800"}],
        evaluation_metrics=[{"metric_name": "Accuracy", "reported_value": "91.5%"}],
        findings=[{"claim_text": "SHAP feature attributions improve explainability over baselines."}],
        limitations=[{"limitation_text": "Evaluated only on English news articles.", "limitation_type": "author_reported"}],
        future_work=[{"direction_text": "Evaluate multimodal audio-visual news."}],
    )
    db.add(ev_record)

    passage1 = EvidencePassage(
        id=f"pas1-{uid}",
        evidence_record_id=ev_record.id,
        paper_id=p1.id,
        category="finding",
        statement="SHAP feature attributions improve explainability over baselines.",
        verbatim_passage="Our results demonstrate that SHAP feature attributions improve explainability over baselines by 14%.",
        page_number=1,
        section_heading="Abstract",
        verification_status="machine_extracted",
    )
    passage2 = EvidencePassage(
        id=f"pas2-{uid}",
        evidence_record_id=ev_record.id,
        paper_id=p1.id,
        category="limitation",
        statement="Evaluated only on English news articles.",
        verbatim_passage="However, our empirical study was restricted to English language news articles.",
        page_number=1,
        section_heading="Abstract",
        verification_status="user_verified",
    )
    db.add_all([passage1, passage2])
    db.commit()

    return req_id, p1.id, p2.id, passage1.id


def test_graph_construction_omits_excluded_papers():
    db = TestingSessionLocal()
    try:
        req_id, p1_id, p2_id, _ = create_test_research_context(db)
        builder = EvidenceGraphBuilder(db)
        run = builder.build_graph(req_id)

        assert run.status == "completed"
        assert run.papers_processed == 1

        repo = GraphRepository(db)
        nodes = repo.get_nodes_by_request(req_id)
        node_labels = [n.label for n in nodes]
        node_types = {n.node_type for n in nodes}

        # Included paper is present
        assert any("Towards Interpretable" in l for l in node_labels)

        # Excluded paper MUST NOT enter active graph
        assert not any("Seismic Wave" in l for l in node_labels)

        # Core semantic entity types are present
        assert "RESEARCH_REQUEST" in node_types
        assert "RESEARCH_QUESTION" in node_types
        assert "PAPER" in node_types
        assert "AUTHOR" in node_types
        assert "METHOD" in node_types
        assert "MODEL" in node_types
        assert "DATASET" in node_types
        assert "METRIC" in node_types
        assert "CLAIM" in node_types
        assert "FINDING" in node_types
        assert "LIMITATION" in node_types
        assert "EVIDENCE_PASSAGE" in node_types

        # Check relationships
        edges = repo.get_edges_by_request(req_id)
        rel_types = {e.relationship_type for e in edges}
        assert "HAS_QUESTION" in rel_types
        assert "INCLUDES_PAPER" in rel_types
        assert "AUTHORED_BY" in rel_types
        assert "USES_METHOD" in rel_types
        assert "USES_MODEL" in rel_types
        assert "USES_DATASET" in rel_types
        assert "EVALUATED_USING" in rel_types
        assert "REPORTS_CLAIM" in rel_types
        assert "REPORTS_LIMITATION" in rel_types
        assert "HAS_EVIDENCE" in rel_types
        assert "SUPPORTS" in rel_types
    finally:
        db.close()


def test_graph_construction_idempotent():
    db = TestingSessionLocal()
    try:
        req_id, _, _, _ = create_test_research_context(db)
        builder = EvidenceGraphBuilder(db)

        # Run 1
        run1 = builder.build_graph(req_id)
        count_nodes_1 = run1.total_nodes
        count_edges_1 = run1.total_edges

        # Run 2 (rebuild)
        run2 = builder.build_graph(req_id)
        count_nodes_2 = run2.total_nodes
        count_edges_2 = run2.total_edges

        # Repeated build MUST NOT duplicate nodes or edges
        assert count_nodes_1 == count_nodes_2
        assert count_edges_1 == count_edges_2
        assert run2.nodes_added == 0
        assert run2.edges_added == 0
    finally:
        db.close()


def test_graph_validation_integrity_audit():
    db = TestingSessionLocal()
    try:
        req_id, _, _, _ = create_test_research_context(db)
        builder = EvidenceGraphBuilder(db)
        run = builder.build_graph(req_id)

        validator = GraphValidationService(db)
        val = validator.validate_graph(req_id, build_run_id=run.id)

        assert val.integrity_status in ("valid", "warnings_detected")
        assert val.total_nodes > 0
        assert val.total_relationships > 0
        assert val.claims_with_evidence >= 1
        assert val.findings_with_passages >= 1
        assert val.abstract_only_count == 1
    finally:
        db.close()
