# Counterevidence Retrieval Methodology

## 1. Problem Statement
Conventional literature review approaches and LLM workflows suffer from confirmation bias: once a research gap hypothesis is formulated (e.g., "No prior work combines Graph Neural Networks with Control Barrier Functions for autonomous navigation"), they typically retrieve only papers supporting this premise.

Phase 5 implements **Adversarial Literature Retrieval**, formulating queries specifically calibrated to find papers that *have* implemented, tested, or benchmarked the hypothesized gap.

## 2. Multi-Perspective Query Formulation
For every candidate research gap, the `CounterevidenceQueryGenerator` generates 4 distinct query types:

| Query Type | Purpose | Query Construction Heuristic |
|---|---|---|
| **Direct Counter** | Retrieve direct solutions | `"{key_terms} implementation evaluation benchmark"` |
| **Methodology Application** | Check technical adoption | `"{method} applied to {domain} experimental results"` |
| **Synonym Expansion** | Overcome vocabulary mismatches | Expands terms using domain synonym dictionaries (e.g., RAG $\to$ RALM, Dense Retrieval Augmentation) |
| **Newer Publications** | Catch recent advancements | Appends recent publication years (e.g., `2023 2024 recent advancements`) |

## 3. Academic Retrieval & Deduplication
Retrieval is executed against 4 academic databases:
1. **OpenAlex**: Broad multidisciplinary coverage with rich concept hierarchies.
2. **Semantic Scholar**: CS/AI focused, provides TLDRs, citation intents, and open-access links.
3. **Crossref**: Publisher-authoritative metadata, DOIs, and citation links.
4. **arXiv**: Pre-print coverage ensuring the latest cutting-edge implementations are checked.

### Deduplication Pipeline:
- **DOI Match**: Exact lowercase DOI matching against previously retrieved corpus.
- **Title Fingerprinting**: Stripped whitespace, lowercased, punctuation-normalized similarity matching.
- **Corpus Segregation**: Publications discovered through counterevidence are tagged with `discovery_tag="counterevidence_discovered"`, preventing pollution of the initial screening baseline while enabling targeted evidence extraction.
