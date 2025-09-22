"""
Local JSON storage manager (replaces Firestore).
"""
import json
import os
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
        """Get contract data from local storage or database."""
        # Try local storage first
        local_data = self.get_contract_status(contract_id)
        if local_data and local_data.get('processed_data'):
            return local_data
        
        # Fallback to database
        return self._get_from_database(contract_id)
    
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
        """Store processed contract data."""
        try:
            data = self._load_data()
            if contract_id not in data:
                data[contract_id] = {
                    'contract_id': contract_id,
                    'created_at': datetime.now().isoformat()
                }
            
            # Store in both local storage and database
            data[contract_id]['processed_data'] = contract_data
            data[contract_id]['updated_at'] = datetime.now().isoformat()
            data[contract_id]['status'] = 'completed'
            
            self._save_data(data)
            
            # Also store in Supabase for persistence
            self._store_in_database(contract_id, contract_data)
            
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
                supabase.table('contracts').upsert({
                    'contract_id': contract_id,
                    'data': contract_data,
                    'created_at': datetime.now().isoformat(),
                    'status': 'completed'
                }).execute()
                
                logger.info(f"Contract {contract_id} stored in database")
        except Exception as e:
            logger.warning(f"Failed to store in database: {e}")