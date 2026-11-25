# Candidate Gap Evidence Traceability (Phase 4)

## 1. Traceability Architecture

Every `CandidateResearchGap` maintains an unbroken, bidirectional provenance chain to source scientific literature:

```
+-------------------------------------------------------------+
|                     CandidateResearchGap                    |
|  id: 7ac7240f-a0ed-494b-873c-0decdc1998b2                   |
|  title: "Out-of-Distribution Generalization Gap"             |
|  category: "generalisation_gap"                             |
+-------------------------------------------------------------+
                              │
                              ▼
+-------------------------------------------------------------+
|                       GapEvidenceLink                       |
|  id: link-001                                               |
|  relationship_type: "reports_limitation"                    |
|  contribution_explanation: "Author reports limitation..."   |
+-------------------------------------------------------------+
                              │
                              ▼
+-------------------------------------------------------------+
|                       EvidencePassage                       |
|  id: pass-3                                                 |
|  page_number: 7                                             |
|  section_heading: "Generalization Bounds"                   |
|  verbatim_passage: "Fidelity degrades significantly when    |
|    tested on out-of-distribution Bemis-Murcko scaffolds."  |
+-------------------------------------------------------------+
                              │
                              ▼
+-------------------------------------------------------------+
|                            Paper                            |
|  id: p-003                                                  |
|  title: "ProtGNN: Interpretable Biomolecular Graph..."      |
|  authors: ["Zaixi Zhang", "Qi Liu", "Chee-Kong Lee"]        |
|  year: 2023 | venue: "Bioinformatics"                      |
+-------------------------------------------------------------+
```

---

## 2. Provenance API

The `SynthesisReviewService.get_gap_with_provenance(gap_id)` endpoint returns the complete trace:
- Full candidate gap metadata.
- All associated `GapEvidenceLink` objects.
- Embedded passage text, section heading, and page number.
- Full bibliographic metadata of the supporting paper.

Researchers can inspect this provenance chain in the frontend **Gap Detail & Review Drawer** before approving any gap for Phase 5 retrieval.
