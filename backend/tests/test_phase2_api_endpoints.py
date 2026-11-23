"""Integration Tests for Phase 2 API Endpoints."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models.paper import Paper
from backend.app.models.research_request import ResearchRequest
from backend.tests.conftest import TestingSessionLocal

client = TestClient(app)


def test_screening_and_evidence_api_workflow():
    import uuid
    uid = uuid.uuid4().hex[:8]
    p1_id = f"api-p1-{uid}"
    p2_id = f"api-p2-{uid}"

    db = TestingSessionLocal()
    try:
        # Create a research request
        req = ResearchRequest(
            topic="Explainable Misinformation Detection",
            objective="Analyze explainable AI methods",
            domain="Computer Science",
            start_year=2019,
            end_year=2026,
        )
        db.add(req)
        db.commit()

        # Add 2 papers
        p1 = Paper(
            id=p1_id,
            request_id=req.id,
            title="Explainable Misinformation Detection via Feature Attributions",
            normalized_title="explainable misinformation detection via feature attributions",
            authors=["Researcher One"],
            abstract="In this work we study explainable misinformation detection models using SHAP. Our method achieves an accuracy of 90.5%. However, computational cost is a limitation.",
            publication_year=2022,
            keywords=["XAI", "misinformation"],
        )
        p2 = Paper(
            id=p2_id,
            request_id=req.id,
            title="Thermodynamic Analysis of Supercritical Carbon Dioxide Turbines",
            normalized_title="thermodynamic analysis of supercritical carbon dioxide turbines",
            authors=["Researcher Two"],
            abstract="Efficiency simulations of closed-loop Brayton cycle power systems.",
            publication_year=2020,
            keywords=["turbines", "energy"],
        )
        db.add_all([p1, p2])
        db.commit()
        req_id = req.id
    finally:
        db.close()

    # 1. Execute Screening Run
    res = client.post(f"/api/research-requests/{req_id}/screening-runs")
    assert res.status_code == 201
    run_data = res.json()
    assert run_data["total_papers"] == 2
    assert run_data["included_count"] == 1
    assert run_data["excluded_count"] == 1

    # 2. Get Screening Results
    res_dec = client.get(f"/api/research-requests/{req_id}/screening-results")
    assert res_dec.status_code == 200
    decisions = res_dec.json()
    assert len(decisions) == 2

    # 3. Test Human Override
    override_payload = {
        "decision": "included",
        "reviewer_notes": "Reviewed and included as a cross-domain baseline comparator.",
    }
    res_ov = client.put(f"/api/papers/{p2_id}/screening-decision", json=override_payload)
    assert res_ov.status_code == 200
    ov_data = res_ov.json()
    assert ov_data["decision"] == "included"
    assert ov_data["is_human_override"] is True
    assert ov_data["original_decision"] == "excluded"

    # 4. Check Document Status (Before Upload)
    res_doc = client.get(f"/api/papers/{p1_id}/document-status")
    assert res_doc.status_code == 200
    assert res_doc.json()["has_document"] is False

    # 5. Extract Evidence (force mock backend for reliable deterministic test)
    res_ext = client.post(f"/api/papers/{p1_id}/extract-evidence?backend=mock")
    assert res_ext.status_code == 201
    ext_data = res_ext.json()
    assert ext_data["paper_id"] == p1_id
    assert "research_objective" in ext_data
    assert len(ext_data["passages"]) >= 4

    # 6. Retrieve Extracted Evidence
    res_get_ext = client.get(f"/api/papers/{p1_id}/evidence")
    assert res_get_ext.status_code == 200
    assert res_get_ext.json()["paper_id"] == p1_id

    # 7. Update an Evidence Passage
    passages = res_get_ext.json()["passages"]
    passage_id = passages[0]["id"]
    update_payload = {
        "verification_status": "user_verified",
        "user_notes": "Verified by researcher.",
    }
    res_up = client.put(f"/api/evidence/passages/{passage_id}", json=update_payload)
    assert res_up.status_code == 200
    assert res_up.json()["verification_status"] == "user_verified"
