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
        """Get contract data."""
        return self.get_contract_status(contract_id)