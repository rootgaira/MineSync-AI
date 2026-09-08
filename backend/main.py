"""
FastAPI main application for MineSync AI
"""
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
import os
import shutil
from pathlib import Path

from database import get_db, init_db
from models import Document, DocumentStatus, ExtractedRecord, Query as QueryModel
from schemas import (
    DocumentResponse,
    DocumentListResponse,
    ExtractedRecordResponse,
    QueryCreate,
    QueryResponse,
    AnalyticsResponse,
    ParliamentaryQueryCreate,
    ParliamentaryQueryResponse,
    ReportGenerateRequest,
    ReportResponse,
)

app = FastAPI(
    title="MineSync AI API",
    description="AI-powered geological, mining & production intelligence platform",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    print("✓ MineSync AI backend started")


# ============================================================================
# Document Management Endpoints
# ============================================================================

@app.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Query(...),
    db: Session = Depends(get_db),
):
    """
    Upload a document (PDF, DOCX, XLSX, PNG, JPG).

    - **file**: The document file to upload
    - **document_type**: Type of document (e.g., "production_report", "geological_report")
    """
    try:
        # Validate file type
        allowed_extensions = {".pdf", ".docx", ".xlsx", ".png", ".jpg", ".jpeg"}
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not supported. Allowed: {allowed_extensions}",
            )

        # Save file
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = file_path.stat().st_size

        # Create database record
        db_document = Document(
            filename=file.filename,
            file_path=str(file_path),
            document_type=document_type,
            status=DocumentStatus.UPLOADED,
            file_size=file_size,
            metadata={"uploaded_by": "system", "original_name": file.filename},
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)

        return DocumentResponse.from_orm(db_document)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List all uploaded documents with pagination"""
    documents = db.query(Document).offset(skip).limit(limit).all()
    total = db.query(Document).count()
    return DocumentListResponse(
        documents=[DocumentResponse.from_orm(doc) for doc in documents],
        total=total,
    )


@app.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get details of a specific document"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse.from_orm(document)


@app.post("/documents/{document_id}/process")
async def process_document(document_id: int, db: Session = Depends(get_db)):
    """
    Trigger processing of a document (OCR, text extraction, AI extraction).
    In Phase 1, this is a stub. Phase 2 will implement actual processing.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # For Phase 1, just update status to show it was triggered
    document.status = DocumentStatus.PROCESSING
    db.commit()
    db.refresh(document)

    return {
        "message": "Document processing started",
        "document_id": document_id,
        "status": document.status,
    }


# ============================================================================
# Extraction Endpoints
# ============================================================================

@app.get("/documents/{document_id}/extraction", response_model=list[ExtractedRecordResponse])
async def get_extraction(document_id: int, db: Session = Depends(get_db)):
    """Get extracted records for a document"""
    records = (
        db.query(ExtractedRecord)
        .filter(ExtractedRecord.source_document_id == document_id)
        .all()
    )
    return [ExtractedRecordResponse.from_orm(record) for record in records]


# ============================================================================
# Query Endpoints
# ============================================================================

@app.post("/query", response_model=QueryResponse)
async def create_query(
    query: QueryCreate,
    db: Session = Depends(get_db),
):
    """
    Create a natural language query.
    Phase 1 endpoint - Phase 5 will implement RAG and LLM response.
    """
    db_query = QueryModel(
        user_question=query.user_question,
        query_type=query.query_type,
        metadata=query.metadata,
    )
    db.add(db_query)
    db.commit()
    db.refresh(db_query)
    return QueryResponse.from_orm(db_query)


# ============================================================================
# Parliamentary Query Endpoints
# ============================================================================

@app.post("/parliamentary-query", response_model=ParliamentaryQueryResponse)
async def parliamentary_query(
    query: ParliamentaryQueryCreate,
    db: Session = Depends(get_db),
):
    """
    Parliamentary/High-priority query with structured response.
    Phase 1 endpoint - Phase 6 will implement full workflow.
    """
    # For Phase 1, return stub response
    db_query = QueryModel(
        user_question=query.question,
        query_type="parliamentary",
        metadata={
            "entities": query.entities,
            "metrics": query.metrics,
            "date_range": query.date_range,
        },
    )
    db.add(db_query)
    db.commit()
    db.refresh(db_query)

    return ParliamentaryQueryResponse(
        query_id=db_query.id,
        draft_response="[Draft response will be generated in Phase 6]",
        evidence_table={},
        sources=[],
        confidence=0.0,
    )


# ============================================================================
# Report Endpoints
# ============================================================================

@app.post("/reports/generate", response_model=ReportResponse)
async def generate_report(
    report_request: ReportGenerateRequest,
    db: Session = Depends(get_db),
):
    """
    Generate a report based on filters.
    Phase 1 endpoint - Phase 7 will implement full report generation.
    """
    from models import Report

    report = Report(
        title=f"{report_request.report_type.capitalize()} Report",
        report_type=report_request.report_type,
        filters={
            "subsidiary": report_request.subsidiary,
            "mine": report_request.mine,
            "financial_year": report_request.financial_year,
            "date_range": report_request.date_range,
        },
        content="[Report content will be generated in Phase 7]",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return ReportResponse.from_orm(report)


# ============================================================================
# Analytics Endpoints
# ============================================================================

@app.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(db: Session = Depends(get_db)):
    """Get dashboard analytics"""
    total_docs = db.query(Document).count()
    processed_docs = (
        db.query(Document)
        .filter(Document.status == DocumentStatus.PROCESSED)
        .count()
    )
    failed_docs = (
        db.query(Document).filter(Document.status == DocumentStatus.FAILED).count()
    )
    total_records = db.query(ExtractedRecord).count()
    total_queries = db.query(QueryModel).count()

    return AnalyticsResponse(
        total_documents=total_docs,
        processed_documents=processed_docs,
        failed_documents=failed_docs,
        total_extracted_records=total_records,
        total_queries=total_queries,
        total_reports=0,
        validation_alerts=0,
        production_total=None,
        target_total=None,
    )


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "MineSync AI Backend"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
