"""
RAG (Retrieval Augmented Generation) API endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

router = APIRouter()

class QueryRequest(BaseModel):
    question: str
    contract_id: Optional[str] = None

class SummaryRequest(BaseModel):
    contract_id: str

class RiskAnalysisRequest(BaseModel):
    contract_id: str

class RedlineRequest(BaseModel):
    contract_id: str

class NegotiationRequest(BaseModel):
    contract_id: str
    negotiation_points: List[str]

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5

@router.post("/query")
async def query_contract(request: QueryRequest):
    """Answer questions using RAG across all contracts."""
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        from pipeline.rag_generator import ContractRAGGenerator
        rag_generator = ContractRAGGenerator()
        
        # Use the proper RAG generator to answer questions
        answer = rag_generator.query_contract(request.question, request.contract_id)
        
        return {"answer": answer, "question": request.question}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/summary")
async def generate_summary(request: SummaryRequest):
    """Generate contract summary."""
    try:
        from pipeline.rag_generator import ContractRAGGenerator
        from pipeline.supabase_storage import SupabaseStorageManager
        
        storage_manager = SupabaseStorageManager()
        contract = storage_manager.get_contract(request.contract_id)
        
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        rag_generator = ContractRAGGenerator()
        summary = rag_generator.generate_summary(contract)
        
        return {"summary": summary, "contract_id": request.contract_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/risks")
async def analyze_risks(request: RiskAnalysisRequest):
    """Analyze contract risks."""
    try:
        from pipeline.rag_generator import ContractRAGGenerator
        from pipeline.local_storage import DatabaseStorageManager
        from models.contract import ProcessedContract, Clause
        
        storage_manager = DatabaseStorageManager()
        contract_data = storage_manager.get_contract(request.contract_id)
        
        if not contract_data:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        processed_data = contract_data.get('processed_data', {})
        if not processed_data.get('success') or not processed_data.get('contract'):
            return {"risks": [], "contract_id": request.contract_id}
        
        contract_dict = processed_data['contract']
        
        # Convert to ProcessedContract object
        clauses = []
        for clause_data in contract_dict.get('clauses', []):
            if isinstance(clause_data, dict):
                clause = Clause(
                    id=clause_data.get('id', ''),
                    text=clause_data.get('text', ''),
                    clause_type=clause_data.get('clause_type', 'general')
                )
                clauses.append(clause)
        
        contract = ProcessedContract(
            text=contract_dict.get('text', ''),
            clauses=clauses,
            metadata=contract_dict.get('metadata', {})
        )
        
        # Use RAG generator for comprehensive risk analysis
        rag_generator = ContractRAGGenerator()
        risks = rag_generator.analyze_risks(contract)
        
        return {"risks": risks, "contract_id": request.contract_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/redlines")
async def suggest_redlines(request: RedlineRequest):
    """Suggest contract redlines."""
    try:
        from pipeline.rag_generator import ContractRAGGenerator
        from pipeline.supabase_storage import SupabaseStorageManager
        
        storage_manager = SupabaseStorageManager()
        contract = storage_manager.get_contract(request.contract_id)
        
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        rag_generator = ContractRAGGenerator()
        redlines = rag_generator.suggest_redlines(contract)
        
        return {"redlines": redlines, "contract_id": request.contract_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/negotiate")
async def negotiate_terms(request: NegotiationRequest):
    """Generate negotiation strategies."""
    try:
        from pipeline.rag_generator import ContractRAGGenerator
        from pipeline.supabase_storage import SupabaseStorageManager
        
        storage_manager = SupabaseStorageManager()
        contract = storage_manager.get_contract(request.contract_id)
        
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        rag_generator = ContractRAGGenerator()
        strategies = rag_generator.negotiate_terms(contract, request.negotiation_points)
        
        return {"strategies": strategies, "contract_id": request.contract_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search_similar(request: SearchRequest):
    """Search similar contracts."""
    try:
        from pipeline.rag_generator import ContractRAGGenerator
        
        rag_generator = ContractRAGGenerator()
        results = rag_generator.search_similar_contracts(request.query, request.limit)
        
        return {"results": results, "query": request.query}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/answer")
async def answer_questions(request: QueryRequest):
    """Answer questions about contracts (legacy endpoint)."""
    try:
        from pipeline.rag_generator import ContractRAGGenerator
        
        rag_generator = ContractRAGGenerator()
        answer = rag_generator.query_contract(request.question, request.contract_id)
        
        return {"answer": answer, "question": request.question}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))