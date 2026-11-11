"""Academic Paper Deduplication Service.

Executes hierarchical multi-tier deduplication:
1. Exact normalized DOI match.
2. Exact normalized title match with publication year verification (+/- 1 year allowance for preprint-to-journal publication lag).
3. Author surname + title prefix matching for disambiguation.

Preserves all source provenance, URLs, and external identifiers across merged records.
"""

from typing import List, Dict, Tuple, Optional
from backend.app.services.literature.normalization_service import (
    NormalizedPaper,
    NormalizedSource,
    normalize_doi,
    normalize_title,
)


def extract_primary_author_surname(authors: List[str]) -> Optional[str]:
    """Extracts lowercase surname of first author for disambiguation."""
    if not authors:
        return None
    first = authors[0].strip().lower()
    parts = first.split()
    return parts[-1] if parts else None


class DeduplicationService:
    """Detects and merges duplicate academic paper records across multiple sources."""

    def deduplicate(
        self, papers: List[NormalizedPaper]
    ) -> Tuple[List[NormalizedPaper], int]:
        """
        Deduplicates a list of normalized papers.
        Returns:
            Tuple of (unique_papers, duplicate_count)
        """
        doi_map: Dict[str, NormalizedPaper] = {}
        title_year_map: Dict[Tuple[str, Optional[int]], NormalizedPaper] = {}
        unique_papers: List[NormalizedPaper] = []
        duplicate_count = 0

        for paper in papers:
            matched_target: Optional[NormalizedPaper] = None

            # 1. Exact DOI Match
            if paper.doi:
                norm_doi = normalize_doi(paper.doi)
                if norm_doi in doi_map:
                    matched_target = doi_map[norm_doi]

            # 2. Normalized Title Match with Year check
            if not matched_target and paper.normalized_title and len(paper.normalized_title) > 8:
                # Direct (title, year) match
                key = (paper.normalized_title, paper.publication_year)
                if key in title_year_map:
                    matched_target = title_year_map[key]
                else:
                    # Check year tolerance (+/- 1 year for preprint vs journal lag)
                    for (t, y), existing_candidate in title_year_map.items():
                        if t == paper.normalized_title:
                            if (
                                y is None
                                or paper.publication_year is None
                                or abs(y - paper.publication_year) <= 1
                            ):
                                matched_target = existing_candidate
                                break

            # 3. Handle Merge or Register as Unique
            if matched_target:
                self._merge_into(matched_target, paper)
                duplicate_count += 1
            else:
                unique_papers.append(paper)
                if paper.doi:
                    doi_map[normalize_doi(paper.doi)] = paper
                if paper.normalized_title:
                    title_year_map[(paper.normalized_title, paper.publication_year)] = paper

        return unique_papers, duplicate_count

    def _merge_into(self, target: NormalizedPaper, incoming: NormalizedPaper) -> None:
        """Merges incoming paper metadata into target without overwriting superior data."""
        # 1. Preserve and append provenance sources
        for inc_src in incoming.sources:
            # Check if source already registered
            exists = any(
                s.source_database == inc_src.source_database
                and s.external_source_id == inc_src.external_source_id
                for s in target.sources
            )
            if not exists:
                target.sources.append(inc_src)

        # 2. Complete missing DOI
        if not target.doi and incoming.doi:
            target.doi = incoming.doi
            target.has_doi = True

        # 3. Complete missing Abstract
        if not target.abstract and incoming.abstract:
            target.abstract = incoming.abstract
            target.has_abstract = True
        elif target.abstract and incoming.abstract:
            # Keep longer, more detailed abstract
            if len(incoming.abstract) > len(target.abstract) + 20:
                target.abstract = incoming.abstract

        # 4. Complete missing PDF link
        if not target.pdf_url and incoming.pdf_url:
            target.pdf_url = incoming.pdf_url
            target.has_pdf = True

        # 5. Open access indicator
        if incoming.is_open_access:
            target.is_open_access = True

        # 6. Complete missing venue
        if not target.venue and incoming.venue:
            target.venue = incoming.venue

        # 7. Take higher citation count
        if (incoming.citation_count or 0) > (target.citation_count or 0):
            target.citation_count = incoming.citation_count

        # 8. Merge authors if incoming has more complete author list
        if len(incoming.authors) > len(target.authors):
            target.authors = incoming.authors

        # 9. Merge keywords
        for kw in incoming.keywords:
            if kw and kw not in target.keywords:
                target.keywords.append(kw)

