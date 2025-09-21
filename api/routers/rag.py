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
        from pipeline.rag_generator import ContractRAGGenerator
        
        rag_generator = ContractRAGGenerator()
        answer = rag_generator.query_contract(request.question, request.contract_id)
        
        return {"answer": answer, "question": request.question}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/summary")
async def generate_summary(request: SummaryRequest):
    """Generate contract summary."""
    try:
        from pipeline.rag_generator import ContractRAGGenerator
        from pipeline.local_storage import LocalStorageManager
        
        storage_manager = LocalStorageManager()
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
        from pipeline.local_storage import LocalStorageManager
        
        storage_manager = LocalStorageManager()
        contract_data = storage_manager.get_contract(request.contract_id)
        
        if not contract_data:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        # Get processed contract data
        processed_data = contract_data.get('processed_data', {})
        if not processed_data.get('success') or not processed_data.get('contract'):
            return {"risks": [], "contract_id": request.contract_id, "message": "No processed contract data"}
        
        contract_dict = processed_data['contract']
        if not isinstance(contract_dict, dict):
            return {"risks": [], "contract_id": request.contract_id, "message": "Invalid contract format"}
        
        # Simple risk analysis based on keywords
        risks = []
        clauses_data = contract_dict.get('clauses', [])
        
        risk_keywords = {
            'liability': ['liability', 'damages', 'indemnify', 'hold harmless'],
            'payment': ['payment', 'fee', 'invoice', 'compensation'],
            'termination': ['terminate', 'termination', 'end', 'expire'],
            'confidentiality': ['confidential', 'proprietary', 'non-disclosure'],
            'intellectual_property': ['intellectual property', 'copyright', 'patent', 'license'],
            'governing_law': ['governing law', 'jurisdiction', 'court', 'legal']
        }
        
        for clause_dict in clauses_data:
            if isinstance(clause_dict, dict):
                clause_text = clause_dict.get('text', '').lower()
                
                for risk_type, keywords in risk_keywords.items():
                    for keyword in keywords:
                        if keyword in clause_text:
                            risks.append({
                                'risk_type': risk_type,
                                'severity': 'high' if risk_type == 'liability' else 'medium',
                                'description': f'Found {risk_type} risk: {keyword}',
                                'clause_id': clause_dict.get('id', ''),
                                'clause_text': clause_dict.get('text', '')[:200] + '...'
                            })
                            break
        
        return {"risks": risks, "contract_id": request.contract_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/redlines")
async def suggest_redlines(request: RedlineRequest):
    """Suggest contract redlines."""
    try:
        from pipeline.rag_generator import ContractRAGGenerator
        from pipeline.local_storage import LocalStorageManager
        
        storage_manager = LocalStorageManager()
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
        from pipeline.local_storage import LocalStorageManager
        
        storage_manager = LocalStorageManager()
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