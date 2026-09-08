"""
Phase 3: AI Data Extraction
Extracts structured mining data from document text using local LLM
"""
import logging
import json
from typing import Dict, Optional
from sqlalchemy.orm import Session
import requests

from models import ExtractedRecord, DocumentPage

logger = logging.getLogger(__name__)

# Extraction schema for mining documents
EXTRACTION_SCHEMA = {
    "subsidiary": "Name of mining subsidiary/company",
    "mine": "Name of the mine or mining operation",
    "project": "Project name if applicable",
    "location": "Geographic location (state, region, coalfield)",
    "financial_year": "Financial year (e.g., 2025-26, FY2025-26)",
    "production_value": "Production quantity (numeric)",
    "production_unit": "Unit of production (MT, tons, kg)",
    "target_value": "Target production quantity (numeric)",
    "target_unit": "Unit of target (MT, tons, kg)",
}

EXTRACTION_PROMPT = """
Extract mining production data from this text. Return ONLY valid JSON with these fields:
{
  "subsidiary": "mining company name",
  "mine": "mine name",
  "location": "geographic location",
  "financial_year": "financial year",
  "production_value": 125.6 (number or null),
  "production_unit": "MT" (or tons, kg, etc),
  "target_value": 130.0 (number or null),
  "target_unit": "MT" (or tons, kg, etc)
}

Return null for fields you cannot extract. Return ONLY the JSON, no other text.

Text to extract from:
"""


class LocalLLMExtractor:
    """Extracts structured data using local LLM via Ollama"""

    def __init__(self, ollama_url: str = "http://localhost:11434"):
        """Initialize extractor with Ollama connection"""
        self.ollama_url = ollama_url
        self.model = "mistral"  # Using Mistral as default (small, fast)
        self.available = self._check_ollama()

    def _check_ollama(self) -> bool:
        """Check if Ollama is available"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            if response.status_code == 200:
                logger.info("✓ Ollama LLM available")
                return True
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
        return False

    def extract_data(self, text: str, max_length: int = 2000) -> Dict:
        """
        Extract structured data from text using local LLM

        Args:
            text: Document text to extract from
            max_length: Max chars to send (to keep LLM request manageable)

        Returns:
            {
                "success": bool,
                "data": {...extracted fields...},
                "confidence": float (0-1),
                "model": str,
                "error": str (if failed)
            }
        """
        if not self.available:
            return {
                "success": False,
                "error": "Ollama not available. Install with: ollama pull mistral",
                "data": self._get_empty_extraction(),
            }

        try:
            # Trim text if too long
            if len(text) > max_length:
                text = text[:max_length]

            # Prepare prompt
            prompt = EXTRACTION_PROMPT + "\n\n" + text

            # Call Ollama
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.1,  # Low temperature for consistent extraction
                },
                timeout=30,
            )

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Ollama error: {response.text}",
                    "data": self._get_empty_extraction(),
                }

            # Parse response
            result = response.json()
            response_text = result.get("response", "")

            # Extract JSON from response
            data = self._parse_json_response(response_text)

            # Calculate confidence based on filled fields
            filled_fields = sum(1 for v in data.values() if v)
            confidence = min(filled_fields / len(data), 1.0)

            logger.info(f"Extracted data: {data} (confidence: {confidence})")

            return {
                "success": True,
                "data": data,
                "confidence": confidence,
                "model": self.model,
            }

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "LLM request timeout",
                "data": self._get_empty_extraction(),
            }
        except Exception as e:
            logger.error(f"Extraction error: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": self._get_empty_extraction(),
            }

    def _parse_json_response(self, text: str) -> Dict:
        """Extract JSON from LLM response"""
        try:
            # Try to find JSON in response
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = text[start:end]
                return json.loads(json_str)
        except Exception as e:
            logger.warning(f"Failed to parse JSON: {e}")

        return self._get_empty_extraction()

    def _get_empty_extraction(self) -> Dict:
        """Return empty extraction template"""
        return {
            "subsidiary": None,
            "mine": None,
            "project": None,
            "location": None,
            "financial_year": None,
            "production_value": None,
            "production_unit": None,
            "target_value": None,
            "target_unit": None,
        }


class ExtractionService:
    """Service to orchestrate AI extraction and storage"""

    @staticmethod
    def extract_from_document(
        db: Session,
        document_id: int,
        extractor: Optional[LocalLLMExtractor] = None,
    ) -> Dict:
        """
        Extract data from all pages of a document

        Args:
            db: Database session
            document_id: Document ID
            extractor: LLM extractor (creates if None)

        Returns:
            {
                "success": bool,
                "records_created": int,
                "avg_confidence": float,
                "error": str (if failed)
            }
        """
        if extractor is None:
            extractor = LocalLLMExtractor()

        try:
            # Get all pages for document
            pages = db.query(DocumentPage).filter(
                DocumentPage.document_id == document_id
            ).all()

            if not pages:
                return {
                    "success": False,
                    "error": "No pages found for document",
                    "records_created": 0,
                }

            records_created = 0
            confidence_scores = []

            # Extract from each page
            for page in pages:
                if not page.raw_text:
                    continue

                # Extract data
                result = extractor.extract_data(page.raw_text)

                if not result["success"]:
                    logger.warning(f"Extraction failed for page {page.page_number}: {result['error']}")
                    continue

                # Create extracted record
                extracted_data = result["data"]
                confidence = result.get("confidence", 0.0)

                record = ExtractedRecord(
                    source_document_id=document_id,
                    source_page=page.page_number,
                    subsidiary=extracted_data.get("subsidiary"),
                    mine=extracted_data.get("mine"),
                    project=extracted_data.get("project"),
                    location=extracted_data.get("location"),
                    financial_year=extracted_data.get("financial_year"),
                    production_value=extracted_data.get("production_value"),
                    production_unit=extracted_data.get("production_unit"),
                    target_value=extracted_data.get("target_value"),
                    target_unit=extracted_data.get("target_unit"),
                    extracted_data=extracted_data,
                    validation_status="pending",
                    confidence_score=confidence,
                )

                db.add(record)
                records_created += 1
                confidence_scores.append(confidence)

            db.commit()

            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0

            logger.info(f"Created {records_created} extracted records with avg confidence {avg_confidence}")

            return {
                "success": True,
                "records_created": records_created,
                "avg_confidence": avg_confidence,
            }

        except Exception as e:
            logger.error(f"Extraction service error: {e}")
            return {
                "success": False,
                "error": str(e),
                "records_created": 0,
            }


# Singleton instance
_extractor = None


def get_extractor() -> LocalLLMExtractor:
    """Get or create extractor instance"""
    global _extractor
    if _extractor is None:
        _extractor = LocalLLMExtractor()
    return _extractor
