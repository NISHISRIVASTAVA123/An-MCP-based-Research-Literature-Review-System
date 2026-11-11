"""Unit tests for Research Request validation and inputs."""

import pytest
from pydantic import ValidationError
from backend.app.schemas.research import ResearchRequestCreate


def test_valid_research_request():
    payload = {
        "topic": "Explainable AI for Fake News Detection",
        "objective": "Identify limitations and verification gaps in existing explainable fake news models",
        "domain": "Artificial Intelligence",
        "start_year": 2018,
        "end_year": 2024,
        "max_papers": 30,
        "citation_style": "IEEE",
        "research_questions": [
            "What explanation mechanisms are most prevalent in fake news detection?",
            "Are existing explanations robust against adversarial perturbations?"
        ],
        "inclusion_criteria": ["Peer-reviewed publications", "Focus on text disinformation"],
        "exclusion_criteria": ["Image-only detection", "Articles before 2018"],
    }
    req = ResearchRequestCreate(**payload)
    assert req.topic == "Explainable AI for Fake News Detection"
    assert len(req.research_questions) == 2
    assert req.start_year == 2018
    assert req.end_year == 2024


def test_empty_topic_rejected():
    with pytest.raises(ValidationError) as exc:
        ResearchRequestCreate(
            topic="   ",
            objective="Valid objective of sufficient length here",
            domain="NLP",
            start_year=2020,
            end_year=2023,
        )
    assert "topic" in str(exc.value).lower()


def test_empty_objective_rejected():
    with pytest.raises(ValidationError) as exc:
        ResearchRequestCreate(
            topic="Valid Research Topic",
            objective="",
            domain="NLP",
            start_year=2020,
            end_year=2023,
        )
    assert "objective" in str(exc.value).lower()


def test_invalid_year_range_rejected():
    with pytest.raises(ValidationError) as exc:
        ResearchRequestCreate(
            topic="Explainable AI for Fake News Detection",
            objective="Identify limitations in existing explainable models",
            domain="AI",
            start_year=2025,
            end_year=2019,  # start > end
        )
    assert "cannot be later than end year" in str(exc.value)


def test_missing_optional_inputs_use_sensible_defaults():
    req = ResearchRequestCreate(
        topic="Graph Neural Networks in Drug Discovery",
        objective="Systematic survey of molecular graph representation learning",
        domain="Bioinformatics",
    )
    assert req.max_papers == 25
    assert req.citation_style == "IEEE"
    assert "openalex" in req.preferred_databases
    assert "arxiv" in req.preferred_databases
    assert req.research_questions == []

