"""Deterministic Rule-Based Scientific Evidence Extractor.

Extracts structured research dimensions, models, datasets, metrics,
findings, author-reported limitations, and future work from scientific text
using deterministic linguistic and pattern matching with exact passage attribution.
Provides 100% offline, reproducible functionality without requiring paid LLM keys.
"""

import re
from typing import List, Dict, Any, Optional
from backend.app.services.extraction.base_extractor import BaseEvidenceExtractor
from backend.app.schemas.evidence import (
    StructuredEvidenceExtraction,
    ResearchObjectiveItem,
    MethodologyItem,
    DatasetItem,
    EvaluationMetricItem,
    FindingItem,
    LimitationItem,
    FutureWorkItem,
)

METRIC_PATTERNS = [
    (r"(?:accuracy|acc)\s*(?:of|is|reached|achieves?)?\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?\s*%)", "Accuracy"),
    (r"(?:f1|f-score|f1-score)\s*(?:of|is|reached|achieves?)?\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?\s*%)", "F1-Score"),
    (r"(?:precision)\s*(?:of|is|reached|achieves?)?\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?\s*%)", "Precision"),
    (r"(?:recall)\s*(?:of|is|reached|achieves?)?\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?\s*%)", "Recall"),
    (r"(?:auc|roc-auc)\s*(?:of|is|reached|achieves?)?\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)", "AUC-ROC"),
    (r"(?:bleu)\s*(?:of|is|reached|achieves?)?\s*[:=]?\s*([0-9]+(?:\.[0-9]+)?)", "BLEU"),
]

KNOWN_METHODS = [
    "Transformer", "BERT", "RoBERTa", "LLaMA", "GPT", "SHAP", "LIME",
    "Attention Mechanism", "Graph Neural Network", "GNN", "CNN", "LSTM",
    "BiLSTM", "Support Vector Machine", "SVM", "Random Forest", "XGBoost",
    "Explainable AI", "XAI", "Prompt Engineering", "Fine-tuning", "Contrastive Learning",
    "Adversarial Training", "Cross-Entropy", "Reinforcement Learning",
]

KNOWN_DATASETS = [
    "LIAR", "FakeNewsNet", "Twitter", "Weibo", "PolitiFact", "GossipCop",
    "FEVER", "CoAID", "SST-2", "GLUE", "SuperGLUE", "SQuAD", "ImageNet",
    "MIMIC-III", "PubMed", "arXiv", "Common Crawl",
]


class RuleBasedEvidenceExtractor(BaseEvidenceExtractor):
    """Deterministic scientific evidence extractor."""

    async def extract_evidence(
        self,
        paper_id: str,
        title: str,
        abstract: Optional[str],
        fulltext_sections: List[Dict[str, Any]],
        source_scope: str,
    ) -> StructuredEvidenceExtraction:
        # Build searchable sentences with page & section metadata
        sentence_pool: List[Dict[str, Any]] = []

        if source_scope == "full_text" and fulltext_sections:
            for sec in fulltext_sections:
                p_num = sec.get("page_number", 1)
                heading = sec.get("heading", "Body")
                text = sec.get("text", "")
                for raw_s in re.split(r"(?<=[.!?])\s+", text):
                    s = raw_s.strip()
                    if len(s) > 25:
                        sentence_pool.append({
                            "text": s,
                            "page": p_num,
                            "section": heading,
                        })
        elif abstract:
            for raw_s in re.split(r"(?<=[.!?])\s+", abstract):
                s = raw_s.strip()
                if len(s) > 20:
                    sentence_pool.append({
                        "text": s,
                        "page": 1,
                        "section": "Abstract",
                    })

        # 1. Research Objective
        obj_sentence = None
        for item in sentence_pool:
            t_low = item["text"].lower()
            if any(k in t_low for k in ["aims to", "we propose", "this paper investigates", "this study focuses", "goal of this", "we address", "we study"]):
                obj_sentence = item
                break

        if not obj_sentence:
            obj_sentence = sentence_pool[0] if sentence_pool else {
                "text": f"Investigates {title}.",
                "page": 1,
                "section": "Title",
            }

        research_objective = ResearchObjectiveItem(
            problem_statement=obj_sentence["text"][:300],
            motivation=f"Addressed in the context of scientific inquiry into {title}.",
            significance="Reported in paper scope.",
            supporting_passage=obj_sentence["text"],
            page_number=obj_sentence.get("page"),
            section_heading=obj_sentence.get("section"),
        )

        # 2. Methodologies
        methodologies: List[MethodologyItem] = []
        full_text_corpus = " ".join([item["text"] for item in sentence_pool])

        for method in KNOWN_METHODS:
            pattern = re.compile(rf"\b{re.escape(method)}\b", re.IGNORECASE)
            for item in sentence_pool:
                if pattern.search(item["text"]):
                    methodologies.append(MethodologyItem(
                        approach_name=method,
                        approach_type="algorithm_or_model",
                        description=f"Utilized or evaluated in paper: {item['text'][:150]}...",
                        baselines_compared=[],
                        experimental_setup=None,
                        supporting_passage=item["text"],
                        page_number=item.get("page"),
                        section_heading=item.get("section"),
                    ))
                    break
            if len(methodologies) >= 5:
                break

        if not methodologies:
            methodologies.append(MethodologyItem(
                approach_name="Empirical Evaluation",
                approach_type="empirical",
                description="Empirical study detailed in paper methodology.",
                supporting_passage=obj_sentence["text"],
                page_number=obj_sentence.get("page"),
                section_heading=obj_sentence.get("section"),
            ))

        # 3. Datasets
        datasets: List[DatasetItem] = []
        for dname in KNOWN_DATASETS:
            d_pattern = re.compile(rf"\b{re.escape(dname)}\b", re.IGNORECASE)
            for item in sentence_pool:
                if d_pattern.search(item["text"]):
                    datasets.append(DatasetItem(
                        dataset_name=dname,
                        source_or_origin="Reported in experiment",
                        reported_sample_size=None,
                        train_test_split=None,
                        modality="text",
                        supporting_passage=item["text"],
                        page_number=item.get("page"),
                        section_heading=item.get("section"),
                    ))
                    break
            if len(datasets) >= 4:
                break

        # Also search for generic "dataset" sentences
        if not datasets:
            for item in sentence_pool:
                if "dataset" in item["text"].lower() or "corpus" in item["text"].lower():
                    datasets.append(DatasetItem(
                        dataset_name="Experimental Dataset",
                        source_or_origin=item["text"][:120],
                        supporting_passage=item["text"],
                        page_number=item.get("page"),
                        section_heading=item.get("section"),
                    ))
                    break

        # 4. Evaluation Metrics
        metrics: List[EvaluationMetricItem] = []
        for pat, mname in METRIC_PATTERNS:
            for item in sentence_pool:
                match = re.search(pat, item["text"], re.IGNORECASE)
                if match:
                    val = match.group(1).strip()
                    metrics.append(EvaluationMetricItem(
                        metric_name=mname,
                        reported_value=val,
                        experimental_context=item["text"][:150],
                        supporting_passage=item["text"],
                        page_number=item.get("page"),
                        section_heading=item.get("section"),
                    ))
                    break

        # 5. Findings
        findings: List[FindingItem] = []
        for item in sentence_pool:
            t_low = item["text"].lower()
            if any(k in t_low for k in ["outperforms", "achieves higher", "results show that", "demonstrates significant", "improvement of", "superior performance", "we observe that"]):
                findings.append(FindingItem(
                    finding_statement=item["text"],
                    percentage_gain_or_delta=None,
                    is_statistically_tested=None,
                    supporting_passage=item["text"],
                    page_number=item.get("page"),
                    section_heading=item.get("section"),
                ))
                if len(findings) >= 5:
                    break

        if not findings and sentence_pool:
            findings.append(FindingItem(
                finding_statement=sentence_pool[-1]["text"],
                supporting_passage=sentence_pool[-1]["text"],
                page_number=sentence_pool[-1].get("page"),
                section_heading=sentence_pool[-1].get("section"),
            ))

        # 6. Limitations (Strictly author-reported)
        limitations: List[LimitationItem] = []
        for item in sentence_pool:
            t_low = item["text"].lower()
            if any(k in t_low for k in ["limitation", "restricted to", "however, our", "fails to", "small sample", "computational overhead", "not evaluated on", "boundary condition"]):
                limitations.append(LimitationItem(
                    limitation_text=item["text"],
                    limitation_type="author_reported",
                    aspect="generalization_or_scope",
                    supporting_passage=item["text"],
                    page_number=item.get("page"),
                    section_heading=item.get("section"),
                ))
                if len(limitations) >= 4:
                    break

        # 7. Future Work
        future_work: List[FutureWorkItem] = []
        for item in sentence_pool:
            t_low = item["text"].lower()
            if any(k in t_low for k in ["in future work", "future research", "we plan to", "we hope to extend", "promising direction", "open question"]):
                future_work.append(FutureWorkItem(
                    direction_text=item["text"],
                    potential_impact="Identified by paper authors.",
                    supporting_passage=item["text"],
                    page_number=item.get("page"),
                    section_heading=item.get("section"),
                ))
                if len(future_work) >= 3:
                    break

        # 8. Contributions
        contributions = [
            f"Formulated research problem: {research_objective.problem_statement[:120]}...",
            f"Evaluated methodology including {', '.join([m.approach_name for m in methodologies[:3]])}.",
        ]

        uncertainties = []
        if source_scope == "abstract_only":
            uncertainties.append("Extraction restricted to abstract metadata; detailed experimental parameters unavailable.")
        if not metrics:
            uncertainties.append("No explicit numerical performance metrics identified in extracted text.")
        if not limitations:
            uncertainties.append("No explicit author-reported limitations section detected.")

        return StructuredEvidenceExtraction(
            paper_id=paper_id,
            source_scope=source_scope,
            extraction_status="completed",
            research_objective=research_objective,
            methodologies=methodologies,
            datasets=datasets,
            evaluation_metrics=metrics,
            findings=findings,
            limitations=limitations,
            future_work=future_work,
            contributions=contributions,
            uncertainties=uncertainties,
        )

