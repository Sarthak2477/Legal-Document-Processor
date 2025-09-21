#!/usr/bin/env python3
"""Test what clauses are actually being extracted."""

from pipeline.local_storage import LocalStorageManager

def test_clause_extraction():
    storage = LocalStorageManager()
    all_data = storage._load_data()
    
    print("=== CLAUSE EXTRACTION TEST ===")
    
    for contract_id, contract_info in all_data.items():
        print(f"\nContract: {contract_id}")
        processed_data = contract_info.get('processed_data', {})
        
        if processed_data.get('success') and processed_data.get('contract'):
            contract_data = processed_data['contract']
            print(f"Contract data type: {type(contract_data)}")
            
            if isinstance(contract_data, str):
                print(f"Contract stored as string: {contract_data[:300]}...")
                continue
            
            clauses_data = contract_data.get('clauses', [])
            print(f"Total clauses: {len(clauses_data)}")
            
            # Show first 3 clauses in detail
            for i, clause in enumerate(clauses_data[:3]):
                print(f"\n--- Clause {i+1} ---")
                print(f"Type: {type(clause)}")
                print(f"Keys: {clause.keys() if isinstance(clause, dict) else 'Not a dict'}")
                
                if isinstance(clause, dict):
                    text = clause.get('text', 'NO TEXT KEY')
                    print(f"Text length: {len(text)}")
                    print(f"Text preview: {text[:200]}...")
                else:
                    print(f"Raw clause: {str(clause)[:200]}...")

if __name__ == "__main__":
    test_clause_extraction()