"""
Health check endpoints.
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def health_check():
    return {"status": "healthy", "service": "contract-processor"}

@router.get("/ready")
async def readiness_check():
    # Add database/service checks here
    return {"status": "ready"}