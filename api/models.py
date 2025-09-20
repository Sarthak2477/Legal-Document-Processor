"""
Pydantic models for API request/response schemas.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ProcessingStatus(str, Enum):
    """Contract processing status enum."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskLevel(str, Enum):
    """Risk level enum."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Request Models

class QuestionAnswerRequest(BaseModel):
    """Request model for asking questions about contracts."""
    question: str = Field(..., description="Question to ask about the contract")


class ContractSearchRequest(BaseModel):
    """Request model for contract search."""
    query: str = Field(..., description="Search query")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional search filters")


class BatchProcessingRequest(BaseModel):
    """Request model for batch processing."""
    contract_ids: List[str] = Field(..., description="List of contract IDs to process")
    options: Dict[str, Any] = Field(default_factory=dict, description="Processing options")


# Response Models

class ContractUploadResponse(BaseModel):
    """Response model for contract upload."""
    contract_id: str
    filename: str
    status: ProcessingStatus
    message: str
    upload_time: datetime = Field(default_factory=datetime.now)


class ContractProcessingStatus(BaseModel):
    """Response model for processing status."""
    contract_id: str
    status: ProcessingStatus
    progress: int = Field(ge=0, le=100, description="Processing progress percentage")
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    processing_stats: Optional[Dict[str, Any]] = None


class ClauseInfo(BaseModel):
    """Information about a contract clause."""
    id: str
    text: str
    legal_category: Optional[str] = None
    risk_level: Optional[RiskLevel] = None
    key_terms: List[str] = Field(default_factory=list)
    obligations: List[str] = Field(default_factory=list)
    conditions: List[str] = Field(default_factory=list)
    confidence_score: Optional[float] = None


class SectionInfo(BaseModel):
    """Information about a contract section."""
    id: str
    title: str
    section_type: Optional[str] = None
    importance_score: Optional[float] = None
    clause_count: int
    contains_obligations: bool = False
    contains_conditions: bool = False


class RiskAssessment(BaseModel):
    """Contract risk assessment."""
    overall_risk: RiskLevel
    risk_factors: List[str]
    high_risk_clauses: List[str]
    recommendations: List[str]
    risk_score: float = Field(ge=0.0, le=1.0)


class KeyTerms(BaseModel):
    """Extracted key terms from contract."""
    parties: List[str] = Field(default_factory=list)
    effective_dates: List[str] = Field(default_factory=list)
    payment_terms: List[str] = Field(default_factory=list)
    termination_conditions: List[str] = Field(default_factory=list)
    governing_law: List[str] = Field(default_factory=list)
    obligations: List[str] = Field(default_factory=list)
    conditions: List[str] = Field(default_factory=list)


class ContractAnalysisResponse(BaseModel):
    """Comprehensive contract analysis response."""
    contract_id: str
    filename: str
    processing_date: datetime
    
    # Structure analysis
    sections: List[SectionInfo]
    total_clauses: int
    
    # Content analysis
    summary: str
    key_terms: KeyTerms
    risk_assessment: RiskAssessment
    
    # Legal analysis
    contract_type: Optional[str] = None
    jurisdiction: Optional[str] = None
    compliance_flags: List[str] = Field(default_factory=list)
    missing_clauses: List[str] = Field(default_factory=list)
    unusual_terms: List[str] = Field(default_factory=list)
    
    # Processing metadata
    ocr_method: str
    confidence_score: float
    processing_time: Optional[float] = None


class QuestionAnswerResponse(BaseModel):
    """Response model for question answering."""
    question: str
    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    sources: List[str] = Field(default_factory=list, description="Source clause IDs")
    timestamp: datetime = Field(default_factory=datetime.now)


class ContractSummary(BaseModel):
    """Summary information about a contract."""
    contract_id: str
    filename: str
    status: ProcessingStatus
    upload_date: datetime
    processing_date: Optional[datetime] = None
    file_size: int
    pages: int
    risk_level: Optional[RiskLevel] = None
    contract_type: Optional[str] = None


class ContractListResponse(BaseModel):
    """Response model for contract listing."""
    contracts: List[ContractSummary]
    total: int
    page: int
    limit: int
    has_next: bool
    has_previous: bool


class SearchResult(BaseModel):
    """Individual search result."""
    contract_id: str
    filename: str
    relevance_score: float
    matching_clauses: List[ClauseInfo]
    snippet: str


class ContractSearchResponse(BaseModel):
    """Response model for contract search."""
    query: str
    results: List[SearchResult]
    total_results: int
    search_time: float
    timestamp: datetime = Field(default_factory=datetime.now)


class BatchProcessingResponse(BaseModel):
    """Response model for batch processing."""
    batch_id: str
    status: str
    total_contracts: int
    started_at: datetime = Field(default_factory=datetime.now)


class BatchStatus(BaseModel):
    """Batch processing status."""
    batch_id: str
    status: str
    total_contracts: int
    completed_contracts: int
    failed_contracts: int
    progress: int = Field(ge=0, le=100)
    started_at: datetime
    completed_at: Optional[datetime] = None
    results: Optional[List[Dict[str, Any]]] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    status_code: int
    timestamp: datetime = Field(default_factory=datetime.now)
    details: Optional[Dict[str, Any]] = None


# Analytics Models

class ContractMetrics(BaseModel):
    """Contract processing metrics."""
    total_contracts: int
    processed_contracts: int
    failed_contracts: int
    average_processing_time: float
    risk_distribution: Dict[str, int]
    contract_types: Dict[str, int]
    processing_methods: Dict[str, int]


class UserAnalytics(BaseModel):
    """User analytics data."""
    user_id: str
    total_contracts: int
    contracts_this_month: int
    most_common_risk_level: RiskLevel
    most_common_contract_type: str
    average_contract_size: float
    processing_time_saved: float


# WebSocket Models

class WebSocketMessage(BaseModel):
    """WebSocket message model."""
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


class ProcessingUpdate(BaseModel):
    """Processing progress update."""
    contract_id: str
    status: ProcessingStatus
    progress: int
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)