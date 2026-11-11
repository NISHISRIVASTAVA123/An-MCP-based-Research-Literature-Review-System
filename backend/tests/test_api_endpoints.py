"""Integration tests for FastAPI REST API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import app
from backend.app.models.base import Base
from backend.app.services.persistence.database import get_db

# Create in-memory SQLite database specifically for test isolation
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


client = TestClient(app)


def test_root_and_health_endpoints():
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"


def test_create_and_retrieve_research_request():
    payload = {
        "topic": "Explainable AI for Fake News Detection",
        "objective": "Identify limitations in existing explainable fake news models",
        "domain": "Artificial Intelligence",
        "start_year": 2018,
        "end_year": 2024,
        "max_papers": 20,
        "citation_style": "IEEE",
        "research_questions": [
            "What explanation mechanisms are most prevalent?",
            "Are existing explanations robust against adversarial noise?"
        ],
        "inclusion_criteria": ["Peer-reviewed"],
        "exclusion_criteria": ["Editorials"],
        "preferred_databases": ["openalex", "semantic_scholar", "crossref", "arxiv"],
    }

    # 1. Create Request
    create_res = client.post("/api/research-requests", json=payload)
    assert create_res.status_code == 201
    created_data = create_res.json()
    req_id = created_data["id"]
    assert created_data["topic"] == payload["topic"]
    assert len(created_data["questions"]) == 2

    # 2. Retrieve Request
    get_res = client.get(f"/api/research-requests/{req_id}")
    assert get_res.status_code == 200
    retrieved = get_res.json()
    assert retrieved["id"] == req_id
    assert retrieved["has_strategy"] is False

    # 3. List Requests
    list_res = client.get("/api/research-requests")
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) == 1
    assert items[0]["id"] == req_id


def test_generate_and_update_search_strategy():
    # 1. Create base request
    create_res = client.post(
        "/api/research-requests",
        json={
            "topic": "Neural Network Hallucination",
            "objective": "Mitigate factual hallucinations in LLM generations",
            "domain": "NLP",
            "start_year": 2021,
            "end_year": 2024,
            "research_questions": ["How is hallucination measured?"],
        },
    )
    req_id = create_res.json()["id"]

    # 2. Generate Strategy
    strat_res = client.post(f"/api/research-requests/{req_id}/strategy")
    assert strat_res.status_code == 201
    strat_data = strat_res.json()
    assert len(strat_data["concepts"]) > 0
    assert len(strat_data["queries"]) >= 1

    # 3. Retrieve Strategy
    get_strat = client.get(f"/api/research-requests/{req_id}/strategy")
    assert get_strat.status_code == 200
    assert get_strat.json()["id"] == strat_data["id"]

    # 4. Update Strategy Queries (User customization)
    update_payload = {
        "queries": [
            {
                "target_database": "arxiv",
                "query_text": 'all:"hallucination" AND all:"mitigation"',
                "is_enabled": True,
                "order_index": 0,
            }
        ]
    }
    put_strat = client.put(f"/api/research-requests/{req_id}/strategy", json=update_payload)
    assert put_strat.status_code == 200
    updated_strat = put_strat.json()
    assert len(updated_strat["queries"]) == 1
    assert updated_strat["queries"][0]["target_database"] == "arxiv"


def test_export_endpoints_csv_and_json():
    # Create request
    create_res = client.post(
        "/api/research-requests",
        json={
            "topic": "Counterevidence Retrieval in NLP",
            "objective": "Systematic evaluation of refuting claims",
            "domain": "Artificial Intelligence",
            "start_year": 2020,
            "end_year": 2024,
        },
    )
    req_id = create_res.json()["id"]

    # CSV Export
    csv_res = client.get(f"/api/research-requests/{req_id}/export?format=csv")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert "Paper ID,Title,Authors" in csv_res.text

    # JSON Export
    json_res = client.get(f"/api/research-requests/{req_id}/export?format=json")
    assert json_res.status_code == 200
    assert "application/json" in json_res.headers["content-type"]
    data = json_res.json()
    assert data["request_id"] == req_id
    assert "papers" in data


def test_mcp_tools_directory_endpoint():
    res = client.get("/api/mcp/tools")
    assert res.status_code == 200
    data = res.json()
    assert "tools" in data
    tool_names = [t["name"] for t in data["tools"]]
    assert "search_openalex" in tool_names
    assert "search_semantic_scholar" in tool_names
    assert "search_crossref" in tool_names
    assert "search_arxiv" in tool_names
    assert "retrieve_paper_by_doi" in tool_names
    assert "generate_academic_search_strategy" in tool_names

