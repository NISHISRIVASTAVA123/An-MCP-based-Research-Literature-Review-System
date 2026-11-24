"""Unit Tests for Entity Normalization and Synonym Resolution (Phase 3)."""

import pytest
from backend.app.services.graph.normalization_service import EntityNormalizationService
from backend.tests.conftest import TestingSessionLocal


def test_method_normalization():
    service = EntityNormalizationService()

    # CNN aliases
    c1, r1, conf1, v1 = service.normalize_entity("CNN", "method")
    c2, r2, conf2, v2 = service.normalize_entity("Convolutional Neural Network", "method")
    c3, r3, conf3, v3 = service.normalize_entity("convolutional neural networks", "method")
    c4, r4, conf4, v4 = service.normalize_entity("ConvNet", "method")

    assert c1 == "Convolutional Neural Network"
    assert c2 == "Convolutional Neural Network"
    assert c3 == "Convolutional Neural Network"
    assert c4 == "Convolutional Neural Network"
    assert r1 == "exact_rule"
    assert conf1 == 1.0

    # BERT / Transformer / SHAP / GNN
    b, _, _, _ = service.normalize_entity("BERT", "method")
    t, _, _, _ = service.normalize_entity("transformer architecture", "method")
    s, _, _, _ = service.normalize_entity("SHAP", "method")
    g, _, _, _ = service.normalize_entity("graph neural networks", "method")

    assert b == "BERT"
    assert t == "Transformer"
    assert s == "SHAP"
    assert g == "Graph Neural Network"


def test_metric_normalization():
    service = EntityNormalizationService()

    m1, _, _, _ = service.normalize_entity("f1-score", "metric")
    m2, _, _, _ = service.normalize_entity("F-measure", "metric")
    m3, _, _, _ = service.normalize_entity("F1", "metric")
    m4, _, _, _ = service.normalize_entity("accuracy", "metric")
    m5, _, _, _ = service.normalize_entity("roc-auc", "metric")

    assert m1 == "F1-Score"
    assert m2 == "F1-Score"
    assert m3 == "F1-Score"
    assert m4 == "Accuracy"
    assert m5 == "AUC-ROC"


def test_dataset_conservative_resolution():
    service = EntityNormalizationService()

    d1, _, _, _ = service.normalize_entity("liar dataset", "dataset")
    d2, _, _, _ = service.normalize_entity("FakeNewsNet", "dataset")

    assert d1 == "LIAR"
    assert d2 == "FakeNewsNet"

    # Distinct datasets with different names are NOT merged
    assert d1 != d2


def test_manual_resolution_override():
    db = TestingSessionLocal()
    try:
        service = EntityNormalizationService(db)
        canon, method, conf, verified = service.register_manual_resolution(
            raw_string="Deep Attentive Graph Net",
            canonical_name="Graph Attention Network (GAT)",
            entity_type="method",
        )

        assert canon == "Graph Attention Network (GAT)"
        assert method == "manual_user_override"
        assert conf == 1.0
        assert verified is True

        # Verify subsequent lookup resolves to manual override
        res_canon, res_method, _, _ = service.normalize_entity("Deep Attentive Graph Net", "method")
        assert res_canon == "Graph Attention Network (GAT)"
        assert res_method == "manual_user_override"
    finally:
        db.close()
