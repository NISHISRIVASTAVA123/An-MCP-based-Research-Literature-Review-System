"""Decomposes a candidate research gap hypothesis into independently searchable claims."""

import re
from typing import List, Dict, Any, Optional
from backend.app.models.synthesis import CandidateResearchGap


class GapClaimDecomposer:
    """Decomposes high-level candidate gaps into fine-grained empirical claims for targeted counterevidence retrieval."""

    def decompose_gap(self, gap: CandidateResearchGap) -> List[Dict[str, Any]]:
        """Extracts 3 to 6 distinct, searchable claims from a candidate gap."""
        title = gap.title.strip()
        description = gap.description.strip()
        category = gap.category or "unclassified"
        assumptions = gap.assumptions or []
        unresolved = gap.unresolved_questions or []
        observed_pattern = gap.observed_pattern or ""

        claims: List[Dict[str, Any]] = []

        # Claim 1: Primary Unexplored Problem Claim
        claims.append({
            "claim_text": f"The problem '{title}' remains unaddressed or insufficiently explored in published scientific literature.",
            "claim_type": "unexplored_problem",
            "original_gap_statement": title,
            "generated_keywords": self._extract_key_phrases(title),
            "assumptions_investigated": [f"Assumes lack of published solutions for {title}."],
            "order_index": 1,
        })

        # Claim 2: Missing Methodology / Technique Claim
        method_phrases = self._extract_method_phrases(description + " " + title)
        if method_phrases:
            method_str = " and ".join(method_phrases[:2])
            claims.append({
                "claim_text": f"Existing studies have not implemented or evaluated {method_str} for this specific domain/task.",
                "claim_type": "missing_methodology",
                "original_gap_statement": description[:200],
                "generated_keywords": method_phrases,
                "assumptions_investigated": [f"Assumes {method_str} has not been adapted or benchmarked here."],
                "order_index": 2,
            })
        else:
            claims.append({
                "claim_text": f"Methodological solutions targeting {title} have not been proposed or benchmarked.",
                "claim_type": "missing_methodology",
                "original_gap_statement": description[:200],
                "generated_keywords": self._extract_key_phrases(description[:150]),
                "assumptions_investigated": ["Assumes absence of specific methodological implementations."],
                "order_index": 2,
            })

        # Claim 3: Category-Specific Claim (Empirical, Benchmark/Dataset, Evaluation, or Scalability)
        if "dataset" in category or "benchmark" in category:
            claims.append({
                "claim_text": f"Standardized public benchmark datasets and open evaluations for {title} are missing or inadequate.",
                "claim_type": "missing_dataset",
                "original_gap_statement": observed_pattern or description[:200],
                "generated_keywords": self._extract_key_phrases(title) + ["benchmark", "dataset", "corpus"],
                "assumptions_investigated": ["Assumes no open, standardized datasets exist."],
                "order_index": 3,
            })
        elif "evaluation" in category:
            claims.append({
                "claim_text": f"Empirical evaluations and rigorous metric comparisons for {title} are absent or unverified.",
                "claim_type": "missing_evaluation",
                "original_gap_statement": observed_pattern or description[:200],
                "generated_keywords": self._extract_key_phrases(title) + ["evaluation", "metric", "ablation", "benchmark"],
                "assumptions_investigated": ["Assumes no standardized quantitative evaluations have been conducted."],
                "order_index": 3,
            })
        else:
            claims.append({
                "claim_text": f"Practical implementations and real-world evaluations of {title} remain limited.",
                "claim_type": "untested_assumption",
                "original_gap_statement": observed_pattern or description[:200],
                "generated_keywords": self._extract_key_phrases(title) + ["implementation", "empirical evaluation", "real-world"],
                "assumptions_investigated": ["Assumes gap persists in practical deployment."],
                "order_index": 3,
            })

        # Claim 4: Untested Assumption or Unresolved Question Claim (if present)
        if assumptions and len(assumptions) > 0:
            first_assumption = assumptions[0]
            claims.append({
                "claim_text": f"The assumption that '{first_assumption}' holds true across broader scientific literature.",
                "claim_type": "untested_assumption",
                "original_gap_statement": str(first_assumption),
                "generated_keywords": self._extract_key_phrases(str(first_assumption)),
                "assumptions_investigated": [str(first_assumption)],
                "order_index": 4,
            })
        elif unresolved and len(unresolved) > 0:
            first_unresolved = unresolved[0]
            claims.append({
                "claim_text": f"The open research question: '{first_unresolved}' has not been resolved by recent publications.",
                "claim_type": "unexplored_problem",
                "original_gap_statement": str(first_unresolved),
                "generated_keywords": self._extract_key_phrases(str(first_unresolved)),
                "assumptions_investigated": ["Assumes unresolved question has not been answered by recent literature."],
                "order_index": 4,
            })

        return claims

    def _extract_key_phrases(self, text: str) -> List[str]:
        words = re.findall(r"\b[A-Za-z0-9_-]{3,}\b", text)
        stop_words = {
            "the", "and", "for", "with", "that", "this", "from", "are", "was",
            "were", "has", "have", "been", "which", "such", "into", "more",
            "most", "other", "some", "such", "than", "their", "there", "about",
            "after", "also", "between", "both", "during", "each", "through",
            "study", "paper", "research", "limited", "exists", "lack", "missing",
            "unexplored", "gap", "literature", "existing",
        }
        filtered = [w for w in words if w.lower() not in stop_words]
        # Return unique words maintaining order
        seen = set()
        res = []
        for w in filtered:
            if w.lower() not in seen:
                seen.add(w.lower())
                res.append(w)
        return res[:8]

    def _extract_method_phrases(self, text: str) -> List[str]:
        """Detects canonical methodological keywords like RAG, Multi-Agent, Transformer, GNN, etc."""
        known_methods = [
            "Retrieval-Augmented Generation", "RAG", "Multi-Agent", "Multi-Agent Reasoning",
            "Transformer", "GNN", "Graph Neural Network", "Reinforcement Learning", "RL",
            "Zero-Shot", "Few-Shot", "Dense Retrieval", "Vector Search", "Knowledge Graph",
            "Explainable AI", "XAI", "Contrastive Learning", "Self-Supervised", "Fine-Tuning",
            "Large Language Model", "LLM", "Prompt Engineering", "Hallucination Mitigation",
        ]
        found = []
        for m in known_methods:
            if re.search(rf"\b{re.escape(m)}\b", text, re.IGNORECASE):
                found.append(m)
        return found
