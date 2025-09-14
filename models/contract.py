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


class ContractSection(BaseModel):
    """Contract section containing multiple clauses."""
    title: str
    clauses: List[Clause] = []
    level: int = 1  # Heading level


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


class ProcessedContract(BaseModel):
    """Complete processed contract model."""
    metadata: ContractMetadata
    sections: List[ContractSection] = []
    entities: List[ExtractedEntity] = []
    raw_text: str = ""
    structured_data: Dict[str, Any] = {}
    processing_stats: Dict[str, Any] = {}