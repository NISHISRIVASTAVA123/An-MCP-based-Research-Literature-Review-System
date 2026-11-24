"""Evidence Graph Construction Service (Phase 3).

Orchestrates the 14-step idempotent knowledge graph construction pipeline:
1. Ingests eligible papers accepted by Phase 2 screening (omits excluded papers).
2. Connects research questions, canonical papers, authors, and objectives.
3. Normalizes methods, models, datasets, and evaluation metrics.
4. Anchors extracted findings, scientific claims, limitations, and future directions.
5. Verifiably links every claim and finding to exact source evidence passages.
6. Audits graph integrity and records reproducible build history.
"""

import time
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from backend.app.models.research_request import ResearchRequest
from backend.app.models.paper import Paper
from backend.app.models.screening import ScreeningRun, ScreeningDecision
from backend.app.models.evidence import EvidenceRecord, EvidencePassage
from backend.app.models.document import FulltextDocument
from backend.app.models.graph import (
    GraphNode,
    GraphEdge,
    GraphBuildRun,
    GraphValidationRecord,
)
from backend.app.services.persistence.graph_repository import GraphRepository
from backend.app.services.persistence.screening_repository import ScreeningRepository
from backend.app.services.persistence.evidence_repository import EvidenceRepository
from backend.app.services.graph.normalization_service import EntityNormalizationService
from backend.app.core.logging import logger


class EvidenceGraphBuilder:
    """Builds and idempotently synchronizes the scientific evidence knowledge graph."""

    def __init__(self, db: Session):
        self.db = db
        self.graph_repo = GraphRepository(db)
        self.screening_repo = ScreeningRepository(db)
        self.evidence_repo = EvidenceRepository(db)
        self.normalizer = EntityNormalizationService(db)

    def build_graph(
        self,
        request_id: str,
        trigger_type: str = "full_build",
    ) -> GraphBuildRun:
        """Executes the complete evidence graph construction pipeline for a research request."""
        start_time = time.time()
        logger.info(f"Starting evidence graph build for Request '{request_id}' (trigger: {trigger_type})")

        # 1. Retrieve Research Request
        req = self.db.get(ResearchRequest, request_id)
        if not req:
            raise ValueError(f"Research request {request_id} not found.")

        # 2. Check for screening run
        latest_screening_run = self.screening_repo.get_latest_run(request_id)
        if not latest_screening_run:
            raise ValueError(
                "No screening run found. Execute Phase 2 paper screening before building evidence graph."
            )

        decisions = self.screening_repo.get_decisions_for_run(latest_screening_run.id)
        decisions_by_paper = {d.paper_id: d for d in decisions}

        # Filter: Excluded papers MUST NOT enter the active graph
        eligible_papers: List[Tuple[Paper, ScreeningDecision]] = []
        for p in req.papers:
            dec = decisions_by_paper.get(p.id)
            if dec and dec.decision != "excluded":
                eligible_papers.append((p, dec))

        logger.info(
            f"Screening filter applied: {len(eligible_papers)} eligible papers selected "
            f"out of {len(req.papers)} total retrieved papers."
        )

        nodes_added = 0
        nodes_updated = 0
        edges_added = 0
        papers_processed = 0

        # Helper to track upserts
        def _track_node(node_res: Tuple[GraphNode, bool]):
            nonlocal nodes_added, nodes_updated
            if node_res[1]:
                nodes_added += 1
            else:
                nodes_updated += 1
            return node_res[0]

        def _track_edge(edge_res: Tuple[GraphEdge, bool]):
            nonlocal edges_added
            if edge_res[1]:
                edges_added += 1
            return edge_res[0]

        # 3. Create Root RESEARCH_REQUEST Node
        req_node = _track_node(
            self.graph_repo.upsert_node(
                request_id=request_id,
                node_type="RESEARCH_REQUEST",
                label=req.topic,
                normalized_label=req.topic.strip(),
                entity_key=f"REQUEST:{req.id}",
                properties={
                    "topic": req.topic,
                    "objective": req.objective,
                    "domain": req.domain,
                    "start_year": req.start_year,
                    "end_year": req.end_year,
                },
            )
        )

        # 4. Create User RESEARCH_OBJECTIVE Node
        obj_node = _track_node(
            self.graph_repo.upsert_node(
                request_id=request_id,
                node_type="RESEARCH_OBJECTIVE",
                label=f"Objective: {req.objective[:100]}...",
                normalized_label=req.objective.strip(),
                entity_key=f"OBJECTIVE_USER:{req.id}",
                properties={
                    "objective_text": req.objective,
                    "objective_type": "user_defined",
                },
            )
        )
        _track_edge(
            self.graph_repo.upsert_edge(
                request_id=request_id,
                source_node_id=req_node.id,
                target_node_id=obj_node.id,
                relationship_type="HAS_OBJECTIVE",
                edge_key=f"{req_node.id}:HAS_OBJECTIVE:{obj_node.id}",
            )
        )

        # 5. Create RESEARCH_QUESTION Nodes
        rq_nodes: List[GraphNode] = []
        for q in req.questions:
            rq_node = _track_node(
                self.graph_repo.upsert_node(
                    request_id=request_id,
                    node_type="RESEARCH_QUESTION",
                    label=q.question_text,
                    normalized_label=q.question_text.strip(),
                    entity_key=f"QUESTION:{q.id}",
                    properties={"question_text": q.question_text, "question_id": q.id},
                )
            )
            rq_nodes.append(rq_node)
            _track_edge(
                self.graph_repo.upsert_edge(
                    request_id=request_id,
                    source_node_id=req_node.id,
                    target_node_id=rq_node.id,
                    relationship_type="HAS_QUESTION",
                    edge_key=f"{req_node.id}:HAS_QUESTION:{rq_node.id}",
                )
            )

        # 6. Process Each Eligible Paper
        for paper, decision in eligible_papers:
            papers_processed += 1
            doc = paper.documents[0] if paper.documents else None
            latest_evidence = self.evidence_repo.get_latest_evidence_by_paper(paper.id)
            passages = self.evidence_repo.get_passages_by_paper(paper.id)

            source_scope = "abstract_only"
            if latest_evidence and latest_evidence.extraction_run:
                source_scope = latest_evidence.extraction_run.source_scope

            # Paper Node
            paper_props = {
                "title": paper.title,
                "doi": paper.doi,
                "publication_year": paper.publication_year,
                "venue": paper.venue,
                "publication_type": paper.publication_type,
                "screening_status": decision.decision,
                "is_human_override": decision.is_human_override,
                "reviewer_notes": decision.reviewer_notes,
                "has_pdf": paper.has_pdf,
                "has_fulltext": bool(doc),
                "fulltext_status": doc.extraction_status if doc else "no_fulltext",
                "source_scope": source_scope,
            }

            paper_node = _track_node(
                self.graph_repo.upsert_node(
                    request_id=request_id,
                    node_type="PAPER",
                    label=paper.title,
                    normalized_label=paper.normalized_title or paper.title.lower().strip(),
                    entity_key=f"PAPER:{paper.id}",
                    source_paper_id=paper.id,
                    properties=paper_props,
                )
            )

            # Link Request -> Paper
            _track_edge(
                self.graph_repo.upsert_edge(
                    request_id=request_id,
                    source_node_id=req_node.id,
                    target_node_id=paper_node.id,
                    relationship_type="INCLUDES_PAPER",
                    edge_key=f"{req_node.id}:INCLUDES_PAPER:{paper_node.id}",
                    source_paper_id=paper.id,
                )
            )

            # Authors
            for author_name in (paper.authors or []):
                cleaned_author = author_name.strip()
                if len(cleaned_author) < 2:
                    continue
                author_key = f"AUTHOR:{cleaned_author.lower()}"
                author_node = _track_node(
                    self.graph_repo.upsert_node(
                        request_id=request_id,
                        node_type="AUTHOR",
                        label=cleaned_author,
                        normalized_label=cleaned_author.lower(),
                        entity_key=author_key,
                        properties={"name": cleaned_author},
                    )
                )
                _track_edge(
                    self.graph_repo.upsert_edge(
                        request_id=request_id,
                        source_node_id=paper_node.id,
                        target_node_id=author_node.id,
                        relationship_type="AUTHORED_BY",
                        edge_key=f"{paper_node.id}:AUTHORED_BY:{author_node.id}",
                        source_paper_id=paper.id,
                    )
                )

            # Process Evidence Passages
            passage_nodes_by_category: Dict[str, List[GraphNode]] = {}
            for passage in passages:
                p_key = f"PASSAGE:{passage.id}"
                p_label = f"[p.{passage.page_number or 1} {passage.section_heading or 'Body'}] {passage.statement[:55]}..."
                passage_node = _track_node(
                    self.graph_repo.upsert_node(
                        request_id=request_id,
                        node_type="EVIDENCE_PASSAGE",
                        label=p_label,
                        normalized_label=passage.statement.lower()[:200],
                        entity_key=p_key,
                        source_paper_id=paper.id,
                        evidence_passage_id=passage.id,
                        properties={
                            "statement": passage.statement,
                            "exact_passage": passage.verbatim_passage,
                            "page_number": passage.page_number,
                            "section_heading": passage.section_heading,
                            "verification_status": passage.verification_status,
                            "user_notes": passage.user_notes,
                            "category": passage.category,
                        },
                    )
                )
                passage_nodes_by_category.setdefault(passage.category.lower(), []).append(passage_node)

                # Link Paper -> Evidence Passage
                _track_edge(
                    self.graph_repo.upsert_edge(
                        request_id=request_id,
                        source_node_id=paper_node.id,
                        target_node_id=passage_node.id,
                        relationship_type="HAS_EVIDENCE",
                        edge_key=f"{paper_node.id}:HAS_EVIDENCE:{passage_node.id}",
                        source_paper_id=paper.id,
                        evidence_passage_id=passage.id,
                    )
                )

            # Process Structured Evidence Dimensions
            if latest_evidence:
                def _normalize_list(val: Any) -> List[Any]:
                    if not val:
                        return []
                    if isinstance(val, dict):
                        if "items" in val and isinstance(val["items"], list):
                            return val["items"]
                        if "data" in val and isinstance(val["data"], list):
                            return val["data"]
                        return [val]
                    if isinstance(val, list):
                        return val
                    return [val]

                # 6.1 Methodologies & Models
                for method_item in _normalize_list(latest_evidence.methodology):
                    if isinstance(method_item, dict):
                        raw_method = method_item.get("approach_name") or method_item.get("name") or ""
                        raw_model = method_item.get("model_architecture")
                    else:
                        raw_method = str(method_item).strip()
                        raw_model = None

                    if not raw_method:
                        continue
                    canon_method, method_rule, method_conf, _ = self.normalizer.normalize_entity(
                        raw_method, "method", request_id
                    )
                    method_key = f"METHOD:{canon_method.lower()}"
                    method_node = _track_node(
                        self.graph_repo.upsert_node(
                            request_id=request_id,
                            node_type="METHOD",
                            label=canon_method,
                            normalized_label=canon_method.lower(),
                            entity_key=method_key,
                            properties={
                                "method_name": canon_method,
                                "raw_reported_name": raw_method,
                                "resolution_method": method_rule,
                                "confidence": method_conf,
                            },
                        )
                    )
                    _track_edge(
                        self.graph_repo.upsert_edge(
                            request_id=request_id,
                            source_node_id=paper_node.id,
                            target_node_id=method_node.id,
                            relationship_type="USES_METHOD",
                            edge_key=f"{paper_node.id}:USES_METHOD:{method_node.id}",
                            source_paper_id=paper.id,
                            properties={"raw_name": raw_method},
                        )
                    )

                    # Architecture / Model
                    if raw_model:
                        canon_model, model_rule, model_conf, _ = self.normalizer.normalize_entity(
                            raw_model, "model", request_id
                        )
                        model_key = f"MODEL:{canon_model.lower()}"
                        model_node = _track_node(
                            self.graph_repo.upsert_node(
                                request_id=request_id,
                                node_type="MODEL",
                                label=canon_model,
                                normalized_label=canon_model.lower(),
                                entity_key=model_key,
                                properties={
                                    "model_name": canon_model,
                                    "raw_reported_name": raw_model,
                                    "resolution_method": model_rule,
                                    "confidence": model_conf,
                                },
                            )
                        )
                        _track_edge(
                            self.graph_repo.upsert_edge(
                                request_id=request_id,
                                source_node_id=paper_node.id,
                                target_node_id=model_node.id,
                                relationship_type="USES_MODEL",
                                edge_key=f"{paper_node.id}:USES_MODEL:{model_node.id}",
                                source_paper_id=paper.id,
                                properties={"raw_name": raw_model},
                            )
                        )

                # 6.2 Datasets
                for ds_item in _normalize_list(latest_evidence.datasets):
                    if isinstance(ds_item, dict):
                        raw_ds = ds_item.get("dataset_name") or ds_item.get("name") or ""
                        sample_size = ds_item.get("sample_size")
                        ds_domain = ds_item.get("domain")
                    else:
                        raw_ds = str(ds_item).strip()
                        sample_size = None
                        ds_domain = None

                    if not raw_ds:
                        continue
                    canon_ds, ds_rule, ds_conf, _ = self.normalizer.normalize_entity(
                        raw_ds, "dataset", request_id
                    )
                    ds_key = f"DATASET:{canon_ds.lower()}"
                    ds_node = _track_node(
                        self.graph_repo.upsert_node(
                            request_id=request_id,
                            node_type="DATASET",
                            label=canon_ds,
                            normalized_label=canon_ds.lower(),
                            entity_key=ds_key,
                            properties={
                                "dataset_name": canon_ds,
                                "raw_reported_name": raw_ds,
                                "sample_size": sample_size,
                                "domain": ds_domain,
                                "resolution_method": ds_rule,
                                "confidence": ds_conf,
                            },
                        )
                    )
                    _track_edge(
                        self.graph_repo.upsert_edge(
                            request_id=request_id,
                            source_node_id=paper_node.id,
                            target_node_id=ds_node.id,
                            relationship_type="USES_DATASET",
                            edge_key=f"{paper_node.id}:USES_DATASET:{ds_node.id}",
                            source_paper_id=paper.id,
                            properties={"raw_name": raw_ds},
                        )
                    )

                # 6.3 Evaluation Metrics
                for metric_item in _normalize_list(latest_evidence.evaluation_metrics):
                    if isinstance(metric_item, dict):
                        raw_metric = metric_item.get("metric_name") or metric_item.get("name") or ""
                        rep_value = metric_item.get("reported_value")
                        metric_task = metric_item.get("task")
                    else:
                        raw_metric = str(metric_item).strip()
                        rep_value = None
                        metric_task = None

                    if not raw_metric:
                        continue
                    canon_metric, m_rule, m_conf, _ = self.normalizer.normalize_entity(
                        raw_metric, "metric", request_id
                    )
                    metric_key = f"METRIC:{canon_metric.lower()}"
                    metric_node = _track_node(
                        self.graph_repo.upsert_node(
                            request_id=request_id,
                            node_type="METRIC",
                            label=canon_metric,
                            normalized_label=canon_metric.lower(),
                            entity_key=metric_key,
                            properties={
                                "metric_name": canon_metric,
                                "raw_reported_name": raw_metric,
                                "resolution_method": m_rule,
                                "confidence": m_conf,
                            },
                        )
                    )
                    _track_edge(
                        self.graph_repo.upsert_edge(
                            request_id=request_id,
                            source_node_id=paper_node.id,
                            target_node_id=metric_node.id,
                            relationship_type="EVALUATED_USING",
                            edge_key=f"{paper_node.id}:EVALUATED_USING:{metric_node.id}",
                            source_paper_id=paper.id,
                            properties={
                                "reported_value": rep_value,
                                "task": metric_task,
                            },
                        )
                    )

                # 6.4 Findings & Claims
                for idx, finding_item in enumerate(_normalize_list(latest_evidence.findings)):
                    if isinstance(finding_item, dict):
                        statement = (
                            finding_item.get("finding_statement")
                            or finding_item.get("claim_text")
                            or finding_item.get("statement")
                            or finding_item.get("finding")
                            or ""
                        )
                        emp_support = finding_item.get("empirical_support")
                        significance = finding_item.get("significance")
                    else:
                        statement = str(finding_item).strip()
                        emp_support = None
                        significance = None

                    if not statement:
                        continue
                    f_hash = hashlib.md5(statement.encode()).hexdigest()[:10]
                    f_key = f"FINDING:{paper.id}:{f_hash}"
                    finding_node = _track_node(
                        self.graph_repo.upsert_node(
                            request_id=request_id,
                            node_type="FINDING",
                            label=statement[:110] + ("..." if len(statement) > 110 else ""),
                            normalized_label=statement.lower()[:200],
                            entity_key=f_key,
                            source_paper_id=paper.id,
                            properties={
                                "statement": statement,
                                "empirical_support": emp_support,
                                "significance": significance,
                                "source_scope": source_scope,
                            },
                        )
                    )
                    _track_edge(
                        self.graph_repo.upsert_edge(
                            request_id=request_id,
                            source_node_id=paper_node.id,
                            target_node_id=finding_node.id,
                            relationship_type="REPORTS_FINDING",
                            edge_key=f"{paper_node.id}:REPORTS_FINDING:{finding_node.id}",
                            source_paper_id=paper.id,
                        )
                    )

                    # Distinct Scientific Claim Node
                    claim_key = f"CLAIM:{paper.id}:{f_hash}"
                    claim_node = _track_node(
                        self.graph_repo.upsert_node(
                            request_id=request_id,
                            node_type="CLAIM",
                            label=statement[:110] + ("..." if len(statement) > 110 else ""),
                            normalized_label=statement.lower()[:200],
                            entity_key=claim_key,
                            source_paper_id=paper.id,
                            properties={
                                "claim_text": statement,
                                "claim_type": "empirical_finding_claim",
                                "verification_status": "machine_extracted",
                                "source_scope": source_scope,
                            },
                        )
                    )
                    _track_edge(
                        self.graph_repo.upsert_edge(
                            request_id=request_id,
                            source_node_id=paper_node.id,
                            target_node_id=claim_node.id,
                            relationship_type="REPORTS_CLAIM",
                            edge_key=f"{paper_node.id}:REPORTS_CLAIM:{claim_node.id}",
                            source_paper_id=paper.id,
                        )
                    )

                    # Link Supporting Evidence Passages
                    matching_passages = passage_nodes_by_category.get("finding", [])
                    for p_node in matching_passages:
                        _track_edge(
                            self.graph_repo.upsert_edge(
                                request_id=request_id,
                                source_node_id=p_node.id,
                                target_node_id=claim_node.id,
                                relationship_type="SUPPORTS",
                                edge_key=f"{p_node.id}:SUPPORTS:{claim_node.id}",
                                source_paper_id=paper.id,
                                evidence_passage_id=p_node.evidence_passage_id,
                            )
                        )
                        _track_edge(
                            self.graph_repo.upsert_edge(
                                request_id=request_id,
                                source_node_id=p_node.id,
                                target_node_id=finding_node.id,
                                relationship_type="SUPPORTS",
                                edge_key=f"{p_node.id}:SUPPORTS:{finding_node.id}",
                                source_paper_id=paper.id,
                                evidence_passage_id=p_node.evidence_passage_id,
                            )
                        )

                # 6.5 Limitations
                for idx, lim_item in enumerate(_normalize_list(latest_evidence.limitations)):
                    if isinstance(lim_item, dict):
                        lim_text = lim_item.get("limitation_text") or lim_item.get("statement") or ""
                        lim_origin = lim_item.get("limitation_type", "author_reported")
                        severity = lim_item.get("severity", "moderate")
                    else:
                        lim_text = str(lim_item).strip()
                        lim_origin = "author_reported"
                        severity = "moderate"

                    if not lim_text:
                        continue
                    l_hash = hashlib.md5(lim_text.encode()).hexdigest()[:10]
                    lim_key = f"LIMITATION:{paper.id}:{l_hash}"
                    lim_node = _track_node(
                        self.graph_repo.upsert_node(
                            request_id=request_id,
                            node_type="LIMITATION",
                            label=lim_text[:110] + ("..." if len(lim_text) > 110 else ""),
                            normalized_label=lim_text.lower()[:200],
                            entity_key=lim_key,
                            source_paper_id=paper.id,
                            properties={
                                "limitation_text": lim_text,
                                "limitation_origin": lim_origin,
                                "severity": severity,
                                "source_scope": source_scope,
                            },
                        )
                    )
                    _track_edge(
                        self.graph_repo.upsert_edge(
                            request_id=request_id,
                            source_node_id=paper_node.id,
                            target_node_id=lim_node.id,
                            relationship_type="REPORTS_LIMITATION",
                            edge_key=f"{paper_node.id}:REPORTS_LIMITATION:{lim_node.id}",
                            source_paper_id=paper.id,
                        )
                    )

                    # Link Supporting Limitation Passages
                    matching_lim_passages = passage_nodes_by_category.get("limitation", [])
                    for p_node in matching_lim_passages:
                        _track_edge(
                            self.graph_repo.upsert_edge(
                                request_id=request_id,
                                source_node_id=p_node.id,
                                target_node_id=lim_node.id,
                                relationship_type="SUPPORTS",
                                edge_key=f"{p_node.id}:SUPPORTS:{lim_node.id}",
                                source_paper_id=paper.id,
                                evidence_passage_id=p_node.evidence_passage_id,
                            )
                        )

                # 6.6 Future Directions
                for idx, dir_item in enumerate(_normalize_list(latest_evidence.future_work)):
                    if isinstance(dir_item, dict):
                        dir_text = dir_item.get("direction_text") or dir_item.get("statement") or ""
                        rationale = dir_item.get("rationale")
                    else:
                        dir_text = str(dir_item).strip()
                        rationale = None

                    if not dir_text:
                        continue
                    d_hash = hashlib.md5(dir_text.encode()).hexdigest()[:10]
                    dir_key = f"DIRECTION:{paper.id}:{d_hash}"
                    dir_node = _track_node(
                        self.graph_repo.upsert_node(
                            request_id=request_id,
                            node_type="FUTURE_DIRECTION",
                            label=dir_text[:110] + ("..." if len(dir_text) > 110 else ""),
                            normalized_label=dir_text.lower()[:200],
                            entity_key=dir_key,
                            source_paper_id=paper.id,
                            properties={
                                "direction_text": dir_text,
                                "rationale": rationale,
                                "source_scope": source_scope,
                            },
                        )
                    )
                    _track_edge(
                        self.graph_repo.upsert_edge(
                            request_id=request_id,
                            source_node_id=paper_node.id,
                            target_node_id=dir_node.id,
                            relationship_type="PROPOSES_FUTURE_DIRECTION",
                            edge_key=f"{paper_node.id}:PROPOSES_FUTURE_DIRECTION:{dir_node.id}",
                            source_paper_id=paper.id,
                        )
                    )

        # Commit all graph nodes and edges
        self.db.commit()

        # 7. Aggregate Total Graph Stats
        all_nodes = self.graph_repo.get_nodes_by_request(request_id)
        all_edges = self.graph_repo.get_edges_by_request(request_id)
        execution_time = time.time() - start_time

        summary = {
            "eligible_papers_count": len(eligible_papers),
            "excluded_papers_omitted": len(req.papers) - len(eligible_papers),
            "total_nodes": len(all_nodes),
            "total_edges": len(all_edges),
            "nodes_added": nodes_added,
            "nodes_updated": nodes_updated,
            "edges_added": edges_added,
        }

        build_run = self.graph_repo.create_build_run(
            request_id=request_id,
            trigger_type=trigger_type,
            total_nodes=len(all_nodes),
            total_edges=len(all_edges),
            nodes_added=nodes_added,
            nodes_updated=nodes_updated,
            edges_added=edges_added,
            papers_processed=papers_processed,
            execution_time_seconds=round(execution_time, 3),
            summary=summary,
            status="completed",
        )

        logger.info(
            f"Evidence Graph Build Run #{build_run.run_number} finished for {request_id}: "
            f"{len(all_nodes)} nodes, {len(all_edges)} edges in {execution_time:.2f}s."
        )
        return build_run
