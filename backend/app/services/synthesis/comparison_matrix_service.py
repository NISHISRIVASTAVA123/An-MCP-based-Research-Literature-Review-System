"""Paper Comparison Matrix Service (Phase 4).

Generates dynamic, multidimensional comparative matrices across selected literature,
extracting objectives, methodologies, models, benchmarks, metrics, findings, and limitations.
Supports filtering, sorting, pagination, and CSV/Markdown export.
"""

import io
import csv
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.schemas.synthesis import (
    PaperComparisonRow,
    PaperComparisonMatrixResponse,
)
from backend.app.models.paper import Paper
from backend.app.services.synthesis.evidence_retrieval_service import EvidenceRetrievalService


class PaperComparisonMatrixService:
    """Constructs dynamic multi-paper comparison tables with verifiable evidence attribution."""

    def __init__(self, db: Session):
        self.db = db
        self.retrieval_service = EvidenceRetrievalService(db)

    def generate_matrix(
        self,
        request_id: str,
        paper_ids: Optional[List[str]] = None,
        method_filter: Optional[str] = None,
        dataset_filter: Optional[str] = None,
        model_filter: Optional[str] = None,
        year_filter: Optional[int] = None,
        sort_by: str = "year_desc",
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> PaperComparisonMatrixResponse:
        """Builds a structured comparison matrix for selected or eligible papers."""
        # 1. Fetch target papers
        if paper_ids:
            all_papers = [
                p for p in self.retrieval_service.get_eligible_papers_for_request(request_id)
                if p.id in paper_ids
            ]
        else:
            all_papers = self.retrieval_service.get_eligible_papers_for_request(request_id)

        rows: List[PaperComparisonRow] = []

        for paper in all_papers:
            # Check year filter
            if year_filter and paper.publication_year != year_filter:
                continue

            # Fetch evidence record & passages
            ev_rec = self.retrieval_service.get_structured_evidence_by_paper(paper.id)
            passages = self.retrieval_service.get_evidence_passages_by_paper(paper.id)

            # Extract dimensions cleanly
            methodologies = self._extract_names(getattr(ev_rec, "methodology", None) if ev_rec else None, "method_name")
            models = self._extract_names(getattr(ev_rec, "models", None) if ev_rec else None, "model_name")
            if not models and ev_rec and getattr(ev_rec, "methodology", None):
                meth = ev_rec.methodology
                if isinstance(meth, dict):
                    models = self._extract_names(meth.get("models") or meth.get("algorithms"), "model_name")
                elif isinstance(meth, list):
                    models = self._extract_names(meth, "model_architecture")
            datasets = self._extract_names(getattr(ev_rec, "datasets", None) if ev_rec else None, "dataset_name")
            metrics = self._extract_names(getattr(ev_rec, "evaluation_metrics", getattr(ev_rec, "metrics", None)) if ev_rec else None, "metric_name")
            findings = self._extract_strings(getattr(ev_rec, "findings", None) if ev_rec else None, "finding_text")
            limitations = self._extract_strings(getattr(ev_rec, "limitations", None) if ev_rec else None, "limitation_text")
            future_dirs = self._extract_strings(getattr(ev_rec, "future_work", None) if ev_rec else None, "direction_text")
            objectives = self._extract_strings(getattr(ev_rec, "research_objective", getattr(ev_rec, "objectives", None)) if ev_rec else None, "objective_text")

            # Check method filter
            if method_filter:
                clean_mf = method_filter.strip().lower()
                if not any(clean_mf in m.lower() for m in methodologies):
                    continue

            # Check dataset filter
            if dataset_filter:
                clean_df = dataset_filter.strip().lower()
                if not any(clean_df in d.lower() for d in datasets):
                    continue

            # Check model filter
            if model_filter:
                clean_modf = model_filter.strip().lower()
                if not any(clean_modf in m.lower() for m in models):
                    continue

            row = PaperComparisonRow(
                paper_id=paper.id,
                title=paper.title,
                authors=paper.authors or [],
                year=paper.publication_year,
                venue=paper.venue,
                research_objectives=objectives or ["Not reported"],
                research_questions=[paper.title],
                methodologies=methodologies or ["Not reported"],
                models=models or ["Not reported"],
                datasets=datasets or ["Not reported"],
                metrics=metrics or ["Not reported"],
                experimental_setup="Empirical benchmark evaluation" if datasets else "Not reported",
                main_findings=findings or ["Not reported"],
                reported_limitations=limitations or ["Not reported"],
                future_directions=future_dirs or ["Not reported"],
                evidence_count=len(passages),
            )
            rows.append(row)

        # 2. Sorting
        if sort_by == "year_desc":
            rows.sort(key=lambda r: (r.year or 0), reverse=True)
        elif sort_by == "year_asc":
            rows.sort(key=lambda r: (r.year or 0))
        elif sort_by == "title_asc":
            rows.sort(key=lambda r: r.title.lower())
        elif sort_by == "evidence_count":
            rows.sort(key=lambda r: r.evidence_count, reverse=True)

        total_count = len(rows)

        # 3. Pagination
        if limit:
            rows = rows[offset : offset + limit]

        columns = [
            "Paper Title",
            "Authors",
            "Year",
            "Venue",
            "Research Objectives",
            "Methodologies",
            "Models / Architectures",
            "Datasets",
            "Evaluation Metrics",
            "Main Findings",
            "Reported Limitations",
            "Future Directions",
            "Evidence Count",
        ]

        return PaperComparisonMatrixResponse(
            request_id=request_id,
            total_papers=total_count,
            columns=columns,
            rows=rows,
        )

    def export_matrix_csv(self, matrix: PaperComparisonMatrixResponse) -> str:
        """Serializes the comparison matrix to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(matrix.columns)

        for r in matrix.rows:
            writer.writerow([
                r.title,
                "; ".join(r.authors),
                r.year or "Not reported",
                r.venue or "Not reported",
                "; ".join(r.research_objectives),
                "; ".join(r.methodologies),
                "; ".join(r.models),
                "; ".join(r.datasets),
                "; ".join(r.metrics),
                "; ".join(r.main_findings),
                "; ".join(r.reported_limitations),
                "; ".join(r.future_directions),
                r.evidence_count,
            ])
        return output.getvalue()

    def export_matrix_markdown(self, matrix: PaperComparisonMatrixResponse) -> str:
        """Serializes the comparison matrix to standard GitHub Markdown."""
        lines = [
            f"# Literature Paper Comparison Matrix (Total Papers: {matrix.total_papers})\n",
            "| Title | Year | Methodologies | Models | Datasets | Metrics | Findings | Limitations |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for r in matrix.rows:
            clean_title = r.title.replace("|", "/")[:60]
            methods = ", ".join(r.methodologies)[:40]
            models = ", ".join(r.models)[:30]
            datasets = ", ".join(r.datasets)[:30]
            metrics = ", ".join(r.metrics)[:30]
            findings = "; ".join(r.main_findings)[:50]
            limits = "; ".join(r.reported_limitations)[:50]
            lines.append(
                f"| **{clean_title}** | {r.year or 'N/A'} | {methods} | {models} | {datasets} | {metrics} | {findings} | {limits} |"
            )
        return "\n".join(lines)

    def _extract_names(self, data: Any, key_name: str) -> List[str]:
        """Safely extracts names from structured list or dictionary."""
        if not data:
            return []
        items = data.get("items", []) if isinstance(data, dict) else data
        if not isinstance(items, list):
            items = [items]

        results = []
        for item in items:
            if isinstance(item, dict):
                val = (
                    item.get(key_name)
                    or item.get("name")
                    or item.get("label")
                    or item.get("approach_name")
                    or item.get("model_architecture")
                    or item.get("model_name")
                    or item.get("method_name")
                    or item.get("dataset_name")
                    or item.get("metric_name")
                )
                if val and str(val).strip():
                    results.append(str(val).strip())
            elif isinstance(item, str) and item.strip():
                results.append(item.strip())
        return list(dict.fromkeys(results))  # preserve order deduplication

    def _extract_strings(self, data: Any, key_name: str) -> List[str]:
        """Safely extracts statements/strings from structured evidence blocks."""
        if not data:
            return []
        items = data.get("items", []) if isinstance(data, dict) else data
        if not isinstance(items, list):
            items = [items]

        results = []
        for item in items:
            if isinstance(item, dict):
                val = (
                    item.get(key_name)
                    or item.get("statement")
                    or item.get("text")
                    or item.get("finding")
                    or item.get("claim_text")
                    or item.get("limitation_text")
                    or item.get("direction_text")
                    or item.get("objective_text")
                    or item.get("problem_statement")
                )
                if val and str(val).strip():
                    results.append(str(val).strip())
            elif isinstance(item, str) and item.strip():
                results.append(item.strip())
        return list(dict.fromkeys(results))
