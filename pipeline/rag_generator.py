"""
RAG (Retrieval Augmented Generation) module for contract analysis and generation.
"""
import logging
from typing import List, Dict, Any, Optional
import os

try:
    from google import genai
except ImportError:
    # Mock class for testing when dependencies are not available
    class genai:
        class Client:
            def __init__(self):
                pass
            
            class models:
                @staticmethod
                def generate_content(model, contents):
                    class MockResponse:
                        text = f"Mock response: {contents[:100]}..."
                    return MockResponse()

from models.contract import Clause, ProcessedContract


class RAGGenerator:
    """Handles retrieval augmented generation for contract analysis."""
    
    def __init__(self):
        """Initialize RAG generator."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize Gemini client with API key
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            # Use mock client for testing
            self.client = genai.Client() if hasattr(genai, 'Client') else None
        
        # Initialize embedder
        from pipeline.embedder import ContractEmbedder
        self.embedder = ContractEmbedder(
            supabase_url=os.getenv("SUPABASE_URL"),
            supabase_key=os.getenv("SUPABASE_KEY")
        )
    
    def query_contract(self, contract_id: str, question: str) -> str:
        """Answer questions about a specific contract using RAG."""
        try:
            # Search for relevant clauses
            results = self.embedder.search_similar_clauses(
                query_text=question,
                limit=5,
                contract_id=contract_id,
                use_hybrid=True
            )
            
            if not results:
                return "No relevant information found in the contract."
            
            # Create context from relevant clauses
            context = "\n\n".join([result['text'] for result in results])
            
            # Create prompt
            prompt = f"""Based on the following contract clauses, answer the question:

Contract Clauses:
{context}

Question: {question}

Answer: Provide a clear, accurate answer based only on the contract clauses above. If the information is not available in the clauses, say so."""
            
            # Generate answer using Gemini
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt
            )
            return response.text
            
        except Exception as e:
            self.logger.error(f"Query failed: {e}")
            return "I'm sorry, I couldn't process your question."
    
    def generate_summary(self, contract: ProcessedContract) -> str:
        """Generate a summary of the contract."""
        try:
            # Extract key sections
            key_sections = []
            for section in contract.sections[:5]:  # First 5 sections
                for clause in section.clauses[:2]:  # First 2 clauses per section
                    key_sections.append(clause.text)
            
            context = "\n\n".join(key_sections)
            
            prompt = f"""Summarize the following contract in plain language:

Contract Content:
{context}

Summary: Provide a concise summary covering the main points, parties involved, key obligations, and important terms."""
            
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt
            )
            return response.text
            
        except Exception as e:
            self.logger.error(f"Summary generation failed: {e}")
            return "Unable to generate summary."
    
    def analyze_risks(self, contract: ProcessedContract) -> List[Dict[str, Any]]:
        """Analyze contract for potential risks."""
        try:
            risks = []
            
            # Analyze each section for risks
            for section in contract.sections:
                for clause in section.clauses:
                    if any(keyword in clause.text.lower() for keyword in 
                          ['liability', 'penalty', 'termination', 'breach', 'damages']):
                        
                        prompt = f"""Analyze this contract clause for potential risks:

Clause: {clause.text}

Risk Analysis: Identify any potential risks, their severity (High/Medium/Low), and brief explanation."""
                        
                        response = self.client.models.generate_content(
                            model="gemini-2.0-flash-exp",
                            contents=prompt
                        )
                        analysis = response.text
                        
                        risks.append({
                            'clause_id': clause.id,
                            'clause_text': clause.text[:200] + "...",
                            'risk_analysis': analysis,
                            'severity': 'Medium'  # Default
                        })
            
            return risks[:10]  # Return top 10 risks
            
        except Exception as e:
            self.logger.error(f"Risk analysis failed: {e}")
            return []
    
    def search_similar_contracts(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar contracts or clauses."""
        try:
            results = self.embedder.search_similar_clauses(
                query_text=query,
                limit=limit,
                use_hybrid=True
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []


class ContractRAGGenerator(RAGGenerator):
    """Legacy class name for backward compatibility."""
    pass