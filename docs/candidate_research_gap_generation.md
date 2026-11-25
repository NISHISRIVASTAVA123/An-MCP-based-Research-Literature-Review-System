# Candidate Research Gap Generation (Phase 4)

## 1. Grounding & Zero-Fabrication Guarantee

The `CandidateResearchGapGenerator` formulates evidence-backed candidate research gaps from synthesized patterns and author-reported limitations.

**The Golden Principle**: Every generated candidate gap must be supported by traceable evidence from the actual retrieved literature. The system never invents papers, citations, evidence passages, findings, or limitations.

---

## 2. Gap Taxonomy (10 Academic Categories)

The engine classifies candidate gaps into 10 structured categories:

1. `empirical_gap`: Contradictory, inconsistent, or unverified empirical evaluations across retrieved studies.
2. `methodological_gap`: Limitations in algorithmic scalability, mathematical formulation, or modeling assumptions.
3. `theoretical_gap`: Lack of theoretical foundations, formal convergence guarantees, or interpretability bounds.
4. `evaluation_gap`: Over-reliance on non-standard, synthetic, or unrepresentative benchmarks; missing standard metrics.
5. `generalisation_gap`: Failure or degradation of performance when evaluated on out-of-distribution or transfer domains.
6. `application_gap`: Inability or unverified performance in real-world environments beyond controlled academic testbeds.
7. `deployment_gap`: Severe computational latency, memory footprint, or energy consumption impeding practical deployment.
8. `synthesis_gap`: Disconnection between two mature methodologies that have not been investigated in combination.
9. `data_gap`: Scarcity of high-quality annotated training data, extreme class imbalance, or sparse multimodal signals.
10. `reproducibility_gap`: Missing hyperparameters, private datasets, or non-deterministic experimental protocols.

---

## 3. Database Reference Validation

Before persisting any candidate gap:
1. `supporting_paper_ids` are strictly validated against existing rows in SQLite `papers` table. Any non-existent paper ID triggers immediate rejection.
2. `GapEvidenceLink` records are created only for authenticated `EvidencePassage` rows in the database.
3. Gaps lacking evidence grounding or referencing orphan entities are automatically discarded.

---

## 4. Phase 5 Forward-Compatible Validation Queries

Every candidate gap generates automated search queries for downstream **Phase 5 Explicit Counterevidence Retrieval**:
- Target phrases designed to search academic databases specifically to disprove or contextualize the gap.
- Example: `"out-of-distribution generalization molecular GNN benchmark"`
- If Phase 5 subsequently retrieves papers solving the issue, the gap is rejected or refined during Phase 7 classification.
