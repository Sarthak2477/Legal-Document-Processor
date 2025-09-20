"""
FastAPI main application for contract processing.
"""
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from api.routers import contracts, search, health

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
app.include_router(contracts.router, prefix="/contracts", tags=["contracts"])
app.include_router(search.router, prefix="/search", tags=["search"])

@app.get("/")
async def root():
    return {"message": "Contract Processing API", "version": "1.0.0"}


