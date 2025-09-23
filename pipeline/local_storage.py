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

class DatabaseStorageManager:
    """Database-only storage for contract data."""
    
    def __init__(self):
        self._supabase_client = None
    
    def _get_supabase_client(self):
        """Get cached Supabase client."""
        if self._supabase_client is None:
            from config import settings
            if getattr(settings, 'SUPABASE_URL', None) and getattr(settings, 'SUPABASE_KEY', None):
                from supabase import create_client
                self._supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        return self._supabase_client
    
    def get_contract_status(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """Get contract processing status (database-only)."""
        try:
            result = self._get_from_database(contract_id)
            if result:
                return result
            # Return default status if not found
            return {
                'contract_id': contract_id,
                'status': 'not_found',
                'message': 'Contract not found'
            }
        except Exception as e:
            logger.error(f"Error getting contract status for {contract_id}: {e}")
            return {
                'contract_id': contract_id,
                'status': 'error',
                'message': f'Status check failed: {str(e)}'
            }
    
    def update_contract_status(self, contract_id: str, status: str, progress: int = 0) -> bool:
        """Update contract processing status (database-only)."""
        try:
            # Update status in database only
            from config import settings
            
            if not getattr(settings, 'SUPABASE_URL', None) or not getattr(settings, 'SUPABASE_KEY', None):
                logger.warning("Supabase not configured - cannot update status")
                return False
                
            from supabase import create_client
            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            
            # Try update first, then insert if not exists
            try:
                result = supabase.table('contracts').update({
                    'status': status,
                    'updated_at': datetime.now().isoformat()
                }).eq('contract_id', contract_id).execute()
                
                if not result.data:
                    # Insert if update didn't affect any rows
                    result = supabase.table('contracts').insert({
                        'contract_id': contract_id,
                        'status': status,
                        'updated_at': datetime.now().isoformat(),
                        'data': {}
                    }).execute()
            except Exception as e:
                if '23505' in str(e):  # Duplicate key error
                    # Record exists, just update
                    result = supabase.table('contracts').update({
                        'status': status,
                        'updated_at': datetime.now().isoformat()
                    }).eq('contract_id', contract_id).execute()
                else:
                    raise
            
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error updating status: {e}")
            return False
    
    def get_contract(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """Get contract data (database-only)."""
        # Get data ONLY from database
        return self._get_from_database(contract_id)
    
    def _get_from_database(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """Get contract data from Supabase."""
        try:
            from config import settings
            
            if not getattr(settings, 'SUPABASE_URL', None) or not getattr(settings, 'SUPABASE_KEY', None):
                logger.debug("Supabase not configured, skipping database lookup")
                return None
                
            from supabase import create_client
            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            
            result = supabase.table('contracts').select('*').eq('contract_id', contract_id).execute()
            
            if result.data:
                contract_data = result.data[0]
                logger.info(f"✅ Retrieved {contract_id} from database")
                return {
                    'contract_id': contract_id,
                    'status': contract_data.get('status', 'completed'),
                    'processed_data': contract_data.get('data', {}),
                    'created_at': contract_data.get('created_at'),
                    'updated_at': contract_data.get('updated_at')
                }
            else:
                logger.info(f"Contract {contract_id} not found in database")
                
        except ImportError:
            logger.warning("Supabase library not available")
        except Exception as e:
            logger.error(f"Database retrieval failed for {contract_id}: {e}")
        
        return None
    
    def store_processed_contract(self, contract_id: str, contract_data: Dict[str, Any]) -> bool:
        """Store processed contract data (database-only)."""
        try:
            # Store ONLY in database, no local storage
            success = self._store_in_database(contract_id, contract_data)
            

            
            return success
        except Exception as e:
            logger.error(f"Error storing contract: {e}")
            return False
    

    def _store_in_database(self, contract_id: str, contract_data: Dict[str, Any]):
        """Store contract data in Supabase for persistence."""
        try:
            from config import settings
            
            logger.info(f"Attempting to store {contract_id} in database")
            logger.info(f"Supabase URL exists: {bool(getattr(settings, 'SUPABASE_URL', None))}")
            logger.info(f"Supabase Key exists: {bool(getattr(settings, 'SUPABASE_KEY', None))}")
            
            if not getattr(settings, 'SUPABASE_URL', None) or not getattr(settings, 'SUPABASE_KEY', None):
                logger.warning("Supabase credentials not configured - storing locally only")
                return
            
            from supabase import create_client
            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            
            # Convert datetime objects to strings for JSON serialization
            def serialize_datetime(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                return obj
            
            # Clean contract data for JSON serialization
            import json
            clean_data = json.loads(json.dumps(contract_data, default=serialize_datetime))
            
            # Try update first, then insert if not exists
            try:
                result = supabase.table('contracts').update({
                    'data': clean_data,
                    'status': 'completed',
                    'updated_at': datetime.now().isoformat()
                }).eq('contract_id', contract_id).execute()
                
                if not result.data:
                    # Insert if update didn't affect any rows
                    result = supabase.table('contracts').insert({
                        'contract_id': contract_id,
                        'data': clean_data,
                        'created_at': datetime.now().isoformat(),
                        'status': 'completed'
                    }).execute()
            except Exception as e:
                if '23505' in str(e):  # Duplicate key error
                    # Record exists, just update
                    result = supabase.table('contracts').update({
                        'data': clean_data,
                        'status': 'completed',
                        'updated_at': datetime.now().isoformat()
                    }).eq('contract_id', contract_id).execute()
                else:
                    raise
            
            if result.data:
                logger.info(f"✅ Contract {contract_id} stored in database successfully")
                return True
            else:
                logger.error(f"❌ Failed to store {contract_id}: No data returned")
                return False
        except ImportError as e:
            logger.error(f"Supabase library not available: {e}")
            return False
        except Exception as e:
            logger.error(f"Database storage failed for {contract_id}: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            return False
    
    def get_all_contracts(self) -> Dict[str, Any]:
        """Get all contracts from database."""
        return self._load_data()
    
    def list_contracts(self) -> list:
        """List all contracts."""
        try:
            from config import settings
            
            if not getattr(settings, 'SUPABASE_URL', None) or not getattr(settings, 'SUPABASE_KEY', None):
                logger.debug("Supabase not configured, returning empty list")
                return []
                
            from supabase import create_client
            supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            
            result = supabase.table('contracts').select('contract_id, status, created_at, updated_at').execute()
            
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error listing contracts: {e}")
            return []
    
    def _load_data(self) -> Dict[str, Any]:
        """Load all data from database."""
        contracts = self.list_contracts()
        return {"contracts": contracts}

# Alias for backward compatibility
LocalStorageManager = DatabaseStorageManager
