# Research Theme Identification Specification (Phase 4)

## 1. Objective

The `ResearchThemeService` identifies recurring conceptual themes across the retrieved scientific literature by clustering normalized entities from the Phase 3 Evidence Graph and Phase 2 structured evidence extractions.

---

## 2. Theme Discovery Categories

Themes are clustered into three primary scientific categories:

1. **Methodological Themes**:
   - Identifies recurring algorithmic techniques, frameworks, and architectures across papers.
   - Example: *"Multi-Head Attention Methodological Framework"*
   - Quantified by paper frequency: *"Investigation and application of Multi-Head Attention across 3 of 4 retrieved studies."*
   - Links supporting claims and evidence passages directly to the theme.

2. **Empirical Benchmark Themes**:
   - Identifies recurring evaluation datasets and benchmark testbeds.
   - Example: *"Empirical Evaluation on MoleculeNet BBBP"*
   - Tracks how many papers share the same experimental baseline.

3. **Recurring Limitation Themes**:
   - Clusters common constraints explicitly reported by authors across independent papers.
   - Example: *"Scalability & Computational Complexity Constraints"*
   - Identifies shared bottlenecks (e.g., quadratic memory complexity, real-time inference latency, out-of-distribution performance collapse).

---

## 3. Scope Qualification Principle

Every identified theme is strictly qualified with explicit denominator statements:
- Theme descriptions explicitly state the exact sample size (e.g. `"2 of 3 retrieved studies in this collection"`).
- Themes are never framed as representative of the entire scientific field, but strictly bounded to the active search collection.
