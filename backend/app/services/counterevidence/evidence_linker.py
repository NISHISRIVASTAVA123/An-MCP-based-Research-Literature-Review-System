"""Passage-level ground-truth extractor and verifiable evidence linker for counterevidence."""

import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.models.paper import Paper
from backend.app.models.document import FulltextDocument
from backend.app.models.evidence import EvidencePassage
from backend.app.models.counterevidence import CounterevidenceAssessment, CounterevidenceEvidence
from backend.app.services.persistence.counterevidence_repository import CounterevidenceRepository


class CounterevidenceEvidenceLinker:
    """Extracts, validates, and anchors inspectable verbatim source passages for counterevidence assessments."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = CounterevidenceRepository(db)

    def link_evidence_to_assessment(
        self,
        assessment: CounterevidenceAssessment,
        paper: Paper,
        candidate_gap_id: str,
        fulltext_doc: Optional[FulltextDocument] = None,
    ) -> List[CounterevidenceEvidence]:
        """Extracts verbatim source passages and creates traceable CounterevidenceEvidence records."""
        evidence_items: List[CounterevidenceEvidence] = []

        # 1. Check if full-text document sections are accessible
        if fulltext_doc and fulltext_doc.extracted_sections:
            for sec in fulltext_doc.extracted_sections:
                sec_heading = sec.get("heading", "Document Body")
                page_num = sec.get("page_number", 1)
                text = sec.get("text", "")

                # Search for methodology or result sentences
                sentences = re.split(r"(?<=[.!?])\s+", text)
                for s in sentences:
                    s_clean = s.strip()
                    if len(s_clean) < 30:
                        continue

                    # Look for empirical contribution or finding markers
                    if any(k in s_clean.lower() for k in [
                        "we propose", "we implement", "our model achieves", "results demonstrate",
                        "accuracy of", "outperforms", "significant improvement", "we benchmark",
                        "our proposed", "we evaluate", "we demonstrate", "reduces attack", "resolves"
                    ]):
                        item = self.repo.save_evidence_item(
                            assessment_id=assessment.id,
                            candidate_gap_id=candidate_gap_id,
                            paper_id=paper.id,
                            verbatim_passage=s_clean,
                            page_number=page_num,
                            section_heading=sec_heading,
                            evidence_summary=f"Reports empirical implementation / evaluation in {sec_heading}: {s_clean[:140]}...",
                            source_reference=f"{paper.title} (Page {page_num}, Section: {sec_heading})",
                            evidence_type="experimental_result" if "result" in s_clean.lower() else "methodology",
                            is_verbatim_quote=True,
                            verification_status="source_supported",
                        )
                        evidence_items.append(item)
                        if len(evidence_items) >= 3:
                            break
                if len(evidence_items) >= 3:
                    break

        # 2. Check if Phase 2 evidence passages already exist for this paper
        if not evidence_items:
            stmt = select(EvidencePassage).where(EvidencePassage.paper_id == paper.id).limit(3)
            existing_passages = list(self.db.execute(stmt).scalars().all())
            for pas in existing_passages:
                item = self.repo.save_evidence_item(
                    assessment_id=assessment.id,
                    candidate_gap_id=candidate_gap_id,
                    paper_id=paper.id,
                    evidence_passage_id=pas.id,
                    verbatim_passage=pas.verbatim_passage or pas.statement,
                    page_number=pas.page_number,
                    section_heading=pas.section_heading or "Full Text",
                    evidence_summary=f"Passage grounding: {pas.statement[:140]}...",
                    source_reference=f"{paper.title} (Page {pas.page_number or 1})",
                    evidence_type="finding" if pas.category == "finding" else "methodology",
                    is_verbatim_quote=bool(pas.verbatim_passage),
                    verification_status=pas.verification_status or "source_supported",
                )
                evidence_items.append(item)

        # 3. Fallback to abstract if full-text passages are unavailable
        if not evidence_items and paper.abstract:
            abstract_sentences = re.split(r"(?<=[.!?])\s+", paper.abstract)
            for s in abstract_sentences:
                s_clean = s.strip()
                if len(s_clean) > 30 and any(k in s_clean.lower() for k in ["we propose", "results show", "our approach", "we achieve", "we evaluate"]):
                    item = self.repo.save_evidence_item(
                        assessment_id=assessment.id,
                        candidate_gap_id=candidate_gap_id,
                        paper_id=paper.id,
                        verbatim_passage=s_clean,
                        page_number=1,
                        section_heading="Abstract",
                        evidence_summary=f"Abstract statement: {s_clean[:140]}...",
                        source_reference=f"{paper.title} (Abstract)",
                        evidence_type="finding",
                        is_verbatim_quote=True,
                        verification_status="abstract_supported",
                    )
                    evidence_items.append(item)
                    break

        return evidence_items
