"""
Training script using train.json contract documents.
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
    """Process contract documents from train.json and store in Supabase."""
    
    # Initialize components
    layout_parser = LayoutParser(use_layoutlm=False)
    preprocessor = ContractPreprocessor()
    
    from supabase import create_client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    embedder = ContractEmbedder()
    embedder.supabase = create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None
    
    if not embedder.supabase:
        print("Error: SUPABASE_URL and SUPABASE_KEY environment variables must be set")
        return
    
    print("✓ Supabase connection established")
    
    # Load contract documents
    with open('tests/train.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Process first 100 documents
    documents = data['documents']
    print(f"Processing {len(documents)} contract documents...")
    
    all_clauses = []
    
    for doc in documents:
        # Split contract text into sections
        sections = doc['text'].split('\n\n')
        
        for i, section in enumerate(sections):
            if len(section.strip()) > 100:  # Only meaningful sections
                clause = Clause(
                    id=f"contract_{doc['id']}_section_{i}",
                    text=section.strip(),
                    legal_category=layout_parser._determine_clause_type(section),
                    risk_level=layout_parser.risk_assessor.assess(section),
                    key_terms=layout_parser._extract_key_terms(section),
                    metadata={
                        "source": "contract_training",
                        "document_id": doc['id'],
                        "file_name": doc['file_name'],
                        "section_number": i,
                        "processing_date": str(datetime.now())
                    }
                )
                all_clauses.append(clause)
        
        print(f"✓ Processed contract {doc['id']}: {doc['file_name']}")
    
    print(f"Total clauses extracted: {len(all_clauses)}")
    
    # Preprocess clauses
    processed_clauses = preprocessor.preprocess_clauses(all_clauses)
    print(f"✓ Preprocessed {len(processed_clauses)} clauses")
    
    # Generate embeddings
    clauses_with_embeddings = embedder.generate_embeddings(processed_clauses)
    print(f"✓ Generated embeddings for {len(clauses_with_embeddings)} clauses")
    
    # Store in Supabase
    print("Storing in vector database...")
    try:
        data = []
        for clause in clauses_with_embeddings:
            if clause.embedding:
                data.append({
                    "contract_id": "contract_training",
                    "clause_id": clause.id,
                    "text": clause.text,
                    "embedding": clause.embedding,
                    "metadata": clause.metadata
                })
        
        if data:
            result = embedder.supabase.table("clause_vectors").insert(data).execute()
            print(f"✅ Successfully stored {len(data)} contract clauses")
        else:
            print("❌ No data to store")
            
    except Exception as e:
        print(f"❌ Storage failed: {e}")
    
    print("Training completed!")

if __name__ == "__main__":
    train_model()
