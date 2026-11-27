# Counterevidence Classification Framework & Evidence Hierarchy

## 1. Relevance Classification Taxonomy
Retrieved publications are classified into five explicit tiers:

1. **`direct_counterevidence`**:
   - The publication directly implements, benchmarks, or validates the exact capability claimed as an unexplored gap.
   - **Requirement**: Must be backed by Level 1 (Full-Text) passage ground truth.

2. **`partial_counterevidence`**:
   - The publication addresses substantial components, evaluates a closely related architecture, or provides evidence for a sub-claim while leaving other sub-claims open.
   - Also used when strong evidence exists in the abstract, but full text is not yet verified.

3. **`related_evidence`**:
   - Shares domain vocabulary and technical themes, but does not solve or disprove the claimed gap.

4. **`not_relevant`**:
   - Semantic drift or off-target keyword collision (e.g., medical barrier functions vs control barrier functions).

5. **`insufficient_information`**:
   - Metadata-only or truncated abstract insufficient for scholarly evaluation.

---

## 2. Evidence Hierarchy Levels

| Level | Name | Authoritative Weight | Criteria |
|---|---|---|---|
| **Level 1** | Full-Text Ground Truth | Authoritative (Highest) | Verbatim excerpt extracted from Section and Page of verified PDF/Full-Text document. |
| **Level 2** | Abstract-Supported | Provisional (Medium) | Explicit claim identified in scientific abstract. Marked: *"Requires full-text passage verification"*. |
| **Level 3** | Citation-Inferred | Weak (Low) | Mentioned in related work or citation context without empirical evaluation details. |
| **Level 4** | Metadata-Only | Inconclusive (Lowest) | Only title, venue, or year available; zero textual passage evidence. |

---

## 3. Gap Impact Assessment & Resilience Rating
The `CounterevidenceProfileAggregator` evaluates the balance of evidence to assign an overall resilience rating to the candidate gap:

- **`strongly_challenged`**: Direct counterevidence confirmed with Level 1 full-text passages. High probability of false/hallucinated research gap.
- **`partially_challenged`**: Partial counterevidence or multiple abstract-level challenges exist. Gap must be narrowed or qualified.
- **`weakly_challenged`**: Only related evidence found; core sub-claims remain unaddressed.
- **`unchallenged`**: Zero counterevidence found after exhaustive multi-angle querying. Gap exhibits high resilience and genuine scientific novelty.
- **`inconclusive`**: Insufficient full-text availability across retrieved papers.
