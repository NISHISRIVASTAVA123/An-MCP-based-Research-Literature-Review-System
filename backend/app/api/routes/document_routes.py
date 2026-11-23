"""API Routes for Full-Text Scientific Documents and PDF Processing."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from backend.app.services.persistence.database import get_db
from backend.app.services.persistence.repositories import PaperRepository
from backend.app.services.persistence.document_repository import DocumentRepository
from backend.app.services.document.downloader import DocumentDownloader
from backend.app.services.document.pdf_processor import ScientificPdfProcessor
from backend.app.schemas.document import DocumentStatusResponse, DocumentRetrieveResponse
from backend.app.core.logging import logger

router = APIRouter(tags=["Document Processing"])


@router.post(
    "/api/papers/{paper_id}/retrieve-full-text",
    response_model=DocumentRetrieveResponse,
    summary="Attempt permitted automated open-access full-text retrieval",
)
async def retrieve_full_text(
    paper_id: str,
    db: Session = Depends(get_db),
):
    """Attempts legal open-access retrieval from academic provider URLs or arXiv repository."""
    paper_repo = PaperRepository(db)
    doc_repo = DocumentRepository(db)
    downloader = DocumentDownloader()
    processor = ScientificPdfProcessor()

    paper = paper_repo.get_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail=f"Paper {paper_id} not found")

    success, source_type, file_bytes, message, source_url = await downloader.retrieve_paper_pdf(paper)
    if not success or not file_bytes:
        return DocumentRetrieveResponse(
            paper_id=paper_id,
            success=False,
            document_id=None,
            source_type=source_type,
            source_url=source_url,
            extraction_status="no_access",
            page_count=0,
            message=message,
        )

    # Save to disk
    file_path, file_size, file_hash = downloader.save_pdf(paper.id, file_bytes)

    # Process PDF layout and extract sections
    parsed = processor.process_pdf(file_bytes)

    # Save document database record
    doc = doc_repo.create_document(
        paper_id=paper.id,
        source_type=source_type,
        file_path=file_path,
        file_size_bytes=file_size,
        file_hash_sha256=file_hash,
        extraction_status=parsed["status"],
        page_count=parsed["page_count"],
        extracted_sections=parsed["sections"],
        raw_text=parsed["raw_text"],
        error_details=parsed.get("error"),
    )

    return DocumentRetrieveResponse(
        paper_id=paper_id,
        success=True,
        document_id=doc.id,
        source_type=source_type,
        source_url=source_url,
        extraction_status=doc.extraction_status,
        page_count=doc.page_count,
        message=f"Full-text successfully extracted ({doc.page_count} pages, {len(doc.extracted_sections)} sections).",
    )


@router.post(
    "/api/papers/{paper_id}/upload-pdf",
    response_model=DocumentRetrieveResponse,
    summary="Upload scientific paper PDF file",
)
async def upload_paper_pdf(
    paper_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Processes user-uploaded PDF file for papers without open-access URLs."""
    paper_repo = PaperRepository(db)
    doc_repo = DocumentRepository(db)
    downloader = DocumentDownloader()
    processor = ScientificPdfProcessor()

    paper = paper_repo.get_by_id(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail=f"Paper {paper_id} not found")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(content) > 35 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds maximum size limit (35 MB)")

    # Save to disk
    file_path, file_size, file_hash = downloader.save_pdf(paper.id, content)

    # Process with PyMuPDF
    parsed = processor.process_pdf(content)

    doc = doc_repo.create_document(
        paper_id=paper.id,
        source_type="user_upload",
        file_path=file_path,
        file_size_bytes=file_size,
        file_hash_sha256=file_hash,
        extraction_status=parsed["status"],
        page_count=parsed["page_count"],
        extracted_sections=parsed["sections"],
        raw_text=parsed["raw_text"],
        error_details=parsed.get("error"),
    )

    return DocumentRetrieveResponse(
        paper_id=paper_id,
        success=doc.extraction_status in ("success", "partial"),
        document_id=doc.id,
        source_type="user_upload",
        source_url=None,
        extraction_status=doc.extraction_status,
        page_count=doc.page_count,
        message=f"User PDF uploaded and parsed: status {doc.extraction_status} ({doc.page_count} pages).",
    )


@router.get(
    "/api/papers/{paper_id}/document-status",
    response_model=DocumentStatusResponse,
    summary="Get full-text document processing status",
)
def get_document_status(
    paper_id: str,
    db: Session = Depends(get_db),
):
    """Returns layout, page count, and extraction status for a paper."""
    doc_repo = DocumentRepository(db)
    doc = doc_repo.get_by_paper_id(paper_id)

    if not doc:
        return DocumentStatusResponse(
            paper_id=paper_id,
            has_document=False,
            extraction_status="no_access",
            page_count=0,
            section_headings=[],
            total_characters_extracted=0,
        )

    headings = list(dict.fromkeys([s.get("heading") for s in doc.extracted_sections if s.get("heading")]))

    return DocumentStatusResponse(
        paper_id=paper_id,
        has_document=True,
        document_id=doc.id,
        source_type=doc.source_type,
        file_size_bytes=doc.file_size_bytes,
        page_count=doc.page_count,
        extraction_status=doc.extraction_status,
        section_headings=headings,
        total_characters_extracted=len(doc.raw_text or ""),
        error_details=doc.error_details,
        retrieved_at=doc.retrieved_at,
    )
