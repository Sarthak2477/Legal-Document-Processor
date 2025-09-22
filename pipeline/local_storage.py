"""
Local JSON storage manager (replaces Firestore).
"""
import json
import os
import gc
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class LocalStorageManager:
    """Local JSON file storage for contract metadata."""
    
    def __init__(self, storage_dir: str = "data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.contracts_file = self.storage_dir / "contracts.json"
        self._ensure_files()
    
    def _ensure_files(self):
        """Create storage files if they don't exist."""
        if not self.contracts_file.exists():
            self._save_data({})
    
    def _load_data(self) -> Dict[str, Any]:
        """Load data from JSON file."""
        try:
            with open(self.contracts_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_data(self, data: Dict[str, Any]):
        """Save data to JSON file."""
        with open(self.contracts_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def get_contract_status(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """Get contract processing status."""
        data = self._load_data()
        return data.get(contract_id)
    
    def update_contract_status(self, contract_id: str, status: str, progress: int = 0) -> bool:
        """Update contract processing status."""
        try:
            data = self._load_data()
            if contract_id not in data:
                data[contract_id] = {
                    'contract_id': contract_id,
                    'created_at': datetime.now().isoformat()
                }
            
            data[contract_id].update({
                'status': status,
                'progress': progress,
                'updated_at': datetime.now().isoformat()
            })
            
            self._save_data(data)
            return True
        except Exception as e:
            logger.error(f"Error updating status: {e}")
            return False
    
    def get_contract(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """Get contract data (always from database for full data)."""
        # Check if contract exists in local metadata
        local_data = self.get_contract_status(contract_id)
        if not local_data:
            return None
        
        # Always get full data from database to save memory
        db_data = self._get_from_database(contract_id)
        if db_data:
            return db_data
        
        # Fallback to local if database fails
        return local_data
    
    def _get_from_database(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """Get contract data from Supabase."""
        try:
            from config import settings
            if settings.SUPABASE_URL and settings.SUPABASE_KEY:
                from supabase import create_client
                supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                
                result = supabase.table('contracts').select('*').eq('contract_id', contract_id).execute()
                
                if result.data:
                    contract_data = result.data[0]
                    return {
                        'contract_id': contract_id,
                        'status': contract_data.get('status', 'completed'),
                        'processed_data': contract_data.get('data', {}),
                        'created_at': contract_data.get('created_at'),
                        'updated_at': contract_data.get('created_at')
                    }
        except Exception as e:
            logger.warning(f"Failed to get from database: {e}")
        
        return None
    
    def store_processed_contract(self, contract_id: str, contract_data: Dict[str, Any]) -> bool:
        """Store processed contract data (database-only for memory efficiency)."""
        try:
            data = self._load_data()
            if contract_id not in data:
                data[contract_id] = {
                    'contract_id': contract_id,
                    'created_at': datetime.now().isoformat()
                }
            
            # Store only minimal metadata in memory
            data[contract_id].update({
                'status': 'completed',
                'updated_at': datetime.now().isoformat(),
                'has_processed_data': True,
                'clause_count': len(contract_data.get('contract', {}).get('clauses', [])) if contract_data.get('success') else 0
            })
            
            self._save_data(data)
            
            # Store full data in database only
            self._store_in_database(contract_id, contract_data)
            
            # Force garbage collection to free memory
            del contract_data
            gc.collect()
            
            return True
        except Exception as e:
            logger.error(f"Error storing contract: {e}")
            return False
    
    def _store_in_database(self, contract_id: str, contract_data: Dict[str, Any]):
        """Store contract data in Supabase for persistence."""
        try:
            from config import settings
            if settings.SUPABASE_URL and settings.SUPABASE_KEY:
                from supabase import create_client
                supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                
                # Store contract metadata
                # Compress data before storing
                import json
                compressed_data = json.dumps(contract_data, separators=(',', ':'))  # Minimal JSON
                
                supabase.table('contracts').upsert({
                    'contract_id': contract_id,
                    'data': json.loads(compressed_data),  # Store as JSONB
                    'created_at': datetime.now().isoformat(),
                    'status': 'completed'
                }).execute()
                
                logger.info(f"Contract {contract_id} stored in database")
        except Exception as e:
            logger.warning(f"Failed to store in database: {e}")