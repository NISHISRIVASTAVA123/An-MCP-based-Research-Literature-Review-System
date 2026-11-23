# Scientific PDF Processing & Section Demarcation Architecture

## 1. Document Acquisition Pipeline

Phase 2 implements a multi-tier document acquisition strategy:

```
[Paper Record]
      │
      ├───────────────────────┬────────────────────────┐
      ▼                       ▼                        ▼
[arXiv Identifier]     [OpenAlex OA URL]       [Direct User Upload]
      │                       │                        │
      ▼                       ▼                        ▼
[HTTP Stream Fetch]    [HTTP Stream Fetch]    [Multipart Form Upload]
      │                       │                        │
      └───────────────────────┴────────────────────────┘
                              │
                              ▼
               [Magic Byte & Header Check]
                 (Validates `%PDF-` signature)
                              │
                              ▼
               [SHA-256 Digest Computation]
                 (Duplicate & integrity check)
                              │
                              ▼
               [Local Storage Persistence]
                 (`data/fulltext_documents/{uuid}.pdf`)
```

---

## 2. PyMuPDF (`fitz`) Scientific Document Parser

Scientific articles present challenging typography: multi-column layouts, floating figure captions, footnote sidebars, and dense mathematical notation.

The PDF processing engine (`backend/app/services/document/pdf_processor.py`) utilizes PyMuPDF:

### Section Demarcation Regex Heuristics
The parser detects canonical academic section headers using case-insensitive anchored regex:
- **Abstract**: `r'^(?:abstract)\b'`
- **Introduction**: `r'^(?:\d+[\.\s]+)?(?:introduction|overview)\b'`
- **Related Work**: `r'^(?:\d+[\.\s]+)?(?:related\s+work|prior\s+work|literature\s+review)\b'`
- **Methodology**: `r'^(?:\d+[\.\s]+)?(?:methodology|methods|proposed\s+approach|system\s+model|architecture)\b'`
- **Experiments**: `r'^(?:\d+[\.\s]+)?(?:experiments|experimental\s+setup|evaluation)\b'`
- **Results**: `r'^(?:\d+[\.\s]+)?(?:results|findings|empirical\s+analysis)\b'`
- **Discussion / Limitations**: `r'^(?:\d+[\.\s]+)?(?:discussion|limitations|threats\s+to\s+validity)\b'`
- **Conclusion / Future Work**: `r'^(?:\d+[\.\s]+)?(?:conclusion|future\s+work|conclusions)\b'`
- **References**: `r'^(?:\d+[\.\s]+)?(?:references|bibliography)\b'`

### Reference Section Truncation
To avoid extracting citations and prior literature claims as current paper contributions, any content appearing after the detected `References` or `Bibliography` heading is segregated and excluded from candidate finding and limitation extraction.

### Quality and OCR Assessment
- **Text Density Check**: Documents with fewer than 50 text characters per page are flagged with `is_scanned_ocr: true` and `extraction_status: "scanned_image_ocr_needed"`.
- **Corrupted Byte Handling**: If `fitz.open()` raises `FileDataError`, the document is marked as `corrupted_pdf` and gracefully excluded from automated parsing without crashing the server.
- **Table / Formula Detection**: Scans for standard LaTeX equation markers and tab-separated numerical blocks, flagging `has_tables: true` and `has_equations: true`.
