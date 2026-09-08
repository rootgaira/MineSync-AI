"""
Document processing module for MineSync AI
Handles OCR, text extraction, and document classification
"""
import os
from pathlib import Path
from typing import Dict, List, Tuple
import logging

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None

try:
    from openpyxl import load_workbook
except ImportError:
    load_workbook = None

try:
    from PIL import Image
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None

try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process documents and extract text using OCR and parsing"""

    def __init__(self):
        """Initialize document processor with OCR engines"""
        self.ocr_tesseract = self._init_tesseract()
        self.ocr_paddle = self._init_paddleocr()

    def _init_tesseract(self) -> bool:
        """Initialize Tesseract OCR"""
        if pytesseract is None:
            logger.warning("Tesseract not available, install pytesseract")
            return False

        try:
            # Try to run tesseract to verify installation
            pytesseract.get_tesseract_version()
            logger.info("✓ Tesseract OCR initialized")
            return True
        except Exception as e:
            logger.warning(f"Tesseract not found: {e}")
            return False

    def _init_paddleocr(self) -> bool:
        """Initialize PaddleOCR for multilingual support"""
        if PaddleOCR is None:
            logger.warning("PaddleOCR not available, install paddleocr")
            return False

        try:
            # Initialize with English language
            # Downloads model on first run (~50MB)
            self.paddle_ocr_engine = PaddleOCR(use_angle_cls=True, lang="en")
            logger.info("✓ PaddleOCR initialized")
            return True
        except Exception as e:
            logger.warning(f"PaddleOCR initialization failed: {e}")
            return False

    def process_document(self, file_path: str) -> Dict:
        """
        Process a document based on file type
        Returns: {
            "success": bool,
            "pages": [{"page_number": int, "text": str}, ...],
            "metadata": {
                "file_type": str,
                "total_pages": int,
                "processing_method": str,
                "ocr_used": bool
            },
            "error": str (if failed)
        }
        """
        try:
            file_ext = Path(file_path).suffix.lower()

            if file_ext == ".pdf":
                return self._process_pdf(file_path)
            elif file_ext == ".docx":
                return self._process_docx(file_path)
            elif file_ext == ".xlsx":
                return self._process_xlsx(file_path)
            elif file_ext in [".png", ".jpg", ".jpeg"]:
                return self._process_image(file_path)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported file type: {file_ext}",
                }

        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def _process_pdf(self, file_path: str) -> Dict:
        """Extract text from PDF using PyMuPDF"""
        if fitz is None:
            return {
                "success": False,
                "error": "PyMuPDF not installed. Install with: pip install pymupdf",
            }

        try:
            doc = fitz.open(file_path)
            pages = []
            total_pages = len(doc)

            for page_num in range(total_pages):
                page = doc[page_num]

                # Try to extract text
                text = page.get_text()

                # If PDF is scanned/image-based, use OCR
                if not text.strip():
                    logger.info(f"Page {page_num + 1} appears to be image-based, using OCR")
                    text = self._ocr_page_from_pdf(page)

                pages.append({
                    "page_number": page_num + 1,
                    "text": text,
                })

            doc.close()

            return {
                "success": True,
                "pages": pages,
                "metadata": {
                    "file_type": "pdf",
                    "total_pages": total_pages,
                    "processing_method": "PyMuPDF + OCR",
                    "ocr_used": any(len(p["text"]) == 0 for p in pages),
                },
            }

        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            return {
                "success": False,
                "error": f"PDF processing failed: {str(e)}",
            }

    def _ocr_page_from_pdf(self, pdf_page) -> str:
        """Use OCR to extract text from a PDF page"""
        try:
            # Convert PDF page to image
            pix = pdf_page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
            img_data = pix.tobytes("png")

            # Save temporarily
            temp_path = "/tmp/page_ocr.png"
            with open(temp_path, "wb") as f:
                f.write(img_data)

            # Run OCR
            text = self._ocr_image(temp_path)

            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)

            return text

        except Exception as e:
            logger.error(f"PDF page OCR failed: {e}")
            return ""

    def _process_docx(self, file_path: str) -> Dict:
        """Extract text from DOCX using python-docx"""
        if DocxDocument is None:
            return {
                "success": False,
                "error": "python-docx not installed. Install with: pip install python-docx",
            }

        try:
            doc = DocxDocument(file_path)

            # Extract all paragraphs
            text_content = "\n".join([para.text for para in doc.paragraphs])

            # Extract from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join([cell.text for cell in row.cells])
                    text_content += "\n" + row_text

            return {
                "success": True,
                "pages": [{
                    "page_number": 1,
                    "text": text_content,
                }],
                "metadata": {
                    "file_type": "docx",
                    "total_pages": 1,
                    "processing_method": "python-docx",
                    "ocr_used": False,
                },
            }

        except Exception as e:
            logger.error(f"DOCX processing failed: {e}")
            return {
                "success": False,
                "error": f"DOCX processing failed: {str(e)}",
            }

    def _process_xlsx(self, file_path: str) -> Dict:
        """Extract text from XLSX using openpyxl"""
        if load_workbook is None:
            return {
                "success": False,
                "error": "openpyxl not installed. Install with: pip install openpyxl",
            }

        try:
            workbook = load_workbook(file_path)

            pages = []
            for sheet_index, sheet_name in enumerate(workbook.sheetnames):
                sheet = workbook[sheet_name]

                # Extract all cell values
                rows = []
                for row in sheet.iter_rows(values_only=True):
                    row_text = " | ".join([str(cell) if cell is not None else "" for cell in row])
                    rows.append(row_text)

                sheet_text = "\n".join(rows)

                pages.append({
                    "page_number": sheet_index + 1,
                    "text": sheet_text,
                })

            workbook.close()

            return {
                "success": True,
                "pages": pages,
                "metadata": {
                    "file_type": "xlsx",
                    "total_pages": len(workbook.sheetnames),
                    "processing_method": "openpyxl",
                    "ocr_used": False,
                },
            }

        except Exception as e:
            logger.error(f"XLSX processing failed: {e}")
            return {
                "success": False,
                "error": f"XLSX processing failed: {str(e)}",
            }

    def _process_image(self, file_path: str) -> Dict:
        """Extract text from image using OCR"""
        if Image is None:
            return {
                "success": False,
                "error": "Pillow not installed. Install with: pip install pillow",
            }

        try:
            text = self._ocr_image(file_path)

            return {
                "success": True,
                "pages": [{
                    "page_number": 1,
                    "text": text,
                }],
                "metadata": {
                    "file_type": "image",
                    "total_pages": 1,
                    "processing_method": "OCR",
                    "ocr_used": True,
                },
            }

        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return {
                "success": False,
                "error": f"Image processing failed: {str(e)}",
            }

    def _ocr_image(self, image_path: str) -> str:
        """Run OCR on image using available engines"""
        text = ""

        # Try PaddleOCR first (multilingual, no language dependency)
        if self.ocr_paddle:
            try:
                logger.info(f"Using PaddleOCR for {image_path}")
                result = self.paddle_ocr_engine.ocr(image_path, cls=True)
                if result:
                    # Result is list of lists of tuples: [[(text, confidence), ...], ...]
                    text = "\n".join([
                        line_text
                        for line in result
                        for (line_text, _) in line
                    ])
                    if text:
                        return text
            except Exception as e:
                logger.warning(f"PaddleOCR failed: {e}")

        # Fallback to Tesseract
        if self.ocr_tesseract:
            try:
                logger.info(f"Using Tesseract OCR for {image_path}")
                image = Image.open(image_path)
                text = pytesseract.image_to_string(image)
                if text:
                    return text
            except Exception as e:
                logger.warning(f"Tesseract OCR failed: {e}")

        logger.warning(f"No OCR available for {image_path}")
        return ""

    def classify_document(self, text: str) -> str:
        """
        Classify document type based on content
        Returns: "production_report", "geological_report", "annual_report", etc.
        """
        text_lower = text.lower()

        # Keywords for classification
        production_keywords = ["production", "output", "mt", "metric tons", "coal", "iron"]
        geological_keywords = ["geological", "mineral", "ore", "deposit", "stratum", "geology"]
        annual_keywords = ["annual", "yearly", "fiscal year", "fy", "financial year"]
        environmental_keywords = ["environmental", "impact", "pollution", "emission", "water"]
        project_keywords = ["project", "development", "construction", "facility", "plant"]

        # Score each category
        scores = {
            "production_report": sum(1 for kw in production_keywords if kw in text_lower),
            "geological_report": sum(1 for kw in geological_keywords if kw in text_lower),
            "annual_report": sum(1 for kw in annual_keywords if kw in text_lower),
            "environmental_report": sum(1 for kw in environmental_keywords if kw in text_lower),
            "project_report": sum(1 for kw in project_keywords if kw in text_lower),
        }

        # Return highest scoring category
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        else:
            return "administrative_document"  # Default

    def extract_tables(self, text: str) -> List[Dict]:
        """
        Extract table-like structures from text
        Returns: [{"headers": [...], "rows": [[...], ...]}, ...]
        """
        # Simple table detection: look for pipe-separated or aligned columns
        tables = []
        lines = text.split("\n")

        current_table = None
        for line in lines:
            # Detect table separators (lines with | or multiple spaces)
            if " | " in line or "\t" in line:
                if current_table is None:
                    current_table = []
                # Split by pipe or tabs
                cells = line.split(" | ") if " | " in line else line.split("\t")
                current_table.append([cell.strip() for cell in cells])
            else:
                if current_table and len(current_table) > 1:
                    tables.append({
                        "headers": current_table[0] if current_table else [],
                        "rows": current_table[1:] if len(current_table) > 1 else [],
                    })
                current_table = None

        return tables


# Singleton instance
_processor = None


def get_processor() -> DocumentProcessor:
    """Get or create document processor instance"""
    global _processor
    if _processor is None:
        _processor = DocumentProcessor()
    return _processor
