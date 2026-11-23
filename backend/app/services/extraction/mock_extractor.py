"""Mock Scientific Evidence Extractor for Automated Testing."""

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


class MockEvidenceExtractor(BaseEvidenceExtractor):
    """Predictable mock extractor generating deterministic scientific evidence fixtures."""

    async def extract_evidence(
        self,
        paper_id: str,
        title: str,
        abstract: Optional[str],
        fulltext_sections: List[Dict[str, Any]],
        source_scope: str,
    ) -> StructuredEvidenceExtraction:
        return StructuredEvidenceExtraction(
            paper_id=paper_id,
            source_scope=source_scope,
            extraction_status="completed",
            research_objective=ResearchObjectiveItem(
                problem_statement=f"Evaluate limitations of explainability in {title}.",
                motivation="Existing explainable methods lack empirical consistency.",
                significance="Critical for verified model trust.",
                supporting_passage=abstract or f"In this paper we investigate {title}.",
                page_number=1,
                section_heading="Introduction",
            ),
            methodologies=[
                MethodologyItem(
                    approach_name="SHAP Analysis",
                    approach_type="algorithm",
                    description="Calculates Shapley values to interpret feature attributions.",
                    baselines_compared=["LIME", "Random Forest Baseline"],
                    supporting_passage="We apply SHAP to measure feature attributions.",
                    page_number=3,
                    section_heading="Methodology",
                ),
            ],
            datasets=[
                DatasetItem(
                    dataset_name="LIAR Benchmark",
                    source_or_origin="Wang (2017)",
                    reported_sample_size="12,800 statements",
                    train_test_split="80/10/10",
                    modality="text",
                    supporting_passage="Experiments are conducted on the benchmark LIAR dataset.",
                    page_number=4,
                    section_heading="Experiments",
                ),
            ],
            evaluation_metrics=[
                EvaluationMetricItem(
                    metric_name="F1-Score",
                    reported_value="84.2%",
                    comparator_baseline_value="79.1%",
                    experimental_context="5-fold cross validation on test split",
                    supporting_passage="The proposed model achieves an F1-Score of 84.2%.",
                    page_number=5,
                    section_heading="Results",
                ),
            ],
            findings=[
                FindingItem(
                    finding_statement="Explanation consistency drops under minor adversarial perturbations.",
                    percentage_gain_or_delta=None,
                    is_statistically_tested=True,
                    supporting_passage="Our results demonstrate that explanation consistency drops significantly.",
                    page_number=6,
                    section_heading="Discussion",
                ),
            ],
            limitations=[
                LimitationItem(
                    limitation_text="Evaluation was limited to English-language textual news.",
                    limitation_type="author_reported",
                    aspect="generalization",
                    supporting_passage="A primary limitation is that our study was restricted to English textual articles.",
                    page_number=7,
                    section_heading="Limitations",
                ),
            ],
            future_work=[
                FutureWorkItem(
                    direction_text="Extend verification to multimodal video misinformation datasets.",
                    potential_impact="Broader domain coverage.",
                    supporting_passage="In future work, we plan to extend verification to multimodal video streams.",
                    page_number=7,
                    section_heading="Conclusion & Future Work",
                ),
            ],
            contributions=[
                "First systematic audit of explanation robustness in fake news classifiers.",
                "Publicly available reproducible benchmark suite.",
            ],
            uncertainties=[
                "Cross-language generalization remains unverified.",
            ] if source_scope == "full_text" else [
                "Full text was unavailable; extracted solely from abstract metadata.",
            ],
        )

