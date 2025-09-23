"""
Data models for contract processing pipeline.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime


class Clause(BaseModel):
    """Individual contract clause model."""
    id: str
    text: str
    clause_type: Optional[str] = None
    section: Optional[str] = None
    subsection: Optional[str] = None
    entities: Dict[str, List[str]] = {}
    embedding: Optional[List[float]] = None
    page_number: Optional[int] = None
    confidence_score: Optional[float] = None
    metadata: Dict[str, Any] = {}
    # Legal-specific fields
    legal_category: Optional[str] = None  # payment, termination, liability, etc.
    risk_level: Optional[str] = None  # low, medium, high, critical
    key_terms: List[str] = []  # extracted key legal terms
    obligations: List[str] = []  # identified obligations
    conditions: List[str] = []  # conditional statements
    references: List[str] = []  # cross-references to other clauses


class ContractSection(BaseModel):
    """Contract section containing multiple clauses."""
    id: str
    title: str
    text: str
    clauses: List[Clause] = []
    level: int = 1  # Heading level
    metadata: Dict[str, Any] = {}
    # Legal-specific fields
    section_type: Optional[str] = None  # definitions, terms, obligations, etc.
    importance_score: Optional[float] = None  # calculated importance
    contains_obligations: bool = False
    contains_conditions: bool = False


class ExtractedEntity(BaseModel):
    """Named entity extracted from contract text."""
    text: str
    label: str
    start: int
    end: int
    confidence: Optional[float] = None


class ContractMetadata(BaseModel):
    """Contract metadata and processing information."""
    filename: str
    file_path: str
    file_size: int
    pages: int
    processing_date: datetime
    ocr_method: str
    language: str = "en"
    confidence_score: Optional[float] = None
    # Legal-specific metadata
    contract_type: Optional[str] = None  # NDA, employment, service, etc.
    jurisdiction: Optional[str] = None
    governing_law: Optional[str] = None
    parties: List[str] = []  # contract parties
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    key_obligations: List[str] = []


class ProcessedContract(BaseModel):
    """Complete processed contract model."""
    metadata: ContractMetadata
    sections: List[ContractSection] = []
    clauses: List[Clause] = []
    entities: List[ExtractedEntity] = []
    raw_text: str = ""
    structured_data: Dict[str, Any] = {}
    processing_stats: Dict[str, Any] = {}
    # Legal analysis results
    risk_assessment: Dict[str, Any] = {}  # overall risk analysis
    compliance_flags: List[str] = []  # potential compliance issues
    missing_clauses: List[str] = []  # standard clauses that are missing
    unusual_terms: List[str] = []  # terms that deviate from standard
    summary: Optional[str] = None  # AI-generated summary
