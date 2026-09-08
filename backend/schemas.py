"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# Document schemas
class DocumentCreate(BaseModel):
    filename: str
    document_type: str


class DocumentResponse(BaseModel):
    id: int
    filename: str
    document_type: str
    status: str
    upload_date: datetime
    file_size: int
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int


# Extracted record schemas
class ExtractedRecordCreate(BaseModel):
    source_document_id: int
    source_page: Optional[int] = None
    subsidiary: Optional[str] = None
    mine: Optional[str] = None
    project: Optional[str] = None
    location: Optional[str] = None
    financial_year: Optional[str] = None
    production_value: Optional[float] = None
    production_unit: Optional[str] = None
    target_value: Optional[float] = None
    target_unit: Optional[str] = None
    extracted_data: Dict[str, Any]
    validation_status: Optional[str] = None
    confidence_score: Optional[float] = None


class ExtractedRecordResponse(BaseModel):
    id: int
    source_document_id: int
    source_page: Optional[int]
    subsidiary: Optional[str]
    mine: Optional[str]
    project: Optional[str]
    location: Optional[str]
    financial_year: Optional[str]
    production_value: Optional[float]
    production_unit: Optional[str]
    target_value: Optional[float]
    target_unit: Optional[str]
    extracted_data: Dict[str, Any]
    validation_status: Optional[str]
    confidence_score: Optional[float]
    extraction_timestamp: datetime

    class Config:
        from_attributes = True


# Query schemas
class QueryCreate(BaseModel):
    user_question: str
    query_type: str = "standard"  # "standard" or "parliamentary"
    metadata: Optional[Dict[str, Any]] = None


class QueryResponse(BaseModel):
    id: int
    user_question: str
    query_type: str
    created_at: datetime

    class Config:
        from_attributes = True


# Query Answer schema
class QueryAnswer(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    validation_status: str


# Parliamentary Query schemas
class ParliamentaryQueryCreate(BaseModel):
    question: str
    entities: Optional[List[str]] = None  # subsidiary, mine names
    metrics: Optional[List[str]] = None  # what to extract
    date_range: Optional[Dict[str, str]] = None  # "from", "to"


class ParliamentaryQueryResponse(BaseModel):
    query_id: int
    draft_response: str
    evidence_table: Dict[str, Any]
    sources: List[Dict[str, Any]]
    confidence: float


# Report schemas
class ReportGenerateRequest(BaseModel):
    report_type: str  # "production", "geological", "parliamentary"
    subsidiary: Optional[str] = None
    mine: Optional[str] = None
    financial_year: Optional[str] = None
    date_range: Optional[Dict[str, str]] = None
    include_trends: bool = True
    include_target_vs_actual: bool = True
    include_anomalies: bool = False
    include_sources: bool = True


class ReportResponse(BaseModel):
    id: int
    title: str
    report_type: str
    generated_at: datetime
    file_path: Optional[str] = None

    class Config:
        from_attributes = True


# Validation result schemas
class ValidationResultResponse(BaseModel):
    id: int
    record_id: int
    validation_type: str
    status: str
    message: str
    resolved: int
    created_at: datetime

    class Config:
        from_attributes = True


# Analytics schemas
class AnalyticsResponse(BaseModel):
    total_documents: int
    processed_documents: int
    failed_documents: int
    total_extracted_records: int
    total_queries: int
    total_reports: int
    validation_alerts: int
    production_total: Optional[float] = None
    target_total: Optional[float] = None


# Topic schemas
class TopicResponse(BaseModel):
    id: int
    name: str
    keyword_frequency: Dict[str, int]
    document_count: int
    created_at: datetime

    class Config:
        from_attributes = True
