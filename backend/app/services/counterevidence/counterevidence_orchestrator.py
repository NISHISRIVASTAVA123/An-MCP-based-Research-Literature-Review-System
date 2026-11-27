"""Counterevidence Retrieval Agent Orchestrator (Phase 5).

Coordinates the end-to-end multi-agent counterevidence workflow:
Claim Decomposition -> Query Generation -> Multi-Provider Retrieval ->
Relevance Classification -> Verifiable Passage Extraction -> Profile Synthesis.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.models.synthesis import CandidateResearchGap
from backend.app.models.counterevidence import CounterevidenceSearchRun
from backend.app.models.document import FulltextDocument
from backend.app.services.persistence.counterevidence_repository import CounterevidenceRepository
from backend.app.services.counterevidence.claim_decomposer import GapClaimDecomposer
from backend.app.services.counterevidence.query_generator import CounterevidenceQueryGenerator
from backend.app.services.counterevidence.retrieval_service import CounterevidenceRetrievalService
from backend.app.services.counterevidence.relevance_assessor import CounterevidenceRelevanceAssessor
from backend.app.services.counterevidence.evidence_linker import CounterevidenceEvidenceLinker
from backend.app.services.counterevidence.profile_aggregator import CounterevidenceProfileAggregator
from backend.app.core.logging import logger


class CounterevidenceOrchestrator:
    """Orchestrates the complete autonomous counterevidence retrieval and evidence grounding pipeline."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = CounterevidenceRepository(db)
        self.decomposer = GapClaimDecomposer()
        self.query_gen = CounterevidenceQueryGenerator()
        self.retrieval = CounterevidenceRetrievalService(db)
        self.assessor = CounterevidenceRelevanceAssessor()
        self.linker = CounterevidenceEvidenceLinker(db)
        self.aggregator = CounterevidenceProfileAggregator(db)

    async def execute_search_for_gap(
        self,
        candidate_gap_id: str,
        research_request_id: str,
        databases: Optional[List[str]] = None,
        max_results_per_query: int = 10,
        search_run: Optional[CounterevidenceSearchRun] = None,
        auto_extract_evidence: bool = True,
    ) -> Dict[str, Any]:
        """Runs the complete counterevidence pipeline for a single candidate research gap."""
        stmt = select(CandidateResearchGap).where(CandidateResearchGap.id == candidate_gap_id)
        gap = self.db.execute(stmt).scalar_one_or_none()
        if not gap:
            raise ValueError(f"CandidateResearchGap '{candidate_gap_id}' not found.")

        # Create or update run record
        if not search_run:
            search_run = self.repo.create_search_run(
                research_request_id=research_request_id,
                candidate_gap_id=candidate_gap_id,
                initiated_by="agent",
                configuration_snapshot={
                    "gap_title": gap.title,
                    "databases": databases or ["openalex", "semantic_scholar", "arxiv", "crossref"],
                    "max_results": max_results_per_query,
                },
            )

        run_id = search_run.id

        try:
            # 1. Claim Decomposition
            self.repo.update_run_status(run_id, "decomposing_claims")
            claim_dicts = self.decomposer.decompose_gap(gap)
            saved_claims = []
            for c_dict in claim_dicts:
                c = self.repo.save_claim(
                    candidate_gap_id=candidate_gap_id,
                    claim_text=c_dict["claim_text"],
                    claim_type=c_dict["claim_type"],
                    original_gap_statement=c_dict.get("original_gap_statement"),
                    generated_keywords=c_dict.get("generated_keywords", []),
                    assumptions_investigated=c_dict.get("assumptions_investigated", []),
                    order_index=c_dict.get("order_index", 0),
                )
                c_dict["id"] = c.id
                saved_claims.append(c)

            # 2. Query Generation
            self.repo.update_run_status(run_id, "generating_queries", claims_count=len(saved_claims))
            query_dicts = self.query_gen.generate_queries_for_claims(
                candidate_gap_id=candidate_gap_id,
                gap_title=gap.title,
                claims=claim_dicts,
                databases=databases,
            )
            saved_queries = []
            for q_dict in query_dicts:
                q = self.repo.save_query(
                    search_run_id=run_id,
                    candidate_gap_id=candidate_gap_id,
                    query_text=q_dict["query_text"],
                    query_type=q_dict["query_type"],
                    search_rationale=q_dict["search_rationale"],
                    source_database=q_dict["source_database"],
                    claim_id=q_dict.get("claim_id"),
                )
                saved_queries.append(q)

            # 3. Multi-Provider Retrieval
            self.repo.update_run_status(run_id, "searching_databases", queries_count=len(saved_queries))
            all_papers = []
            new_pubs_count = 0

            for q_model in saved_queries:
                papers_and_status = await self.retrieval.execute_query(
                    query_model=q_model,
                    research_request_id=research_request_id,
                    limit=max_results_per_query,
                )
                for paper, is_new in papers_and_status:
                    all_papers.append(paper)
                    if is_new:
                        new_pubs_count += 1

            # 4. Relevance Assessment & Evidence Extraction
            self.repo.update_run_status(
                run_id,
                "assessing_relevance",
                pubs_count=len(all_papers),
                new_count=new_pubs_count,
            )

            # Assess unique papers
            seen_paper_ids = set()
            for paper in all_papers:
                if paper.id in seen_paper_ids:
                    continue
                seen_paper_ids.add(paper.id)

                # Look up fulltext doc if present
                stmt_doc = select(FulltextDocument).where(FulltextDocument.paper_id == paper.id)
                ft_doc = self.db.execute(stmt_doc).scalar_one_or_none()

                assessment_data = self.assessor.assess_paper_against_gap(
                    paper=paper,
                    gap=gap,
                    fulltext_doc=ft_doc,
                )

                # Save assessment record
                assessment = self.repo.save_assessment(
                    candidate_gap_id=candidate_gap_id,
                    paper_id=paper.id,
                    search_run_id=run_id,
                    relevance_classification=assessment_data["relevance_classification"],
                    impact_classification=assessment_data["impact_classification"],
                    explanation=assessment_data["explanation"],
                    actual_contribution_identified=assessment_data["actual_contribution_identified"],
                    research_problem_addressed=assessment_data["research_problem_addressed"],
                    relevant_methodology=assessment_data.get("relevant_methodology"),
                    evidence_level=assessment_data["evidence_level"],
                    is_abstract_based=assessment_data["is_abstract_based"],
                    confidence_indicator=assessment_data["confidence_indicator"],
                    assessment_method=assessment_data.get("assessment_method", "rule_based_deterministic"),
                    verification_status=assessment_data["verification_status"],
                )

                # 5. Extract and link inspectable evidence passages
                if auto_extract_evidence and assessment.relevance_classification in (
                    "direct_counterevidence", "partial_counterevidence", "related_evidence"
                ):
                    self.linker.link_evidence_to_assessment(
                        assessment=assessment,
                        paper=paper,
                        candidate_gap_id=candidate_gap_id,
                        fulltext_doc=ft_doc,
                    )

            # 6. Synthesize Counterevidence Profile
            self.repo.update_run_status(run_id, "generating_profile")
            profile = self.aggregator.aggregate_profile_for_gap(
                candidate_gap_id=candidate_gap_id,
                search_run_id=run_id,
            )

            # Mark run as completed
            self.repo.update_run_status(run_id, "completed")

            return {
                "search_run_id": run_id,
                "candidate_gap_id": candidate_gap_id,
                "claims_count": len(saved_claims),
                "queries_count": len(saved_queries),
                "total_retrieved": profile.total_retrieved,
                "direct_counterevidence_count": profile.direct_counterevidence_count,
                "partial_counterevidence_count": profile.partial_counterevidence_count,
                "impact_assessment": profile.impact_assessment,
                "status": "completed",
            }

        except Exception as e:
            logger.error(f"Error in counterevidence pipeline for gap {candidate_gap_id}: {e}", exc_info=True)
            self.repo.update_run_status(run_id, "failed", error_message=str(e))
            raise

    async def execute_search_for_all_gaps(
        self,
        research_request_id: str,
        databases: Optional[List[str]] = None,
        max_results_per_query: int = 10,
    ) -> List[Dict[str, Any]]:
        """Runs counterevidence retrieval across all candidate gaps in a research request."""
        stmt = (
            select(CandidateResearchGap)
            .where(CandidateResearchGap.research_request_id == research_request_id)
            .order_by(CandidateResearchGap.created_at)
        )
        gaps = list(self.db.execute(stmt).scalars().all())
        if not gaps:
            return []

        results = []
        for gap in gaps:
            res = await self.execute_search_for_gap(
                candidate_gap_id=gap.id,
                research_request_id=research_request_id,
                databases=databases,
                max_results_per_query=max_results_per_query,
            )
            results.append(res)
        return results
