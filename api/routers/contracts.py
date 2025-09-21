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
    contract_id: Optional[str] = None

class ProcessContractResponse(BaseModel):
    status: str
    contract_id: str
    message: str

def process_contract_background(file_path: str, contract_id: str):
    """Background task for contract processing."""
    import os
    try:
        from pipeline.orchestrator import ContractPipeline
        from pipeline.firestore_manager import FirestoreManager
        
        # Initialize status
        from pipeline.local_storage import LocalStorageManager
        storage_manager = LocalStorageManager()
        storage_manager.update_contract_status(contract_id, 'processing', 0)
        
        pipeline = ContractPipeline()
        result = pipeline.process_contract(file_path, contract_id)
        
        # Update status to completed
        storage_manager.update_contract_status(contract_id, 'completed', 100)
        
        logger.info(f"Contract {contract_id} processed successfully")
        
        # Cleanup temporary file after processing
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Temporary file {file_path} cleaned up")
        
        return result
    except Exception as e:
        # Update status to failed and cleanup
        try:
            from pipeline.local_storage import LocalStorageManager
            storage_manager = LocalStorageManager()
            storage_manager.update_contract_status(contract_id, 'failed', 0)
        except:
            pass
            
        if os.path.exists(file_path):
            os.remove(file_path)
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
            contract_id
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
        from pipeline.local_storage import LocalStorageManager
        
        storage_manager = LocalStorageManager()
        status = storage_manager.get_contract_status(contract_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{contract_id}")
async def get_contract(contract_id: str):
    """Get processed contract data."""
    try:
        from pipeline.local_storage import LocalStorageManager
        
        storage_manager = LocalStorageManager()
        contract = storage_manager.get_contract(contract_id)
        
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        return contract
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))