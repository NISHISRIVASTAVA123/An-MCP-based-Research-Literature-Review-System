"""Tests for Explicit Counterevidence Retrieval, Traceability, and APIs (Phase 5).

Verifies claim decomposition, multi-angle query generation, retrieval & deduplication,
evidence ground-truth anchoring, relevance assessment hierarchy, impact profiling,
REST endpoints, and MCP tools.
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.base import Base
from backend.app.models.research_request import ResearchRequest
from backend.app.models.paper import Paper
from backend.app.models.document import FulltextDocument
from backend.app.models.synthesis import SynthesisRun, CandidateResearchGap
from backend.app.models.counterevidence import (
    CounterevidenceClaim,
    CounterevidenceSearchQuery,
    CounterevidencePublication,
    CounterevidenceAssessment,
    CounterevidenceEvidence,
    CounterevidenceProfile,
    CounterevidenceSearchRun,
)
from backend.app.services.counterevidence.retrieval_service import CounterevidenceRetrievalService
from backend.app.services.counterevidence.claim_decomposer import GapClaimDecomposer
from backend.app.services.counterevidence.query_generator import CounterevidenceQueryGenerator
from backend.app.services.counterevidence.relevance_assessor import CounterevidenceRelevanceAssessor
from backend.app.services.counterevidence.profile_aggregator import CounterevidenceProfileAggregator
from backend.app.services.counterevidence.counterevidence_orchestrator import CounterevidenceOrchestrator
from backend.app.services.mcp.tools import (
    tool_generate_counterevidence_queries,
    tool_get_counterevidence_profile,
    tool_get_counterevidence_publications,
    tool_extract_counterevidence_evidence,
    tool_assess_counterevidence_relevance,
)
from backend.tests.conftest import TestingSessionLocal, test_engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_data():
    """Initializes tables and seeds a research request, synthesis run, and candidate gap."""
    db = TestingSessionLocal()
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    req = ResearchRequest(
        id="req-ce-test-1",
        topic="Reinforcement Learning for Autonomous Driving",
        objective="Analyze safety constraints and sample efficiency",
        domain="Artificial Intelligence",
        start_year=2020,
        end_year=2024,
    )
    p1 = Paper(
        id="p-ce-existing-1",
        request_id=req.id,
        title="Safe Policy Optimization via Barrier Functions",
        normalized_title="safe policy optimization via barrier functions",
        authors=["Alice Smith"],
        publication_year=2022,
        doi="10.1000/existing-1",
    )
    synth_run = SynthesisRun(
        id="synth-run-ce-1",
        research_request_id=req.id,
        status="completed",
    )
    gap = CandidateResearchGap(
        id="gap-ce-test-1",
        synthesis_run_id=synth_run.id,
        research_request_id=req.id,
        title="Unexplored Scalability of Multi-Agent Barrier Functions in Dense Urban Driving",
        category="unexplored_methodology",
        description="Existing control barrier certificates fail to scale beyond 10 interacting vehicles due to quadratic complexity in dense urban intersections.",
        rationale="Scalability bounds reported across multiple CARLA studies.",
        observed_pattern="Dense multi-agent interactions scale quadratically.",
        preliminary_confidence=0.85,
        confidence_explanation="Multiple papers note scalability bounds.",
        assumptions=["Barrier functions require pairwise distance calculations", "Vehicles operate in dense environments"],
        known_limitations=["Tested only in CARLA with 4 agents"],
        potential_counterexamples=["Decentralized control barrier certificates"],
        unresolved_questions=["Can graph neural networks approximate high-dimensional barrier certificates?"],
        suggested_validation_queries=["multi-agent barrier function scalable urban traffic"],
        supporting_paper_ids=[p1.id],
    )

    db.add_all([req, p1, synth_run, gap])
    db.commit()
    db.close()


def test_gap_claim_decomposer_decomposes_gap_into_empirical_claims():
    """Verifies that a candidate gap is decomposed into 3-4 distinct empirical claims."""
    decomposer = GapClaimDecomposer()
    gap = CandidateResearchGap(
        id="temp-gap-1",
        title="Unexplored Scalability of Multi-Agent Barrier Functions",
        description="Existing control barrier certificates fail to scale beyond 10 interacting vehicles due to quadratic complexity in dense traffic.",
        category="unexplored_methodology",
        assumptions=["Pairwise calculations required"],
        unresolved_questions=["Can decentralized barriers scale?"],
    )
    claims = decomposer.decompose_gap(gap)

    assert len(claims) >= 3
    claim_types = [c["claim_type"] for c in claims]
    assert "unexplored_problem" in claim_types
    assert "missing_methodology" in claim_types
    for c in claims:
        assert len(c["claim_text"]) > 10
        assert "generated_keywords" in c


def test_query_generator_generates_multi_angle_queries():
    """Verifies query generator produces diverse query types across claims."""
    generator = CounterevidenceQueryGenerator()
    claims = [
        {"id": "c1", "claim_text": "Scalability of multi-agent barrier certificates has not been evaluated in dense traffic", "claim_type": "unexplored_problem", "generated_keywords": ["barrier certificates", "dense traffic", "scalability"]},
        {"id": "c2", "claim_text": "No existing methods apply decentralized barrier certificates in urban scenarios", "claim_type": "missing_methodology", "generated_keywords": ["decentralized barrier", "urban driving"]},
    ]
    queries = generator.generate_queries_for_claims(
        candidate_gap_id="gap-ce-test-1",
        gap_title="Scalability of Multi-Agent Barrier Functions",
        claims=claims,
        databases=["openalex", "semantic_scholar"],
    )

    assert len(queries) >= 4
    query_types = {q["query_type"] for q in queries}
    assert "direct_counter" in query_types
    for q in queries:
        assert len(q["query_text"]) > 5
        assert "search_rationale" in q
        assert "source_database" in q


def test_relevance_assessor_enforces_evidence_hierarchy():
    """Verifies relevance assessment categorizes into tiers and enforces full-text vs abstract levels."""
    assessor = CounterevidenceRelevanceAssessor()
    gap = CandidateResearchGap(
        id="gap-eval-1",
        title="Scalability of Multi-Agent Barrier Functions in Dense Urban Driving",
        description="Barrier certificates fail to scale beyond 10 vehicles in dense traffic.",
    )

    # Case 1: Paper with full text matching gap claim directly
    paper_fulltext = Paper(
        id="p-ft-1",
        request_id="req-ce-test-1",
        title="Decentralized Barrier Functions for Scalable Multi-Robot Navigation in Dense Traffic",
        abstract="We demonstrate scalability up to 100 autonomous agents in dense traffic navigation.",
    )
    fulltext_doc = FulltextDocument(
        id="ftd-1",
        paper_id="p-ft-1",
        extraction_status="success",
        extracted_sections=[
            {"heading": "4. Experimental Results", "text": "We evaluate our decentralized barrier certificates with up to 120 interacting vehicles in dense urban intersection simulation, disproving previous scalability limits.", "page_number": 7}
        ],
    )
    res_fulltext = assessor.assess_paper_against_gap(paper_fulltext, gap, fulltext_doc=fulltext_doc)
    assert res_fulltext["relevance_classification"] in ("direct_counterevidence", "partial_counterevidence")
    assert res_fulltext["evidence_level"] == "level_1_fulltext_passage"

    # Case 2: Abstract-only paper (cannot claim full-text verification)
    paper_abstract = Paper(
        id="p-abs-1",
        request_id="req-ce-test-1",
        title="Scalable Control Barrier Functions for Swarm Systems",
        abstract="We propose scalable control barrier functions for large swarms with 50 robots.",
    )
    res_abstract = assessor.assess_paper_against_gap(paper_abstract, gap, fulltext_doc=None)
    assert res_abstract["evidence_level"] in ("level_2_abstract_supported", "level_4_metadata_only")

    # Case 3: Completely irrelevant paper
    paper_irrel = Paper(
        id="p-irr-1",
        request_id="req-ce-test-1",
        title="Deep Learning for Plant Pathology Classification",
        abstract="We use Convolutional Neural Networks to classify tomato leaf disease images.",
    )
    res_irrel = assessor.assess_paper_against_gap(paper_irrel, gap, fulltext_doc=None)
    assert res_irrel["relevance_classification"] == "not_relevant"


def test_counterevidence_rest_apis_and_lifecycle():
    """Verifies HTTP endpoints for search execution, query retrieval, assessments, and reviews."""
    db = TestingSessionLocal()

    # 1. Mock retrieval execute_query
    p_mock = Paper(
        id="p-mock-ce-1",
        request_id="req-ce-test-1",
        title="Decentralized Control Barrier Functions for Dense Traffic",
        normalized_title="decentralized control barrier functions for dense traffic",
        authors=["Bob Vance"],
        publication_year=2023,
        venue="IEEE Transactions on Robotics",
        doi="10.1000/new-counter-1",
        abstract="We evaluate decentralized barrier functions with 50 autonomous vehicles in dense urban grids.",
    )

    async def mock_exec_query(query_model, research_request_id, limit=10):
        return [(p_mock, True)]

    with patch.object(
        CounterevidenceRetrievalService,
        "execute_query",
        side_effect=mock_exec_query,
    ):
        res = client.post(
            "/api/counterevidence/gaps/gap-ce-test-1/search",
            json={"max_queries": 4, "max_results_per_query": 3, "download_fulltext": False},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["candidate_gap_id"] == "gap-ce-test-1"
        assert data["total_retrieved"] >= 0

    # 2. Get decomposed claims
    res_claims = client.get("/api/counterevidence/gaps/gap-ce-test-1/claims")
    assert res_claims.status_code == 200
    claims_list = res_claims.json()
    assert len(claims_list) >= 3

    # 3. Get generated queries
    res_queries = client.get("/api/counterevidence/gaps/gap-ce-test-1/queries")
    assert res_queries.status_code == 200
    queries_list = res_queries.json()
    assert len(queries_list) >= 3

    # 4. Get publications
    res_pubs = client.get("/api/counterevidence/gaps/gap-ce-test-1/publications")
    assert res_pubs.status_code == 200

    # 5. Get assessments
    res_asmts = client.get("/api/counterevidence/gaps/gap-ce-test-1/assessments")
    assert res_asmts.status_code == 200
    asmts_list = res_asmts.json()
    if len(asmts_list) > 0:
        assessment_id = asmts_list[0]["id"]

        # 6. Submit human review audit
        res_review = client.post(
            f"/api/counterevidence/assessments/{assessment_id}/review",
            json={
                "override_relevance": "partial_counterevidence",
                "reviewer_notes": "Simulation only, lacks real-world physical vehicle experiments.",
            },
        )
        assert res_review.status_code == 200
        reviewed_data = res_review.json()
        assert reviewed_data["human_review_status"] in ("confirmed", "human_reviewed")
        assert reviewed_data["relevance_classification"] == "partial_counterevidence"

    # 7. Rebuild profile
    res_rebuild = client.post("/api/counterevidence/gaps/gap-ce-test-1/profile/rebuild")
    assert res_rebuild.status_code == 200
    rebuilt_prof = res_rebuild.json()
    assert rebuilt_prof["candidate_gap_id"] == "gap-ce-test-1"

    # 8. Get evidence passages
    res_evd = client.get("/api/counterevidence/gaps/gap-ce-test-1/evidence")
    assert res_evd.status_code == 200

    db.close()


def test_counterevidence_mcp_tools():
    """Verifies registered MCP tools for Phase 5."""
    db = TestingSessionLocal()
    try:
        # 1. MCP tool generate queries
        queries_result = tool_generate_counterevidence_queries("gap-ce-test-1", db=db)
        assert "error" not in queries_result
        assert "decomposed_claims" in queries_result
        assert len(queries_result["decomposed_claims"]) >= 3
        assert "generated_queries" in queries_result

        # 2. MCP tool get publications
        pubs_result = tool_get_counterevidence_publications("gap-ce-test-1", db=db)
        assert isinstance(pubs_result, list)

        # 3. MCP tool extract evidence
        evd_result = tool_extract_counterevidence_evidence("gap-ce-test-1", db=db)
        assert isinstance(evd_result, list)

        # 4. MCP tool assess relevance
        relevance_result = tool_assess_counterevidence_relevance("gap-ce-test-1", "p-ce-existing-1", db=db)
        assert "error" not in relevance_result
        assert "relevance_classification" in relevance_result
        assert "evidence_level" in relevance_result
    finally:
        db.close()
