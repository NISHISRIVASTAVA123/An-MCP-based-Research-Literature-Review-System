"""Controlled Entity Normalization and Canonical Resolution Service (Phase 3).

Standardizes methods, models, datasets, metrics, and scientific concepts
without aggressive lossy merging. Preserves original author-reported text
and supports human-in-the-loop overrides.
"""

import re
from typing import Dict, Any, Tuple, Optional, List
from sqlalchemy.orm import Session
from backend.app.services.persistence.graph_repository import GraphRepository
from backend.app.core.logging import logger

METHOD_DICTIONARY: Dict[str, str] = {
    "cnn": "Convolutional Neural Network",
    "convolutional neural network": "Convolutional Neural Network",
    "convolutional neural networks": "Convolutional Neural Network",
    "convnet": "Convolutional Neural Network",
    "bert": "BERT",
    "bidirectional encoder representations from transformers": "BERT",
    "roberta": "RoBERTa",
    "transformer": "Transformer",
    "transformers": "Transformer",
    "transformer architecture": "Transformer",
    "shap": "SHAP",
    "shapley additive explanations": "SHAP",
    "lime": "LIME",
    "local interpretable model-agnostic explanations": "LIME",
    "gnn": "Graph Neural Network",
    "graph neural network": "Graph Neural Network",
    "graph neural networks": "Graph Neural Network",
    "svm": "Support Vector Machine",
    "support vector machine": "Support Vector Machine",
    "support vector machines": "Support Vector Machine",
    "random forest": "Random Forest",
    "random forests": "Random Forest",
    "rf": "Random Forest",
    "xgboost": "XGBoost",
    "federated learning": "Federated Learning",
    "transfer learning": "Transfer Learning",
    "contrastive learning": "Contrastive Learning",
    "adversarial training": "Adversarial Training",
    "reinforcement learning": "Reinforcement Learning",
    "rl": "Reinforcement Learning",
    "attention mechanism": "Attention Mechanism",
    "self-attention": "Attention Mechanism",
    "explainable ai": "Explainable AI",
    "xai": "Explainable AI",
    "interpretable ml": "Explainable AI",
    "retrieval-augmented generation": "Retrieval-Augmented Generation",
    "rag": "Retrieval-Augmented Generation",
}

MODEL_FAMILIES: Dict[str, str] = {
    "bert": "BERT",
    "roberta": "RoBERTa",
    "gpt": "GPT",
    "gpt-3": "GPT",
    "gpt-4": "GPT",
    "llama": "LLaMA",
    "llama-2": "LLaMA",
    "t5": "T5",
    "resnet": "ResNet",
    "vgg": "VGG",
}

METRIC_DICTIONARY: Dict[str, str] = {
    "f1": "F1-Score",
    "f-score": "F1-Score",
    "f1-score": "F1-Score",
    "f1 score": "F1-Score",
    "f_score": "F1-Score",
    "f-measure": "F1-Score",
    "macro-f1": "Macro-F1",
    "micro-f1": "Micro-F1",
    "acc": "Accuracy",
    "accuracy": "Accuracy",
    "top-1 accuracy": "Accuracy",
    "precision": "Precision",
    "prec": "Precision",
    "recall": "Recall",
    "rec": "Recall",
    "auc": "AUC-ROC",
    "roc-auc": "AUC-ROC",
    "roc_auc": "AUC-ROC",
    "auc-roc": "AUC-ROC",
    "bleu": "BLEU",
    "bleu-4": "BLEU",
    "rouge": "ROUGE",
    "rouge-l": "ROUGE",
    "rmse": "RMSE",
    "mae": "MAE",
}

DATASET_DICTIONARY: Dict[str, str] = {
    "liar": "LIAR",
    "liar dataset": "LIAR",
    "fakenewsnet": "FakeNewsNet",
    "fake news net": "FakeNewsNet",
    "politifact": "PolitiFact",
    "gossipcop": "GossipCop",
    "fever": "FEVER",
    "coaid": "CoAID",
    "glue": "GLUE",
    "glue benchmark": "GLUE",
    "superglue": "SuperGLUE",
    "squad": "SQuAD",
    "squad 2.0": "SQuAD",
    "mimic-iii": "MIMIC-III",
    "pubmed": "PubMed",
    "arxiv": "arXiv",
}

# Normalized helper maps for robust space/hyphen/underscore insensitive lookup
_NORM_METHODS = {re.sub(r"[\s_\-]+", " ", k.lower()).strip(): v for k, v in METHOD_DICTIONARY.items()}
_NORM_MODELS = {re.sub(r"[\s_\-]+", " ", k.lower()).strip(): v for k, v in MODEL_FAMILIES.items()}
_NORM_METRICS = {re.sub(r"[\s_\-]+", " ", k.lower()).strip(): v for k, v in METRIC_DICTIONARY.items()}
_NORM_DATASETS = {re.sub(r"[\s_\-]+", " ", k.lower()).strip(): v for k, v in DATASET_DICTIONARY.items()}


class EntityNormalizationService:
    """Provides controlled entity normalization, synonym resolution, and alias tracking."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.repo = GraphRepository(db) if db else None

    def normalize_entity(
        self,
        raw_name: str,
        entity_type: str,
        request_id: Optional[str] = None,
    ) -> Tuple[str, str, float, bool]:
        """Normalizes an entity name using database aliases and curated dictionaries.

        Returns:
            Tuple of (canonical_name, resolution_method, confidence, is_verified)
        """
        if not raw_name or not raw_name.strip():
            return "Unknown", "empty_fallback", 0.0, False

        cleaned = raw_name.strip()
        lower_key = cleaned.lower()
        norm_key = re.sub(r"[\s_\-]+", " ", lower_key).strip()

        # 1. Check existing alias in database repository
        if self.repo:
            alias = self.repo.get_alias_by_raw(cleaned, entity_type.lower())
            if alias:
                return (
                    alias.normalized_name,
                    alias.resolution_method,
                    alias.confidence,
                    alias.is_verified,
                )

        # 2. Check curated domain dictionaries
        t_low = entity_type.lower()
        if t_low in ("method", "approach"):
            if norm_key in _NORM_METHODS:
                canon = _NORM_METHODS[norm_key]
                if self.repo:
                    self.repo.upsert_alias(cleaned, canon, "method", "exact_rule", 1.0, True, request_id)
                return canon, "exact_rule", 1.0, True

        elif t_low in ("model", "architecture"):
            if norm_key in _NORM_MODELS:
                canon = _NORM_MODELS[norm_key]
                if self.repo:
                    self.repo.upsert_alias(cleaned, canon, "model", "exact_rule", 1.0, True, request_id)
                return canon, "exact_rule", 1.0, True
            # Check method dictionary fallback for models (e.g. BERT/CNN)
            if norm_key in _NORM_METHODS:
                canon = _NORM_METHODS[norm_key]
                if self.repo:
                    self.repo.upsert_alias(cleaned, canon, "model", "exact_rule", 0.95, True, request_id)
                return canon, "exact_rule", 0.95, True

        elif t_low in ("metric", "evaluation_metric"):
            if norm_key in _NORM_METRICS:
                canon = _NORM_METRICS[norm_key]
                if self.repo:
                    self.repo.upsert_alias(cleaned, canon, "metric", "exact_rule", 1.0, True, request_id)
                return canon, "exact_rule", 1.0, True

        elif t_low == "dataset":
            if norm_key in _NORM_DATASETS:
                canon = _NORM_DATASETS[norm_key]
                if self.repo:
                    self.repo.upsert_alias(cleaned, canon, "dataset", "exact_rule", 1.0, True, request_id)
                return canon, "exact_rule", 1.0, True

        # 3. Deterministic formatting fallback (preserves casing for acronyms, title-cases others)
        canon = self._clean_canonical_string(cleaned)
        # Store unverified alias in DB for human audit
        if self.repo:
            self.repo.upsert_alias(
                cleaned, canon, t_low, "normalized_fallback", 0.70, False, request_id
            )
        return canon, "normalized_fallback", 0.70, False

    def register_manual_resolution(
        self,
        raw_string: str,
        canonical_name: str,
        entity_type: str,
        request_id: Optional[str] = None,
    ) -> Tuple[str, str, float, bool]:
        """Manually overrides or merges an entity alias with researcher verification."""
        if not self.repo:
            raise ValueError("Database session required for manual alias resolution.")

        alias = self.repo.upsert_alias(
            raw_string=raw_string.strip(),
            normalized_name=canonical_name.strip(),
            entity_type=entity_type.lower(),
            resolution_method="manual_user_override",
            confidence=1.0,
            is_verified=True,
            request_id=request_id,
        )
        logger.info(
            f"Registered manual entity resolution: '{raw_string}' -> '{canonical_name}' ({entity_type})"
        )
        return alias.normalized_name, alias.resolution_method, alias.confidence, alias.is_verified

    @staticmethod
    def _clean_canonical_string(text: str) -> str:
        s = text.strip()
        # If text is all uppercase (e.g., 'BERT', 'GNN', 'AUC'), keep as is
        if s.isupper() and len(s) <= 8:
            return s
        # Title case if multi-word lowercase
        if s.islower():
            return " ".join(w.capitalize() for w in s.split())
        return s
