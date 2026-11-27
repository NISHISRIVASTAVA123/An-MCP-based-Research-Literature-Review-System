# Evidence Traceability Design & Passage Verification Architecture

## 1. Traceability Mandate
A core tenet of this framework is that **no claim or gap assessment can be based on ungrounded model assertion or title similarity alone**. Every counterevidence claim must be anchored to inspectable, verbatim source passages.

## 2. Passage Data Structure
Passages are modeled via `CounterevidenceEvidence` and linked to `CounterevidenceAssessment`:
```json
{
  "id": "ev-uuid-001",
  "assessment_id": "asmt-uuid-102",
  "paper_id": "p-10492",
  "verbatim_passage": "We evaluate our decentralized barrier certificates with up to 120 interacting vehicles in dense urban intersection simulation, disproving previous scalability limits.",
  "page_number": 7,
  "section_heading": "4. Experimental Results and Scalability",
  "evidence_type": "empirical_finding",
  "is_verbatim_quote": true,
  "verification_status": "source_supported",
  "evidence_level": "level_1_fulltext_passage"
}
```

## 3. Full-Text Processing Pipeline
1. **Paper Ingestion**: Checks open-access URLs and PDF archives.
2. **Document Segmentation**: Breaks documents into titled sections (Abstract, Methodology, Experiments, Discussion, Limitations).
3. **Passage Extraction**: Uses regex and sentence tokenization to extract substantive sentences describing models, datasets, metrics, and empirical results.
4. **Coordinate Anchoring**: Captures exact section titles and page numbers.
5. **Human Audit Trail**: Researchers can inspect the passage in the UI, override classifications, and log reviewer notes which are permanently persisted and linked to the assessment.
