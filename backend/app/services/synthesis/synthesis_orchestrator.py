"""Literature Synthesis Orchestrator (Phase 4).

Coordinates the end-to-end execution of a synthesis run: evidence retrieval,
comparison matrix generation, theme identification, pattern analysis,
narrative synthesis, and candidate research-gap generation.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.synthesis import SynthesisRun
from backend.app.schemas.synthesis import SynthesisRunCreate, SynthesisRunResponse
from backend.app.services.persistence.synthesis_repository import SynthesisRepository
from backend.app.services.synthesis.evidence_retrieval_service import EvidenceRetrievalService
from backend.app.services.synthesis.comparison_matrix_service import PaperComparisonMatrixService
from backend.app.services.synthesis.theme_service import ResearchThemeService
from backend.app.services.synthesis.pattern_analysis_service import PatternAnalysisService
from backend.app.services.synthesis.synthesis_engine import LiteratureSynthesisEngine
from backend.app.services.synthesis.gap_generator import CandidateResearchGapGenerator
from backend.app.core.logging import logger


class SynthesisOrchestrator:
    """Coordinates versioned literature synthesis runs."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = SynthesisRepository(db)
        self.retrieval_service = EvidenceRetrievalService(db)
        self.matrix_service = PaperComparisonMatrixService(db)
        self.theme_service = ResearchThemeService(db)
        self.pattern_service = PatternAnalysisService(db)
        self.synthesis_engine = LiteratureSynthesisEngine(db)
        self.gap_generator = CandidateResearchGapGenerator(db)

    def execute_synthesis_run(
        self,
        request_id: str,
        payload: Optional[SynthesisRunCreate] = None,
    ) -> SynthesisRun:
        """Executes a full, versioned literature synthesis run."""
        # 1. Determine selected papers
        eligible_papers = self.retrieval_service.get_eligible_papers_for_request(request_id)
        if payload and payload.selected_paper_ids:
            selected_ids = [p.id for p in eligible_papers if p.id in payload.selected_paper_ids]
        else:
            selected_ids = [p.id for p in eligible_papers]

        if not selected_ids:
            raise ValueError(f"No eligible screened papers found for research request '{request_id}'.")

        graph_version = self.retrieval_service.get_latest_graph_build_version(request_id)

        config = payload.synthesis_configuration if payload else {}
        prompt_version = payload.prompt_version if payload else "v1.0-academic"
        model_provider = payload.model_provider if payload else "rule_deterministic"
        model_name = payload.model_name if payload else "deterministic-engine"

        # 2. Create SynthesisRun record
        run = self.repo.create_synthesis_run(
            request_id=request_id,
            selected_paper_ids=selected_ids,
            synthesis_configuration=config,
            prompt_version=prompt_version,
            model_provider=model_provider,
            model_name=model_name,
            evidence_graph_version=graph_version,
        )

        try:
            logger.info(f"Starting SynthesisRun #{run.run_number} ({run.id}) for request {request_id} with {len(selected_ids)} papers.")

            # Stage A: Identify Themes
            self.repo.update_synthesis_run_status(run.id, "identifying_themes")
            themes_data = self.theme_service.identify_themes(request_id, selected_paper_ids=selected_ids)
            self.repo.create_literature_themes(run.id, themes_data)

            # Stage B: Analyze Patterns
            self.repo.update_synthesis_run_status(run.id, "analysing_patterns")
            patterns_data = self.pattern_service.analyze_patterns(request_id, selected_paper_ids=selected_ids)
            self.repo.create_literature_patterns(run.id, patterns_data)

            # Stage C: Generate Structured Narrative Synthesis
            self.repo.update_synthesis_run_status(run.id, "generating_synthesis")
            synthesis_output = self.synthesis_engine.generate_synthesis(
                request_id, selected_paper_ids=selected_ids, config=config
            )

            # Stage D: Generate Candidate Research Gaps
            self.repo.update_synthesis_run_status(run.id, "generating_candidate_gaps")
            self.gap_generator.generate_candidate_gaps(
                request_id=request_id,
                synthesis_run_id=run.id,
                selected_paper_ids=selected_ids,
                patterns=patterns_data,
                themes=themes_data,
            )

            # Mark Completed
            completed_run = self.repo.update_synthesis_run_status(
                run.id,
                status="completed",
                summary_narrative=synthesis_output.get("sections", {}),
            )
            logger.info(f"SynthesisRun {run.id} successfully completed.")
            return completed_run or run

        except Exception as e:
            logger.exception(f"SynthesisRun {run.id} failed: {e}")
            self.repo.update_synthesis_run_status(run.id, status="failed", error_details=str(e))
            raise
