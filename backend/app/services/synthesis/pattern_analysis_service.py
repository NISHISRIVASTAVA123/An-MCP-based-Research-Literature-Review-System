"""Literature Pattern and Trend Analysis Service (Phase 4).

Computes empirical distributions, methodology frequencies, dataset cross-tabulations,
evaluation patterns, and temporal publication trends across retrieved papers.
Ensures rigorous denominator qualification ("X of N retrieved papers").
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter
from sqlalchemy.orm import Session
from backend.app.services.synthesis.evidence_retrieval_service import EvidenceRetrievalService
from backend.app.core.logging import logger


class PatternAnalysisService:
    """Analyzes distributions and empirical patterns across the scientific evidence graph."""

    def __init__(self, db: Session):
        self.db = db
        self.retrieval_service = EvidenceRetrievalService(db)

    def analyze_patterns(
        self,
        request_id: str,
        selected_paper_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Performs statistical aggregation across methodologies, datasets, models, metrics, and years."""
        eligible_papers = self.retrieval_service.get_eligible_papers_for_request(request_id)
        if selected_paper_ids:
            papers = [p for p in eligible_papers if p.id in selected_paper_ids]
        else:
            papers = eligible_papers

        total_papers = len(papers)
        if total_papers == 0:
            logger.info(f"No papers available for pattern analysis in request {request_id}.")
            return []

        target_paper_ids = {p.id for p in papers}

        # 1. Methodology Pattern Analysis
        methods_by_paper = self.retrieval_service.get_methods_with_associated_papers(request_id)
        method_freq = {}
        for m_name, p_ids in methods_by_paper.items():
            relevant = [pid for pid in p_ids if pid in target_paper_ids]
            if relevant:
                method_freq[m_name] = relevant

        method_dist = {
            m: {
                "count": len(pids),
                "percentage": round((len(pids) / total_papers) * 100, 1),
                "paper_ids": pids,
            }
            for m, pids in method_freq.items()
        }

        # 2. Dataset Pattern Analysis
        datasets_by_paper = self.retrieval_service.get_datasets_with_associated_papers(request_id)
        dataset_freq = {}
        for d_name, p_ids in datasets_by_paper.items():
            relevant = [pid for pid in p_ids if pid in target_paper_ids]
            if relevant:
                dataset_freq[d_name] = relevant

        dataset_dist = {
            d: {
                "count": len(pids),
                "percentage": round((len(pids) / total_papers) * 100, 1),
                "paper_ids": pids,
            }
            for d, pids in dataset_freq.items()
        }

        # 3. Method-Dataset Combinations (Co-occurrence)
        method_dataset_cooccurrence: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for m_name, m_pids in method_freq.items():
            for d_name, d_pids in dataset_freq.items():
                shared = set(m_pids).intersection(set(d_pids))
                if shared:
                    method_dataset_cooccurrence[m_name][d_name] = len(shared)

        # 4. Model Pattern Analysis
        models_by_paper = self.retrieval_service.get_models_with_associated_papers(request_id)
        model_dist = {
            mod: {
                "count": len([pid for pid in pids if pid in target_paper_ids]),
                "paper_ids": [pid for pid in pids if pid in target_paper_ids],
            }
            for mod, pids in models_by_paper.items()
            if any(pid in target_paper_ids for pid in pids)
        }

        # 5. Evaluation Metric Patterns
        metrics_by_paper = self.retrieval_service.get_metrics_with_associated_papers(request_id)
        metric_dist = {
            met: {
                "count": len([pid for pid in pids if pid in target_paper_ids]),
                "paper_ids": [pid for pid in pids if pid in target_paper_ids],
            }
            for met, pids in metrics_by_paper.items()
            if any(pid in target_paper_ids for pid in pids)
        }

        # 6. Publication Temporal Trends (Year distribution)
        year_counter: Counter = Counter()
        for p in papers:
            yr = p.publication_year or "Unknown"
            year_counter[yr] += 1

        year_dist = dict(sorted(year_counter.items(), key=lambda x: str(x[0])))

        # 7. Synthesize into standard LiteraturePattern objects
        patterns = []

        # Pattern 1: Methodology Distribution
        top_methods = sorted(method_dist.items(), key=lambda x: x[1]["count"], reverse=True)
        top_m_text = (
            f"Most prevalent methodologies: {', '.join([f'{m} ({data['count']}/{total_papers})' for m, data in top_methods[:3]])}"
            if top_methods
            else "Methodologies were not consistently reported across the selected papers."
        )
        patterns.append({
            "pattern_type": "methodology",
            "description": f"Distribution of algorithmic methodologies across {total_papers} retrieved papers.",
            "observed_data": {
                "total_papers": total_papers,
                "method_frequencies": method_dist,
                "top_methods": [m[0] for m in top_methods[:5]],
            },
            "related_paper_ids": list(target_paper_ids),
            "related_evidence_ids": [],
            "interpretation": top_m_text,
            "confidence": 0.88,
            "limitations": "Reflects explicitly extracted methodology terms; alternative aliases may exist.",
        })

        # Pattern 2: Dataset Benchmarking Landscape
        top_datasets = sorted(dataset_dist.items(), key=lambda x: x[1]["count"], reverse=True)
        top_d_text = (
            f"Prominent evaluation benchmarks: {', '.join([f'{d} ({data['count']}/{total_papers})' for d, data in top_datasets[:3]])}"
            if top_datasets
            else "Standardized datasets were not consistently reported in abstracts."
        )
        patterns.append({
            "pattern_type": "dataset",
            "description": f"Benchmark dataset usage across {total_papers} retrieved studies.",
            "observed_data": {
                "total_papers": total_papers,
                "dataset_frequencies": dataset_dist,
                "co_occurrence_with_methods": {k: dict(v) for k, v in method_dataset_cooccurrence.items()},
            },
            "related_paper_ids": list(target_paper_ids),
            "related_evidence_ids": [],
            "interpretation": top_d_text,
            "confidence": 0.85,
            "limitations": "Evaluations performed only on abstract-reported or open-access full-text benchmarks.",
        })

        # Pattern 3: Evaluation Metrics
        top_metrics = sorted(metric_dist.items(), key=lambda x: x[1]["count"], reverse=True)
        top_met_text = (
            f"Standard evaluation metrics employed: {', '.join([f'{m} ({data['count']}/{total_papers})' for m, data in top_metrics[:3]])}"
            if top_metrics
            else "Specific evaluation metrics were not extracted from the available text."
        )
        patterns.append({
            "pattern_type": "evaluation",
            "description": f"Evaluation metric distribution across {total_papers} papers.",
            "observed_data": {
                "total_papers": total_papers,
                "metric_frequencies": metric_dist,
            },
            "related_paper_ids": list(target_paper_ids),
            "related_evidence_ids": [],
            "interpretation": top_met_text,
            "confidence": 0.82,
            "limitations": "Reporting density varies between papers with full-text access vs abstract-only access.",
        })

        # Pattern 4: Publication Trends
        patterns.append({
            "pattern_type": "publication_trend",
            "description": f"Temporal publication trajectory across {total_papers} papers.",
            "observed_data": {
                "total_papers": total_papers,
                "year_distribution": year_dist,
            },
            "related_paper_ids": list(target_paper_ids),
            "related_evidence_ids": [],
            "interpretation": f"Publications span years {min(year_dist.keys()) if year_dist else 'N/A'} to {max(year_dist.keys()) if year_dist else 'N/A'}.",
            "confidence": 0.95,
            "limitations": "Temporal coverage depends on the search timeframe specified in the research request.",
        })

        return patterns
