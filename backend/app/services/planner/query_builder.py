"""Database-specific Query Builder.

Tailors search queries for the unique syntactical requirements of OpenAlex,
Semantic Scholar, Crossref, and arXiv APIs.
"""

from typing import List, Dict


def build_openalex_query(topic: str, keywords: List[str]) -> str:
    """OpenAlex supports search parameter matching title/abstract."""
    # Select top 2-3 focused keywords or main topic
    if keywords:
        top_k = keywords[:3]
        return " ".join([f'"{k}"' if " " in k else k for k in top_k])
    return f'"{topic}"'


def build_semantic_scholar_query(topic: str, keywords: List[str]) -> str:
    """Semantic Scholar graph query parameter."""
    if len(keywords) >= 2:
        return f"{keywords[0]} {keywords[1]}"
    return topic


def build_crossref_query(topic: str, keywords: List[str]) -> str:
    """Crossref bibliographic query."""
    if keywords:
        return f"{keywords[0]} {topic}"
    return topic


def build_arxiv_query(topic: str, keywords: List[str]) -> str:
    """arXiv API query syntax using all: prefix and uppercase AND/OR."""
    # Example: all:"explainable ai" AND all:"fake news"
    if len(keywords) >= 2:
        k1, k2 = keywords[0], keywords[1]
        return f'all:"{k1}" AND all:"{k2}"'
    elif keywords:
        return f'all:"{keywords[0]}"'
    return f'all:"{topic}"'


def generate_database_queries(
    topic: str,
    keywords: List[str],
    query_combinations: List[str],
    preferred_databases: List[str],
) -> List[Dict[str, any]]:
    """Builds a structured collection of queries mapped to specific academic databases."""
    queries = []

    # Map target databases
    targets = [db.lower() for db in preferred_databases] or [
        "openalex",
        "semantic_scholar",
        "crossref",
        "arxiv",
    ]

    for db in targets:
        if db == "openalex":
            q_text = build_openalex_query(topic, keywords)
            queries.append({
                "target_database": "openalex",
                "query_text": q_text,
                "is_enabled": True,
            })
        elif db in ("semantic_scholar", "semanticscholar"):
            q_text = build_semantic_scholar_query(topic, keywords)
            queries.append({
                "target_database": "semantic_scholar",
                "query_text": q_text,
                "is_enabled": True,
            })
        elif db == "crossref":
            q_text = build_crossref_query(topic, keywords)
            queries.append({
                "target_database": "crossref",
                "query_text": q_text,
                "is_enabled": True,
            })
        elif db == "arxiv":
            q_text = build_arxiv_query(topic, keywords)
            queries.append({
                "target_database": "arxiv",
                "query_text": q_text,
                "is_enabled": True,
            })

    return queries

