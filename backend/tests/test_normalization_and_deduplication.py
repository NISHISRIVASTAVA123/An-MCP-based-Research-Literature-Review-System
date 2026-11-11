"""Unit tests for Metadata Normalization and Multi-Tier Deduplication."""

from backend.app.services.providers.base_provider import RawPaperRecord
from backend.app.services.literature.normalization_service import (
    NormalizationService,
    normalize_doi,
    normalize_title,
)
from backend.app.services.literature.deduplication_service import DeduplicationService


def test_doi_and_title_normalization():
    assert normalize_doi("https://doi.org/10.1145/3308558.3313704") == "10.1145/3308558.3313704"
    assert normalize_doi("DOI: 10.1145/3308558.3313704") == "10.1145/3308558.3313704"
    assert normalize_doi(None) is None

    assert normalize_title("Explainable AI: A Survey on XAI Methods!") == "explainable ai a survey on xai methods"
    assert normalize_title("  Model Interpretability -- SHAP & LIME  ") == "model interpretability shap lime"


def test_normalization_handles_missing_fields_gracefully():
    normalizer = NormalizationService()
    raw = RawPaperRecord(
        source_database="crossref",
        external_id="10.1000/182",
        title="Minimal Metadata Study",
        authors=[],
        abstract=None,
        publication_year=2021,
        doi="10.1000/182",
    )

    norm = normalizer.normalize_record(raw)
    assert norm.title == "Minimal Metadata Study"
    assert norm.has_abstract is False
    assert norm.abstract is None
    assert norm.has_doi is True
    assert norm.has_pdf is False
    assert len(norm.sources) == 1
    assert norm.sources[0].source_database == "crossref"


def test_deduplication_exact_doi_match_merges_provenance():
    normalizer = NormalizationService()
    dedup = DeduplicationService()

    raw1 = RawPaperRecord(
        source_database="openalex",
        external_id="W12345",
        title="A Survey on Explainable Artificial Intelligence",
        authors=["Alice Smith", "Bob Jones"],
        abstract="Comprehensive survey of XAI techniques.",
        publication_year=2020,
        doi="10.1016/j.inffus.2019.12.012",
        citation_count=500,
    )

    raw2 = RawPaperRecord(
        source_database="semantic_scholar",
        external_id="S2_98765",
        title="A Survey on Explainable Artificial Intelligence (XAI)",
        authors=["Alice Smith", "B. Jones"],
        abstract="Comprehensive survey of XAI techniques covering post-hoc and intrinsic.",
        publication_year=2020,
        doi="10.1016/j.inffus.2019.12.012",  # Same DOI
        pdf_url="https://arxiv.org/pdf/1908.01234.pdf",
        citation_count=550,
    )

    norm1 = normalizer.normalize_record(raw1)
    norm2 = normalizer.normalize_record(raw2)

    unique, dup_count = dedup.deduplicate([norm1, norm2])

    assert len(unique) == 1
    assert dup_count == 1
    merged = unique[0]

    # Provenance preserved from both providers
    source_dbs = [s.source_database for s in merged.sources]
    assert "openalex" in source_dbs
    assert "semantic_scholar" in source_dbs

    # Merged the PDF URL and higher citation count
    assert merged.pdf_url == "https://arxiv.org/pdf/1908.01234.pdf"
    assert merged.citation_count == 550
    assert "intrinsic" in merged.abstract  # Kept longer, richer abstract


def test_deduplication_title_and_year_match_without_doi():
    normalizer = NormalizationService()
    dedup = DeduplicationService()

    raw1 = RawPaperRecord(
        source_database="arxiv",
        external_id="2201.0001",
        title="Evaluating Research Gaps via Evidence Graphs",
        authors=["Carol White"],
        abstract="We introduce evidence graph verification.",
        publication_year=2022,
        doi=None,  # Preprint has no DOI yet
    )

    raw2 = RawPaperRecord(
        source_database="semantic_scholar",
        external_id="S2_4444",
        title="Evaluating Research Gaps via Evidence Graphs",
        authors=["Carol White"],
        abstract="We introduce evidence graph verification.",
        publication_year=2022,
        doi="10.1145/3333333",  # Published conference version has DOI
    )

    norm1 = normalizer.normalize_record(raw1)
    norm2 = normalizer.normalize_record(raw2)

    unique, dup_count = dedup.deduplicate([norm1, norm2])

    assert len(unique) == 1
    assert dup_count == 1
    assert unique[0].doi == "10.1145/3333333"


def test_distinct_papers_with_different_titles_not_merged():
    normalizer = NormalizationService()
    dedup = DeduplicationService()

    raw1 = RawPaperRecord(
        source_database="crossref",
        title="Deep Learning in Medical Imaging Vol 1",
        authors=["Dr. A"],
        publication_year=2021,
        doi="10.1000/vol1",
    )
    raw2 = RawPaperRecord(
        source_database="crossref",
        title="Deep Learning in Medical Imaging Vol 2",
        authors=["Dr. A"],
        publication_year=2022,
        doi="10.1000/vol2",
    )

    norm1 = normalizer.normalize_record(raw1)
    norm2 = normalizer.normalize_record(raw2)

    unique, dup_count = dedup.deduplicate([norm1, norm2])
    assert len(unique) == 2
    assert dup_count == 0

