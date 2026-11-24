"""Unit and Service Tests for Graph Traversal and Provenance Queries (Phase 3)."""

import pytest
from backend.tests.conftest import TestingSessionLocal
from backend.tests.test_graph_construction import create_test_research_context
from backend.app.services.graph.graph_builder import EvidenceGraphBuilder
from backend.app.services.graph.graph_query_service import EvidenceGraphQueryService
from backend.app.models.paper import Paper
from backend.app.models.screening import ScreeningDecision, ScreeningRun
from backend.app.models.evidence import ExtractionRun, EvidenceRecord


def test_graph_queries_and_provenance_tracing():
    db = TestingSessionLocal()
    try:
        req_id, p1_id, _, pas1_id = create_test_research_context(db)
        builder = EvidenceGraphBuilder(db)
        builder.build_graph(req_id)

        query_service = EvidenceGraphQueryService(db)

        # 1. Query papers by method
        papers_with_shap = query_service.find_papers_by_method(req_id, "SHAP")
        assert len(papers_with_shap) >= 1
        assert papers_with_shap[0]["paper_id"] == p1_id

        # 2. Query papers by dataset
        papers_with_liar = query_service.find_papers_by_dataset(req_id, "LIAR")
        assert len(papers_with_liar) >= 1
        assert papers_with_liar[0]["paper_id"] == p1_id

        # 3. Query papers by model
        papers_with_bert = query_service.find_papers_by_model(req_id, "BERT")
        assert len(papers_with_bert) >= 1

        # 4. Findings by paper
        findings = query_service.find_findings_by_paper(p1_id)
        assert len(findings) >= 1
        assert "SHAP feature attributions" in findings[0]["statement"]

        # 5. Cross-paper limitations
        limitations = query_service.find_limitations_cross_papers(req_id, "author_reported")
        assert len(limitations) >= 1
        assert "English" in limitations[0]["limitation_text"]

        # 6. Passages supporting claim
        repo = builder.graph_repo
        claim_nodes = repo.get_nodes_by_request(req_id, node_type="CLAIM")
        assert len(claim_nodes) >= 1
        claim_id = claim_nodes[0].id

        passages = query_service.find_passages_supporting_claim(claim_id)
        assert len(passages) >= 1
        assert "SHAP feature attributions improve" in passages[0]["exact_passage"]

        # 7. End-to-end Claim Provenance Chain
        chain = query_service.get_claim_provenance_chain(claim_id)
        assert chain.claim_id == claim_id
        assert chain.paper_id == p1_id
        assert chain.has_evidence_passage is True
        assert chain.page_number == 1
        assert chain.section_heading == "Abstract"
        assert chain.is_provenance_complete is True
    finally:
        db.close()


def test_shared_methods_and_datasets_between_papers():
    db = TestingSessionLocal()
    try:
        req_id, p1_id, _, _ = create_test_research_context(db)

        # Add a second included paper that also uses SHAP and LIAR
        p3 = Paper(
            id=f"p3-shared-test",
            request_id=req_id,
            title="Second Study on LIAR with SHAP Interpretability",
            normalized_title="second study on liar with shap interpretability",
            authors=["David Brown"],
            publication_year=2023,
            has_abstract=True,
        )
        db.add(p3)

        srun = db.query(ScreeningRun).filter(ScreeningRun.request_id == req_id).first()
        dec3 = ScreeningDecision(
            id=f"dec3-shared",
            run_id=srun.id,
            paper_id=p3.id,
            decision="included",
            stage="metadata_abstract",
            reason="Relevant.",
        )
        db.add(dec3)

        ext_run = ExtractionRun(
            id="ext-p3",
            paper_id=p3.id,
            source_scope="abstract_only",
            extractor_backend="rule_based",
            status="completed",
        )
        db.add(ext_run)

        ev3 = EvidenceRecord(
            id="ev-p3",
            extraction_run_id=ext_run.id,
            paper_id=p3.id,
            methodology=[{"approach_name": "SHAP"}],
            datasets=[{"dataset_name": "LIAR"}],
            evaluation_metrics=[],
            findings=[],
            limitations=[],
            future_work=[],
        )
        db.add(ev3)
        db.commit()

        builder = EvidenceGraphBuilder(db)
        builder.build_graph(req_id)

        query_service = EvidenceGraphQueryService(db)

        shared_methods = query_service.find_shared_methods_between_papers(p1_id, p3.id)
        shared_datasets = query_service.find_shared_datasets_between_papers(p1_id, p3.id)

        assert "SHAP" in shared_methods
        assert "LIAR" in shared_datasets
    finally:
        db.close()
