"""Unit and Integration Tests for Paper Screening Service (Phase 2)."""

import pytest
from backend.app.models.paper import Paper
from backend.app.models.research_request import ResearchRequest, ResearchQuestion
from backend.app.services.screening.criteria_evaluator import ScreeningCriteriaEvaluator
from backend.app.services.screening.screening_service import ScreeningService
from backend.tests.conftest import TestingSessionLocal


def test_relevant_paper_included():
    evaluator = ScreeningCriteriaEvaluator()
    req = ResearchRequest(
        id="test-req-1",
        topic="Explainable AI for Fake News Detection",
        objective="Analyze explanation mechanisms like SHAP and LIME in fake news detection",
        domain="Artificial Intelligence",
        start_year=2018,
        end_year=2026,
    )
    paper = Paper(
        id="paper-1",
        request_id="test-req-1",
        title="Towards Explainable Fake News Detection via SHAP and LIME Interpretability",
        normalized_title="towards explainable fake news detection via shap and lime interpretability",
        authors=["Alice Smith", "Bob Jones"],
        abstract="In this work, we present an explainable AI framework for detecting misinformation using SHAP and LIME.",
        publication_year=2022,
        keywords=["fake news", "explainable AI", "SHAP"],
    )

    decision, reason, evaluated, satisfied, unsatisfied, missing, conf = evaluator.evaluate_paper(paper, req)
    assert decision == "included"
    assert "publication_timeframe" in satisfied
    assert "topic_relevance" in satisfied
    assert conf >= 0.70


def test_timeframe_outside_excluded():
    evaluator = ScreeningCriteriaEvaluator()
    req = ResearchRequest(
        id="test-req-2",
        topic="Explainable AI for Fake News Detection",
        objective="Examine fake news approaches",
        domain="Artificial Intelligence",
        start_year=2020,
        end_year=2024,
    )
    paper = Paper(
        id="paper-2",
        request_id="test-req-2",
        title="Early Fake News Classification",
        normalized_title="early fake news classification",
        authors=["Charlie Brown"],
        abstract="A study on fake news.",
        publication_year=2015,  # Outside 2020-2024
        keywords=[],
    )

    decision, reason, evaluated, satisfied, unsatisfied, missing, conf = evaluator.evaluate_paper(paper, req)
    assert decision == "excluded"
    assert "publication_timeframe" in unsatisfied
    assert "2015" in reason


def test_irrelevant_paper_excluded():
    evaluator = ScreeningCriteriaEvaluator()
    req = ResearchRequest(
        id="test-req-3",
        topic="Explainable AI for Fake News Detection",
        objective="Explainable misinformation models",
        domain="Artificial Intelligence",
        start_year=2018,
        end_year=2026,
    )
    paper = Paper(
        id="paper-3",
        request_id="test-req-3",
        title="Quantum Teleportation Protocols over Terrestrial Free-Space Optical Channels",
        normalized_title="quantum teleportation protocols over terrestrial free-space optical channels",
        authors=["David Miller"],
        abstract="We demonstrate continuous-variable quantum key distribution using photonic states in atmospheric channels.",
        publication_year=2021,
        keywords=["quantum", "photonics"],
    )

    decision, reason, evaluated, satisfied, unsatisfied, missing, conf = evaluator.evaluate_paper(paper, req)
    assert decision == "excluded"
    assert "topic_relevance" in unsatisfied


def test_missing_abstract_marked_needs_review():
    evaluator = ScreeningCriteriaEvaluator()
    req = ResearchRequest(
        id="test-req-4",
        topic="Explainable AI for Fake News Detection",
        objective="Fake news interpretability",
        domain="Artificial Intelligence",
        start_year=2018,
        end_year=2026,
    )
    paper = Paper(
        id="paper-4",
        request_id="test-req-4",
        title="Explainable Fake News Detection Approaches",
        normalized_title="explainable fake news detection approaches",
        authors=["Eve White"],
        abstract=None,  # Missing abstract
        publication_year=2023,
        keywords=[],
    )

    decision, reason, evaluated, satisfied, unsatisfied, missing, conf = evaluator.evaluate_paper(paper, req)
    assert decision == "needs_human_review"
    assert "abstract" in missing


def test_user_exclusion_criteria_applied():
    evaluator = ScreeningCriteriaEvaluator()
    req = ResearchRequest(
        id="test-req-5",
        topic="Explainable AI for Fake News Detection",
        objective="Fake news interpretability",
        domain="Artificial Intelligence",
        start_year=2018,
        end_year=2026,
        exclusion_criteria=["Non-English publications", "Opinion piece"],
    )
    paper = Paper(
        id="paper-5",
        request_id="test-req-5",
        title="An Opinion Piece on Fake News and Journalism",
        normalized_title="an opinion piece on fake news and journalism",
        authors=["Frank Green"],
        abstract="This is an opinion piece on why fake news spreads rapidly.",
        publication_year=2021,
        keywords=[],
    )

    decision, reason, evaluated, satisfied, unsatisfied, missing, conf = evaluator.evaluate_paper(paper, req)
    assert decision == "excluded"
    assert "exclusion_criteria" in unsatisfied


def test_screening_service_batch_and_human_override():
    import uuid
    uid = uuid.uuid4().hex[:8]
    p1_id = f"fl-p1-{uid}"
    p2_id = f"fl-p2-{uid}"
    db = TestingSessionLocal()
    try:
        # Create request
        req = ResearchRequest(
            topic="Federated Learning in Healthcare",
            objective="Investigate privacy-preserving clinical models",
            domain="Healthcare Informatics",
            start_year=2019,
            end_year=2025,
        )
        db.add(req)
        db.commit()

        # Add 2 papers
        p1 = Paper(
            id=p1_id,
            request_id=req.id,
            title="Privacy-Preserving Federated Learning for Clinical Healthcare Records",
            normalized_title="privacy-preserving federated learning for clinical healthcare records",
            authors=["Dr. A"],
            abstract="We evaluate federated learning on multi-hospital clinical healthcare records.",
            publication_year=2021,
            keywords=["federated learning", "healthcare"],
        )
        p2 = Paper(
            id=p2_id,
            request_id=req.id,
            title="Solar Cell Efficiency in Extreme Cold Environments",
            normalized_title="solar cell efficiency in extreme cold environments",
            authors=["Dr. B"],
            abstract="Photovoltaic performance measurements in Antarctic stations.",
            publication_year=2020,
            keywords=["solar", "photovoltaic"],
        )
        db.add_all([p1, p2])
        db.commit()

        service = ScreeningService(db)
        run = service.execute_screening_run(req.id)

        assert run.total_papers == 2
        assert run.included_count == 1
        assert run.excluded_count == 1

        # Check human override
        repo = service.screening_repo
        updated = repo.update_human_override(
            paper_id=p2.id,
            new_decision="included",
            reviewer_notes="Included for cross-domain comparison methodology.",
        )
        assert updated is not None
        assert updated.decision == "included"
        assert updated.is_human_override is True
        assert updated.original_decision == "excluded"
    finally:
        db.close()
