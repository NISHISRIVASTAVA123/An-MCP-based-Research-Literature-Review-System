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


def test_pdf_upload_endpoint():
    import uuid
    from backend.tests.test_pdf_processing import create_synthetic_scientific_pdf

    p_id = f"upload-p-{uuid.uuid4().hex[:8]}"
    db = TestingSessionLocal()
    try:
        req = ResearchRequest(topic="AI", objective="Explainable models", domain="CS", start_year=2020, end_year=2024)
        db.add(req)
        db.commit()

        paper = Paper(
            id=p_id,
            request_id=req.id,
            title="Synthetic PDF Paper for Upload Test",
            normalized_title="synthetic pdf paper for upload test",
            publication_year=2023,
        )
        db.add(paper)
        db.commit()
    finally:
        db.close()

    pdf_bytes = create_synthetic_scientific_pdf()
    files = {"file": ("paper.pdf", pdf_bytes, "application/pdf")}
    res = client.post(f"/api/papers/{p_id}/upload-pdf", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["paper_id"] == p_id
    assert data["page_count"] == 2
    assert data["extraction_status"] == "success"

    # Verify document-status endpoint reflects the uploaded document
    res_status = client.get(f"/api/papers/{p_id}/document-status")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data["has_document"] is True
    assert status_data["page_count"] == 2
    assert len(status_data["section_headings"]) >= 2


@pytest.mark.asyncio
async def test_phase2_mcp_tools():
    from backend.app.services.mcp.tools import tool_screen_paper_content, tool_extract_paper_evidence

    # 1. Test MCP screening tool
    screen_res = tool_screen_paper_content(
        title="Towards Explainable Misinformation Detection using SHAP",
        abstract="We present an explainable AI framework for detecting misinformation using SHAP.",
        topic="Explainable AI for Misinformation Detection",
        objective="Analyze explanation mechanisms in misinformation detection",
        start_year=2020,
        end_year=2026,
        publication_year=2023,
    )
    assert screen_res["decision"] == "included"
    assert screen_res["confidence_score"] >= 0.70

    # 2. Test MCP evidence extraction tool
    ext_res = await tool_extract_paper_evidence(
        paper_id="mcp-test-1",
        title="Towards Explainable Misinformation Detection using SHAP",
        abstract="In this paper we propose an explainable framework on the LIAR dataset. It achieves an accuracy of 91.2%.",
        raw_text=None,
    )
    assert ext_res["paper_id"] == "mcp-test-1"
    assert any("LIAR" in d["dataset_name"] for d in ext_res["datasets"])
    assert any(m["metric_name"] == "Accuracy" for m in ext_res["evaluation_metrics"])

