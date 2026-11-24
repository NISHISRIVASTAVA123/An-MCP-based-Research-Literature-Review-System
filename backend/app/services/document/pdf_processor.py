"""Scientific Document PDF Processing Service.

Uses PyMuPDF (fitz) to extract layout-aware, page-indexed, and section-demarcated
text representations of scientific articles while preserving exact page numbers
and isolating reference sections.
"""

import re
from typing import Dict, Any, List, Tuple, Optional
try:
    import pymupdf as fitz
except ImportError:
    import fitz  # PyMuPDF fallback
from backend.app.core.logging import logger

COMMON_SECTIONS = [
    r"abstract",
    r"introduction",
    r"related\s+work",
    r"background",
    r"problem\s+formulation",
    r"methodology",
    r"methods",
    r"proposed\s+approach",
    r"model\s+architecture",
    r"system\s+design",
    r"experimental\s+setup",
    r"datasets?",
    r"experiments?",
    r"results?",
    r"evaluation",
    r"discussion",
    r"limitations?",
    r"future\s+work",
    r"conclusions?",
    r"references?",
    r"bibliography",
]

SECTION_PATTERN = re.compile(
    rf"^(?:[0-9IVX]+\.?\s*)?(?:{'|'.join(COMMON_SECTIONS)})(?:\s*[:\-]|\s*$)",
    re.IGNORECASE,
)


class ScientificPdfProcessor:
    """Extracts structured, page-referenced text from scientific PDF documents."""

    def process_pdf(self, file_bytes: bytes) -> Dict[str, Any]:
        """Parses a scientific PDF and returns page-by-page layout-aware text.

        Returns:
            Dictionary with:
            - status: "success" | "partial" | "scanned_ocr_required" | "corrupt_unreadable"
            - page_count: Total pages
            - total_characters: Total character count
            - sections: List of layout section objects
            - raw_text: Full contiguous text
            - references_text: Isolated references section
            - error: Optional error string
        """
        # Validate magic header
        if not file_bytes.startswith(b"%PDF-"):
            return {
                "status": "corrupt_unreadable",
                "page_count": 0,
                "total_characters": 0,
                "sections": [],
                "raw_text": "",
                "references_text": "",
                "error": "File does not start with valid PDF magic bytes (%PDF-).",
            }

        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as e:
            return {
                "status": "corrupt_unreadable",
                "page_count": 0,
                "total_characters": 0,
                "sections": [],
                "raw_text": "",
                "references_text": "",
                "error": f"Failed to open PDF document: {e}",
            }

        page_count = len(doc)
        if page_count == 0:
            return {
                "status": "corrupt_unreadable",
                "page_count": 0,
                "total_characters": 0,
                "sections": [],
                "raw_text": "",
                "references_text": "",
                "error": "Document contains 0 pages.",
            }

        extracted_sections: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []
        references_parts: List[str] = []
        is_in_references = False
        current_heading = "Preamble"

        total_chars = 0
        has_images = False

        for page_num in range(1, page_count + 1):
            page = doc[page_num - 1]
            text = page.get_text("text")
            char_count = len(text.strip())
            total_chars += char_count

            # Check if page has images
            if not has_images and len(page.get_images()) > 0:
                has_images = True

            # Identify layout blocks and potential headings
            lines = text.split("\n")
            page_body_lines: List[str] = []

            for line in lines:
                trimmed = line.strip()
                if not trimmed:
                    continue

                # Heading detection
                if len(trimmed) < 80 and SECTION_PATTERN.match(trimmed):
                    current_heading = trimmed
                    if re.search(r"references?|bibliography", trimmed, re.IGNORECASE):
                        is_in_references = True
                    else:
                        is_in_references = False

                if is_in_references:
                    references_parts.append(trimmed)
                else:
                    page_body_lines.append(trimmed)

            page_content = "\n".join(page_body_lines)
            full_text_parts.append(page_content)

            extracted_sections.append({
                "page_number": page_num,
                "heading": current_heading,
                "text": page_content,
                "char_count": char_count,
            })

        doc.close()

        # Quality determination
        if total_chars >= 500:
            status = "success"
        elif 50 <= total_chars < 500:
            status = "partial"
        elif total_chars < 50 and has_images:
            status = "scanned_ocr_required"
        else:
            status = "corrupt_unreadable"

        return {
            "status": status,
            "page_count": page_count,
            "total_characters": total_chars,
            "sections": extracted_sections,
            "raw_text": "\n\n".join(full_text_parts),
            "references_text": "\n".join(references_parts),
            "error": None if status in ("success", "partial") else f"Low text density detected ({total_chars} chars across {page_count} pages).",
        }

