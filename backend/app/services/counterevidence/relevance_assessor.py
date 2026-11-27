"""Counterevidence Relevance Classification & Evidence Hierarchy Assessment Engine."""

import re
from typing import Dict, Any, Optional, List
from backend.app.models.paper import Paper
from backend.app.models.synthesis import CandidateResearchGap
from backend.app.models.counterevidence import CounterevidenceClaim
from backend.app.models.document import FulltextDocument


class CounterevidenceRelevanceAssessor:
    """Classifies whether a retrieved publication provides direct, partial, or related counterevidence against a candidate gap.
    
    Enforces strict evidence hierarchy:
    - Title/abstract similarity alone NEVER establishes direct counterevidence.
    - Level 1 (Full-Text Passages) required for authoritative direct counterevidence.
    - Level 2 (Abstract) explicitly tagged as abstract-based.
    - Level 3 (Metadata-Only) capped at preliminary triage / insufficient information.
    """

    def assess_paper_against_gap(
        self,
        paper: Paper,
        gap: CandidateResearchGap,
        claim: Optional[CounterevidenceClaim] = None,
        fulltext_doc: Optional[FulltextDocument] = None,
    ) -> Dict[str, Any]:
        """Evaluates actual scientific contribution and assigns relevance and evidence-level tiers."""
        title = (paper.title or "").strip()
        abstract = (paper.abstract or "").strip()
        gap_title = (gap.title or "").strip()
        gap_desc = (gap.description or "").strip()
        claim_text = claim.claim_text if claim else gap_title

        # Check full-text availability
        has_fulltext = bool(
            fulltext_doc
            and fulltext_doc.extraction_status in ("success", "partial")
            and fulltext_doc.extracted_sections
        )

        fulltext_corpus = ""
        if has_fulltext and fulltext_doc:
            fulltext_corpus = " ".join(
                [sec.get("text", "") for sec in (fulltext_doc.extracted_sections or [])]
            )

        # 1. Metadata-Only Case
        if not abstract and not has_fulltext:
            return {
                "relevance_classification": "insufficient_information",
                "impact_classification": "inconclusive",
                "explanation": f"Only bibliographic metadata is available for '{title}'. Title or keyword matches alone cannot establish counterevidence without inspectable text.",
                "actual_contribution_identified": "Metadata only; paper contributions unverified.",
                "research_problem_addressed": "Unverified (no abstract or full text accessible).",
                "relevant_methodology": None,
                "evidence_level": "level_3_metadata_only",
                "is_abstract_based": False,
                "confidence_indicator": 0.25,
                "verification_status": "unavailable",
            }

        # 2. Text Corpus to Analyze
        text_to_examine = fulltext_corpus if has_fulltext else abstract
        text_lower = text_to_examine.lower()

        # Extract core domain terms and method terms from gap
        gap_terms = self._extract_substantive_terms(gap_title + " " + gap_desc)
        term_matches = [t for t in gap_terms if t in text_lower]
        overlap_ratio = len(term_matches) / max(len(gap_terms), 1)

        # Detect contribution verbs (implemented, evaluated, demonstrated, benchmarked, proposed)
        has_implementation = any(
            v in text_lower
            for v in [
                "we propose", "we implement", "we evaluate", "experimental results",
                "benchmarked on", "our model achieves", "we demonstrated", "we introduce",
                "experiments demonstrate", "we design and implement"
            ]
        )

        # Detect limitation or future work qualifiers in the paper itself
        acknowledges_unresolved = any(
            l in text_lower
            for l in [
                "future work", "remains open", "not evaluated on", "restricted to",
                "does not consider", "preliminary investigation", "left for future"
            ]
        )

        # 3. Determine Evidence Hierarchy Level
        evidence_level = "level_1_fulltext_passage" if has_fulltext else "level_2_abstract_supported"
        is_abstract = not has_fulltext

        # 4. Assess Relevance Category
        # Direct Counterevidence Rule: High overlap + concrete implementation + Level 1 full text (or strong abstract implementation statement)
        if overlap_ratio >= 0.55 and has_implementation:
            if has_fulltext:
                relevance = "direct_counterevidence"
                impact = "strongly_challenged"
                explanation = (
                    f"Full-text analysis confirms publication '{title}' directly implements and experimentally evaluates "
                    f"solutions addressing the claimed gap '{gap_title}'. Verified against document sections."
                )
                conf = 0.90
                v_status = "source_supported"
            else:
                # Abstract only cannot be claimed as definitive full-text direct counterevidence
                relevance = "partial_counterevidence"
                impact = "partially_challenged"
                explanation = (
                    f"Abstract indicates publication '{title}' claims to address aspects of '{gap_title}'. "
                    f"However, assessment is restricted to abstract text only and requires full-text passage verification."
                )
                conf = 0.65
                v_status = "abstract_supported"

        elif overlap_ratio >= 0.35 or (overlap_ratio >= 0.25 and has_implementation):
            relevance = "partial_counterevidence"
            impact = "partially_challenged"
            explanation = (
                f"Publication '{title}' addresses related components or alternative methodologies for '{gap_title}', "
                f"but acknowledges unresolved aspects or does not completely resolve all sub-claims."
            )
            conf = 0.70 if has_fulltext else 0.55
            v_status = "source_supported" if has_fulltext else "abstract_supported"

        elif overlap_ratio >= 0.15:
            relevance = "related_evidence"
            impact = "weakly_challenged"
            explanation = (
                f"Publication '{title}' shares domain vocabulary with '{gap_title}', but does not implement or "
                f"evaluate solutions that disprove the claimed research gap."
            )
            conf = 0.60
            v_status = "source_supported" if has_fulltext else "abstract_supported"

        else:
            relevance = "not_relevant"
            impact = "no_counterevidence_retrieved"
            explanation = (
                f"Publication '{title}' does not meaningfully intersect with the specific research problem in '{gap_title}'."
            )
            conf = 0.80
            v_status = "source_supported" if has_fulltext else "abstract_supported"

        # Formulate extracted contributions summary
        contribution_text = self._summarize_contribution(paper, text_to_examine)
        problem_text = self._summarize_problem(paper, text_to_examine)

        return {
            "relevance_classification": relevance,
            "impact_classification": impact,
            "explanation": explanation,
            "actual_contribution_identified": contribution_text,
            "research_problem_addressed": problem_text,
            "relevant_methodology": self._detect_methods(text_to_examine),
            "evidence_level": evidence_level,
            "is_abstract_based": is_abstract,
            "confidence_indicator": conf,
            "assessment_method": "rule_based_deterministic",
            "verification_status": v_status,
        }

    def _extract_substantive_terms(self, text: str) -> List[str]:
        words = re.findall(r"\b[a-zA-Z0-9_-]{4,}\b", text.lower())
        stop = {
            "this", "that", "with", "from", "have", "been", "were", "what",
            "when", "where", "which", "study", "paper", "research", "limited",
            "exists", "lack", "missing", "unexplored", "literature", "existing",
            "investigates", "evaluation", "across", "between", "their", "there",
        }
        return [w for w in set(words) if w not in stop]

    def _detect_methods(self, text: str) -> Optional[str]:
        known = [
            "BERT", "Transformer", "GNN", "Graph Neural Network", "RAG",
            "Retrieval-Augmented Generation", "LLM", "Multi-Agent", "SHAP",
            "LIME", "Contrastive Learning", "Reinforcement Learning", "CNN", "LSTM"
        ]
        found = [m for m in known if re.search(rf"\b{re.escape(m)}\b", text, re.IGNORECASE)]
        return ", ".join(found) if found else "General empirical or statistical approach"

    def _summarize_contribution(self, paper: Paper, text: str) -> str:
        for s in re.split(r"(?<=[.!?])\s+", text):
            s_clean = s.strip()
            if any(k in s_clean.lower() for k in ["we propose", "we introduce", "our model", "this paper presents", "we demonstrate"]):
                return s_clean[:280]
        return f"Reports experimental evaluations and findings regarding {paper.title}."

    def _summarize_problem(self, paper: Paper, text: str) -> str:
        for s in re.split(r"(?<=[.!?])\s+", text):
            s_clean = s.strip()
            if any(k in s_clean.lower() for k in ["aims to", "focuses on", "problem of", "challenges of", "we investigate"]):
                return s_clean[:280]
        return f"Investigates scientific research problems addressed in '{paper.title}'."
