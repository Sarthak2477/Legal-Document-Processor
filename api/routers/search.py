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

@router.post("/generate-summary/{contract_id}")
async def generate_summary(contract_id: str):
    """Generate AI summary of a contract."""
    from pipeline.local_storage import LocalStorageManager
    from pipeline.rag_generator import ContractRAGGenerator
    
    storage_manager = LocalStorageManager()
    contract_data = storage_manager.get_contract(contract_id)
    
    if not contract_data:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    # Check if processed data exists
    processed_data = contract_data.get('processed_data')
    if not processed_data or not processed_data.get('success'):
        return {
            "summary": "Contract processing failed or incomplete. Please reprocess the contract.",
            "contract_id": contract_id,
            "status": contract_data.get("status", "unknown")
        }
    
    # Get the processed contract
    contract_dict = processed_data.get('contract')
    if not contract_dict:
        return {
            "summary": "No contract data available for summary generation.",
            "contract_id": contract_id,
            "status": contract_data.get("status", "unknown")
        }
    
    # Simple text-based summary from clauses
    clauses_text = ""
    clauses_data = contract_dict.get('clauses', [])
    
    for i, clause_dict in enumerate(clauses_data[:10], 1):
        clause_text = clause_dict.get('text', 'No text available')
        clauses_text += f"Clause {i}: {clause_text[:300]}...\n\n"
    
    if not clauses_text:
        return {
            "summary": "No contract clauses found for summary generation.",
            "contract_id": contract_id,
            "status": "no_clauses"
        }
    
    # Generate summary using RAG with simple prompt
    rag_generator = ContractRAGGenerator()
    
    prompt = f"""Summarize this contract based on the following clauses:

{clauses_text}

Provide a brief summary covering:
- Contract type and purpose
- Key terms and obligations
- Important provisions

Keep it concise and clear."""
    
    summary = rag_generator._generate_with_llm(prompt)
    
    return {"summary": summary, "contract_id": contract_id}