"""
Search and RAG endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10
    similarity_threshold: Optional[float] = 0.7
    contract_id: Optional[str] = None
    legal_category: Optional[str] = None

class RAGRequest(BaseModel):
    contract_id: str
    question: str

@router.post("/similar-clauses")
async def search_similar_clauses(request: SearchRequest):
    """Search for similar clauses using vector similarity."""
    try:
        from pipeline.embedder import ContractEmbedder
        import os
        
        embedder = ContractEmbedder(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_KEY")
        )
        
        results = embedder.search_similar_clauses(
            query_text=request.query,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold,
            contract_id=request.contract_id,
            legal_category=request.legal_category
        )
        
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rag-query")
async def rag_query(request: RAGRequest):
    """Query contract using RAG (Retrieval Augmented Generation)."""
    try:
        from pipeline.rag_generator import RAGGenerator
        
        rag_generator = RAGGenerator()
        answer = rag_generator.query_contract(request.contract_id, request.question)
        
        return {"answer": answer, "contract_id": request.contract_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-summary/{contract_id}")
async def generate_summary(contract_id: str):
    """Generate AI summary of a contract."""
    try:
        from pipeline.rag_generator import RAGGenerator
        from pipeline.firestore_manager import FirestoreManager
        
        firestore_manager = FirestoreManager()
        contract = firestore_manager.get_contract(contract_id)
        
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        rag_generator = RAGGenerator()
        summary = rag_generator.generate_summary(contract)
        
        return {"summary": summary, "contract_id": contract_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))