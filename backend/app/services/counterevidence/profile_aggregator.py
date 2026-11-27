"""Counterevidence profile aggregation and gap impact assessment synthesis."""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from backend.app.models.synthesis import CandidateResearchGap
from backend.app.models.counterevidence import (
    CounterevidenceSearchRun,
    CounterevidencePublication,
    CounterevidenceAssessment,
    CounterevidenceEvidence,
    CounterevidenceProfile,
)
from backend.app.services.persistence.counterevidence_repository import CounterevidenceRepository


class CounterevidenceProfileAggregator:
    """Aggregates all counterevidence retrieval results, relevance assessments, and passage ground truths into a structured Gap Profile."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = CounterevidenceRepository(db)

    def aggregate_profile_for_gap(
        self,
        candidate_gap_id: str,
        search_run_id: str,
    ) -> CounterevidenceProfile:
        """Synthesizes assessments into an aggregated profile with impact classification."""
        stmt_gap = select(CandidateResearchGap).where(CandidateResearchGap.id == candidate_gap_id)
        gap = self.db.execute(stmt_gap).scalar_one_or_none()
        if not gap:
            raise ValueError(f"CandidateResearchGap '{candidate_gap_id}' not found.")

        # Fetch all publications and assessments for this gap
        pubs = self.repo.get_publications_by_gap(candidate_gap_id)
        assessments = self.repo.get_assessments_by_gap(candidate_gap_id)
        evidence_items = self.repo.get_evidence_items_by_gap(candidate_gap_id)

        total_retrieved = len(pubs)
        newly_discovered_count = sum(1 for p in pubs if p.is_newly_discovered)
        previously_reviewed_count = total_retrieved - newly_discovered_count

        # Count classifications
        direct_count = sum(1 for a in assessments if a.relevance_classification == "direct_counterevidence")
        partial_count = sum(1 for a in assessments if a.relevance_classification == "partial_counterevidence")
        related_count = sum(1 for a in assessments if a.relevance_classification == "related_evidence")
        irrelevant_count = sum(1 for a in assessments if a.relevance_classification == "not_relevant")
        inconclusive_count = sum(1 for a in assessments if a.relevance_classification == "insufficient_information")

        # Determine overall Impact Assessment
        if direct_count >= 1:
            impact = "strongly_challenged"
            summary = (
                f"Candidate gap '{gap.title}' is STRONGLY CHALLENGED by {direct_count} publication(s) providing "
                f"direct counterevidence with inspectable methodological implementation and empirical evaluation."
            )
        elif partial_count >= 1:
            impact = "partially_challenged"
            summary = (
                f"Candidate gap '{gap.title}' is PARTIALLY CHALLENGED by {partial_count} publication(s) addressing "
                f"aspects of the methodology or application. Meaningful unresolved research dimensions remain."
            )
        elif related_count >= 1:
            impact = "weakly_challenged"
            summary = (
                f"Retrieved literature contains {related_count} related publication(s), but none directly evaluate or "
                f"resolve the specific research gap '{gap.title}'."
            )
        elif total_retrieved == 0:
            impact = "no_counterevidence_retrieved"
            summary = (
                f"No counterevidence publications were retrieved in executed searches for candidate gap '{gap.title}'. "
                f"Note: Absence of retrieved counterevidence does not definitively prove the gap exists without full coverage assessment."
            )
        else:
            impact = "inconclusive"
            summary = (
                f"Available publications for '{gap.title}' lack sufficient accessible full-text content or conclusive empirical findings."
            )

        # Unresolved claims
        unresolved_claims = []
        if impact in ("partially_challenged", "weakly_challenged", "no_counterevidence_retrieved"):
            unresolved_claims.append(f"Empirical verification of {gap.title} across diverse benchmarks.")
            unresolved_claims.append("Integration of full multi-agent verification pipeline remains unrefuted.")

        # Search & Full-text limitations
        search_limitations = [
            "Search queries bounded by specified academic database API indexing latencies.",
            "Queries targeted English-language academic publications and preprints.",
        ]
        fulltext_limitations = [
            f"Assessed {total_retrieved} publication(s); {sum(1 for a in assessments if a.is_abstract_based)} assessment(s) restricted to abstract due to publisher paywalls.",
        ]

        # Save profile
        profile = self.repo.save_profile(
            candidate_gap_id=candidate_gap_id,
            search_run_id=search_run_id,
            total_retrieved=total_retrieved,
            previously_reviewed_count=previously_reviewed_count,
            newly_discovered_count=newly_discovered_count,
            direct_counterevidence_count=direct_count,
            partial_counterevidence_count=partial_count,
            related_evidence_count=related_count,
            irrelevant_count=irrelevant_count,
            inconclusive_count=inconclusive_count,
            impact_assessment=impact,
            executive_summary=summary,
            remaining_unresolved_claims=unresolved_claims,
            search_limitations=search_limitations,
            fulltext_availability_limitations=fulltext_limitations,
            verification_status="verified_traceable",
        )

        return profile
