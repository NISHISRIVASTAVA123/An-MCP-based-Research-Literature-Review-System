"""FastAPI routes for exporting literature review metadata as CSV or JSON."""

import csv
import io
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.services.persistence.database import get_db
from backend.app.services.persistence.repositories import (
    ResearchRequestRepository,
    PaperRepository,
)

router = APIRouter(prefix="/api/research-requests", tags=["Exports"])


@router.get("/{request_id}/export")
def export_papers(
    request_id: str,
    format: str = Query("json", description="Export format: 'csv' or 'json'"),
    db: Session = Depends(get_db),
):
    """
    Exports collected academic literature metadata in CSV or JSON format.
    Includes normalized metadata, original source identifiers, and provenance.
    """
    req_repo = ResearchRequestRepository(db)
    req = req_repo.get_by_id(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Research request not found.")

    paper_repo = PaperRepository(db)
    papers, total = paper_repo.list_by_request(
        request_id=request_id,
        page=1,
        page_size=1000,
        sort_by="year",
        sort_order="desc",
    )

    clean_format = format.lower().strip()

    if clean_format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)

        # Header row
        writer.writerow([
            "Paper ID",
            "Title",
            "Authors",
            "Publication Year",
            "Publication Date",
            "Venue",
            "Publication Type",
            "DOI",
            "URL",
            "PDF URL",
            "Citation Count",
            "Has Abstract",
            "Abstract",
            "Is Open Access",
            "Source Databases",
            "External Source IDs",
            "Research Topic",
            "Request ID",
        ])

        for p in papers:
            authors_str = "; ".join(p.authors) if isinstance(p.authors, list) else str(p.authors)
            sources_str = "; ".join([s.source_database for s in p.sources])
            ext_ids_str = "; ".join([f"{s.source_database}:{s.external_source_id or 'none'}" for s in p.sources])

            writer.writerow([
                p.id,
                p.title,
                authors_str,
                p.publication_year or "",
                p.publication_date or "",
                p.venue or "",
                p.publication_type or "",
                p.doi or "",
                p.url or "",
                p.pdf_url or "",
                p.citation_count or 0,
                "Yes" if p.has_abstract else "No",
                p.abstract or "",
                "Yes" if p.is_open_access else "No",
                sources_str,
                ext_ids_str,
                req.topic,
                req.id,
            ])

        output.seek(0)
        filename = f"literature_review_{req.id[:8]}.csv"
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    elif clean_format == "json":
        export_data = {
            "request_id": req.id,
            "topic": req.topic,
            "objective": req.objective,
            "domain": req.domain,
            "publication_timeframe": f"{req.start_year}-{req.end_year}",
            "exported_at": req.updated_at.isoformat(),
            "total_papers": total,
            "papers": [
                {
                    "id": p.id,
                    "title": p.title,
                    "normalized_title": p.normalized_title,
                    "authors": p.authors,
                    "publication_year": p.publication_year,
                    "publication_date": p.publication_date,
                    "venue": p.venue,
                    "publication_type": p.publication_type,
                    "doi": p.doi,
                    "url": p.url,
                    "pdf_url": p.pdf_url,
                    "citation_count": p.citation_count,
                    "has_abstract": p.has_abstract,
                    "abstract": p.abstract,
                    "is_open_access": p.is_open_access,
                    "keywords": p.keywords,
                    "sources": [
                        {
                            "source_database": s.source_database,
                            "external_source_id": s.external_source_id,
                            "source_url": s.source_url,
                            "retrieved_at": s.retrieved_at.isoformat(),
                        }
                        for s in p.sources
                    ],
                }
                for p in papers
            ],
        }

        filename = f"literature_review_{req.id[:8]}.json"
        json_str = json.dumps(export_data, indent=2)
        return Response(
            content=json_str,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported export format. Choose 'json' or 'csv'.")

