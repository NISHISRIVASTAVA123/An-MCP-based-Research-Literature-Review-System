"""Generates multi-perspective counterevidence queries targeting contradictory publications."""

from typing import List, Dict, Any, Optional


class CounterevidenceQueryGenerator:
    """Generates targeted academic search queries designed specifically to find counterevidence."""

    SYNONYM_MAP = {
        "retrieval-augmented generation": ["RAG", "knowledge-augmented generation", "dense retrieval augmentation"],
        "rag": ["retrieval-augmented generation", "retrieval augmented language model", "RALM"],
        "multi-agent": ["multi-agent systems", "collaborative agents", "agentic workflows", "multi-agent reasoning"],
        "hallucination": ["factual error", "faithfulness", "grounding", "hallucination mitigation", "unfaithful generation"],
        "literature review": ["systematic review", "scientific literature synthesis", "research paper analysis"],
        "knowledge graph": ["evidence graph", "ontology", "heterogeneous information network", "semantic network"],
        "explainable ai": ["XAI", "interpretable machine learning", "model explanations", "SHAP", "LIME"],
        "graph neural network": ["GNN", "graph convolutional network", "GCN", "graph attention network", "GAT"],
    }

    def generate_queries_for_claims(
        self,
        candidate_gap_id: str,
        gap_title: str,
        claims: List[Dict[str, Any]],
        databases: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Generates diverse counterevidence queries across selected academic providers."""
        target_dbs = databases or ["openalex", "semantic_scholar", "arxiv", "crossref"]
        queries: List[Dict[str, Any]] = []

        for claim in claims:
            claim_id = claim.get("id")
            claim_type = claim.get("claim_type", "unexplored_problem")
            keywords = claim.get("generated_keywords", [])
            key_term_str = " ".join(keywords[:4]) if keywords else gap_title

            # Query 1: Direct Counter Query (Searches for implementations/solutions directly)
            direct_text = f"{key_term_str} implementation evaluation"
            queries.append({
                "candidate_gap_id": candidate_gap_id,
                "claim_id": claim_id,
                "query_text": direct_text,
                "query_type": "direct_counter",
                "search_rationale": "Directly probes literature for existing implementations or evaluations of the supposedly unaddressed technique.",
                "source_database": target_dbs[0 % len(target_dbs)],
            })

            # Query 2: Methodology Application / Solution Query
            method_text = f"{key_term_str} framework benchmark"
            queries.append({
                "candidate_gap_id": candidate_gap_id,
                "claim_id": claim_id,
                "query_text": method_text,
                "query_type": "methodology_application",
                "search_rationale": "Searches for published frameworks or benchmark studies solving the claimed gap.",
                "source_database": target_dbs[1 % len(target_dbs)],
            })

            # Query 3: Synonym & Alternative Terminology Query
            synonyms = self._find_synonyms(key_term_str)
            if synonyms:
                syn_text = f"{' '.join(synonyms[:3])} practical approach"
                queries.append({
                    "candidate_gap_id": candidate_gap_id,
                    "claim_id": claim_id,
                    "query_text": syn_text,
                    "query_type": "synonym_expansion",
                    "search_rationale": "Tests whether alternative technical terminology or synonymous architecture names already addressed this gap.",
                    "source_database": target_dbs[2 % len(target_dbs)],
                })

            # Query 4: Newer Publications Query (Targeting recent advances)
            newer_text = f"advances in {key_term_str} recent results"
            queries.append({
                "candidate_gap_id": candidate_gap_id,
                "claim_id": claim_id,
                "query_text": newer_text,
                "query_type": "newer_publications",
                "search_rationale": "Targets recent preprints and conference publications that may have subsequently solved the gap.",
                "source_database": target_dbs[3 % len(target_dbs)],
            })

        return queries

    def _find_synonyms(self, text: str) -> List[str]:
        t_low = text.lower()
        found: List[str] = []
        for term, syns in self.SYNONYM_MAP.items():
            if term in t_low:
                found.extend(syns)
        return found
