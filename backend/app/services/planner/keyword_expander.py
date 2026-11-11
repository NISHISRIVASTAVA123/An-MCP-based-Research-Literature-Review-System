"""Keyword Expander and Academic Concept Decomposer.

Provides deterministic academic concept extraction and synonym mapping
without mandating external paid LLM APIs.
"""

import re
from typing import List, Dict, Set


# Academic domain vocabulary and synonym dictionaries
DOMAIN_SYNONYM_MAP: Dict[str, List[str]] = {
    # AI & ML Concepts
    "explainable ai": ["xai", "model interpretability", "interpretable machine learning", "transparent models"],
    "xai": ["explainable artificial intelligence", "model interpretability", "black-box explanations"],
    "fake news detection": ["misinformation detection", "disinformation classification", "rumor verification", "fact-checking"],
    "misinformation": ["disinformation", "fake news", "unverified claims", "false rumors"],
    "large language models": ["llms", "foundation models", "generative ai", "transformer models"],
    "llm": ["large language model", "foundation model", "transformer language model"],
    "hallucination": ["factual inconsistency", "generation error", "unfaithful generation", "fabrication"],
    "knowledge graph": ["evidence graph", "semantic network", "knowledge base", "ontology"],
    "graph neural network": ["gnn", "graph convolutional network", "gcn", "graph attention network"],
    "reinforcement learning": ["rl", "policy optimization", "q-learning", "reinforcement learning from human feedback", "rlhf"],
    "natural language processing": ["nlp", "computational linguistics", "text mining", "text analysis"],
    "computer vision": ["image processing", "visual recognition", "object detection", "deep vision"],
    "counterevidence": ["contradictory evidence", "refuting evidence", "counter-claims", "opposing findings"],
    "claim verification": ["fact verification", "evidence verification", "truthfulness assessment", "automated fact-checking"],
    "research gap": ["unexplored research area", "open challenge", "future direction", "literature limitation"],
    "interpretability": ["explainability", "feature attribution", "post-hoc explanation", "lime", "shap"],
    "lime": ["local interpretable model-agnostic explanations", "feature attribution", "perturbation explanation"],
    "shap": ["shapley additive explanations", "game-theoretic attribution", "shapley values"],
    "cybersecurity": ["network security", "threat detection", "vulnerability assessment", "intrusion detection"],
    "privacy": ["differential privacy", "federated learning", "confidential computing", "data anonymization"],
    "bias": ["algorithmic fairness", "demographic parity", "ethical ai", "bias mitigation"],
    "benchmark": ["evaluation benchmark", "empirical evaluation", "baseline comparison", "dataset evaluation"],
}

STOP_WORDS: Set[str] = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with", "by",
    "from", "about", "into", "through", "during", "before", "after", "above", "below",
    "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do",
    "does", "did", "using", "based", "approach", "method", "system", "study", "analysis",
    "identify", "investigate", "explore", "evaluate", "assess", "proposed", "novel", "framework"
}


def clean_text(text: str) -> str:
    """Removes special characters and normalizes whitespace."""
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s-]", "", text)).strip()


def extract_key_phrases(text: str) -> List[str]:
    """Extracts meaningful n-grams (1-3 words) excluding stop words."""
    cleaned = clean_text(text.lower())
    words = [w for w in cleaned.split() if w and w not in STOP_WORDS and len(w) > 2]

    phrases = []
    # Single words
    phrases.extend(words)

    # Bigrams
    raw_words = cleaned.split()
    for i in range(len(raw_words) - 1):
        w1, w2 = raw_words[i], raw_words[i + 1]
        if w1 not in STOP_WORDS or w2 not in STOP_WORDS:
            if len(w1) > 2 and len(w2) > 2:
                phrases.append(f"{w1} {w2}")

    # Trigrams
    for i in range(len(raw_words) - 2):
        w1, w2, w3 = raw_words[i], raw_words[i + 1], raw_words[i + 2]
        if (w1 not in STOP_WORDS or w3 not in STOP_WORDS) and len(w2) > 1:
            phrases.append(f"{w1} {w2} {w3}")

    return list(dict.fromkeys(phrases))


def expand_keywords(topic: str, objective: str, domain: str, research_questions: List[str]) -> Dict[str, any]:
    """Generates structured academic concepts, keywords, and synonyms."""
    all_text = f"{topic}. {objective}. {domain}. " + " ".join(research_questions)
    lowered_text = all_text.lower()

    concepts: List[str] = []
    keywords: Set[str] = set()
    synonyms: Dict[str, List[str]] = {}

    # Extract foundational concept from topic
    topic_cleaned = clean_text(topic)
    if topic_cleaned:
        concepts.append(topic_cleaned)

    # Check for domain vocabulary matches
    for term, syns in DOMAIN_SYNONYM_MAP.items():
        if term in lowered_text:
            if term not in [c.lower() for c in concepts]:
                concepts.append(term.title())
            keywords.add(term)
            keywords.update(syns[:3])
            synonyms[term] = syns

    # Extract additional phrases from topic and questions
    topic_phrases = extract_key_phrases(topic)
    for p in topic_phrases[:4]:
        keywords.add(p)

    for q in research_questions:
        q_phrases = extract_key_phrases(q)
        for p in q_phrases[:2]:
            keywords.add(p)

    # Ensure domain is included
    if domain:
        clean_domain = clean_text(domain)
        if clean_domain.lower() not in [k.lower() for k in keywords]:
            keywords.add(clean_domain)

    # Generate pairwise query combinations
    key_list = list(keywords)[:6]
    query_combinations: List[str] = []
    if len(key_list) >= 2:
        for i in range(len(key_list)):
            for j in range(i + 1, min(i + 3, len(key_list))):
                k1, k2 = key_list[i], key_list[j]
                query_combinations.append(f'"{k1}" AND "{k2}"')
    else:
        query_combinations.append(f'"{topic_cleaned}"')

    # Deduplicate concepts and keywords
    unique_concepts = list(dict.fromkeys(concepts))[:6]
    unique_keywords = sorted(list(keywords), key=len, reverse=True)[:15]

    return {
        "concepts": unique_concepts or [topic.strip()],
        "keywords": unique_keywords,
        "synonyms": synonyms,
        "query_combinations": query_combinations[:8],
    }

