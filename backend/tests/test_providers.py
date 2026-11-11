"""Unit tests for Academic Provider Adapters with mocked network responses."""

import pytest
from unittest.mock import AsyncMock, patch
import httpx

from backend.app.services.providers.openalex_provider import (
    OpenAlexProvider,
    reconstruct_openalex_abstract,
)
from backend.app.services.providers.semantic_scholar_provider import SemanticScholarProvider
from backend.app.services.providers.crossref_provider import CrossrefProvider, strip_jats_xml
from backend.app.services.providers.arxiv_provider import ArxivProvider
from backend.app.services.providers.base_provider import (
    ProviderTimeoutError,
    ProviderRateLimitError,
)


def test_openalex_abstract_inversion_reconstruction():
    inverted = {
        "This": [0],
        "paper": [1],
        "evaluates": [2],
        "model": [3],
        "interpretability": [4],
    }
    reconstructed = reconstruct_openalex_abstract(inverted)
    assert reconstructed == "This paper evaluates model interpretability"


def test_crossref_strip_jats_xml():
    xml_abstract = "<jats:p>Explainable AI is <jats:italic>critical</jats:italic> for trust.</jats:p>"
    clean = strip_jats_xml(xml_abstract)
    assert clean == "Explainable AI is critical for trust."


@pytest.mark.asyncio
async def test_openalex_provider_parse_mock():
    provider = OpenAlexProvider()
    mock_response_data = {
        "results": [
            {
                "id": "https://openalex.org/W2995341234",
                "display_name": "Interpretable Machine Learning in Healthcare",
                "doi": "https://doi.org/10.1038/s41746-020-00345-z",
                "publication_year": 2021,
                "publication_date": "2021-03-15",
                "authorships": [
                    {"author": {"display_name": "Sarah Connor"}},
                    {"author": {"display_name": "John Connor"}},
                ],
                "abstract_inverted_index": {
                    "Explainable": [0],
                    "models": [1],
                    "assist": [2],
                    "clinicians.": [3],
                },
                "primary_location": {
                    "source": {"display_name": "Nature Digital Medicine"},
                    "pdf_url": "https://nature.com/articles/s41746.pdf",
                },
                "best_oa_location": {
                    "pdf_url": "https://nature.com/articles/s41746.pdf",
                },
                "cited_by_count": 88,
                "concepts": [{"display_name": "Explainable Artificial Intelligence"}],
                "type": "article",
            }
        ]
    }

    mock_resp = httpx.Response(200, json=mock_response_data, request=httpx.Request("GET", "https://api.openalex.org/works"))

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        records = await provider.search("interpretability healthcare", 2020, 2022, 10)

    assert len(records) == 1
    rec = records[0]
    assert rec.title == "Interpretable Machine Learning in Healthcare"
    assert rec.doi == "10.1038/s41746-020-00345-z"
    assert rec.authors == ["Sarah Connor", "John Connor"]
    assert rec.abstract == "Explainable models assist clinicians."
    assert rec.pdf_url == "https://nature.com/articles/s41746.pdf"
    assert rec.venue == "Nature Digital Medicine"
    assert rec.citation_count == 88


@pytest.mark.asyncio
async def test_semantic_scholar_provider_parse_mock():
    provider = SemanticScholarProvider()
    mock_data = {
        "data": [
            {
                "paperId": "abcdef123456",
                "title": "A Benchmark for Counterfactual Explanation Stability",
                "authors": [{"name": "Dr. Smith"}, {"name": "Prof. Turing"}],
                "year": 2023,
                "publicationDate": "2023-06-10",
                "venue": "NeurIPS",
                "abstract": "We evaluate how stable counterfactual explanations are.",
                "citationCount": 42,
                "externalIds": {"DOI": "10.5555/neurips.2023.1"},
                "openAccessPdf": {"url": "https://arxiv.org/pdf/2306.01234"},
                "publicationTypes": ["Conference"],
            }
        ]
    }

    mock_resp = httpx.Response(200, json=mock_data, request=httpx.Request("GET", "https://api.semanticscholar.org"))

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        records = await provider.search("counterfactual benchmark", 2022, 2024, 10)

    assert len(records) == 1
    assert records[0].title == "A Benchmark for Counterfactual Explanation Stability"
    assert records[0].doi == "10.5555/neurips.2023.1"
    assert records[0].venue == "NeurIPS"
    assert records[0].pdf_url == "https://arxiv.org/pdf/2306.01234"


@pytest.mark.asyncio
async def test_arxiv_provider_atom_xml_parse():
    provider = ArxivProvider()
    sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
      <entry>
        <id>http://arxiv.org/abs/2301.99999v1</id>
        <title> Automated Literature Review via Agentic Verification </title>
        <summary> This paper introduces agentic counterevidence verification. </summary>
        <author><name>Alice Green</name></author>
        <author><name>Bob Brown</name></author>
        <published>2023-01-15T12:00:00Z</published>
        <link href="http://arxiv.org/pdf/2301.99999v1" title="pdf" type="application/pdf"/>
        <arxiv:primary_category term="cs.AI"/>
      </entry>
    </feed>
    """

    mock_resp = httpx.Response(200, text=sample_xml, request=httpx.Request("GET", "https://export.arxiv.org"))

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        records = await provider.search("agentic verification", 2022, 2024, 5)

    assert len(records) == 1
    assert records[0].title == "Automated Literature Review via Agentic Verification"
    assert records[0].authors == ["Alice Green", "Bob Brown"]
    assert records[0].publication_year == 2023
    assert records[0].pdf_url == "http://arxiv.org/pdf/2301.99999v1"
    assert records[0].venue == "arXiv (cs.AI)"


@pytest.mark.asyncio
async def test_provider_rate_limit_and_timeout_errors():
    provider = SemanticScholarProvider()

    # Rate limit (429)
    rate_resp = httpx.Response(429, request=httpx.Request("GET", "https://api.semanticscholar.org"))
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = rate_resp
        with pytest.raises(ProviderRateLimitError):
            await provider.search("test query")

    # Timeout
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.TimeoutException("Connection timed out")
        with pytest.raises(ProviderTimeoutError):
            await provider.search("test query")

