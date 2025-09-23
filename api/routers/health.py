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

@router.get("/supabase")
async def test_supabase():
    """Test Supabase connection."""
    try:
        from config import settings
        
        has_url = bool(getattr(settings, 'SUPABASE_URL', None))
        has_key = bool(getattr(settings, 'SUPABASE_KEY', None))
        
        if not has_url or not has_key:
            return {
                "status": "error",
                "message": "Supabase credentials missing",
                "has_url": has_url,
                "has_key": has_key
            }
        
        from supabase import create_client
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        
        result = supabase.table('contracts').select('count').limit(1).execute()
        
        return {
            "status": "success",
            "message": "Supabase connected",
            "table_accessible": True
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }
