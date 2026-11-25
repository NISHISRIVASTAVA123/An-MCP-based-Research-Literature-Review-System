# Paper Comparison Matrix Specification (Phase 4)

## 1. Overview

The `PaperComparisonMatrixService` produces dynamic, multidimensional comparative tables across eligible research papers. It transforms heterogeneous extractions into a standardized schema that facilitates direct visual and programmatic comparison across 13 scientific dimensions.

---

## 2. Matrix Dimensions

Every row in the comparison matrix corresponds to an eligible scientific paper with the following schema:

| Column | Data Type | Extraction Source | Description / Fallback |
|---|---|---|---|
| `Paper Title` | string | `Paper.title` | Full title of publication |
| `Authors` | list of string | `Paper.authors` | Author list |
| `Year` | integer | `Paper.publication_year` | Publication year |
| `Venue` | string | `Paper.venue` | Conference or journal name |
| `Research Objectives` | list of string | `EvidenceRecord.research_objective` | Primary aims of the study ("Not reported" if missing) |
| `Research Questions` | list of string | `ResearchQuestion` / Title | Inferred or formal research questions |
| `Methodologies` | list of string | `EvidenceRecord.methodology` | Algorithmic techniques, frameworks |
| `Models / Architectures` | list of string | `EvidenceRecord.methodology["models"]` | Specific model architectures (e.g. Transformer, PPO, GIN) |
| `Datasets` | list of string | `EvidenceRecord.datasets` | Benchmarks evaluated on |
| `Evaluation Metrics` | list of string | `EvidenceRecord.evaluation_metrics` | Quantitative metrics used |
| `Experimental Setup` | string | Synthesized | Experimental condition indicator |
| `Main Findings` | list of string | `EvidenceRecord.findings` | Quantified empirical claims |
| `Reported Limitations` | list of string | `EvidenceRecord.limitations` | Author-reported constraints and weaknesses |
| `Future Directions` | list of string | `EvidenceRecord.future_work` | Open research directions proposed |
| `Evidence Count` | integer | `count(EvidencePassage)` | Total verbatim evidence passages backing the paper |

---

## 3. Strict Truthfulness & "Not Reported" Handling

To avoid misleading comparisons or synthetic hallucination:
- Missing dimensions are explicitly rendered as `"Not reported"`.
- The system never assumes an unmentioned dataset, model, or metric was evaluated.
- Empty extraction fields default to neutral statements without penalizing paper credibility.

---

## 4. Multi-Format Serializers

The service supports direct export to:
- **JSON**: Strongly-typed `PaperComparisonMatrixResponse` for frontend rendering and agent consumption.
- **CSV**: Standard comma-separated values for tabular analysis in spreadsheet software (Excel, pandas).
- **Markdown**: Formatted GitHub Flavored Markdown table for direct inclusion in thesis manuscripts and reports.
