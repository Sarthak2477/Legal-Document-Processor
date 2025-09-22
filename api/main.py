"""
FastAPI main application for contract processing.
"""
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from api.routers import contracts, search, health, upload, rag

app = FastAPI(
    title="Contract Processing API",
    description="API for processing legal contracts with OCR, embeddings, and RAG",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(upload.router, prefix="/upload", tags=["upload"])
app.include_router(contracts.router, prefix="/contracts", tags=["contracts"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(rag.router, prefix="/rag", tags=["rag"])

@app.get("/")
async def root():
    return {"message": "Contract Processing API", "version": "1.0.0"}

@app.on_event("startup")
async def startup_event():
    """Cleanup old files on startup."""
    from pathlib import Path
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    
    # Cleanup old temporary files
    import time
    import os
    current_time = time.time()
    for file_path in upload_dir.glob("*"):
        if file_path.is_file():
            file_age = current_time - file_path.stat().st_mtime
            if file_age > 86400:  # 24 hours
                os.remove(file_path)


