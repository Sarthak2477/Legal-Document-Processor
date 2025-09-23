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
        from pipeline.rag_generator import ContractRAGGenerator
        
        rag_generator = ContractRAGGenerator()
        answer = rag_generator.query_contract(request.question)
        
        return {"answer": answer, "contract_id": request.contract_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/contract/{contract_id}")
async def get_contract_data(contract_id: str):
    """Get contract data directly from database."""
    try:
        from config import settings
        
        if not getattr(settings, 'SUPABASE_URL', None) or not getattr(settings, 'SUPABASE_KEY', None):
            raise HTTPException(status_code=500, detail="Database not configured")
            
        from supabase import create_client
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        
        result = supabase.table('contracts').select('*').eq('contract_id', contract_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail=f"Contract {contract_id} not found in database")
        
        contract_data = result.data[0]
        return {
            "contract_id": contract_id,
            "status": contract_data.get('status', 'unknown'),
            "created_at": contract_data.get('created_at'),
            "has_data": bool(contract_data.get('data')),
            "clause_count": len(contract_data.get('data', {}).get('contract', {}).get('clauses', []))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/generate-summary/{contract_id}")
async def generate_summary(contract_id: str):
    """Generate AI summary of a contract."""
    try:
        from pipeline.local_storage import DatabaseStorageManager
        from pipeline.rag_generator import ContractRAGGenerator
        
        # Get contract data directly from database
        from config import settings
        
        if not getattr(settings, 'SUPABASE_URL', None) or not getattr(settings, 'SUPABASE_KEY', None):
            raise HTTPException(status_code=500, detail="Database not configured")
            
        from supabase import create_client
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        
        result = supabase.table('contracts').select('*').eq('contract_id', contract_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail=f"Contract {contract_id} not found")
        
        contract_row = result.data[0]
        contract_data = contract_row.get('data', {})
        
        if not contract_data or not contract_data.get('success'):
            return {
                "summary": "Contract processing failed or incomplete.",
                "contract_id": contract_id,
                "status": contract_row.get("status", "unknown")
            }
        
        # Get contract clauses from database
        contract_dict = contract_data.get('contract')
        if not contract_dict:
            return {
                "summary": "No contract data available.",
                "contract_id": contract_id,
                "status": "no_data"
            }
        
        # Extract clauses for summary (memory optimized)
        clauses_data = contract_dict.get('clauses', [])
        clauses_text = ""
        
        for i, clause_dict in enumerate(clauses_data[:5], 1):  # Limit to 5 clauses
            clause_text = clause_dict.get('text', '')
            if len(clause_text) > 50:  # Only meaningful clauses
                clauses_text += f"Clause {i}: {clause_text[:200]}...\n\n"
        
        if not clauses_text:
            return {
                "summary": "No contract clauses found.",
                "contract_id": contract_id,
                "status": "no_clauses"
            }
        
        # Generate summary using RAG
        rag_generator = ContractRAGGenerator()
        
        prompt = f"""Summarize this contract:

{clauses_text}

Provide a brief summary covering:
- Contract type and purpose
- Key terms and obligations
- Important provisions

Keep it concise."""
        
        summary = rag_generator._generate_with_llm(prompt)
        
        return {"summary": summary, "contract_id": contract_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
