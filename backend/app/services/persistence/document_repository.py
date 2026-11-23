"""Document database repository."""

from typing import Optional, List
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from backend.app.models.document import FulltextDocument


class DocumentRepository:
    """Repository handling persistence for full-text document records."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_paper_id(self, paper_id: str) -> Optional[FulltextDocument]:
        stmt = (
            select(FulltextDocument)
            .where(FulltextDocument.paper_id == paper_id)
            .order_by(desc(FulltextDocument.retrieved_at))
            .limit(1)
        )
        return self.db.scalars(stmt).first()

    def create_document(
        self,
        paper_id: str,
        source_type: str,
        file_path: Optional[str],
        file_size_bytes: int,
        file_hash_sha256: Optional[str],
        extraction_status: str,
        page_count: int,
        extracted_sections: list,
        raw_text: Optional[str],
        error_details: Optional[str] = None,
    ) -> FulltextDocument:
        doc = FulltextDocument(
            paper_id=paper_id,
            source_type=source_type,
            file_path=file_path,
            file_size_bytes=file_size_bytes,
            file_hash_sha256=file_hash_sha256,
            extraction_status=extraction_status,
            page_count=page_count,
            extracted_sections=extracted_sections,
            raw_text=raw_text,
            error_details=error_details,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

