"""
Database models for MineSync AI
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Enum as SQLEnum, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()


class DocumentStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    file_path = Column(String)
    document_type = Column(String)  # e.g., "production_report", "geological_report"
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.UPLOADED)
    upload_date = Column(DateTime, default=datetime.utcnow)
    file_size = Column(Integer)
    metadata = Column(JSON, nullable=True)  # Additional metadata like source, date extracted, etc.

    # Relationships
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    extractions = relationship("ExtractedRecord", back_populates="source_document")


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), index=True)
    page_number = Column(Integer)
    raw_text = Column(Text)
    extracted_text = Column(Text, nullable=True)

    document = relationship("Document", back_populates="pages")


class ExtractedRecord(Base):
    __tablename__ = "extracted_records"

    id = Column(Integer, primary_key=True, index=True)
    source_document_id = Column(Integer, ForeignKey("documents.id"), index=True)
    source_page = Column(Integer, nullable=True)

    # Core fields
    subsidiary = Column(String, nullable=True, index=True)
    mine = Column(String, nullable=True, index=True)
    project = Column(String, nullable=True)
    location = Column(String, nullable=True)
    financial_year = Column(String, nullable=True, index=True)

    # Production data
    production_value = Column(Float, nullable=True)
    production_unit = Column(String, nullable=True)
    target_value = Column(Float, nullable=True)
    target_unit = Column(String, nullable=True)

    # Metadata
    extracted_data = Column(JSON)  # Full extracted JSON
    validation_status = Column(String, nullable=True)  # "verified", "discrepancy", "flagged"
    confidence_score = Column(Float, nullable=True)
    extraction_timestamp = Column(DateTime, default=datetime.utcnow)

    source_document = relationship("Document", back_populates="extractions")


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("extracted_records.id"))
    validation_type = Column(String)  # "unit_normalization", "cross_document", "anomaly"
    status = Column(String)  # "pass", "warning", "fail"
    message = Column(Text)
    resolved = Column(Integer, default=0)  # 1 if human has reviewed
    created_at = Column(DateTime, default=datetime.utcnow)


class Query(Base):
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    user_question = Column(Text)
    query_type = Column(String)  # "standard", "parliamentary"
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, nullable=True)


class QuerySource(Base):
    __tablename__ = "query_sources"

    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey("queries.id"))
    source_document_id = Column(Integer, ForeignKey("documents.id"))
    source_page = Column(Integer, nullable=True)
    relevance_score = Column(Float, nullable=True)


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    report_type = Column(String)  # "production", "geological", "parliamentary"
    filters = Column(JSON)  # Report generation filters
    content = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)
    file_path = Column(String, nullable=True)


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    keyword_frequency = Column(JSON)  # {"keyword": frequency, ...}
    document_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String)
    entity_type = Column(String)
    entity_id = Column(Integer)
    user_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON, nullable=True)
