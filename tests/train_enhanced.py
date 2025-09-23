"""
Enhanced training script using both CSV legal cases and JSON contract data.
"""
import json
import pandas as pd
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

def train_enhanced_model():
    """Train using both legal cases and contract documents."""
    
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
    
    all_clauses = []
    
    # 1. Process JSON contract documents
    print("Processing contract documents from train.json...")
    try:
        with open('tests/train.json', 'r', encoding='utf-8') as f:
            contract_data = json.load(f)
        
        for doc in contract_data['documents'][:10]:  # Process first 10 contracts
            # Split contract into sections
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
                            "source": "contract_documents",
                            "document_id": doc['id'],
                            "file_name": doc['file_name'],
                            "section_number": i,
                            "processing_date": str(datetime.now())
                        }
                    )
                    all_clauses.append(clause)
        
        print(f"✓ Processed {len([c for c in all_clauses if c.metadata['source'] == 'contract_documents'])} contract sections")
    
    except FileNotFoundError:
        print("⚠️ train.json not found, skipping contract documents")
    
    # 2. Process CSV legal cases
    print("Processing legal cases from dataset.csv...")
    try:
        column_names = ['case_id', 'type', 'case_number', 'petitioner', 'respondent', 
                       'petitioner_advocate', 'respondent_advocate', 'judges', 'additional_info', 'date', 'file_path']
        
        df = pd.read_csv('tests/dataset.csv', names=column_names, skiprows=1)
        df = df.head(500)  # Process 500 legal cases
        
        for idx, row in df.iterrows():
            combined_text = f"Case: {row['case_number']}\nPetitioner: {row['petitioner']}\nRespondent: {row['respondent']}\nJudges: {row['judges']}\nDate: {row['date']}"
            
            clause = Clause(
                id=f"legal_case_{idx}",
                text=combined_text,
                legal_category=layout_parser._determine_clause_type(combined_text),
                risk_level=layout_parser.risk_assessor.assess(combined_text),
                key_terms=layout_parser._extract_key_terms(combined_text),
                metadata={
                    "source": "legal_cases",
                    "case_id": str(row['case_id']),
                    "case_number": str(row['case_number']),
                    "petitioner": str(row['petitioner']),
                    "respondent": str(row['respondent']),
                    "processing_date": str(datetime.now())
                }
            )
            all_clauses.append(clause)
        
        print(f"✓ Processed {len([c for c in all_clauses if c.metadata['source'] == 'legal_cases'])} legal cases")
    
    except FileNotFoundError:
        print("⚠️ dataset.csv not found, skipping legal cases")
    
    if not all_clauses:
        print("❌ No data to process")
        return
    
    # 3. Process and store
    print(f"Total clauses to process: {len(all_clauses)}")
    
    processed_clauses = preprocessor.preprocess_clauses(all_clauses)
    print(f"✓ Preprocessed {len(processed_clauses)} clauses")
    
    clauses_with_embeddings = embedder.generate_embeddings(processed_clauses)
    print(f"✓ Generated embeddings for {len(clauses_with_embeddings)} clauses")
    
    # Store in Supabase
    print("Storing in vector database...")
    try:
        data = []
        for clause in clauses_with_embeddings:
            if clause.embedding:
                data.append({
                    "contract_id": f"training_{clause.metadata['source']}",
                    "clause_id": clause.id,
                    "text": clause.text,
                    "embedding": clause.embedding,
                    "metadata": clause.metadata
                })
        
        if data:
            # Store in batches of 100
            batch_size = 100
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                result = embedder.supabase.table("clause_vectors").insert(batch).execute()
                print(f"✓ Stored batch {i//batch_size + 1}: {len(batch)} items")
            
            print(f"✅ Successfully stored {len(data)} total items")
        else:
            print("❌ No data to store")
            
    except Exception as e:
        print(f"❌ Storage failed: {e}")
    
    print("Enhanced training completed!")

if __name__ == "__main__":
    train_enhanced_model()
