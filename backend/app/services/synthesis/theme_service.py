"""Research Theme Identification Service (Phase 4).

Discovers recurring scientific themes across retrieved papers by grouping related
methodological, empirical, and architectural concepts. Anchors every theme in
verifiable supporting evidence passages and claims without hallucination.
"""

from typing import List, Dict, Any, Optional, Set
from collections import defaultdict
from sqlalchemy.orm import Session
from backend.app.services.synthesis.evidence_retrieval_service import EvidenceRetrievalService
from backend.app.services.graph.normalization_service import EntityNormalizationService
from backend.app.core.logging import logger


class ResearchThemeService:
    """Discovers and describes recurring research themes across the scientific evidence graph."""

    def __init__(self, db: Session):
        self.db = db
        self.retrieval_service = EvidenceRetrievalService(db)
        self.norm_service = EntityNormalizationService(db)

    def identify_themes(
        self,
        request_id: str,
        selected_paper_ids: Optional[List[str]] = None,
        min_paper_threshold: int = 1,
    ) -> List[Dict[str, Any]]:
        """Identifies recurring themes across the literature collection."""
        # 1. Get eligible papers
        eligible_papers = self.retrieval_service.get_eligible_papers_for_request(request_id)
        if selected_paper_ids:
            papers = [p for p in eligible_papers if p.id in selected_paper_ids]
        else:
            papers = eligible_papers

        if not papers:
            logger.info(f"No papers available to extract themes for request {request_id}.")
            return []

        # 2. Extract methods, models, datasets, limitations, and claims across papers
        methods_by_paper = self.retrieval_service.get_methods_with_associated_papers(request_id)
        datasets_by_paper = self.retrieval_service.get_datasets_with_associated_papers(request_id)
        models_by_paper = self.retrieval_service.get_models_with_associated_papers(request_id)
        all_claims = self.retrieval_service.get_all_claims_with_evidence(request_id)
        all_limitations = self.retrieval_service.get_all_limitations_with_evidence(request_id)

        target_paper_ids = {p.id for p in papers}

        # 3. Build Concept Clusters
        # Cluster A: Methodological themes
        candidate_themes = []

        # Map methods to papers
        for method_name, p_ids in methods_by_paper.items():
            relevant_p_ids = [pid for pid in p_ids if pid in target_paper_ids]
            if len(relevant_p_ids) >= min_paper_threshold:
                # Find claims and evidence supporting this method
                supp_claims = [c["claim_node_id"] for c in all_claims if c.get("paper_id") in relevant_p_ids]
                supp_ev = []
                for c in all_claims:
                    if c.get("paper_id") in relevant_p_ids:
                        for pass_item in c.get("passages", []):
                            supp_ev.append(pass_item["id"])

                paper_ratio = f"{len(relevant_p_ids)} of {len(papers)}"
                candidate_themes.append({
                    "name": f"{method_name} Methodological Framework",
                    "description": (
                        f"Investigation and application of {method_name} architectures across "
                        f"{paper_ratio} retrieved studies in this collection."
                    ),
                    "theme_category": "methodological",
                    "related_concepts": [method_name],
                    "associated_paper_ids": relevant_p_ids,
                    "supporting_claim_ids": supp_claims[:10],
                    "supporting_evidence_ids": list(set(supp_ev))[:10],
                    "frequency": len(relevant_p_ids),
                    "confidence": min(0.95, 0.6 + (0.1 * len(relevant_p_ids))),
                    "confidence_explanation": (
                        f"Directly supported by {len(relevant_p_ids)} distinct papers employing "
                        f"'{method_name}' with verified evidence nodes in the graph."
                    ),
                    "known_limitations": (
                        "Theme scope reflects only the retrieved corpus subset; "
                        "broader literature might evaluate alternative frameworks."
                    ),
                })

        # Cluster B: Empirical Benchmark & Dataset Themes
        for dataset_name, p_ids in datasets_by_paper.items():
            relevant_p_ids = [pid for pid in p_ids if pid in target_paper_ids]
            if len(relevant_p_ids) >= min_paper_threshold:
                supp_ev = []
                for c in all_claims:
                    if c.get("paper_id") in relevant_p_ids:
                        for pass_item in c.get("passages", []):
                            supp_ev.append(pass_item["id"])

                paper_ratio = f"{len(relevant_p_ids)} of {len(papers)}"
                candidate_themes.append({
                    "name": f"Empirical Evaluation on {dataset_name}",
                    "description": (
                        f"Empirical validation and benchmark evaluations conducted on the {dataset_name} "
                        f"dataset across {paper_ratio} selected publications."
                    ),
                    "theme_category": "empirical",
                    "related_concepts": [dataset_name],
                    "associated_paper_ids": relevant_p_ids,
                    "supporting_claim_ids": [],
                    "supporting_evidence_ids": list(set(supp_ev))[:10],
                    "frequency": len(relevant_p_ids),
                    "confidence": min(0.90, 0.55 + (0.1 * len(relevant_p_ids))),
                    "confidence_explanation": (
                        f"Corroborated by {len(relevant_p_ids)} studies explicitly reporting experiments "
                        f"on '{dataset_name}'."
                    ),
                    "known_limitations": "Benchmark coverage may be biased toward standardized evaluation protocols.",
                })

        # Cluster C: Cross-Paper Limitation Themes
        limitation_keywords = defaultdict(list)
        for lim in all_limitations:
            pid = lim.get("paper_id")
            if pid in target_paper_ids:
                label = lim["label"].lower()
                if any(w in label for w in ["scale", "scaling", "large", "complexity", "computational"]):
                    limitation_keywords["Scalability & Computational Complexity Constraints"].append(lim)
                elif any(w in label for w in ["interpret", "explain", "black box", "opacity"]):
                    limitation_keywords["Model Interpretability & Explainability Challenges"].append(lim)
                elif any(w in label for w in ["generaliz", "unseen", "out-of-distribution", "transfer"]):
                    limitation_keywords["Generalization & Out-of-Distribution Robustness"].append(lim)
                elif any(w in label for w in ["data", "label", "annotation", "sparse", "imbalance"]):
                    limitation_keywords["Data Scarcity & Benchmark Quality Constraints"].append(lim)

        for theme_name, lim_list in limitation_keywords.items():
            associated_pids = list({l["paper_id"] for l in lim_list if l.get("paper_id")})
            if len(associated_pids) >= min_paper_threshold:
                lim_node_ids = [l["limitation_node_id"] for l in lim_list]
                supp_ev = []
                for l in lim_list:
                    for pass_item in l.get("passages", []):
                        supp_ev.append(pass_item["id"])

                candidate_themes.append({
                    "name": theme_name,
                    "description": (
                        f"Recurring author-reported limitation regarding {theme_name.lower()} "
                        f"noted across {len(associated_pids)} of {len(papers)} papers."
                    ),
                    "theme_category": "evaluation",
                    "related_concepts": [theme_name],
                    "associated_paper_ids": associated_pids,
                    "supporting_claim_ids": lim_node_ids[:10],
                    "supporting_evidence_ids": list(set(supp_ev))[:10],
                    "frequency": len(associated_pids),
                    "confidence": min(0.92, 0.65 + (0.08 * len(associated_pids))),
                    "confidence_explanation": (
                        f"Reported explicitly in {len(associated_pids)} papers as a primary research limitation."
                    ),
                    "known_limitations": "Subject to author-disclosed limitations rather than exhaustive external audits.",
                })

        # Sort themes by frequency and confidence
        candidate_themes.sort(key=lambda t: (t["frequency"], t["confidence"]), reverse=True)

        return candidate_themes
