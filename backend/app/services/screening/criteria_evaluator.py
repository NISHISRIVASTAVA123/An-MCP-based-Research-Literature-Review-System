"""Criteria Evaluator for Academic Paper Screening.

Evaluates papers across 7 rigorous dimensions:
1. Topic relevance
2. Objective relevance
3. Research question alignment
4. Publication timeframe
5. Publication type compatibility
6. User-defined inclusion criteria
7. User-defined exclusion criteria
"""

import re
from typing import Dict, Any, List, Tuple
from backend.app.models.paper import Paper
from backend.app.models.research_request import ResearchRequest


def _stem(w: str) -> str:
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith("es") and len(w) > 4:
        return w[:-2]
    if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
        return w[:-1]
    if w.endswith("ed") and len(w) > 4:
        return w[:-2]
    return w


def _normalize_tokens(text: str) -> set:
    if not text:
        return set()
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    stop_words = {
        "the", "a", "an", "and", "or", "in", "on", "at", "for", "with", "about",
        "against", "between", "into", "through", "during", "before", "after", "above",
        "below", "to", "from", "up", "down", "of", "off", "over", "under", "again",
        "further", "then", "once", "here", "there", "when", "where", "why", "how",
        "all", "any", "both", "each", "few", "more", "most", "other", "some", "such",
        "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "can",
        "will", "just", "don", "should", "now", "approach", "study", "paper", "presents",
    }
    return {_stem(w) for w in cleaned.split() if len(w) > 2 and w not in stop_words}


class ScreeningCriteriaEvaluator:
    """Evaluates paper eligibility against research scope and criteria."""

    def evaluate_paper(
        self,
        paper: Paper,
        request: ResearchRequest,
    ) -> Tuple[str, str, List[str], List[str], List[str], List[str], float]:
        """Evaluates an individual paper against all screening dimensions.

        Returns:
            Tuple of:
            - decision: "included" | "excluded" | "needs_human_review"
            - reason: Human-readable explanation
            - criteria_evaluated: List of dimensions tested
            - criteria_satisfied: List of dimensions passed
            - criteria_unsatisfied: List of dimensions failed
            - missing_information: List of missing metadata fields
            - confidence_score: Estimated heuristic confidence
        """
        criteria_evaluated: List[str] = []
        criteria_satisfied: List[str] = []
        criteria_unsatisfied: List[str] = []
        missing_info: List[str] = []

        paper_text = f"{paper.title} {paper.abstract or ''} {' '.join(paper.keywords or [])}"
        paper_tokens = _normalize_tokens(paper_text)

        # 1. Missing information check
        if not paper.abstract:
            missing_info.append("abstract")

        # 2. Publication Timeframe check
        criteria_evaluated.append("publication_timeframe")
        if paper.publication_year is not None:
            if request.start_year <= paper.publication_year <= request.end_year:
                criteria_satisfied.append("publication_timeframe")
            else:
                criteria_unsatisfied.append("publication_timeframe")
                return (
                    "excluded",
                    f"Publication year ({paper.publication_year}) is outside requested review timeframe ({request.start_year}–{request.end_year}).",
                    criteria_evaluated,
                    criteria_satisfied,
                    criteria_unsatisfied,
                    missing_info,
                    0.95,
                )
        else:
            missing_info.append("publication_year")

        # 3. User Exclusion Criteria check
        criteria_evaluated.append("exclusion_criteria")
        exclusion_triggered = False
        reasons_excluded = []
        if request.exclusion_criteria:
            for excl in request.exclusion_criteria:
                excl_clean = excl.strip().lower()
                if not excl_clean:
                    continue
                # Check for explicit keywords like "non-english", "opinion", "keynote"
                tokens = _normalize_tokens(excl_clean)
                overlap = tokens.intersection(paper_tokens)
                if len(overlap) >= 2 or (len(tokens) == 1 and bool(overlap)):
                    exclusion_triggered = True
                    reasons_excluded.append(excl)

        if exclusion_triggered:
            criteria_unsatisfied.append("exclusion_criteria")
            return (
                "excluded",
                f"Paper matched specified exclusion criteria: {', '.join(reasons_excluded)}.",
                criteria_evaluated,
                criteria_satisfied,
                criteria_unsatisfied,
                missing_info,
                0.85,
            )
        else:
            criteria_satisfied.append("exclusion_criteria")

        # 4. Publication Type check
        criteria_evaluated.append("publication_type")
        if request.publication_types and paper.publication_type:
            requested_types = [t.lower() for t in request.publication_types]
            if paper.publication_type.lower() in requested_types or any(t in paper.publication_type.lower() for t in requested_types):
                criteria_satisfied.append("publication_type")
            else:
                criteria_unsatisfied.append("publication_type")
                return (
                    "excluded",
                    f"Publication type '{paper.publication_type}' does not match requested publication types: {', '.join(request.publication_types)}.",
                    criteria_evaluated,
                    criteria_satisfied,
                    criteria_unsatisfied,
                    missing_info,
                    0.90,
                )
        else:
            criteria_satisfied.append("publication_type")

        # 5. Topic Relevance check
        criteria_evaluated.append("topic_relevance")
        topic_tokens = _normalize_tokens(request.topic)
        title_tokens = _normalize_tokens(paper.title)
        topic_overlap = topic_tokens.intersection(paper_tokens)
        title_overlap = topic_tokens.intersection(title_tokens)

        # Proportion of topic tokens matched
        topic_match_ratio = len(topic_overlap) / max(len(topic_tokens), 1)

        # 6. Objective Relevance check
        criteria_evaluated.append("objective_relevance")
        obj_tokens = _normalize_tokens(request.objective)
        obj_overlap = obj_tokens.intersection(paper_tokens)
        obj_match_ratio = len(obj_overlap) / max(len(obj_tokens), 1)

        # 7. Research Questions Relevance check
        criteria_evaluated.append("rq_relevance")
        rq_matches = 0
        if request.questions:
            for q in request.questions:
                q_tokens = _normalize_tokens(q.question_text)
                if len(q_tokens.intersection(paper_tokens)) >= 2:
                    rq_matches += 1

        # 8. User Inclusion Criteria check
        criteria_evaluated.append("inclusion_criteria")
        inclusion_satisfied = True
        if request.inclusion_criteria:
            matched_inc = 0
            for inc in request.inclusion_criteria:
                inc_tokens = _normalize_tokens(inc)
                if bool(inc_tokens.intersection(paper_tokens)):
                    matched_inc += 1
                elif "peer" in inc_tokens and paper.publication_type in ("journal-article", "proceedings-article"):
                    matched_inc += 1
            if matched_inc == 0 and len(request.inclusion_criteria) > 0:
                inclusion_satisfied = False

        if inclusion_satisfied:
            criteria_satisfied.append("inclusion_criteria")
        else:
            criteria_unsatisfied.append("inclusion_criteria")
            return (
                "excluded",
                f"Paper does not satisfy mandatory user inclusion criteria: {', '.join(request.inclusion_criteria)}.",
                criteria_evaluated,
                criteria_satisfied,
                criteria_unsatisfied,
                missing_info,
                0.75,
            )

        # Decision synthesis
        if topic_match_ratio >= 0.40 or len(title_overlap) >= 2:
            criteria_satisfied.append("topic_relevance")
            if obj_match_ratio >= 0.20 or rq_matches >= 1:
                criteria_satisfied.append("objective_relevance")
                criteria_satisfied.append("rq_relevance")

                # If missing abstract but strong title match, mark for human review
                if not paper.abstract:
                    return (
                        "needs_human_review",
                        "Paper appears relevant based on title, but full abstract is missing from academic providers.",
                        criteria_evaluated,
                        criteria_satisfied,
                        criteria_unsatisfied,
                        missing_info,
                        0.60,
                    )

                return (
                    "included",
                    f"Satisfies topic relevance ({int(topic_match_ratio*100)}% concept overlap), aligns with research objective and timeframe.",
                    criteria_evaluated,
                    criteria_satisfied,
                    criteria_unsatisfied,
                    missing_info,
                    min(0.70 + (topic_match_ratio * 0.25), 0.95),
                )
            else:
                criteria_satisfied.append("topic_relevance")
                return (
                    "needs_human_review",
                    "Matches research topic concepts, but relevance to specific research questions requires human confirmation.",
                    criteria_evaluated,
                    criteria_satisfied,
                    criteria_unsatisfied,
                    missing_info,
                    0.55,
                )
        elif topic_match_ratio >= 0.20 or len(title_overlap) >= 1:
            criteria_satisfied.append("topic_relevance")
            return (
                "needs_human_review",
                "Partial concept overlap detected. Abstract requires human review to confirm thematic alignment.",
                criteria_evaluated,
                criteria_satisfied,
                criteria_unsatisfied,
                missing_info,
                0.50,
            )
        else:
            criteria_unsatisfied.append("topic_relevance")
            return (
                "excluded",
                "Insufficient thematic relevance: paper content exhibits less than 20% vocabulary overlap with research topic.",
                criteria_evaluated,
                criteria_satisfied,
                criteria_unsatisfied,
                missing_info,
                0.80,
            )

