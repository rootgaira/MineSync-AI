"""
Phase 5: Semantic Search & RAG
Retrieval-augmented generation using embeddings and vector search
"""
import logging
import os
from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

try:
    import faiss
except ImportError:
    faiss = None

from models import Document, DocumentPage, ExtractedRecord

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generate and manage embeddings for semantic search"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize embedding model"""
        self.model_name = model_name
        self.model = None
        self.embedding_dim = 384
        self._init_model()

    def _init_model(self):
        """Initialize sentence transformer model"""
        if SentenceTransformer is None:
            logger.warning("sentence-transformers not installed")
            return

        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"✓ Embedding model loaded: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")

    def encode(self, text: str) -> np.ndarray:
        """Encode text to embedding vector"""
        if self.model is None:
            return np.zeros(self.embedding_dim)

        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.astype(np.float32)
        except Exception as e:
            logger.error(f"Encoding failed: {e}")
            return np.zeros(self.embedding_dim)

    def batch_encode(self, texts: List[str]) -> np.ndarray:
        """Encode multiple texts efficiently"""
        if self.model is None:
            return np.zeros((len(texts), self.embedding_dim))

        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings.astype(np.float32)
        except Exception as e:
            logger.error(f"Batch encoding failed: {e}")
            return np.zeros((len(texts), self.embedding_dim))


class VectorStore:
    """Store and search embeddings using FAISS"""

    def __init__(self, embedding_dim: int = 384):
        """Initialize vector store"""
        self.embedding_dim = embedding_dim
        self.index = None
        self.metadata = []
        self._init_index()

    def _init_index(self):
        """Initialize FAISS index"""
        if faiss is None:
            logger.warning("faiss not installed")
            return

        try:
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            logger.info("✓ FAISS vector store initialized")
        except Exception as e:
            logger.error(f"FAISS initialization failed: {e}")

    def add(self, embeddings: np.ndarray, metadata: List[Dict]):
        """Add embeddings to store"""
        if self.index is None:
            return

        try:
            self.index.add(embeddings)
            self.metadata.extend(metadata)
            logger.info(f"Added {len(embeddings)} embeddings to store")
        except Exception as e:
            logger.error(f"Failed to add embeddings: {e}")

    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict]:
        """Search for similar embeddings"""
        if self.index is None or self.index.ntotal == 0:
            return []

        try:
            distances, indices = self.index.search(query_embedding.reshape(1, -1), k)
            results = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx < len(self.metadata):
                    results.append({
                        "metadata": self.metadata[idx],
                        "distance": float(distance),
                        "similarity": 1 / (1 + distance),  # Convert distance to similarity
                    })
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []


class RAGService:
    """Retrieval-Augmented Generation service"""

    def __init__(self):
        """Initialize RAG components"""
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.llm_url = os.getenv("OLLAMA_URL", "http://localhost:11434")

    def index_document(self, db: Session, document_id: int):
        """Index document pages for semantic search"""
        pages = db.query(DocumentPage).filter(
            DocumentPage.document_id == document_id
        ).all()

        if not pages:
            logger.warning(f"No pages to index for document {document_id}")
            return

        texts = []
        metadata = []

        for page in pages:
            if page.raw_text:
                texts.append(page.raw_text)
                metadata.append({
                    "document_id": document_id,
                    "page_id": page.id,
                    "page_number": page.page_number,
                    "type": "page",
                })

        if texts:
            embeddings = self.embedding_service.batch_encode(texts)
            self.vector_store.add(embeddings, metadata)
            logger.info(f"Indexed {len(texts)} pages for document {document_id}")

    def semantic_search(self, query: str, k: int = 5) -> List[Dict]:
        """Search for semantically similar content"""
        query_embedding = self.embedding_service.encode(query)
        results = self.vector_store.search(query_embedding, k)
        return results

    def search_with_structured_data(
        self,
        db: Session,
        query: str,
        filters: Dict = None,
    ) -> Dict:
        """
        Hybrid search: semantic + structured

        Args:
            db: Database session
            query: Search query
            filters: Optional filters (subsidiary, financial_year, etc.)

        Returns:
            {
                "semantic_results": [...],
                "structured_results": [...],
                "combined": [...]
            }
        """
        # Semantic search
        semantic = self.semantic_search(query, k=5)

        # Structured search
        structured = []
        extracted_records = db.query(ExtractedRecord)

        if filters:
            if filters.get("subsidiary"):
                extracted_records = extracted_records.filter(
                    ExtractedRecord.subsidiary == filters["subsidiary"]
                )
            if filters.get("financial_year"):
                extracted_records = extracted_records.filter(
                    ExtractedRecord.financial_year == filters["financial_year"]
                )
            if filters.get("mine"):
                extracted_records = extracted_records.filter(
                    ExtractedRecord.mine == filters["mine"]
                )

        structured_results = extracted_records.limit(5).all()
        for record in structured_results:
            structured.append({
                "type": "extracted_record",
                "record_id": record.id,
                "subsidiary": record.subsidiary,
                "mine": record.mine,
                "production": record.production_value,
                "target": record.target_value,
                "confidence": record.confidence_score,
            })

        # Combine results
        combined = semantic + structured

        return {
            "semantic_results": semantic,
            "structured_results": structured,
            "combined": combined,
            "total_results": len(combined),
        }

    def generate_answer(self, query: str, context: List[str]) -> Dict:
        """
        Generate answer using retrieved context

        Args:
            query: User question
            context: Retrieved context documents

        Returns:
            {
                "answer": str,
                "sources": [...],
                "confidence": float
            }
        """
        import requests

        try:
            # Prepare context
            context_text = "\n\n".join(context)
            prompt = f"""Answer this question based on the provided context:

Question: {query}

Context:
{context_text}

Answer (be specific and cite sources):"""

            # Call local LLM
            response = requests.post(
                f"{self.llm_url}/api/generate",
                json={
                    "model": "mistral",
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=30,
            )

            if response.status_code != 200:
                return {
                    "answer": "Unable to generate answer",
                    "error": response.text,
                    "confidence": 0.0,
                }

            result = response.json()
            answer = result.get("response", "")

            # Calculate confidence based on context quality
            confidence = min(len(context) / 5, 1.0) if context else 0.0

            return {
                "answer": answer,
                "sources": context,
                "context_count": len(context),
                "confidence": confidence,
            }

        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            return {
                "answer": "Error generating answer",
                "error": str(e),
                "confidence": 0.0,
            }


# Singleton instances
_embedding_service = None
_vector_store = None
_rag_service = None


def get_embedding_service() -> EmbeddingService:
    """Get or create embedding service"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


def get_vector_store() -> VectorStore:
    """Get or create vector store"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


def get_rag_service() -> RAGService:
    """Get or create RAG service"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
