"""
FastAPI backend for contract processing pipeline.
Provides REST API endpoints for frontend integration.
"""
import os
import logging
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
from pathlib import Path
import tempfile
import shutil
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

from api.models import (
    ContractUploadResponse, 
    ContractProcessingStatus, 
    ContractAnalysisResponse,
    ContractListResponse,
    ContractSearchRequest,
    ContractSearchResponse,
    QuestionAnswerRequest,
    QuestionAnswerResponse,
    BatchProcessingRequest,
    BatchProcessingResponse,
    ErrorResponse
)
from api.services import ContractService, AuthService
from api.database import DatabaseManager
from api.middleware import ProcessingTimeMiddleware, RequestLoggingMiddleware, SecurityHeadersMiddleware
from api.routes.websocket_routes import router as websocket_router
from api.routes.analytics_routes import router as analytics_router
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thread pool for CPU-intensive tasks
executor = ThreadPoolExecutor(max_workers=4)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Contract Processing API...")
    
    # Initialize services
    app.state.contract_service = ContractService()
    app.state.auth_service = AuthService()
    app.state.db_manager = DatabaseManager()
    
    # Create upload directories
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    logger.info("Contract Processing API started successfully")
    yield
    
    logger.info("Shutting down Contract Processing API...")
    executor.shutdown(wait=True)

# Initialize FastAPI app
app = FastAPI(
    title="Contract Processing API",
    description="Backend API for legal contract processing and analysis",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(ProcessingTimeMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(websocket_router)
app.include_router(analytics_router)

# Security
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate JWT token and get current user."""
    try:
        user = app.state.auth_service.validate_token(credentials.credentials)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Contract Processing API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "services": {
            "database": app.state.db_manager.check_connection(),
            "contract_processor": True,
            "file_storage": True
        },
        "timestamp": datetime.now().isoformat()
    }

# Contract Upload and Processing Endpoints

@app.post("/api/contracts/upload", response_model=ContractUploadResponse, tags=["Contracts"])
async def upload_contract(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    process_immediately: bool = True,
    use_layoutlm: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """
    Upload a contract file for processing.
    
    - **file**: PDF contract file
    - **process_immediately**: Start processing immediately (default: True)
    - **use_layoutlm**: Use LayoutLMv3 for advanced parsing (default: False)
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )
        
        # Save uploaded file
        upload_dir = Path("uploads")
        file_path = upload_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create contract record
        contract_id = await app.state.contract_service.create_contract_record(
            filename=file.filename,
            file_path=str(file_path),
            user_id=current_user["user_id"],
            use_layoutlm=use_layoutlm
        )
        
        # Start processing if requested
        if process_immediately:
            background_tasks.add_task(
                process_contract_background,
                contract_id,
                str(file_path),
                use_layoutlm
            )
            status = "processing"
        else:
            status = "uploaded"
        
        return ContractUploadResponse(
            contract_id=contract_id,
            filename=file.filename,
            status=status,
            message="Contract uploaded successfully"
        )
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/contracts/{contract_id}/process", tags=["Contracts"])
async def process_contract(
    contract_id: str,
    background_tasks: BackgroundTasks,
    use_layoutlm: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Start processing an uploaded contract."""
    try:
        contract = await app.state.contract_service.get_contract(contract_id)
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        if contract["user_id"] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Start background processing
        background_tasks.add_task(
            process_contract_background,
            contract_id,
            contract["file_path"],
            use_layoutlm
        )
        
        await app.state.contract_service.update_contract_status(contract_id, "processing")
        
        return {"message": "Processing started", "contract_id": contract_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Process error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/contracts/{contract_id}/status", response_model=ContractProcessingStatus, tags=["Contracts"])
async def get_processing_status(
    contract_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get contract processing status."""
    try:
        status = await app.state.contract_service.get_processing_status(contract_id)
        if not status:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        if status["user_id"] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return ContractProcessingStatus(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Contract Analysis Endpoints

@app.get("/api/contracts/{contract_id}/analysis", response_model=ContractAnalysisResponse, tags=["Analysis"])
async def get_contract_analysis(
    contract_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive contract analysis."""
    try:
        analysis = await app.state.contract_service.get_contract_analysis(contract_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Contract analysis not found")
        
        if analysis["user_id"] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return ContractAnalysisResponse(**analysis)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/contracts/{contract_id}/question", response_model=QuestionAnswerResponse, tags=["Analysis"])
async def ask_question(
    contract_id: str,
    request: QuestionAnswerRequest,
    current_user: dict = Depends(get_current_user)
):
    """Ask a question about a specific contract using RAG."""
    try:
        # Verify contract access
        contract = await app.state.contract_service.get_contract(contract_id)
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        if contract["user_id"] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get answer using RAG
        answer = await app.state.contract_service.answer_question(
            contract_id, 
            request.question
        )
        
        return QuestionAnswerResponse(
            question=request.question,
            answer=answer["answer"],
            confidence=answer.get("confidence", 0.0),
            sources=answer.get("sources", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Question answering error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Contract Management Endpoints

@app.get("/api/contracts", response_model=ContractListResponse, tags=["Contracts"])
async def list_contracts(
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List user's contracts with pagination."""
    try:
        contracts = await app.state.contract_service.list_user_contracts(
            user_id=current_user["user_id"],
            page=page,
            limit=limit,
            status=status
        )
        
        return ContractListResponse(**contracts)
        
    except Exception as e:
        logger.error(f"List contracts error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/contracts/{contract_id}", tags=["Contracts"])
async def get_contract_details(
    contract_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed contract information."""
    try:
        contract = await app.state.contract_service.get_contract_details(contract_id)
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        if contract["user_id"] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return contract
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get contract error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/contracts/{contract_id}", tags=["Contracts"])
async def delete_contract(
    contract_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a contract and its associated data."""
    try:
        success = await app.state.contract_service.delete_contract(
            contract_id, 
            current_user["user_id"]
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        return {"message": "Contract deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete contract error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Search and Discovery Endpoints

@app.post("/api/contracts/search", response_model=ContractSearchResponse, tags=["Search"])
async def search_contracts(
    request: ContractSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """Search contracts using semantic similarity."""
    try:
        results = await app.state.contract_service.search_contracts(
            query=request.query,
            user_id=current_user["user_id"],
            limit=request.limit,
            filters=request.filters
        )
        
        return ContractSearchResponse(**results)
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/contracts/{contract_id}/similar", tags=["Search"])
async def find_similar_contracts(
    contract_id: str,
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """Find contracts similar to the given contract."""
    try:
        similar = await app.state.contract_service.find_similar_contracts(
            contract_id,
            current_user["user_id"],
            limit
        )
        
        return {"similar_contracts": similar}
        
    except Exception as e:
        logger.error(f"Similar contracts error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Batch Processing Endpoints

@app.post("/api/contracts/batch", response_model=BatchProcessingResponse, tags=["Batch"])
async def batch_process_contracts(
    request: BatchProcessingRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Start batch processing of multiple contracts."""
    try:
        batch_id = await app.state.contract_service.create_batch_job(
            contract_ids=request.contract_ids,
            user_id=current_user["user_id"],
            options=request.options
        )
        
        # Start background batch processing
        background_tasks.add_task(
            process_batch_background,
            batch_id,
            request.contract_ids,
            request.options
        )
        
        return BatchProcessingResponse(
            batch_id=batch_id,
            status="started",
            total_contracts=len(request.contract_ids)
        )
        
    except Exception as e:
        logger.error(f"Batch processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/batch/{batch_id}/status", tags=["Batch"])
async def get_batch_status(
    batch_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get batch processing status."""
    try:
        status = await app.state.contract_service.get_batch_status(batch_id)
        if not status:
            raise HTTPException(status_code=404, detail="Batch job not found")
        
        if status["user_id"] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch status error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# File Download Endpoints

@app.get("/api/contracts/{contract_id}/download", tags=["Files"])
async def download_contract(
    contract_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Download original contract file."""
    try:
        file_path = await app.state.contract_service.get_contract_file_path(
            contract_id, 
            current_user["user_id"]
        )
        
        if not file_path or not Path(file_path).exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=file_path,
            filename=Path(file_path).name,
            media_type='application/pdf'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/contracts/{contract_id}/export", tags=["Files"])
async def export_contract_analysis(
    contract_id: str,
    format: str = "json",
    current_user: dict = Depends(get_current_user)
):
    """Export contract analysis in various formats."""
    try:
        if format not in ["json", "pdf", "docx"]:
            raise HTTPException(status_code=400, detail="Unsupported format")
        
        file_path = await app.state.contract_service.export_analysis(
            contract_id,
            current_user["user_id"],
            format
        )
        
        if not file_path:
            raise HTTPException(status_code=404, detail="Export failed")
        
        media_types = {
            "json": "application/json",
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        }
        
        return FileResponse(
            path=file_path,
            filename=f"contract_analysis_{contract_id}.{format}",
            media_type=media_types[format]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Background Tasks

async def process_contract_background(contract_id: str, file_path: str, use_layoutlm: bool):
    """Background task for contract processing."""
    try:
        logger.info(f"Starting background processing for contract {contract_id}")
        
        # Run processing in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            executor,
            app.state.contract_service.process_contract_sync,
            contract_id,
            file_path,
            use_layoutlm
        )
        
        if result["success"]:
            await app.state.contract_service.update_contract_status(
                contract_id, 
                "completed",
                result
            )
            logger.info(f"Contract {contract_id} processed successfully")
        else:
            await app.state.contract_service.update_contract_status(
                contract_id, 
                "failed",
                {"error": result.get("error")}
            )
            logger.error(f"Contract {contract_id} processing failed: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Background processing error for {contract_id}: {str(e)}")
        await app.state.contract_service.update_contract_status(
            contract_id, 
            "failed",
            {"error": str(e)}
        )

async def process_batch_background(batch_id: str, contract_ids: List[str], options: Dict[str, Any]):
    """Background task for batch processing."""
    try:
        logger.info(f"Starting batch processing {batch_id} for {len(contract_ids)} contracts")
        
        # Run batch processing in thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            executor,
            app.state.contract_service.process_batch_sync,
            batch_id,
            contract_ids,
            options
        )
        
        logger.info(f"Batch processing {batch_id} completed")
        
    except Exception as e:
        logger.error(f"Batch processing error for {batch_id}: {str(e)}")
        await app.state.contract_service.update_batch_status(
            batch_id,
            "failed",
            {"error": str(e)}
        )

# Error Handlers

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            status_code=exc.status_code
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            status_code=500
        ).dict()
    )

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )