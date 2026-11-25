# Research Pattern Analysis Specification (Phase 4)

## 1. Overview

The `PatternAnalysisService` analyzes empirical frequencies, methodology distributions, dataset concentrations, evaluation metric rigor, and temporal trends across the retrieved literature collection.

---

## 2. Quantified Patterns

The service extracts four primary classes of scientific patterns:

1. **Methodology Usage Frequencies**:
   - Frequency count and percentage distribution of distinct methodologies across papers.
   - Tracks cross-method combinations (e.g., papers utilizing both *Mutual Information Maximization* and *Graph Neural Networks*).
   - Identifies dominant vs. niche methodological approaches.

2. **Benchmark Dataset Concentrations**:
   - Frequencies of dataset evaluation across studies.
   - Cross-tabulates datasets with methods (which methods were evaluated on which datasets).
   - Detects dataset mononorms (e.g., over-reliance on a single benchmark suite).

3. **Evaluation Metric Distributions**:
   - Frequency of quantitative evaluation metrics (e.g., Accuracy, F1-Score, BLEU, RMSE, Latency).
   - Identifies evaluation blindspots (e.g., studies reporting accuracy but omitting inference speed or resource consumption).

4. **Temporal Trajectories**:
   - Publication distribution by year across the collection window.
   - Detects shifts in paradigm interest over time.

---

## 3. Qualified Denominators & Statistical Honesty

Every pattern report incorporates explicit denominator statements:
- Percentages are computed against explicit total eligible paper counts ($N_{papers}$).
- Zero-occurrence or single-paper phenomena are explicitly highlighted as *"Observed in 1 of $N$ retrieved papers"* to prevent overgeneralization.
