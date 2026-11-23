"""Unit Tests for Scientific PDF Processing and Layout Extraction."""

import pytest
import fitz
from backend.app.services.document.pdf_processor import ScientificPdfProcessor


def create_synthetic_scientific_pdf() -> bytes:
    """Generates an in-memory 2-page scientific PDF document with sections."""
    doc = fitz.open()

    # Page 1
    page1 = doc.new_page()
    page1.insert_text(
        (50, 72),
        "Towards Explainable Deep Learning Models for Misinformation\n\n"
        "Abstract\n"
        "In this paper we propose an explainable framework for misinformation detection using SHAP and LIME. "
        "Our method achieves an accuracy of 92.4% on the LIAR benchmark.\n\n"
        "1. Introduction\n"
        "Misinformation on social media platforms poses severe societal challenges. "
        "Understanding model decision rationale is essential for human moderation.",
        fontsize=11,
    )

    # Page 2
    page2 = doc.new_page()
    page2.insert_text(
        (50, 72),
        "2. Methodology\n"
        "We construct a transformer architecture integrated with Shapley value attributions.\n\n"
        "3. Limitations\n"
        "Our study is restricted to English news articles and small sample sizes.\n\n"
        "References\n"
        "[1] Wang, W. (2017). 'Liar, Liar Pants on Fire': A New Benchmark Dataset for Fake News Detection.",
        fontsize=11,
    )

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_pdf_processor_successful_extraction():
    processor = ScientificPdfProcessor()
    pdf_bytes = create_synthetic_scientific_pdf()

    result = processor.process_pdf(pdf_bytes)
    assert result["status"] == "success"
    assert result["page_count"] == 2
    assert result["total_characters"] > 300
    assert len(result["sections"]) == 2

    # Check page numbers
    assert result["sections"][0]["page_number"] == 1
    assert result["sections"][1]["page_number"] == 2

    # Check text content
    assert "explainable framework" in result["raw_text"]

    # Check references isolation
    assert "Wang, W." in result["references_text"]


def test_pdf_processor_corrupt_bytes_rejected():
    processor = ScientificPdfProcessor()
    corrupt_bytes = b"This is not a PDF file at all."

    result = processor.process_pdf(corrupt_bytes)
    assert result["status"] == "corrupt_unreadable"
    assert result["page_count"] == 0
    assert result["error"] is not None

