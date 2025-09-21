"""
File upload endpoints with temporary storage.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from pathlib import Path
import shutil
from datetime import datetime
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_contract(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    process_immediately: bool = True
):
    """Upload contract file to temporary storage."""
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files supported")
        
        # Create uploads directory
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = upload_dir / f"{timestamp}_{file.filename}"
        
        # Save file temporarily
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        contract_id = f"contract_{timestamp}"
        
        if process_immediately:
            from .contracts import process_contract_background
            background_tasks.add_task(
                process_contract_background,
                str(file_path),
                contract_id
            )
            status = "processing"
        else:
            status = "uploaded"
        
        return {
            "contract_id": contract_id,
            "filename": file.filename,
            "status": status,
            "message": "File uploaded successfully"
        }
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))