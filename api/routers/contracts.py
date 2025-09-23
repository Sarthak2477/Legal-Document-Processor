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
        from pipeline.local_storage import DatabaseStorageManager
        storage_manager = DatabaseStorageManager()
        storage_manager.update_contract_status(contract_id, 'processing', 0)
        
        pipeline = ContractPipeline()
        result = pipeline.process_contract(file_path)
        
        logger.info(f"Pipeline result keys: {list(result.keys()) if isinstance(result, dict) else 'not dict'}")
        logger.info(f"Pipeline success: {result.get('success') if isinstance(result, dict) else 'unknown'}")
        
        # Store processed contract data
        if result.get('success'):
            logger.info("Processing was successful, attempting to store...")
            
            if result.get('contract'):
                contract = result['contract']
                logger.info(f"Contract object type: {type(contract)}")
                
                # Convert to dict if it's an object
                if hasattr(contract, 'dict'):
                    contract_dict = contract.dict()
                elif hasattr(contract, '__dict__'):
                    contract_dict = contract.__dict__
                else:
                    contract_dict = contract
                
                logger.info(f"Contract dict keys: {list(contract_dict.keys()) if isinstance(contract_dict, dict) else 'not dict'}")
                
                # Create storage result
                storage_result = {
                    'success': True,
                    'contract': contract_dict
                }
                
                # Log clause info
                if isinstance(contract_dict, dict) and 'clauses' in contract_dict:
                    clauses = contract_dict['clauses']
                    logger.info(f"Found {len(clauses)} clauses")
                    if clauses and isinstance(clauses[0], dict):
                        logger.info(f"First clause text length: {len(clauses[0].get('text', ''))}")
                else:
                    logger.warning("No clauses found in contract dict")
                
                success = storage_manager.store_processed_contract(contract_id, storage_result)
                logger.info(f"Storage success: {success}")
            else:
                logger.error("No contract object in result")
                storage_manager.store_processed_contract(contract_id, {'success': False, 'error': 'No contract data'})
        else:
            logger.error(f"Processing failed: {result.get('error', 'Unknown error')}")
            storage_manager.store_processed_contract(contract_id, result)
        
        # Update status to completed
        storage_manager.update_contract_status(contract_id, 'completed', 100)
        
        logger.info(f"Contract {contract_id} processing completed")
        
        # Cleanup temporary file after processing
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Temporary file {file_path} cleaned up")
        
        return result
    except Exception as e:
        # Update status to failed and cleanup
        try:
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
        from pipeline.local_storage import DatabaseStorageManager
        
        storage_manager = DatabaseStorageManager()
        status = storage_manager.get_contract_status(contract_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/{contract_id}")
async def get_contract(contract_id: str):
    """Get processed contract data."""
    try:
        from pipeline.local_storage import DatabaseStorageManager
        
        storage_manager = DatabaseStorageManager()
        contract = storage_manager.get_contract(contract_id)
        
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        return contract
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/{contract_id}")
async def debug_contract(contract_id: str):
    """Debug contract data structure."""
    try:
        from config import settings
        from supabase import create_client
        
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        result = supabase.table('contracts').select('*').eq('contract_id', contract_id).execute()
        
        if not result.data:
            return {"error": "Contract not found"}
            
        contract_data = result.data[0]
        data = contract_data.get('data', {})
        
        debug_info = {
            "contract_id": contract_id,
            "status": contract_data.get('status'),
            "has_data": bool(data),
            "data_keys": list(data.keys()) if isinstance(data, dict) else "not dict",
            "success": data.get('success') if isinstance(data, dict) else None
        }
        
        if isinstance(data, dict) and data.get('contract'):
            contract_obj = data['contract']
            debug_info.update({
                "contract_keys": list(contract_obj.keys()) if isinstance(contract_obj, dict) else "not dict"
            })
            
            if isinstance(contract_obj, dict) and 'clauses' in contract_obj:
                clauses = contract_obj['clauses']
                debug_info.update({
                    "clause_count": len(clauses) if isinstance(clauses, list) else 0,
                    "first_clause_text_length": len(clauses[0].get('text', '')) if clauses and isinstance(clauses[0], dict) else 0
                })
        
        return debug_info
        
    except Exception as e:
        return {"error": str(e)}
