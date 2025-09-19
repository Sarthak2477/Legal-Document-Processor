"""
Business logic services for the API.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
import uuid

from pipeline.orchestrator import ContractPipeline
from pipeline.embedder import ContractEmbedder
from api.database import DatabaseManager
from config import settings

logger = logging.getLogger(__name__)


class ContractService:
    """Service for contract processing and management."""
    
    def __init__(self):
        self.pipeline = ContractPipeline()
        self.db = DatabaseManager()
        self.embedder = ContractEmbedder(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_KEY
        )
    
    async def create_contract_record(
        self, 
        filename: str, 
        file_path: str, 
        user_id: str,
        use_layoutlm: bool = False
    ) -> str:
        """Create a new contract record in the database."""
        contract_id = str(uuid.uuid4())
        
        contract_data = {
            "contract_id": contract_id,
            "filename": filename,
            "file_path": file_path,
            "user_id": user_id,
            "status": "uploaded",
            "upload_date": datetime.now(),
            "use_layoutlm": use_layoutlm,
            "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else 0
        }
        
        await self.db.create_contract(contract_data)
        return contract_id
    
    async def get_contract(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """Get contract by ID."""
        return await self.db.get_contract(contract_id)
    
    async def update_contract_status(
        self, 
        contract_id: str, 
        status: str, 
        result: Optional[Dict[str, Any]] = None
    ):
        """Update contract processing status."""
        update_data = {
            "status": status,
            "updated_at": datetime.now()
        }
        
        if status == "processing":
            update_data["processing_started"] = datetime.now()
        elif status in ["completed", "failed"]:
            update_data["processing_completed"] = datetime.now()
            
        if result:
            update_data["processing_result"] = result
            
        await self.db.update_contract(contract_id, update_data)
    
    def process_contract_sync(
        self, 
        contract_id: str, 
        file_path: str, 
        use_layoutlm: bool
    ) -> Dict[str, Any]:
        """Synchronous contract processing for background tasks."""
        try:
            logger.info(f"Processing contract {contract_id} with file {file_path}")
            
            # Configure pipeline
            config = {"use_layoutlm": use_layoutlm}
            self.pipeline.config = config
            
            # Process contract
            result = self.pipeline.process_contract(file_path)
            
            if result["success"]:
                # Store additional analysis data
                self._store_analysis_data(contract_id, result)
                
            return result
            
        except Exception as e:
            logger.error(f"Contract processing error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _store_analysis_data(self, contract_id: str, result: Dict[str, Any]):
        """Store detailed analysis data."""
        try:
            contract = result.get("contract")
            analysis = result.get("analysis", {})
            
            if contract:
                # Store sections and clauses
                asyncio.create_task(self.db.store_contract_sections(
                    contract_id, 
                    contract.sections
                ))
                
                asyncio.create_task(self.db.store_contract_clauses(
                    contract_id, 
                    contract.clauses
                ))
                
                # Store analysis results
                asyncio.create_task(self.db.store_contract_analysis(
                    contract_id,
                    analysis
                ))
                
        except Exception as e:
            logger.error(f"Error storing analysis data: {str(e)}")
    
    async def get_processing_status(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """Get contract processing status."""
        contract = await self.db.get_contract(contract_id)
        if not contract:
            return None
            
        # Calculate progress based on status
        progress_map = {
            "uploaded": 0,
            "processing": 50,
            "completed": 100,
            "failed": 0
        }
        
        return {
            "contract_id": contract_id,
            "status": contract["status"],
            "progress": progress_map.get(contract["status"], 0),
            "message": contract.get("message"),
            "started_at": contract.get("processing_started"),
            "completed_at": contract.get("processing_completed"),
            "error": contract.get("processing_result", {}).get("error"),
            "processing_stats": contract.get("processing_result", {}).get("processing_stats"),
            "user_id": contract["user_id"]
        }
    
    async def get_contract_analysis(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive contract analysis."""
        contract = await self.db.get_contract(contract_id)
        if not contract or contract["status"] != "completed":
            return None
        
        # Get analysis data
        analysis = await self.db.get_contract_analysis(contract_id)
        sections = await self.db.get_contract_sections(contract_id)
        clauses = await self.db.get_contract_clauses(contract_id)
        
        # Build response
        return {
            "contract_id": contract_id,
            "filename": contract["filename"],
            "processing_date": contract["processing_completed"],
            "sections": sections,
            "total_clauses": len(clauses),
            "summary": analysis.get("summary", ""),
            "key_terms": analysis.get("key_terms", {}),
            "risk_assessment": self._build_risk_assessment(clauses),
            "contract_type": analysis.get("contract_type"),
            "jurisdiction": analysis.get("jurisdiction"),
            "compliance_flags": analysis.get("compliance_flags", []),
            "missing_clauses": analysis.get("missing_clauses", []),
            "unusual_terms": analysis.get("unusual_terms", []),
            "ocr_method": contract.get("processing_result", {}).get("contract", {}).get("metadata", {}).get("ocr_method", "unknown"),
            "confidence_score": contract.get("processing_result", {}).get("contract", {}).get("metadata", {}).get("confidence_score", 0.0),
            "processing_time": contract.get("processing_result", {}).get("processing_time"),
            "user_id": contract["user_id"]
        }
    
    def _build_risk_assessment(self, clauses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build risk assessment from clauses."""
        risk_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        high_risk_clauses = []
        risk_factors = []
        
        for clause in clauses:
            risk_level = clause.get("risk_level", "low")
            risk_counts[risk_level] += 1
            
            if risk_level in ["high", "critical"]:
                high_risk_clauses.append(clause["id"])
                
                # Add risk factors based on clause content
                if "unlimited liability" in clause["text"].lower():
                    risk_factors.append("Unlimited liability exposure")
                if "personal guarantee" in clause["text"].lower():
                    risk_factors.append("Personal guarantee required")
                if "penalty" in clause["text"].lower():
                    risk_factors.append("Penalty clauses present")
        
        # Calculate overall risk
        total_clauses = sum(risk_counts.values())
        if total_clauses == 0:
            overall_risk = "low"
            risk_score = 0.0
        else:
            risk_score = (
                risk_counts["medium"] * 0.3 + 
                risk_counts["high"] * 0.7 + 
                risk_counts["critical"] * 1.0
            ) / total_clauses
            
            if risk_score >= 0.7:
                overall_risk = "critical"
            elif risk_score >= 0.5:
                overall_risk = "high"
            elif risk_score >= 0.3:
                overall_risk = "medium"
            else:
                overall_risk = "low"
        
        return {
            "overall_risk": overall_risk,
            "risk_factors": list(set(risk_factors)),
            "high_risk_clauses": high_risk_clauses,
            "recommendations": self._generate_risk_recommendations(risk_factors),
            "risk_score": risk_score
        }
    
    def _generate_risk_recommendations(self, risk_factors: List[str]) -> List[str]:
        """Generate risk mitigation recommendations."""
        recommendations = []
        
        if "Unlimited liability exposure" in risk_factors:
            recommendations.append("Consider negotiating liability caps or limitations")
        if "Personal guarantee required" in risk_factors:
            recommendations.append("Review personal guarantee terms and consider alternatives")
        if "Penalty clauses present" in risk_factors:
            recommendations.append("Ensure penalty amounts are reasonable and enforceable")
            
        if not recommendations:
            recommendations.append("Review contract terms with legal counsel")
            
        return recommendations
    
    async def answer_question(self, contract_id: str, question: str) -> Dict[str, Any]:
        """Answer question about contract using RAG."""
        try:
            # Use RAG generator to answer question
            answer = self.pipeline.rag_generator.answer_questions(
                question=question,
                contract_id=contract_id
            )
            
            return {
                "answer": answer,
                "confidence": 0.8,  # TODO: Implement confidence scoring
                "sources": []  # TODO: Return source clause IDs
            }
            
        except Exception as e:
            logger.error(f"Question answering error: {str(e)}")
            return {
                "answer": "I'm sorry, I couldn't process your question at this time.",
                "confidence": 0.0,
                "sources": []
            }
    
    async def list_user_contracts(
        self, 
        user_id: str, 
        page: int = 1, 
        limit: int = 20,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """List user's contracts with pagination."""
        offset = (page - 1) * limit
        
        contracts, total = await self.db.list_user_contracts(
            user_id, 
            limit, 
            offset, 
            status
        )
        
        return {
            "contracts": contracts,
            "total": total,
            "page": page,
            "limit": limit,
            "has_next": offset + limit < total,
            "has_previous": page > 1
        }
    
    async def get_contract_details(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed contract information."""
        contract = await self.db.get_contract(contract_id)
        if not contract:
            return None
        
        # Add additional details
        if contract["status"] == "completed":
            sections = await self.db.get_contract_sections(contract_id)
            clauses = await self.db.get_contract_clauses(contract_id)
            contract["sections_count"] = len(sections)
            contract["clauses_count"] = len(clauses)
        
        return contract
    
    async def delete_contract(self, contract_id: str, user_id: str) -> bool:
        """Delete contract and associated data."""
        contract = await self.db.get_contract(contract_id)
        if not contract or contract["user_id"] != user_id:
            return False
        
        # Delete file
        file_path = contract.get("file_path")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Could not delete file {file_path}: {str(e)}")
        
        # Delete from database
        await self.db.delete_contract(contract_id)
        
        # Delete vectors from Supabase
        if self.embedder.supabase:
            try:
                self.embedder.supabase.table("clause_vectors").delete().eq("contract_id", contract_id).execute()
            except Exception as e:
                logger.warning(f"Could not delete vectors for {contract_id}: {str(e)}")
        
        return True
    
    async def search_contracts(
        self, 
        query: str, 
        user_id: str, 
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search contracts using semantic similarity."""
        try:
            start_time = datetime.now()
            
            # Use embedder for semantic search
            search_results = self.embedder.search_similar_clauses(
                query_text=query,
                limit=limit * 3,  # Get more results to filter by user
                use_hybrid=True
            )
            
            # Filter by user and build response
            user_results = []
            for result in search_results:
                # Get contract info
                contract = await self.db.get_contract_by_clause(result["clause_id"])
                if contract and contract["user_id"] == user_id:
                    user_results.append({
                        "contract_id": contract["contract_id"],
                        "filename": contract["filename"],
                        "relevance_score": result.get("similarity", 0.0),
                        "matching_clauses": [result],
                        "snippet": result["text"][:200] + "..."
                    })
                    
                if len(user_results) >= limit:
                    break
            
            search_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "query": query,
                "results": user_results,
                "total_results": len(user_results),
                "search_time": search_time
            }
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return {
                "query": query,
                "results": [],
                "total_results": 0,
                "search_time": 0.0
            }
    
    async def find_similar_contracts(
        self, 
        contract_id: str, 
        user_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find contracts similar to the given contract."""
        try:
            # Get contract clauses
            clauses = await self.db.get_contract_clauses(contract_id)
            if not clauses:
                return []
            
            # Use first few clauses as query
            query_text = " ".join([clause["text"] for clause in clauses[:3]])
            
            # Search for similar clauses
            search_results = self.embedder.search_similar_clauses(
                query_text=query_text,
                limit=limit * 2,
                use_hybrid=True
            )
            
            # Group by contract and filter by user
            contract_scores = {}
            for result in search_results:
                contract = await self.db.get_contract_by_clause(result["clause_id"])
                if (contract and 
                    contract["user_id"] == user_id and 
                    contract["contract_id"] != contract_id):
                    
                    if contract["contract_id"] not in contract_scores:
                        contract_scores[contract["contract_id"]] = {
                            "contract_id": contract["contract_id"],
                            "filename": contract["filename"],
                            "similarity_score": 0.0,
                            "matching_clauses": 0
                        }
                    
                    contract_scores[contract["contract_id"]]["similarity_score"] += result.get("similarity", 0.0)
                    contract_scores[contract["contract_id"]]["matching_clauses"] += 1
            
            # Calculate average similarity and sort
            similar_contracts = []
            for contract_data in contract_scores.values():
                contract_data["similarity_score"] /= contract_data["matching_clauses"]
                similar_contracts.append(contract_data)
            
            similar_contracts.sort(key=lambda x: x["similarity_score"], reverse=True)
            return similar_contracts[:limit]
            
        except Exception as e:
            logger.error(f"Similar contracts error: {str(e)}")
            return []
    
    async def create_batch_job(
        self, 
        contract_ids: List[str], 
        user_id: str,
        options: Dict[str, Any]
    ) -> str:
        """Create a batch processing job."""
        batch_id = str(uuid.uuid4())
        
        batch_data = {
            "batch_id": batch_id,
            "user_id": user_id,
            "contract_ids": contract_ids,
            "total_contracts": len(contract_ids),
            "completed_contracts": 0,
            "failed_contracts": 0,
            "status": "started",
            "options": options,
            "created_at": datetime.now()
        }
        
        await self.db.create_batch_job(batch_data)
        return batch_id
    
    def process_batch_sync(
        self, 
        batch_id: str, 
        contract_ids: List[str], 
        options: Dict[str, Any]
    ):
        """Synchronous batch processing."""
        try:
            completed = 0
            failed = 0
            results = []
            
            for contract_id in contract_ids:
                try:
                    # Get contract info
                    contract = asyncio.run(self.db.get_contract(contract_id))
                    if not contract:
                        failed += 1
                        continue
                    
                    # Process contract
                    result = self.process_contract_sync(
                        contract_id,
                        contract["file_path"],
                        options.get("use_layoutlm", False)
                    )
                    
                    if result["success"]:
                        completed += 1
                        asyncio.run(self.update_contract_status(contract_id, "completed", result))
                    else:
                        failed += 1
                        asyncio.run(self.update_contract_status(contract_id, "failed", result))
                    
                    results.append({
                        "contract_id": contract_id,
                        "success": result["success"],
                        "error": result.get("error")
                    })
                    
                    # Update batch progress
                    progress = int((completed + failed) / len(contract_ids) * 100)
                    asyncio.run(self.db.update_batch_job(batch_id, {
                        "completed_contracts": completed,
                        "failed_contracts": failed,
                        "progress": progress
                    }))
                    
                except Exception as e:
                    logger.error(f"Batch processing error for {contract_id}: {str(e)}")
                    failed += 1
            
            # Mark batch as completed
            asyncio.run(self.db.update_batch_job(batch_id, {
                "status": "completed",
                "completed_at": datetime.now(),
                "results": results
            }))
            
        except Exception as e:
            logger.error(f"Batch processing error: {str(e)}")
            asyncio.run(self.db.update_batch_job(batch_id, {
                "status": "failed",
                "error": str(e)
            }))
    
    async def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get batch processing status."""
        return await self.db.get_batch_job(batch_id)
    
    async def update_batch_status(
        self, 
        batch_id: str, 
        status: str, 
        data: Optional[Dict[str, Any]] = None
    ):
        """Update batch processing status."""
        update_data = {"status": status}
        if data:
            update_data.update(data)
        await self.db.update_batch_job(batch_id, update_data)
    
    async def get_contract_file_path(self, contract_id: str, user_id: str) -> Optional[str]:
        """Get contract file path for download."""
        contract = await self.db.get_contract(contract_id)
        if contract and contract["user_id"] == user_id:
            return contract.get("file_path")
        return None
    
    async def export_analysis(
        self, 
        contract_id: str, 
        user_id: str, 
        format: str
    ) -> Optional[str]:
        """Export contract analysis in specified format."""
        try:
            analysis = await self.get_contract_analysis(contract_id)
            if not analysis or analysis["user_id"] != user_id:
                return None
            
            export_dir = Path("exports")
            export_dir.mkdir(exist_ok=True)
            
            if format == "json":
                file_path = export_dir / f"analysis_{contract_id}.json"
                with open(file_path, "w") as f:
                    json.dump(analysis, f, indent=2, default=str)
                return str(file_path)
            
            # TODO: Implement PDF and DOCX export
            elif format in ["pdf", "docx"]:
                # Placeholder for PDF/DOCX generation
                return None
            
            return None
            
        except Exception as e:
            logger.error(f"Export error: {str(e)}")
            return None


class AuthService:
    """Service for authentication and authorization."""
    
    def __init__(self):
        self.secret_key = settings.FIREBASE_PROJECT_ID or "dev-secret-key"
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token and return user info."""
        # TODO: Implement proper JWT validation with Firebase Auth
        # For now, return mock user for development
        if token == "dev-token":
            return {
                "user_id": "dev-user-123",
                "email": "dev@example.com",
                "name": "Development User"
            }
        
        raise Exception("Invalid token")
    
    def generate_token(self, user_id: str) -> str:
        """Generate JWT token for user."""
        # TODO: Implement proper JWT generation
        return "dev-token"