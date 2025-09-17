"""
Firestore database manager for contract metadata and processing results.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
try:
    from firebase_admin import firestore
except ImportError:
    # Mock firestore for testing
    class firestore:
        @staticmethod
        def client():
            return Mock()
        
        SERVER_TIMESTAMP = "mock_timestamp"
        
        class Query:
            DESCENDING = "desc"

from models.contract import ProcessedContract, ContractMetadata
from unittest.mock import Mock


class FirestoreManager:
    """Manages contract data storage in Firestore."""
    
    def __init__(self):
        """Initialize Firestore client."""
        self.db = firestore.client()
        self.logger = logging.getLogger(__name__)
    
    def store_contract(self, contract: ProcessedContract, contract_id: str) -> bool:
        """
        Store processed contract in Firestore.
        
        Args:
            contract: Processed contract object
            contract_id: Unique identifier for the contract
            
        Returns:
            Success status
        """
        try:
            # TODO: Convert contract to Firestore-compatible format
            contract_data = {
                'metadata': {
                    'filename': contract.metadata.filename,
                    'file_path': contract.metadata.file_path,
                    'file_size': contract.metadata.file_size,
                    'pages': contract.metadata.pages,
                    'processing_date': contract.metadata.processing_date,
                    'ocr_method': contract.metadata.ocr_method,
                    'language': contract.metadata.language,
                    'confidence_score': contract.metadata.confidence_score
                },
                'sections_count': len(contract.sections),
                'entities_count': len(contract.entities),
                'processing_stats': contract.processing_stats,
                'created_at': firestore.SERVER_TIMESTAMP,
                'status': 'completed'
            }
            
            # TODO: Store main contract document
            self.db.collection('contracts').document(contract_id).set(contract_data)
            
            # TODO: Store sections as subcollection
            self._store_sections(contract_id, contract.sections)
            
            # TODO: Store entities as subcollection
            self._store_entities(contract_id, contract.entities)
            
            self.logger.info(f"Contract stored successfully: {contract_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing contract: {str(e)}")
            return False
    
    def store_analysis(self, contract_id: str, analysis: Dict[str, Any]) -> bool:
        """
        Store contract analysis results.
        
        Args:
            contract_id: Contract identifier
            analysis: Analysis results from RAG generator
            
        Returns:
            Success status
        """
        try:
            # TODO: Store analysis in subcollection
            analysis_data = {
                'summary': analysis.get('summary', ''),
                'risks': analysis.get('risks', []),
                'redlines': analysis.get('redlines', []),
                'key_terms': analysis.get('key_terms', {}),
                'generated_at': firestore.SERVER_TIMESTAMP
            }
            
            self.db.collection('contracts').document(contract_id)\
                   .collection('analysis').document('latest').set(analysis_data)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing analysis: {str(e)}")
            return False
    
    def get_contract(self, contract_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve contract by ID.
        
        Args:
            contract_id: Contract identifier
            
        Returns:
            Contract data or None if not found
        """
        try:
            doc_ref = self.db.collection('contracts').document(contract_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving contract: {str(e)}")
            return None
    
    def list_contracts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List all contracts with pagination.
        
        Args:
            limit: Maximum number of contracts to return
            
        Returns:
            List of contract metadata
        """
        try:
            docs = self.db.collection('contracts')\
                         .order_by('created_at', direction=firestore.Query.DESCENDING)\
                         .limit(limit).stream()
            
            contracts = []
            for doc in docs:
                contract_data = doc.to_dict()
                contract_data['id'] = doc.id
                contracts.append(contract_data)
            
            return contracts
            
        except Exception as e:
            self.logger.error(f"Error listing contracts: {str(e)}")
            return []
    
    def store_processing_job(self, job_id: str, job_data: Dict[str, Any]) -> bool:
        """
        Store processing job information for batch operations.
        
        Args:
            job_id: Unique job identifier
            job_data: Job metadata and status
            
        Returns:
            Success status
        """
        try:
            job_data['created_at'] = firestore.SERVER_TIMESTAMP
            job_data['updated_at'] = firestore.SERVER_TIMESTAMP
            
            self.db.collection('processing_jobs').document(job_id).set(job_data)
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing processing job: {str(e)}")
            return False
    
    def update_job_status(self, job_id: str, status: str, progress: int = 0) -> bool:
        """
        Update processing job status.
        
        Args:
            job_id: Job identifier
            status: New status (pending, processing, completed, failed)
            progress: Progress percentage (0-100)
            
        Returns:
            Success status
        """
        try:
            self.db.collection('processing_jobs').document(job_id).update({
                'status': status,
                'progress': progress,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating job status: {str(e)}")
            return False
    
    def _store_sections(self, contract_id: str, sections: List[Any]):
        """Store contract sections as subcollection."""
        # TODO: Store each section with its clauses
        for i, section in enumerate(sections):
            section_data = {
                'title': section.title,
                'level': section.level,
                'clauses_count': len(section.clauses),
                'order': i
            }
            
            self.db.collection('contracts').document(contract_id)\
                   .collection('sections').document(f'section_{i}').set(section_data)
            
            # TODO: Store clauses within each section
            for j, clause in enumerate(section.clauses):
                clause_data = {
                    'text': clause.text,
                    'clause_type': clause.clause_type,
                    'entities': clause.entities,
                    'page_number': clause.page_number,
                    'confidence_score': clause.confidence_score,
                    'order': j
                }
                
                self.db.collection('contracts').document(contract_id)\
                       .collection('sections').document(f'section_{i}')\
                       .collection('clauses').document(f'clause_{j}').set(clause_data)
    
    def _store_entities(self, contract_id: str, entities: List[Any]):
        """Store extracted entities as subcollection."""
        # TODO: Store each entity with its metadata
        for i, entity in enumerate(entities):
            entity_data = {
                'text': entity.text,
                'label': entity.label,
                'start': entity.start,
                'end': entity.end,
                'confidence': entity.confidence
            }
            
            self.db.collection('contracts').document(contract_id)\
                   .collection('entities').document(f'entity_{i}').set(entity_data)