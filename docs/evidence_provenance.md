# Evidence Provenance and Claim Lineage Architecture

## 1. Provenance Invariant

A central hypothesis of this research framework is that unsupported claims and hallucinations can be systematically eliminated by enforcing strict, queryable **provenance chains** back to original academic source documents.

In our system:
> **No scientific claim, finding, or limitation exists in isolation.**  
> Every claim is strictly linked via an unbroken provenance chain to an exact, unparaphrased passage in an authenticated source document.

---

## 2. Complete Provenance Lineage Model

```
+-------------------------------------------------------------------------------+
|                                SCIENTIFIC CLAIM                               |
|  claim_id, claim_text, claim_type, verification_status                        |
+-------------------------------------------------------------------------------+
                                        │
                                        │ (SUPPORTS edge)
                                        ▼
+-------------------------------------------------------------------------------+
|                                EVIDENCE PASSAGE                               |
|  evidence_passage_id, verbatim_passage, page_number, section_heading,         |
|  char_start, char_end, verification_status (machine_extracted / user_verified)|
+-------------------------------------------------------------------------------+
                                        │
                                        │ (HAS_EVIDENCE edge)
                                        ▼
+-------------------------------------------------------------------------------+
|                                 SOURCE PAPER                                  |
|  paper_id, title, doi, publication_year, publication_venue, authors           |
+-------------------------------------------------------------------------------+
                                        │
                                        │ (Extraction context)
                                        ▼
+-------------------------------------------------------------------------------+
|                                DOCUMENT & FILE                                |
|  document_id, source_scope (full_text vs abstract_only),                      |
|  file_hash_sha256, storage_path, page_count                                   |
+-------------------------------------------------------------------------------+
                                        │
                                        │ (Traceability)
                                        ▼
+-------------------------------------------------------------------------------+
|                                EXTRACTION RUN                                 |
|  extraction_run_id, extractor_backend (rule_based / llm_groq), created_at     |
+-------------------------------------------------------------------------------+
                                        │
                                        │ (Context)
                                        ▼
+-------------------------------------------------------------------------------+
|                               RESEARCH REQUEST                                |
|  request_id, topic, research_objective, research_questions                    |
+-------------------------------------------------------------------------------+
```

---

## 3. Provenance Schema (`ProvenanceChainResponse`)

The query engine and API return the full lineage in a consolidated structure:

```json
{
  "claim_id": "b3e921d7-4b53-4881-8b27-02f6cb6495ce",
  "claim_text": "A notable limitation is sensitivity to adversarial token perturbations.",
  "claim_type": "empirical_finding_claim",
  "verification_status": "machine_extracted",
  "has_evidence_passage": true,
  "evidence_passage_id": "pas-7ed15db7",
  "exact_passage": "A notable limitation is sensitivity to adversarial token perturbations.",
  "page_number": 1,
  "section_heading": "Abstract",
  "paper_id": "live-p2-2ffbba",
  "paper_title": "Local Interpretable Explanations for Misinformation Detection with BERT and LIME",
  "paper_doi": "10.1109/live.2ffbba.2",
  "publication_year": 2021,
  "source_scope": "abstract_only",
  "document_id": null,
  "extraction_run_id": "17f2ef56-79e0-4c50-a026-f78557b82563",
  "extractor_backend": "rule_based",
  "research_request_id": "live-req-2ffbba",
  "is_provenance_complete": true,
  "audit_notes": null
}
```

---

## 4. Querying and Inspecting Provenance

### 4.1 REST API
```http
GET /api/evidence-graph/claims/{claim_id}/provenance
```

### 4.2 Model Context Protocol (MCP) Tool
Autonomous verification agents in subsequent phases invoke:
```python
tool_get_evidence_provenance(claim_id="b3e921d7-...")
```

### 4.3 Interactive Frontend Inspector
Clicking on any `CLAIM` or `FINDING` node in the **Evidence Graph Canvas** opens a slide-over details drawer with a **"Inspect Provenance Chain"** button. Clicking this surfaces a full-screen modal showing:
1. The exact claim statement and verification badge.
2. The supporting verbatim quote with page number and section heading.
3. The source paper's title, DOI link, and publication year.
4. The extraction run ID and backend provenance.
