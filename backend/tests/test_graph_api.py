"""Integration and API Endpoint Tests for Evidence Graph and MCP Tools (Phase 3)."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.tests.conftest import TestingSessionLocal
from backend.tests.test_graph_construction import create_test_research_context
from backend.app.services.persistence.graph_repository import GraphRepository
from backend.app.services.mcp.tools import (
    tool_build_evidence_graph,
    tool_synchronize_evidence_graph,
    tool_get_graph_statistics,
    tool_query_papers_by_method,
    tool_query_papers_by_dataset,
    tool_query_papers_by_model,
    tool_get_paper_evidence_graph,
    tool_get_claim_evidence,
    tool_get_evidence_provenance,
    tool_get_graph_validation_report,
    tool_find_shared_methods,
    tool_find_shared_datasets,
)

client = TestClient(app)


def test_evidence_graph_api_endpoints():
    db = TestingSessionLocal()
    try:
        req_id, p1_id, p2_id, pas1_id = create_test_research_context(db)
    finally:
        db.close()

    # 1. Trigger Full Graph Build via API
    build_res = client.post(f"/api/research-requests/{req_id}/evidence-graph/build")
    assert build_res.status_code in [200, 201]
    build_data = build_res.json()
    assert build_data["status"] == "completed"
    assert build_data["total_nodes"] > 5
    assert build_data["total_edges"] > 3
    assert build_data["papers_processed"] == 1  # Only included paper

    # 2. Get Full Evidence Graph
    graph_res = client.get(f"/api/research-requests/{req_id}/evidence-graph")
    assert graph_res.status_code == 200
    graph_data = graph_res.json()
    assert graph_data["request_id"] == req_id
    assert len(graph_data["nodes"]) > 5
    assert len(graph_data["edges"]) > 3
    assert "statistics" in graph_data

    # Find a CLAIM node and a METHOD node for detailed lookups
    claim_nodes = [n for n in graph_data["nodes"] if n["node_type"] == "CLAIM"]
    method_nodes = [n for n in graph_data["nodes"] if n["node_type"] == "METHOD"]
    assert len(claim_nodes) >= 1
    assert len(method_nodes) >= 1
    claim_id = claim_nodes[0]["id"]
    method_node_id = method_nodes[0]["id"]

    # 3. Filtered Graph Query by node_types
    filtered_res = client.get(f"/api/research-requests/{req_id}/evidence-graph?node_types=METHOD,DATASET")
    assert filtered_res.status_code == 200
    filtered_data = filtered_res.json()
    node_types_returned = {n["node_type"] for n in filtered_data["nodes"]}
    assert node_types_returned.issubset({"METHOD", "DATASET"})

    # 4. Get Statistics Endpoint
    stats_res = client.get(f"/api/research-requests/{req_id}/evidence-graph/statistics")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_nodes"] == len(graph_data["nodes"])
    assert "nodes_by_type" in stats
    assert stats["nodes_by_type"].get("PAPER", 0) >= 1

    # 5. Get Validation Audit Report Endpoint
    val_res = client.get(f"/api/research-requests/{req_id}/evidence-graph/validation")
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert val_data["integrity_status"] in ["valid", "warning"]
    assert val_data["total_nodes"] > 0
    assert val_data["claims_with_evidence"] >= 1

    # 6. Get Single Node Details Endpoint
    node_res = client.get(f"/api/evidence-graph/nodes/{method_node_id}")
    assert node_res.status_code == 200
    node_detail = node_res.json()
    assert node_detail["id"] == method_node_id
    assert node_detail["node_type"] == "METHOD"

    # 7. Get Claim Provenance Chain Endpoint
    prov_res = client.get(f"/api/evidence-graph/claims/{claim_id}/provenance")
    assert prov_res.status_code == 200
    prov_data = prov_res.json()
    assert prov_data["claim_id"] == claim_id
    assert prov_data["paper_id"] == p1_id
    assert prov_data["has_evidence_passage"] is True
    assert prov_data["exact_passage"] is not None

    # 8. Query Endpoint Tests
    # Query: papers_by_method
    q_method = client.get(
        f"/api/research-requests/{req_id}/evidence-graph/query",
        params={"query_type": "papers_by_method", "param_a": "SHAP"},
    )
    assert q_method.status_code == 200
    assert len(q_method.json()["results"]) >= 1

    # Query: papers_by_dataset
    q_dataset = client.get(
        f"/api/research-requests/{req_id}/evidence-graph/query",
        params={"query_type": "papers_by_dataset", "param_a": "LIAR"},
    )
    assert q_dataset.status_code == 200
    assert len(q_dataset.json()["results"]) >= 1

    # Query: findings_by_paper
    q_findings = client.get(
        f"/api/research-requests/{req_id}/evidence-graph/query",
        params={"query_type": "findings_by_paper", "param_a": p1_id},
    )
    assert q_findings.status_code == 200
    assert len(q_findings.json()["results"]) >= 1

    # Query: cross_paper_limitations
    q_limits = client.get(
        f"/api/research-requests/{req_id}/evidence-graph/query",
        params={"query_type": "cross_paper_limitations", "param_a": "author_reported"},
    )
    assert q_limits.status_code == 200
    assert len(q_limits.json()["results"]) >= 1

    # Query: unsupported_claims
    q_unsupported = client.get(
        f"/api/research-requests/{req_id}/evidence-graph/query",
        params={"query_type": "unsupported_claims"},
    )
    assert q_unsupported.status_code == 200

    # Query: paper_subgraph
    q_subgraph = client.get(
        f"/api/research-requests/{req_id}/evidence-graph/query",
        params={"query_type": "paper_subgraph", "param_a": p1_id},
    )
    assert q_subgraph.status_code == 200
    assert len(q_subgraph.json()["results"]["nodes"]) >= 3

    # Query: shared_methods
    q_shared_m = client.get(
        f"/api/research-requests/{req_id}/evidence-graph/query",
        params={"query_type": "shared_methods", "param_a": p1_id, "param_b": p1_id},
    )
    assert q_shared_m.status_code == 200
    assert "SHAP" in q_shared_m.json()["results"]

    # Query: shared_datasets
    q_shared_d = client.get(
        f"/api/research-requests/{req_id}/evidence-graph/query",
        params={"query_type": "shared_datasets", "param_a": p1_id, "param_b": p1_id},
    )
    assert q_shared_d.status_code == 200
    assert "LIAR" in q_shared_d.json()["results"]

    # 9. Entity Resolution Alias Override Endpoint
    alias_res = client.post(
        "/api/evidence-graph/entity-resolution",
        json={
            "entity_type": "METHOD",
            "surface_form": "lime feature weightings",
            "canonical_name": "LIME",
            "override_notes": "Expert synonym resolution for LIME",
        },
    )
    assert alias_res.status_code == 200
    assert alias_res.json()["normalized_name"] == "LIME"
    assert alias_res.json()["resolution_method"] == "manual_user_override"

    # 10. Synchronize Endpoint
    sync_res = client.post(f"/api/research-requests/{req_id}/evidence-graph/synchronize")
    assert sync_res.status_code == 200
    sync_data = sync_res.json()
    assert sync_data["status"] in ["completed", "synchronized"]
    assert sync_data["run_number"] >= 2


def test_mcp_phase3_tools_integration():
    """Validates the 12 Phase 3 MCP tool functions for agent invocation."""
    db = TestingSessionLocal()
    try:
        req_id, p1_id, p2_id, pas1_id = create_test_research_context(db)

        # 1. tool_build_evidence_graph
        b_res = tool_build_evidence_graph(req_id, db=db)
        assert b_res["status"] == "completed"
        assert b_res["total_nodes"] > 5

        # 2. tool_synchronize_evidence_graph
        s_res = tool_synchronize_evidence_graph(req_id, db=db)
        assert s_res["status"] == "synchronized"

        # 3. tool_get_graph_statistics
        stats = tool_get_graph_statistics(req_id, db=db)
        assert stats["total_nodes"] > 5
        assert "METHOD" in stats["nodes_by_type"]

        # 4. tool_query_papers_by_method
        papers_shap = tool_query_papers_by_method(req_id, "SHAP", db=db)
        assert len(papers_shap) >= 1
        assert papers_shap[0]["paper_id"] == p1_id

        # 5. tool_query_papers_by_dataset
        papers_liar = tool_query_papers_by_dataset(req_id, "LIAR", db=db)
        assert len(papers_liar) >= 1
        assert papers_liar[0]["paper_id"] == p1_id

        # 6. tool_query_papers_by_model
        papers_bert = tool_query_papers_by_model(req_id, "BERT", db=db)
        assert len(papers_bert) >= 1

        # 7. tool_get_paper_evidence_graph
        p_graph = tool_get_paper_evidence_graph(p1_id, db=db)
        assert p_graph["nodes_count"] >= 3

        # 8. Retrieve claim id for claim-specific tools
        repo = GraphRepository(db)
        claims = repo.get_nodes_by_request(req_id, node_type="CLAIM")
        assert len(claims) >= 1
        cid = claims[0].id

        # 8. tool_get_claim_evidence
        c_ev = tool_get_claim_evidence(cid, db=db)
        assert len(c_ev) >= 1

        # 9. tool_get_evidence_provenance
        prov = tool_get_evidence_provenance(cid, db=db)
        assert prov["claim_id"] == cid
        assert prov["paper_id"] == p1_id
        assert prov["has_evidence_passage"] is True
        assert prov["exact_passage"] is not None

        # 10. tool_get_graph_validation_report
        val = tool_get_graph_validation_report(req_id, db=db)
        assert val["integrity_status"] in ["valid", "warning"]

        # 11. tool_find_shared_methods
        shared_m = tool_find_shared_methods(p1_id, p1_id, db=db)
        assert "SHAP" in shared_m

        # 12. tool_find_shared_datasets
        shared_d = tool_find_shared_datasets(p1_id, p1_id, db=db)
        assert "LIAR" in shared_d

    finally:
        db.close()
