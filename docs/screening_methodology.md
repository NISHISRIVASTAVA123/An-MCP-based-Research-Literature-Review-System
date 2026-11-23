# Scientific Paper Screening Methodology

## 1. Overview and Theoretical Basis

The paper screening system is designed to simulate the rigorous screening protocol of a PRISMA (Preferred Reporting Items for Systematic Reviews and Meta-Analyses) workflow. It evaluates every paper retrieved from academic databases against the researcher's configured objective, research questions, timeframe, and explicit inclusion/exclusion criteria.

---

## 2. Multi-Stage Screening Protocol

Screening operates in sequential stages to maximize precision while minimizing unnecessary full-text processing overhead:

```
[Retrieved Paper]
       │
       ▼
[Stage 1: Metadata & Abstract Screening]
  ├── Timeframe Validation (start_year <= year <= end_year)
  ├── Publication Type Verification (journal, conference_proceeding, preprint)
  ├── Topic & Objective Relevance Scoring
  ├── Methodological Framing Detection
  └── Explicit Exclusion Keyword Scanning
       │
       ├─────────────────────────────────────────┐
       ▼                                         ▼
[Decision: Excluded]                   [Decision: Eligible for Full-Text]
                                                 │
                                                 ▼
                                  [Stage 2: Full-Text Verification]
                                    ├── Empirical Evidence Verification
                                    ├── Detailed Inclusion Criteria Matching
                                    └── Data Completeness Audit
                                                 │
                                                 ├───────────────────────┐
                                                 ▼                       ▼
                                       [Decision: Included]    [Decision: Needs Human Review]
```

---

## 3. Seven Evaluation Dimensions

Each paper is evaluated across 7 distinct dimensions:

### 1. Topic Relevance
- **Evaluation**: Evaluates the lexical overlap and semantic coverage between the paper title/abstract and the research topic keywords.
- **Weighting**: Title matches receive 2.5x weighting relative to abstract matches.

### 2. Research Objective & Question Alignment
- **Evaluation**: Scans for terminology reflecting the user's research objective and specific research questions.
- **Pass Threshold**: Requires positive alignment with at least one research question or key objective aspect.

### 3. Timeframe Compliance
- **Evaluation**: Validates `paper.publication_year` against `[request.start_year, request.end_year]`.
- **Edge Cases**: If publication year is missing from database metadata, the paper is flagged with `missing_information: ["publication_year"]` and marked for human review rather than prematurely rejected.

### 4. Publication Type Matching
- **Evaluation**: Verifies publication medium against user-allowed types (e.g., `journal-article`, `proceedings-article`, `book-chapter`, `preprint`).

### 5. Methodological Presence
- **Evaluation**: Detects methodological vocabulary (e.g., `model`, `algorithm`, `framework`, `architecture`, `benchmark`, `experiment`, `survey`, `evaluation`).
- **Rule**: Papers lacking any identifiable methodology statement are flagged as theoretical/speculative or marked for triage.

### 6. Empirical Outcome & Findings Presence
- **Evaluation**: Identifies whether the work reports concrete outcomes, performance metrics, or experimental findings (e.g., `accuracy`, `latency`, `f1-score`, `demonstrated`, `improved`, `reduced`, `achieved`).

### 7. Explicit Inclusion & Exclusion Rules
- **Inclusion Rules**: User-defined mandatory concepts (e.g., "Must evaluate deep neural architectures").
- **Exclusion Rules**: Disqualifying traits (e.g., "Exclude non-English publications", "Exclude purely position papers"). A match against an exclusion rule results in immediate exclusion with the matching reason cited.

---

## 4. Confidence Score Formulation

The automated confidence score $C \in [0.0, 1.0]$ is computed as a weighted harmonic mean:

$$C = \sum_{i=1}^{N} w_i \cdot s_i$$

Where:
- $w_{\text{topic}} = 0.35$
- $w_{\text{objective}} = 0.25$
- $w_{\text{timeframe}} = 0.15$
- $w_{\text{pub\_type}} = 0.10$
- $w_{\text{methodology}} = 0.15$

If critical metadata (such as the abstract or publication year) is absent, $C$ is automatically capped at $0.50$ and the paper is assigned a decision of `needs_human_review`.

---

## 5. Human-in-the-Loop Override Policy

1. **Non-Destructive Storage**: When a researcher modifies an automated screening decision, the original automated decision is stored in `original_decision`.
2. **Reviewer Attribution**: The reviewer's identity, timestamp (`reviewed_at`), and required justification (`reviewer_notes`) are permanently recorded in the audit trail.
3. **Reproducibility**: The exact criteria configuration used at the moment of screening is snapshotted in `ScreeningRun.criteria_snapshot`. Subsequent changes to the research request do not overwrite historical run criteria.
