"""Unit tests for Search Strategy Generation and Database Query Formatting."""

from backend.app.services.planner.keyword_expander import expand_keywords
from backend.app.services.planner.query_builder import (
    build_openalex_query,
    build_semantic_scholar_query,
    build_crossref_query,
    build_arxiv_query,
    generate_database_queries,
)
from backend.app.services.planner.strategy_generator import DeterministicStrategyPlanner


def test_keyword_expansion_and_concepts():
    topic = "Explainable AI for Fake News Detection"
    objective = "Identify limitations in existing explainable fake news models"
    domain = "Artificial Intelligence"
    questions = ["How do SHAP and LIME perform on misinformation benchmarks?"]

    res = expand_keywords(topic, objective, domain, questions)

    assert "concepts" in res
    assert len(res["concepts"]) >= 1
    # Check that domain vocabulary like xai or misinformation was extracted
    keywords_lower = [k.lower() for k in res["keywords"]]
    assert any("fake news" in k or "misinformation" in k for k in keywords_lower)
    assert any("explainable" in k or "xai" in k or "interpretability" in k for k in keywords_lower)
    assert "query_combinations" in res
    assert len(res["query_combinations"]) >= 1


def test_database_specific_query_builders():
    topic = "Counterevidence in Scientific Claim Verification"
    keywords = ["claim verification", "counterevidence", "fact-checking"]

    # OpenAlex query format
    oa_q = build_openalex_query(topic, keywords)
    assert '"claim verification"' in oa_q

    # Semantic Scholar format
    s2_q = build_semantic_scholar_query(topic, keywords)
    assert "claim verification" in s2_q

    # Crossref format
    cr_q = build_crossref_query(topic, keywords)
    assert "claim verification" in cr_q

    # arXiv syntax (must contain all: prefix and uppercase AND/OR)
    arxiv_q = build_arxiv_query(topic, keywords)
    assert "all:" in arxiv_q
    assert " AND " in arxiv_q


def test_strategy_planner_generates_queries_for_selected_databases():
    planner = DeterministicStrategyPlanner()
    plan = planner.generate(
        topic="Neural Network Hallucination Mitigation",
        objective="Analyze grounded factual verification in LLMs",
        domain="NLP",
        research_questions=["What benchmarks measure hallucination?"],
        preferred_databases=["openalex", "arxiv"],
    )

    assert "concepts" in plan
    assert "keywords" in plan
    assert "queries" in plan

    db_targets = [q["target_database"] for q in plan["queries"]]
    assert "openalex" in db_targets
    assert "arxiv" in db_targets
    assert "semantic_scholar" not in db_targets  # Not in preferred_databases

