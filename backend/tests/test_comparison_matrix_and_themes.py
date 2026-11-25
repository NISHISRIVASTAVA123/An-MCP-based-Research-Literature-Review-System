"""Tests for Paper Comparison Matrix and Research Theme Services (Phase 4).

Verifies multidimensional paper comparisons, handling of missing data,
CSV/Markdown exports, and evidence-grounded research theme discovery.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models.base import Base
from backend.app.models.research_request import ResearchRequest
from backend.app.models.paper import Paper
from backend.app.models.evidence import ExtractionRun, EvidenceRecord, EvidencePassage
from backend.app.models.graph import GraphNode, GraphEdge
from backend.app.services.synthesis.comparison_matrix_service import PaperComparisonMatrixService
from backend.app.services.synthesis.theme_service import ResearchThemeService


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


def test_paper_comparison_matrix_generation_and_exports(db_session):
    """Verifies dynamic paper comparison matrix generation, incomplete field handling, and exports."""
    req = ResearchRequest(
        id="req-matrix-test",
        topic="Transformer Models in NLP",
        objective="Compare attention mechanisms and benchmark evaluations",
        domain="Computer Science",
        start_year=2015,
        end_year=2024,
    )
    # Paper 1: Rich extracted evidence
    p1 = Paper(
        id="paper-101",
        request_id=req.id,
        title="Attention Is All You Need",
        normalized_title="attention is all you need",
        authors=["Vaswani", "Shazeer", "Parmar"],
        publication_year=2017,
        venue="NeurIPS",
    )
    ex1 = ExtractionRun(id="ex-101", paper_id=p1.id, source_scope="abstract_only", extractor_backend="rule_based")
    ev1 = EvidenceRecord(
        id="ev-rec-101",
        extraction_run_id=ex1.id,
        paper_id=p1.id,
        research_objective={"items": [{"objective_text": "Replace recurrence with self-attention."}]},
        methodology={
            "items": [{"method_name": "Multi-Head Attention", "category": "deep_learning"}],
            "models": [{"model_name": "Transformer", "family": "attention"}],
        },
        datasets=[{"dataset_name": "WMT 2014 English-to-German", "size": "4.5M pairs"}],
        evaluation_metrics=[{"metric_name": "BLEU", "category": "accuracy"}],
        findings=[{"finding_text": "Transformer achieves 28.4 BLEU on WMT 2014 En-De."}],
        limitations=[{"limitation_text": "Quadratic memory complexity with sequence length."}],
        future_work=[{"direction_text": "Apply attention to image and speech modalities."}],
    )
    pass1 = EvidencePassage(
        id="pass-101",
        paper_id=p1.id,
        evidence_record_id=ev1.id,
        category="methodology",
        statement="The Transformer allows for significantly more parallelization.",
        verbatim_passage="The Transformer allows for significantly more parallelization.",
        page_number=3,
        section_heading="Model Architecture",
    )

    # Paper 2: Minimal/incomplete extracted evidence
    p2 = Paper(
        id="paper-102",
        request_id=req.id,
        title="Sparse Attention Mechanisms",
        normalized_title="sparse attention mechanisms",
        authors=["Child", "Gray"],
        publication_year=2019,
        venue="arXiv",
    )
    ex2 = ExtractionRun(id="ex-102", paper_id=p2.id, source_scope="abstract_only", extractor_backend="rule_based")
    ev2 = EvidenceRecord(
        id="ev-rec-102",
        extraction_run_id=ex2.id,
        paper_id=p2.id,
        methodology={"items": [{"method_name": "Sparse Attention"}]},
        # Datasets, metrics omitted intentionally to test "Not reported"
    )

    db_session.add_all([req, p1, p2, ex1, ex2, ev1, ev2, pass1])
    db_session.commit()

    service = PaperComparisonMatrixService(db_session)
    matrix = service.generate_matrix(req.id, sort_by="year_desc")

    assert matrix.total_papers == 2
    assert len(matrix.rows) == 2

    # Check Paper 1 complete row
    row1 = next(r for r in matrix.rows if r.paper_id == p1.id)
    assert row1.title == "Attention Is All You Need"
    assert "Multi-Head Attention" in row1.methodologies
    assert "Transformer" in row1.models
    assert "WMT 2014 English-to-German" in row1.datasets
    assert "BLEU" in row1.metrics
    assert row1.evidence_count == 1

    # Check Paper 2 incomplete row defaults to "Not reported"
    row2 = next(r for r in matrix.rows if r.paper_id == p2.id)
    assert "Sparse Attention" in row2.methodologies
    assert row2.datasets == ["Not reported"]
    assert row2.metrics == ["Not reported"]

    # Test CSV Export
    csv_text = service.export_matrix_csv(matrix)
    assert "Attention Is All You Need" in csv_text
    assert "Sparse Attention" in csv_text
    assert "BLEU" in csv_text

    # Test Markdown Export
    md_text = service.export_matrix_markdown(matrix)
    assert "| **Attention Is All You Need** |" in md_text
    assert "Multi-Head Attention" in md_text


def test_research_theme_identification_service(db_session):
    """Verifies that ResearchThemeService clusters methods and limitations into grounded themes."""
    req = ResearchRequest(
        id="req-theme-test",
        topic="GNN Interpretability",
        objective="Identify explainability methods",
        domain="Computer Science",
        start_year=2018,
        end_year=2024,
    )
    p1 = Paper(id="p-thm-1", request_id=req.id, title="GNNExplainer Framework", normalized_title="gnnexplainer framework", publication_year=2019)
    p2 = Paper(id="p-thm-2", request_id=req.id, title="SubGraphX Explanation", normalized_title="subgraphx explanation", publication_year=2021)
    db_session.add_all([req, p1, p2])
    db_session.commit()

    # Graph nodes and edges for USES_METHOD
    m_node = GraphNode(
        id="node-m1",
        request_id=req.id,
        node_type="METHOD",
        label="Graph Neural Network",
        normalized_label="Graph Neural Network",
        entity_key="METHOD:gnn",
    )
    pn1 = GraphNode(
        id="node-p1", request_id=req.id, node_type="PAPER", label=p1.title,
        normalized_label=p1.title, entity_key=f"PAPER:{p1.id}", source_paper_id=p1.id
    )
    pn2 = GraphNode(
        id="node-p2", request_id=req.id, node_type="PAPER", label=p2.title,
        normalized_label=p2.title, entity_key=f"PAPER:{p2.id}", source_paper_id=p2.id
    )
    edge1 = GraphEdge(
        id="edge-m1", request_id=req.id, source_node_id=pn1.id, target_node_id=m_node.id,
        relationship_type="USES_METHOD", edge_key=f"{pn1.id}:USES_METHOD:{m_node.id}"
    )
    edge2 = GraphEdge(
        id="edge-m2", request_id=req.id, source_node_id=pn2.id, target_node_id=m_node.id,
        relationship_type="USES_METHOD", edge_key=f"{pn2.id}:USES_METHOD:{m_node.id}"
    )

    # Limitations on explainability
    lim_node = GraphNode(
        id="node-lim1",
        request_id=req.id,
        node_type="LIMITATION",
        label="Explanation fidelity degrades on dense graphs",
        normalized_label="Explanation fidelity degrades on dense graphs",
        entity_key="LIMITATION:fidelity_dense",
        source_paper_id=p1.id,
        properties={"origin": "author_reported"},
    )

    db_session.add_all([m_node, pn1, pn2, edge1, edge2, lim_node])
    db_session.commit()

    theme_service = ResearchThemeService(db_session)
    themes = theme_service.identify_themes(req.id)

    assert len(themes) >= 1
    # Check Methodological theme
    meth_theme = next((t for t in themes if "Graph Neural Network" in t["name"]), None)
    assert meth_theme is not None
    assert meth_theme["frequency"] == 2
    assert p1.id in meth_theme["associated_paper_ids"]
    assert p2.id in meth_theme["associated_paper_ids"]
