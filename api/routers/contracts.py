"""
Contract processing endpoints.
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class ProcessContractRequest(BaseModel):
    file_path: str
    bucket: Optional[str] = None
    contract_id: Optional[str] = None

class ProcessContractResponse(BaseModel):
    status: str
    contract_id: str
    message: str

def process_contract_background(file_path: str, contract_id: str, bucket: Optional[str] = None):
    """Background task for contract processing."""
    try:
        from pipeline.orchestrator import ContractPipeline
        
        pipeline = ContractPipeline()
        full_path = f"gs://{bucket}/{file_path}" if bucket else file_path
        result = pipeline.process_contract(full_path, contract_id)
        
        logger.info(f"Contract {contract_id} processed successfully")
        return result
    except Exception as e:
        logger.error(f"Contract processing failed: {e}")
        raise

@router.post("/process", response_model=ProcessContractResponse)
async def process_contract(
    request: ProcessContractRequest,
    background_tasks: BackgroundTasks
):
    """Process a contract file in the background."""
    try:
        contract_id = request.contract_id or f"contract_{hash(request.file_path)}"
        
        background_tasks.add_task(
            process_contract_background,
            request.file_path,
            contract_id,
            request.bucket
        )
        
        return ProcessContractResponse(
            status="processing",
            contract_id=contract_id,
            message="Contract processing started"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{contract_id}")
async def get_contract_status(contract_id: str):
    """Get processing status of a contract."""
    try:
        from pipeline.firestore_manager import FirestoreManager
        
        firestore_manager = FirestoreManager()
        status = firestore_manager.get_contract_status(contract_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{contract_id}")
async def get_contract(contract_id: str):
    """Get processed contract data."""
    try:
        from pipeline.firestore_manager import FirestoreManager
        
        firestore_manager = FirestoreManager()
        contract = firestore_manager.get_contract(contract_id)
        
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        return contract
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))