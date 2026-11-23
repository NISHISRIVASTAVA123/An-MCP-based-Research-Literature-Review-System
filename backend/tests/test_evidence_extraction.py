"""Unit Tests for Structured Scientific Evidence Extraction and Passage Tracking."""

import pytest
from backend.app.services.extraction.rule_extractor import RuleBasedEvidenceExtractor
from backend.app.services.extraction.mock_extractor import MockEvidenceExtractor
from backend.app.services.extraction.extraction_service import EvidenceExtractionService
from backend.tests.conftest import TestingSessionLocal
from backend.app.models.paper import Paper
from backend.app.models.research_request import ResearchRequest
from backend.app.models.document import FulltextDocument


@pytest.mark.asyncio
async def test_rule_based_evidence_extraction():
    extractor = RuleBasedEvidenceExtractor()
    title = "Robust Interpretability in Transformer Models for Fake News Detection"
    abstract = (
        "In this paper we propose an explainable AI framework using SHAP and BERT on the LIAR dataset. "
        "Our method achieves an accuracy of 91.5% and an F1-Score of 89.2%. "
        "Results show that attention mechanism improves classification over baseline. "
        "However, our study is restricted to small sample size. "
        "In future work, we plan to evaluate multimodal news."
    )

    res = await extractor.extract_evidence(
        paper_id="test-p1",
        title=title,
        abstract=abstract,
        fulltext_sections=[],
        source_scope="abstract_only",
    )

    assert res.paper_id == "test-p1"
    assert res.source_scope == "abstract_only"
    assert res.research_objective.problem_statement is not None

    # Check methodologies
    method_names = [m.approach_name for m in res.methodologies]
    assert any("BERT" in m or "SHAP" in m or "Explainable AI" in m for m in method_names)

    # Check datasets
    dataset_names = [d.dataset_name for d in res.datasets]
    assert any("LIAR" in d for d in dataset_names)

    # Check evaluation metrics
    metric_names = [m.metric_name for m in res.evaluation_metrics]
    assert "Accuracy" in metric_names or "F1-Score" in metric_names

    # Check limitations
    assert len(res.limitations) >= 1
    assert "restricted to small sample" in res.limitations[0].limitation_text.lower()
    assert res.limitations[0].limitation_type == "author_reported"

    # Check future work
    assert len(res.future_work) >= 1
    assert "multimodal" in res.future_work[0].direction_text.lower()


@pytest.mark.asyncio
async def test_extraction_service_database_persistence():
    import uuid
    p_id = f"ev-p1-{uuid.uuid4().hex[:8]}"
    db = TestingSessionLocal()
    try:
        req = ResearchRequest(
            topic="Explainable AI",
            objective="Evaluate explanation models",
            domain="AI",
            start_year=2020,
            end_year=2024,
        )
        db.add(req)
        db.commit()

        paper = Paper(
            id=p_id,
            request_id=req.id,
            title="Adversarial Robustness of Explainable Graph Neural Networks",
            normalized_title="adversarial robustness of explainable graph neural networks",
            authors=["Alice", "Bob"],
            abstract="We evaluate GNN explanations on graph benchmarks. The method achieves an accuracy of 88.0%. A limitation is high computational cost.",
            publication_year=2023,
            keywords=["GNN", "XAI"],
        )
        db.add(paper)
        db.commit()

        service = EvidenceExtractionService(db, extractor=MockEvidenceExtractor())
        record = await service.extract_paper_evidence(paper.id)

        assert record.paper_id == paper.id
        assert len(record.passages) >= 4

        # Verify passages in DB
        passages = service.evidence_repo.get_passages_by_paper(paper.id)
        assert len(passages) >= 4
        categories = [p.category for p in passages]
        assert "objective" in categories
        assert "methodology" in categories
        assert "finding" in categories

        # Test human verification on a passage
        first_passage = passages[0]
        updated = service.evidence_repo.update_passage(
            passage_id=first_passage.id,
            verification_status="user_verified",
            user_notes="Confirmed against original paper Introduction section.",
        )
        assert updated.verification_status == "user_verified"
        assert updated.user_notes is not None
    finally:
        db.close()
