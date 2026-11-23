# Scientific Evidence Extraction Schema & Zero-Fabrication Protocol

## 1. Zero-Fabrication Protocol

In academic literature reviews, automated hallucination or speculative fabrication of scientific claims poses a critical risk to research gap validity. The Phase 2 evidence extraction engine enforces a strict **Zero-Fabrication Constraint**:

1. **No Imputed Metrics**: If a paper reports "our model improves performance" without an explicit numerical percentage or metric, no numerical value is inferred or generated.
2. **Strict Scope Partitioning**: Every evidence record is explicitly tagged with `source_scope`:
   - `full_text`: Extracted from complete paper body, sections, and references.
   - `abstract_only`: Extracted solely from the abstract. The system NEVER claims an entire paper has been analysed when only its abstract was accessible.
3. **Author-Reported vs System-Inferred Limitations**: Limitations explicitly acknowledged by authors are classified as `author_reported`. Any limitation deduced from methodology constraints or absence of evaluations is classified as `system_inferred`.
4. **Verbatim Text Anchoring**: Every primary claim, finding, or limitation is anchored to an exact textual passage (`verbatim_passage`) in the source text, with page number and section heading.

---

## 2. Structured JSON Schema

Below is the complete TypeScript / Pydantic schema for an extracted scientific evidence record:

```json
{
  "paper_id": "string (UUID)",
  "source_scope": "full_text | abstract_only",
  "extractor_backend": "rule_based | llm_openai | mock",
  
  "research_objective": {
    "problem_statement": "string",
    "primary_goal": "string",
    "target_domain": "string"
  },

  "methodology": {
    "model_type": "string (e.g., Transformer, GNN, ResNet)",
    "algorithms": ["string"],
    "architectural_components": ["string"],
    "theoretical_foundations": ["string"],
    "assumptions": ["string"]
  },

  "datasets": [
    {
      "name": "string (e.g., ImageNet, SQuAD)",
      "size": "string (optional)",
      "domain": "string",
      "access_type": "open | private | benchmark"
    }
  ],

  "evaluation_metrics": [
    {
      "metric_name": "string (e.g., Accuracy, F1-Score, BLEU, Latency)",
      "metric_value": "string | number (optional)",
      "baseline_comparison": "string (optional)"
    }
  ],

  "findings": [
    {
      "claim": "string (succinct claim)",
      "finding_type": "empirical | theoretical | observational",
      "quantitative_evidence": "string (verbatim metric statement)",
      "source_passage": "string (exact quotation)",
      "section_heading": "string",
      "page_number": "number (optional)"
    }
  ],

  "limitations": [
    {
      "limitation_text": "string",
      "limitation_type": "methodological | data_constraint | scalability | generalizability | computational_cost",
      "is_author_reported": true,
      "source_passage": "string",
      "page_number": "number (optional)"
    }
  ],

  "future_work": ["string"],
  "key_contributions": ["string"],
  "epistemic_uncertainties": ["string"],
  "open_questions": ["string"]
}
```

---

## 3. Evidence Passage Anchoring Schema

Each scientific claim is mirrored as an individual row in the `evidence_passages` relational table to enable claim-level graph construction (Phase 3) and verification (Phase 6):

| Field | Type | Description |
|---|---|---|
| `id` | VARCHAR PK | Passage UUID |
| `paper_id` | VARCHAR FK | Reference to parent paper |
| `category` | VARCHAR | `finding`, `limitation`, `methodology`, `metric`, `objective` |
| `statement` | TEXT | Succinct extracted claim statement |
| `verbatim_passage` | TEXT | Exact, verbatim substring from source document |
| `page_number` | INTEGER | Physical PDF page index (1-based) |
| `section_heading` | VARCHAR | Inferred section heading (e.g., `4. Results`, `6. Discussion`) |
| `char_start` | INTEGER | Character start index in extracted text buffer |
| `char_end` | INTEGER | Character end index in extracted text buffer |
| `verification_status`| VARCHAR | `machine_extracted`, `user_verified`, `flagged_incorrect`, `unsupported_needs_review` |
| `user_notes` | TEXT | Optional researcher commentary during manual verification |
