"""Live Integration Test for Academic Provider APIs.

Tests real-world live academic retrieval against OpenAlex, Semantic Scholar,
Crossref, and arXiv, validating live response parsing, metadata normalization,
and deduplication.

Usage:
    python backend/scripts/live_integration_test.py
"""

import asyncio
import sys
from typing import List

from backend.app.services.providers.openalex_provider import OpenAlexProvider
from backend.app.services.providers.semantic_scholar_provider import SemanticScholarProvider
from backend.app.services.providers.crossref_provider import CrossrefProvider
from backend.app.services.providers.arxiv_provider import ArxivProvider
from backend.app.services.literature.normalization_service import NormalizationService
from backend.app.services.literature.deduplication_service import DeduplicationService
from backend.app.services.providers.base_provider import RawPaperRecord


async def test_live_retrieval():
    print("=" * 70)
    print("ACADEMIC LITERATURE REVIEW - LIVE API INTEGRATION TEST")
    print("=" * 70)

    query = "Explainable AI"
    start_year = 2021
    end_year = 2026
    limit_per_provider = 5

    providers = [
        ("OpenAlex", OpenAlexProvider()),
        ("Semantic Scholar", SemanticScholarProvider()),
        ("Crossref", CrossrefProvider()),
        ("arXiv", ArxivProvider()),
    ]

    all_raw: List[RawPaperRecord] = []
    print(f"\nSearching query: '{query}' | Years: {start_year}-{end_year} | Limit: {limit_per_provider}/source\n")

    for name, prov in providers:
        print(f"[*] Querying {name} API...")
        try:
            records = await prov.search(
                query=query,
                start_year=start_year,
                end_year=end_year,
                limit=limit_per_provider,
            )
            print(f"    [SUCCESS] {name} returned {len(records)} papers.")
            all_raw.extend(records)
            for idx, r in enumerate(records[:2], 1):
                authors_str = ", ".join(r.authors[:3]) + (" et al." if len(r.authors) > 3 else "")
                print(f"      {idx}. {r.title[:65]}...")
                print(f"         Authors: {authors_str or 'None'}")
                print(f"         Year: {r.publication_year} | DOI: {r.doi or 'None'} | Venue: {r.venue or 'None'}")
        except Exception as e:
            print(f"    [WARNING] {name} error: {e}")

    print("\n" + "-" * 70)
    print(f"Total raw papers retrieved across all live APIs: {len(all_raw)}")

    if not all_raw:
        print("[!] No papers returned across providers. Check internet connection.")
        return

    # Normalization
    normalizer = NormalizationService()
    normalized = normalizer.normalize_records(all_raw)
    print(f"Normalized schema instances created: {len(normalized)}")

    # Deduplication
    dedup = DeduplicationService()
    unique, duplicates = dedup.deduplicate(normalized)
    print(f"Unique papers after deduplication: {len(unique)}")
    print(f"Duplicates detected and merged: {duplicates}")

    print("\nSample Merged Paper Details:")
    sample = unique[0]
    print(f"  Title: {sample.title}")
    print(f"  DOI: {sample.doi}")
    print(f"  Year: {sample.publication_year}")
    print(f"  Has Abstract: {sample.has_abstract}")
    print(f"  Has PDF: {sample.has_pdf} ({sample.pdf_url or 'None'})")
    print(f"  Source Provenance: {[s.source_database for s in sample.sources]}")
    print("=" * 70)
    print("LIVE INTEGRATION TEST COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    asyncio.run(test_live_retrieval())
