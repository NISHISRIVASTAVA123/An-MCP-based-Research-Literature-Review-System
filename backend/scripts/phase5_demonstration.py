"""Phase 5 Live End-to-End Demonstration Script.

Demonstrates the complete Phase 5 lifecycle:
1. Candidate Research Gap Ingestion (from Phase 4 Synthesis)
2. Claim Decomposition (3-6 empirical sub-claims)
3. Multi-Angle Adversarial Query Generation (Direct, Methodology, Synonyms, Recency)
4. Academic Retrieval, Deduplication, and Discovery Tagging
5. Relevance Assessment & Evidence Hierarchy Enforcement (Level 1 Full-Text vs Level 2 Abstract)
6. Verifiable Passage-Level Ground Truth Extraction (Page numbers & Section headings)
7. Gap Resilience Impact Aggregation & Unresolved Claims Tracking
8. Human Researcher Review Audit & Profile Recalculation
9. Phase 5 Model Context Protocol (MCP) Tools Verification
"""

import sys
import os
import asyncio
from datetime import datetime

# Ensure backend package is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from backend.app.models.base import Base
from backend.app.models.research_request import ResearchRequest
from backend.app.models.paper import Paper
from backend.app.models.document import FulltextDocument
from backend.app.models.synthesis import SynthesisRun, CandidateResearchGap
from backend.app.models.counterevidence import (
    CounterevidenceSearchRun,
    CounterevidenceClaim,
    CounterevidenceSearchQuery,
    CounterevidencePublication,
    CounterevidenceAssessment,
    CounterevidenceEvidence,
    CounterevidenceProfile,
)
from backend.app.services.counterevidence.claim_decomposer import GapClaimDecomposer
from backend.app.services.counterevidence.query_generator import CounterevidenceQueryGenerator
from backend.app.services.counterevidence.relevance_assessor import CounterevidenceRelevanceAssessor
from backend.app.services.counterevidence.evidence_linker import CounterevidenceEvidenceLinker
from backend.app.services.counterevidence.profile_aggregator import CounterevidenceProfileAggregator
from backend.app.services.counterevidence.counterevidence_orchestrator import CounterevidenceOrchestrator
from backend.app.services.persistence.counterevidence_repository import CounterevidenceRepository
from backend.app.services.mcp.tools import (
    tool_generate_counterevidence_queries,
    tool_get_counterevidence_profile,
    tool_get_counterevidence_publications,
    tool_extract_counterevidence_evidence,
    tool_assess_counterevidence_relevance,
)

DEMO_DB = "phase5_demonstration.db"


def run_demonstration():
    print("=" * 80)
    print("PHASE 5 LIVE END-TO-END DEMONSTRATION")
    print("Explicit Counterevidence Retrieval, Evidence Traceability, and Resilience Profiling")
    print("=" * 80)

    # 1. Setup isolated database
    if os.path.exists(DEMO_DB):
        try:
            os.remove(DEMO_DB)
        except Exception:
            pass

    engine = create_engine(f"sqlite:///{DEMO_DB}", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Step 1: Seed Context from Phases 1-4
        print("\n[Step 1] Seeding Phase 1-4 Baseline Context...")
        req = ResearchRequest(
            id="req-demo-p5",
            topic="Robustness of Multimodal Large Language Models Against Adversarial Perturbations",
            objective="Evaluate visual jailbreaks, cross-modal transfer, and defense mechanisms",
            domain="Artificial Intelligence",
            start_year=2022,
            end_year=2024,
        )
        p1 = Paper(
            id="p-base-1",
            request_id=req.id,
            title="Visual Adversarial Examples in Multimodal Foundation Models",
            normalized_title="visual adversarial examples in multimodal foundation models",
            authors=["A. Carlini", "H. Chen"],
            publication_year=2023,
            doi="10.1145/demo-base-1",
        )
        synth_run = SynthesisRun(
            id="synth-demo-run-1",
            research_request_id=req.id,
            status="completed",
        )
        gap = CandidateResearchGap(
            id="gap-demo-1",
            synthesis_run_id=synth_run.id,
            research_request_id=req.id,
            title="Unexplored Cross-Modal Gradient Masking in Vision-Language Defenses",
            category="methodological_gap",
            description="Existing multimodal defense strategies rely on single-modality preprocessing and fail to defend against joint image-text gradient optimization across cross-attention layers.",
            rationale="Identified through cross-paper limitation analysis in 14 multimodal alignment papers.",
            observed_pattern="Single-modality defenses exhibit 82% failure under joint cross-attention perturbations.",
            preliminary_confidence=0.86,
            confidence_explanation="High confidence based on verified CARLA and VQA benchmarks.",
            assumptions=["Cross-attention weights cannot be dynamically neutralized during forward pass."],
            known_limitations=["Tested primarily on CLIP and LLaVA-1.5."],
            potential_counterexamples=["Dual-stream adversarial training or feature projection purification."],
            unresolved_questions=["Can randomized cross-attention smoothing prevent joint gradient convergence?"],
            suggested_validation_queries=["joint image text adversarial defense cross attention smoothing"],
            supporting_paper_ids=[p1.id],
        )

        session.add_all([req, p1, synth_run, gap])
        session.commit()
        print(f"  ✓ Request created: '{req.topic}'")
        print(f"  ✓ Candidate Gap loaded: '{gap.title}' (Confidence: {gap.preliminary_confidence})")

        # Step 2: Claim Decomposition
        print("\n[Step 2] Decomposing Candidate Gap into Empirical Sub-Claims...")
        decomposer = GapClaimDecomposer()
        claims = decomposer.decompose_gap(gap)
        print(f"  ✓ Decomposed into {len(claims)} atomic empirical sub-claims:")
        for idx, c in enumerate(claims, 1):
            print(f"    [{idx}] ({c['claim_type']}): \"{c['claim_text']}\"")

        # Step 3: Multi-Angle Query Generation
        print("\n[Step 3] Formulating Adversarial Counterevidence Queries...")
        query_gen = CounterevidenceQueryGenerator()
        queries = query_gen.generate_queries_for_claims(
            candidate_gap_id=gap.id,
            gap_title=gap.title,
            claims=claims,
            databases=["openalex", "semantic_scholar", "arxiv", "crossref"],
        )
        print(f"  ✓ Formulated {len(queries)} multi-angle academic search queries:")
        for q in queries[:4]:
            print(f"    - Type: {q['query_type'].upper()} ({q['source_database']})")
            print(f"      Query: {q['query_text']}")
            print(f"      Rationale: {q['search_rationale']}")

        # Step 4: Simulated Multi-Provider Retrieval & Deduplication
        print("\n[Step 4] Simulating Academic Retrieval & Provenance Segregation...")
        p_discovered_1 = Paper(
            id="p-disc-1",
            request_id=req.id,
            title="Joint Cross-Attention Smoothing: Defending Multimodal Models Against Transferable Attacks",
            normalized_title="joint cross attention smoothing defending multimodal models against transferable attacks",
            authors=["Elena Rostova", "Marcus Zhao"],
            publication_year=2024,
            venue="CVPR 2024",
            doi="10.1109/cvpr.2024.1001",
            abstract="We introduce Joint Cross-Attention Smoothing (JCAS), demonstrating robust defense against simultaneous visual and textual perturbations across 5 foundation models with 89% accuracy retention.",
        )
        ft_doc_1 = FulltextDocument(
            id="ft-doc-demo-1",
            paper_id=p_discovered_1.id,
            source_type="open_access_pdf",
            extraction_status="success",
            extracted_sections=[
                {
                    "heading": "3. Joint Attention Smoothing Algorithm",
                    "text": "Our proposed defense dynamically perturbs cross-attention projection matrices during inference, neutralizing gradient alignment.",
                    "page_number": 4,
                },
                {
                    "heading": "5. Empirical Evaluation and Benchmark Results",
                    "text": "Under white-box joint optimization attacks on LLaVA-1.5, JCAS reduces attack success rate from 88.4% to 9.2%, directly resolving the vulnerability in cross-modal alignment.",
                    "page_number": 7,
                },
            ],
        )

        p_discovered_2 = Paper(
            id="p-disc-2",
            request_id=req.id,
            title="A Survey of Robustness in Vision-Language Models",
            normalized_title="a survey of robustness in vision language models",
            authors=["David Kim"],
            publication_year=2023,
            venue="ACM Computing Surveys",
            doi="10.1145/acm.2023.2002",
            abstract="A comprehensive survey outlining existing vulnerabilities in multimodal foundation models and future research directions.",
        )

        session.add_all([p_discovered_1, ft_doc_1, p_discovered_2])
        session.commit()
        print(f"  ✓ Ingested Discovered Publication 1 (Full-Text): '{p_discovered_1.title}'")
        print(f"  ✓ Ingested Discovered Publication 2 (Abstract-Only): '{p_discovered_2.title}'")

        # Step 5: Relevance Assessment & Evidence Hierarchy
        print("\n[Step 5] Evaluating Publications Against Gap (Strict Evidence Hierarchy)...")
        assessor = CounterevidenceRelevanceAssessor()
        asmt_1 = assessor.assess_paper_against_gap(p_discovered_1, gap, fulltext_doc=ft_doc_1)
        asmt_2 = assessor.assess_paper_against_gap(p_discovered_2, gap, fulltext_doc=None)

        print(f"  Publication 1 Assessment:")
        print(f"    - Relevance Classification: {asmt_1['relevance_classification']}")
        print(f"    - Impact Classification:    {asmt_1['impact_classification']}")
        print(f"    - Evidence Level:           {asmt_1['evidence_level']} (Full-Text Ground Truth)")
        print(f"    - Verification Status:      {asmt_1['verification_status']}")
        print(f"    - Identified Contribution:  \"{asmt_1['actual_contribution_identified'][:120]}...\"")

        print(f"  Publication 2 Assessment:")
        print(f"    - Relevance Classification: {asmt_2['relevance_classification']}")
        print(f"    - Evidence Level:           {asmt_2['evidence_level']} (Abstract Only / Precluded from Level 1)")

        # Persist Search Run & Assessments in DB
        repo = CounterevidenceRepository(session)
        run = repo.create_search_run(
            research_request_id=req.id,
            candidate_gap_id=gap.id,
        )
        repo.record_publication(
            candidate_gap_id=gap.id,
            search_run_id=run.id,
            paper_id=p_discovered_1.id,
            discovery_source="openalex",
            is_newly_discovered=True,
        )
        repo.record_publication(
            candidate_gap_id=gap.id,
            search_run_id=run.id,
            paper_id=p_discovered_2.id,
            discovery_source="arxiv",
            is_newly_discovered=True,
        )
        repo.update_run_status(
            run_id=run.id,
            status="completed",
            claims_count=len(claims),
            queries_count=len(queries),
            pubs_count=2,
            new_count=2,
        )

        db_asmt_1 = repo.save_assessment(
            candidate_gap_id=gap.id,
            paper_id=p_discovered_1.id,
            search_run_id=run.id,
            relevance_classification=asmt_1["relevance_classification"],
            impact_classification=asmt_1["impact_classification"],
            explanation=asmt_1["explanation"],
            actual_contribution_identified=asmt_1["actual_contribution_identified"],
            research_problem_addressed=asmt_1["research_problem_addressed"],
            relevant_methodology=asmt_1.get("relevant_methodology"),
            evidence_level=asmt_1["evidence_level"],
            is_abstract_based=asmt_1["is_abstract_based"],
            confidence_indicator=asmt_1["confidence_indicator"],
            assessment_method=asmt_1["assessment_method"],
            verification_status=asmt_1["verification_status"],
        )

        db_asmt_2 = repo.save_assessment(
            candidate_gap_id=gap.id,
            paper_id=p_discovered_2.id,
            search_run_id=run.id,
            relevance_classification=asmt_2["relevance_classification"],
            impact_classification=asmt_2["impact_classification"],
            explanation=asmt_2["explanation"],
            actual_contribution_identified=asmt_2["actual_contribution_identified"],
            research_problem_addressed=asmt_2["research_problem_addressed"],
            relevant_methodology=asmt_2.get("relevant_methodology"),
            evidence_level=asmt_2["evidence_level"],
            is_abstract_based=asmt_2["is_abstract_based"],
            confidence_indicator=asmt_2["confidence_indicator"],
            assessment_method=asmt_2["assessment_method"],
            verification_status=asmt_2["verification_status"],
        )

        # Step 6: Verifiable Passage Ground Truth Linking
        print("\n[Step 6] Extracting Verifiable Source Passages with Coordinates...")
        linker = CounterevidenceEvidenceLinker(session)
        ev_items = linker.link_evidence_to_assessment(
            assessment=db_asmt_1,
            paper=p_discovered_1,
            candidate_gap_id=gap.id,
            fulltext_doc=ft_doc_1,
        )
        print(f"  ✓ Extracted {len(ev_items)} passage-level ground truth records:")
        for ev in ev_items:
            print(f"    - Section: \"{ev.section_heading}\" | Page: {ev.page_number}")
            print(f"      Quote:   \"{ev.verbatim_passage[:130]}...\"")
            print(f"      Status:  {ev.verification_status} ({ev.evidence_type})")

        # Step 7: Gap Resilience Impact Aggregation
        print("\n[Step 7] Aggregating Gap Resilience Profile...")
        aggregator = CounterevidenceProfileAggregator(session)
        profile = aggregator.aggregate_profile_for_gap(
            candidate_gap_id=gap.id,
            search_run_id=run.id,
        )
        print(f"  ✓ Profile Synthesized:")
        print(f"    - Gap Resilience Impact:       {profile.impact_assessment.upper()}")
        print(f"    - Direct Counterevidence Count: {profile.direct_counterevidence_count}")
        print(f"    - Partial Counterevidence Count:{profile.partial_counterevidence_count}")
        print(f"    - Executive Summary:           \"{profile.executive_summary[:160]}...\"")
        print(f"    - Remaining Unresolved Claims: {len(profile.remaining_unresolved_claims)}")
        for uc in profile.remaining_unresolved_claims:
            print(f"      * {uc}")

        # Step 8: Human Researcher Audit Simulation
        print("\n[Step 8] Simulating Human Researcher Audit & Override...")
        updated_asmt = repo.update_assessment_review(
            assessment_id=db_asmt_1.id,
            relevance_classification="partial_counterevidence",
            reviewer_reference="Senior AI Researcher (Lead Auditor)",
            reviewer_notes="Paper JCAS operates on static images only; continuous video streaming cross-modal attacks remain open.",
        )
        print(f"  ✓ Human review saved for Assessment {db_asmt_1.id}:")
        print(f"    - Human Review Status:   {updated_asmt.human_review_status}")
        print(f"    - Override Classification: {updated_asmt.relevance_classification}")
        print(f"    - Reviewer Notes:        \"{updated_asmt.reviewer_notes}\"")

        # Recalculate profile
        recalculated_profile = aggregator.aggregate_profile_for_gap(gap.id, run.id)
        print(f"  ✓ Recalculated Impact after Human Audit: {recalculated_profile.impact_assessment.upper()}")

        # Step 9: Phase 5 MCP Tools Verification
        print("\n[Step 9] Executing Phase 5 Model Context Protocol (MCP) Tools...")
        # Tool 1: Queries
        mcp_q = tool_generate_counterevidence_queries(gap.id, db=session)
        print(f"  ✓ MCP tool_generate_counterevidence_queries: Generated {len(mcp_q['generated_queries'])} queries")

        # Tool 2: Profile
        mcp_prof = tool_get_counterevidence_profile(gap.id, db=session)
        print(f"  ✓ MCP tool_get_counterevidence_profile: Impact = {mcp_prof['impact_assessment']}")

        # Tool 3: Publications
        mcp_pubs = tool_get_counterevidence_publications(gap.id, db=session)
        print(f"  ✓ MCP tool_get_counterevidence_publications: {len(mcp_pubs)} publications retrieved")

        # Tool 4: Evidence passages
        mcp_evd = tool_extract_counterevidence_evidence(gap.id, db=session)
        print(f"  ✓ MCP tool_extract_counterevidence_evidence: {len(mcp_evd)} verbatim quotes retrieved")

        # Tool 5: Relevance assessment
        mcp_eval = tool_assess_counterevidence_relevance(gap.id, p_discovered_1.id, db=session)
        print(f"  ✓ MCP tool_assess_counterevidence_relevance: Classification = {mcp_eval['relevance_classification']}")

        print("\n" + "=" * 80)
        print("ALL 9 STEPS IN PHASE 5 LIVE DEMONSTRATION EXECUTED SUCCESSFULLY (100% PASS)")
        print("=" * 80)

    finally:
        session.close()
        engine.dispose()
        if os.path.exists(DEMO_DB):
            try:
                os.remove(DEMO_DB)
            except Exception:
                pass


if __name__ == "__main__":
    run_demonstration()
