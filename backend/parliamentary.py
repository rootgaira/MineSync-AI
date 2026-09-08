"""
Phase 6: Parliamentary Query Assistant
Generates official responses to parliamentary queries with evidence
"""
import logging
from typing import Dict, List
from sqlalchemy.orm import Session
import requests
import json

from models import Query as QueryModel, ExtractedRecord, Document
from rag import get_rag_service
from validation import ValidationService

logger = logging.getLogger(__name__)


class ParliamentaryQueryService:
    """Service for parliamentary query assistance"""

    @staticmethod
    def parse_query(question: str) -> Dict:
        """
        Parse parliamentary query to extract key elements

        Returns:
            {
                "entities": [],
                "metrics": [],
                "time_period": {},
                "aggregation": str
            }
        """
        try:
            ollama_url = "http://localhost:11434"

            prompt = f"""Parse this parliamentary query and extract:
1. Entities (subsidiaries, mines)
2. Metrics (production, target, etc.)
3. Time period (from/to years)
4. Type of comparison/aggregation

Query: {question}

Return as JSON with keys: entities, metrics, time_period (with from/to), aggregation
Return ONLY the JSON."""

            response = requests.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": "mistral",
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "{}")

                # Extract JSON
                try:
                    start = response_text.find("{")
                    end = response_text.rfind("}") + 1
                    if start >= 0 and end > start:
                        parsed = json.loads(response_text[start:end])
                        return parsed
                except:
                    pass

        except Exception as e:
            logger.error(f"Query parsing failed: {e}")

        return {
            "entities": [],
            "metrics": [],
            "time_period": {},
            "aggregation": "summary"
        }

    @staticmethod
    def extract_evidence(
        db: Session,
        entities: List[str],
        metrics: List[str],
        time_period: Dict,
    ) -> List[Dict]:
        """
        Extract evidence data from database

        Returns list of matching records with data
        """
        query = db.query(ExtractedRecord)

        # Filter by entities
        if entities:
            entity_filters = []
            for entity in entities:
                entity_filters.append(ExtractedRecord.subsidiary.ilike(f"%{entity}%"))
                entity_filters.append(ExtractedRecord.mine.ilike(f"%{entity}%"))
            from sqlalchemy import or_
            query = query.filter(or_(*entity_filters))

        # Filter by time period
        if time_period.get("from"):
            query = query.filter(ExtractedRecord.financial_year >= str(time_period["from"]))
        if time_period.get("to"):
            query = query.filter(ExtractedRecord.financial_year <= str(time_period["to"]))

        records = query.all()

        evidence = []
        for record in records:
            evidence_item = {
                "subsidiary": record.subsidiary,
                "mine": record.mine,
                "financial_year": record.financial_year,
                "source_document": record.source_document_id,
                "confidence": record.confidence_score,
            }

            if "production" in metrics:
                evidence_item["production"] = {
                    "value": record.production_value,
                    "unit": record.production_unit,
                }

            if "target" in metrics:
                evidence_item["target"] = {
                    "value": record.target_value,
                    "unit": record.target_unit,
                }

            evidence.append(evidence_item)

        return evidence

    @staticmethod
    def build_evidence_table(evidence: List[Dict]) -> str:
        """Build formatted evidence table"""
        if not evidence:
            return "No evidence data found."

        table = "| Subsidiary | Mine | Year | Production | Target | Confidence |\n"
        table += "|---|---|---|---|---|---|\n"

        for item in evidence:
            prod = f"{item['production']['value']} {item['production']['unit']}" if "production" in item else "—"
            targ = f"{item['target']['value']} {item['target']['unit']}" if "target" in item else "—"
            conf = f"{item['confidence']*100:.0f}%" if item['confidence'] else "—"

            table += f"| {item['subsidiary']} | {item['mine']} | {item['financial_year']} | {prod} | {targ} | {conf} |\n"

        return table

    @staticmethod
    def generate_draft_response(
        question: str,
        evidence: List[Dict],
        evidence_table: str,
    ) -> str:
        """
        Generate official-style draft response

        Uses LLM to synthesize evidence into formal response
        """
        try:
            ollama_url = "http://localhost:11434"

            prompt = f"""Generate an official, formal response to a parliamentary query.

Parliamentary Query: {question}

Supporting Data:
{evidence_table}

Requirements:
1. Professional, formal tone
2. Cite the data provided
3. Include time period covered
4. Acknowledge data sources
5. Be precise and factual
6. Keep to 2-3 paragraphs

Draft Response:"""

            response = requests.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": "mistral",
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "Unable to generate response")

        except Exception as e:
            logger.error(f"Response generation failed: {e}")

        return "Unable to generate official response at this time."

    @staticmethod
    def process_parliamentary_query(
        db: Session,
        question: str,
    ) -> Dict:
        """
        Complete parliamentary query workflow

        Returns:
            {
                "query_id": int,
                "draft_response": str,
                "evidence_table": str,
                "sources": [...],
                "confidence": float,
                "ready_for_approval": bool
            }
        """
        try:
            # Parse query
            parsed = ParliamentaryQueryService.parse_query(question)
            entities = parsed.get("entities", [])
            metrics = parsed.get("metrics", ["production", "target"])
            time_period = parsed.get("time_period", {})

            # Extract evidence
            evidence = ParliamentaryQueryService.extract_evidence(
                db, entities, metrics, time_period
            )

            if not evidence:
                return {
                    "draft_response": "Insufficient data to respond to this query. No matching records found.",
                    "evidence_table": "No data available",
                    "sources": [],
                    "confidence": 0.0,
                    "ready_for_approval": False,
                }

            # Build evidence table
            evidence_table = ParliamentaryQueryService.build_evidence_table(evidence)

            # Generate draft response
            draft_response = ParliamentaryQueryService.generate_draft_response(
                question, evidence, evidence_table
            )

            # Calculate confidence
            avg_confidence = sum(e.get("confidence", 0) for e in evidence) / len(evidence) if evidence else 0

            # Store query in database
            db_query = QueryModel(
                user_question=question,
                query_type="parliamentary",
                extra_metadata={
                    "entities": entities,
                    "metrics": metrics,
                    "time_period": time_period,
                    "evidence_count": len(evidence),
                    "confidence": avg_confidence,
                }
            )
            db.add(db_query)
            db.commit()
            db.refresh(db_query)

            return {
                "query_id": db_query.id,
                "draft_response": draft_response,
                "evidence_table": evidence_table,
                "sources": evidence,
                "confidence": avg_confidence,
                "ready_for_approval": avg_confidence >= 0.7,
            }

        except Exception as e:
            logger.error(f"Parliamentary query processing failed: {e}")
            return {
                "draft_response": f"Error processing query: {str(e)}",
                "evidence_table": "Error",
                "sources": [],
                "confidence": 0.0,
                "ready_for_approval": False,
            }

    @staticmethod
    def approve_and_export(
        db: Session,
        query_id: int,
        edited_response: str = None,
    ) -> Dict:
        """
        Approve query response and prepare for export

        Returns:
            {
                "status": "approved",
                "export_format": "text",
                "content": str,
                "timestamp": str
            }
        """
        query = db.query(QueryModel).filter(QueryModel.id == query_id).first()

        if not query:
            return {"status": "error", "message": "Query not found"}

        # Use edited response if provided
        response_content = edited_response or query.extra_metadata.get("draft_response", "")

        # Mark as approved in metadata
        query.extra_metadata["approved"] = True
        query.extra_metadata["approved_at"] = str(logging.datetime.datetime.now())
        db.commit()

        logger.info(f"Query {query_id} approved for export")

        return {
            "status": "approved",
            "query_id": query_id,
            "export_format": "text",
            "content": response_content,
            "ready_for_distribution": True,
        }
