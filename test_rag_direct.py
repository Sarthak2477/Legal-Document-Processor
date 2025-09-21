#!/usr/bin/env python3
"""Direct test of RAG functionality."""

from pipeline.rag_generator import ContractRAGGenerator

def test_rag_direct():
    rag = ContractRAGGenerator()
    
    question = "What are the key terms?"
    print(f"Testing question: {question}")
    
    answer = rag.query_contract(question)
    print(f"Answer: {answer}")

if __name__ == "__main__":
    test_rag_direct()