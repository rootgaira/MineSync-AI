"""
Document processing service
Handles processing workflow: extract → store → classify
"""
import logging
from typing import Dict, List
from sqlalchemy.orm import Session

from models import Document, DocumentStatus, DocumentPage
from processor import get_processor

logger = logging.getLogger(__name__)


class ProcessingService:
    """Service to orchestrate document processing"""

    @staticmethod
    def process_document_file(
        db: Session,
        document_id: int,
        file_path: str,
    ) -> Dict:
        """
        Process a document file and store results in database

        Args:
            db: Database session
            document_id: ID of document to process
            file_path: Path to file on disk

        Returns:
            {
                "success": bool,
                "message": str,
                "document_id": int,
                "pages_extracted": int,
                "classification": str,
                "error": str (if failed)
            }
        """
        try:
            # Get document from database
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                return {
                    "success": False,
                    "error": f"Document {document_id} not found",
                }

            # Update status to processing
            document.status = DocumentStatus.PROCESSING
            db.commit()

            logger.info(f"Starting processing of document {document_id}: {document.filename}")

            # Get processor
            processor = get_processor()

            # Process document
            result = processor.process_document(file_path)

            if not result["success"]:
                # Mark as failed
                document.status = DocumentStatus.FAILED
                document.extra_metadata = {
                    "error": result.get("error", "Unknown error"),
                }
                db.commit()
                logger.error(f"Document processing failed: {result['error']}")
                return {
                    "success": False,
                    "error": result.get("error"),
                    "document_id": document_id,
                }

            # Extract and classify
            pages = result.get("pages", [])
            metadata = result.get("metadata", {})

            # Combine all text for classification
            all_text = " ".join([p["text"] for p in pages])

            # Classify document
            classification = processor.classify_document(all_text)

            # Extract tables from combined text
            tables = processor.extract_tables(all_text)

            # Store pages in database
            for page_data in pages:
                page = DocumentPage(
                    document_id=document_id,
                    page_number=page_data["page_number"],
                    raw_text=page_data["text"],
                    extracted_text=None,  # Will be populated by Phase 3 (AI extraction)
                )
                db.add(page)

            # Update document with processing metadata
            document.status = DocumentStatus.PROCESSED
            document.document_type = classification
            document.extra_metadata = {
                "processing_method": metadata.get("processing_method"),
                "total_pages": metadata.get("total_pages"),
                "ocr_used": metadata.get("ocr_used"),
                "file_type": metadata.get("file_type"),
                "tables_detected": len(tables),
                "processed": True,
            }

            db.commit()

            logger.info(
                f"Successfully processed document {document_id}: "
                f"{len(pages)} pages, classified as {classification}"
            )

            return {
                "success": True,
                "message": f"Document processed successfully",
                "document_id": document_id,
                "pages_extracted": len(pages),
                "classification": classification,
                "tables_detected": len(tables),
                "processing_method": metadata.get("processing_method"),
            }

        except Exception as e:
            logger.error(f"Error in processing service: {e}")
            try:
                document = db.query(Document).filter(Document.id == document_id).first()
                if document:
                    document.status = DocumentStatus.FAILED
                    document.extra_metadata = {"error": str(e)}
                    db.commit()
            except:
                pass
            return {
                "success": False,
                "error": str(e),
                "document_id": document_id,
            }

    @staticmethod
    def get_document_pages(db: Session, document_id: int) -> List[Dict]:
        """Get all pages for a document"""
        pages = db.query(DocumentPage).filter(
            DocumentPage.document_id == document_id
        ).all()

        return [
            {
                "id": page.id,
                "page_number": page.page_number,
                "raw_text": page.raw_text,
                "extracted_text": page.extracted_text,
            }
            for page in pages
        ]

    @staticmethod
    def get_document_text(db: Session, document_id: int) -> str:
        """Get combined text from all pages of a document"""
        pages = db.query(DocumentPage).filter(
            DocumentPage.document_id == document_id
        ).order_by(DocumentPage.page_number).all()

        return "\n\n---PAGE BREAK---\n\n".join([
            f"Page {page.page_number}:\n{page.raw_text}"
            for page in pages
        ])
