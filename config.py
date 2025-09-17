"""
Configuration settings for the contract processing pipeline.
"""
import os
from typing import Optional

try:
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        from pydantic import BaseSettings
    except ImportError:
        # Fallback for testing without pydantic
        class BaseSettings:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)


class Settings(BaseSettings):
    # Firebase configuration
    FIREBASE_PROJECT_ID: Optional[str] = None
    FIREBASE_STORAGE_BUCKET: Optional[str] = None
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    
    # Vector database configuration
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    
    # Google Cloud AI configuration
    VERTEX_AI_PROJECT: Optional[str] = None
    VERTEX_AI_LOCATION: str = "us-central1"
    VERTEX_AI_MODEL: str = "text-bison@001"
    
    # Hugging Face configuration
    HUGGINGFACE_API_KEY: Optional[str] = None
    
    # OCR settings
    TESSERACT_PATH: str = "/usr/bin/tesseract"
    
    # Model settings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    LLM_MODEL: str = "text-bison@001"
    SPACY_MODEL: str = "en_core_web_sm"
    
    # Processing settings
    MAX_CLAUSE_LENGTH: int = 1000
    MIN_CLAUSE_LENGTH: int = 10
    SIMILARITY_THRESHOLD: float = 0.7
    
    class Config:
        env_file = ".env"


settings = Settings()