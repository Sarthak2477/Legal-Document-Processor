"""
Training script to store legal case embeddings in Supabase vector database using pipeline components.
"""
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pipeline.layout_parser import LayoutParser
from pipeline.preprocessor import ContractPreprocessor
from pipeline.embedder import ContractEmbedder
from models.contract import Clause
from datetime import datetime

def train_model():
    """Process legal cases as clauses using pipeline components and store in Supabase."""
    
    # Initialize pipeline components
    layout_parser = LayoutParser(use_layoutlm=False)
    preprocessor = ContractPreprocessor()
    
    # Initialize embedder without setup function
    from supabase import create_client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    embedder = ContractEmbedder()
    embedder.supabase = create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None
    
    if not embedder.supabase:
        print("Error: SUPABASE_URL and SUPABASE_KEY environment variables must be set")
        return
    
    # Test direct Supabase connection
    print("Testing Supabase connection...")
    try:
        test_result = embedder.supabase.table("clause_vectors").select("count").execute()
        print(f"✓ Supabase connection successful: {test_result}")
    except Exception as e:
        print(f"✗ Supabase connection failed: {e}")
        return
    
    # Read JSON dataset
    with open('tests/legal_dataset.json', 'r', encoding='utf-8') as f:
        qa_data = json.load(f)
    
    # Process only first 1000 items
    qa_data = qa_data[3000:4000]
    
    print(f"Processing {len(qa_data)} Q&A pairs using pipeline components...")
    
    all_clauses = []
    
    for idx, item in enumerate(qa_data):
        # Create context from Q&A pair
        combined_text = f"Case: {item.get('case_name', '')}\nDate: {item.get('judgment_date', '')}\nQuestion: {item.get('question', '')}\nAnswer: {item.get('answer', '')}"
        
        # Create clause using pipeline approach
        clause = Clause(
            id=f"qa_{idx}",
            text=combined_text,
            legal_category=layout_parser._determine_clause_type(combined_text),
            risk_level=layout_parser.risk_assessor.assess(combined_text),
            key_terms=layout_parser._extract_key_terms(combined_text),
            metadata={
                "source": "legal_qa_dataset",
                "case_name": item.get('case_name', ''),
                "judgment_date": item.get('judgment_date', ''),
                "question": item.get('question', ''),
                "answer": item.get('answer', ''),
                "processing_date": str(datetime.now())
            }
        )
        
        all_clauses.append(clause)
        print(f"✓ Created clause for: {item.get('case_name', 'Unknown')[:50]}...")
    
    # Preprocess clauses
    processed_clauses = preprocessor.preprocess_clauses(all_clauses)
    print(f"✓ Preprocessed {len(processed_clauses)} clauses")
    
    # Generate embeddings
    clauses_with_embeddings = embedder.generate_embeddings(processed_clauses)
    print(f"✓ Generated embeddings for {len(clauses_with_embeddings)} clauses")
    
    # Debug: Check embeddings before storage
    print(f"Debug: Clauses with embeddings: {len(clauses_with_embeddings)}")
    for i, clause in enumerate(clauses_with_embeddings[:3]):
        print(f"Debug: Clause {i} has embedding: {clause.embedding is not None}")
        if clause.embedding:
            print(f"Debug: Embedding length: {len(clause.embedding)}")
    
    # Test manual insertion first
    # print("Testing manual insertion...")
    # try:
    #     test_data = {
    #         "contract_id": "test_contract",
    #         "clause_id": "test_clause",
    #         "text": "This is a test clause",
    #         "embedding": [0.1] * 384,  # 384-dimension test vector
    #         "metadata": {"test": True}
    #     }
    #     manual_result = embedder.supabase.table("clause_vectors").insert(test_data).execute()
    #     print(f"✓ Manual insertion successful: {manual_result}")
    # except Exception as e:
    #     print(f"✗ Manual insertion failed: {e}")
    #     import traceback
    #     traceback.print_exc()
    #     return
    
    # Store directly in Supabase (bypass embedder)
    print("Storing clauses directly...")
    try:
        data = []
        for clause in clauses_with_embeddings:
            if clause.embedding:
                data.append({
                    "contract_id": "legal_qa_training",
                    "clause_id": clause.id,
                    "text": clause.text,
                    "embedding": clause.embedding,
                    "metadata": clause.metadata
                })
        
        if data:
            result = embedder.supabase.table("clause_vectors").insert(data).execute()
            print(f"✓ Successfully stored {len(data)} clauses directly: {result}")
        else:
            print("✗ No data to store")
            
    except Exception as e:
        print(f"✗ Direct storage failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("Training completed!")

if __name__ == "__main__":
    train_model()