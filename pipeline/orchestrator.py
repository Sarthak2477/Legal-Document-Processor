"""
Main pipeline orchestrator for contract processing.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from pipeline.ocr_extractor import OCRExtractor
from pipeline.layout_parser import LayoutParser
from pipeline.preprocessor import ContractPreprocessor
from pipeline.embedder import ContractEmbedder
from pipeline.rag_generator import ContractRAGGenerator
from pipeline.firestore_manager import FirestoreManager
from models.contract import ProcessedContract
from config import settings


class ContractPipeline:
    """Main orchestrator for the contract processing pipeline."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize pipeline with all processing components."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # TODO: Initialize all pipeline components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all processing components."""
        # TODO: Initialize OCR extractor
        self.ocr_extractor = OCRExtractor(
            tesseract_path=settings.TESSERACT_PATH
        )
        
        # TODO: Initialize layout parser
        self.layout_parser = LayoutParser(
            use_layoutlm=self.config.get('use_layoutlm', False)
        )
        
        # TODO: Initialize preprocessor
        self.preprocessor = ContractPreprocessor(
            spacy_model=settings.SPACY_MODEL
        )
        
        # TODO: Initialize embedder
        self.embedder = ContractEmbedder(
            model_name=settings.EMBEDDING_MODEL,
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_KEY
        )
        
        # TODO: Initialize RAG generator
        self.rag_generator = ContractRAGGenerator()
        
        # TODO: Initialize Firestore manager
        self.firestore_manager = FirestoreManager()
    
    def process_contract(
        self, 
        file_path: str, 
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a single contract through the entire pipeline.
        
        Args:
            file_path: Path to contract file
            output_dir: Directory to save outputs (optional)
            
        Returns:
            Processing results and file paths
        """
        self.logger.info(f"Processing contract: {file_path}")
        start_time = datetime.now()
        
        try:
            # Step 1 - OCR/Text Extraction
            result = self.ocr_extractor.extract_text(file_path)
            if result is None or len(result) != 2:
                raise ValueError("OCR extraction failed or returned invalid result")
            
            raw_text, metadata = result
            if raw_text is None or metadata is None:
                raise ValueError("OCR extraction returned None values")
            
            self.logger.info("✓ Text extraction completed")
            
            # Step 2 - Layout & Semantic Parsing
            contract = self.layout_parser.parse_structure(raw_text, metadata)
            if contract is None:
                raise ValueError("Layout parsing failed")
            
            self.logger.info("✓ Layout parsing completed")
            
            # Step 3 - Preprocessing & Normalization
            processed_clauses = self.preprocessor.preprocess_clauses(contract.clauses)
            contract.clauses = processed_clauses
            self.logger.info("✓ Preprocessing completed")
            
            # Step 4 - Generate Embeddings
            clauses_with_embeddings = self.embedder.generate_embeddings(contract.clauses)
            contract.clauses = clauses_with_embeddings
            self.logger.info("✓ Embeddings generated")
            
            # Step 5 - Store Vectors (if database available)
            if settings.SUPABASE_URL:
                contract_id = Path(file_path).stem
                self.embedder.store_vectors(contract.clauses, contract_id)
                self.logger.info("✓ Vectors stored")
            
            # Step 6 - Generate Analysis
            analysis = self._generate_analysis(contract)
            self.logger.info("✓ Analysis completed")
            
            # Save outputs
            if output_dir:
                output_paths = self._save_outputs(contract, analysis, output_dir)
            else:
                output_paths = {}
            
            # Store in Firestore (if available)
            contract_id = Path(file_path).stem
            try:
                self.firestore_manager.store_contract(contract, contract_id)
                self.firestore_manager.store_analysis(contract_id, analysis)
            except Exception as e:
                self.logger.warning(f"Firestore storage failed: {e}")
            
            processing_time = datetime.now() - start_time
            
            return {
                'success': True,
                'contract': contract,
                'analysis': analysis,
                'output_paths': output_paths,
                'contract_id': contract_id,
                'processing_time': processing_time
            }
            
        except Exception as e:
            self.logger.error(f"Pipeline error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path
            }
    
    def process_batch(
        self, 
        file_paths: list, 
        output_dir: str,
        parallel: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Process multiple contracts in batch.
        
        Args:
            file_paths: List of contract file paths
            output_dir: Directory to save all outputs
            parallel: Whether to process in parallel
            
        Returns:
            List of processing results
        """
        # TODO: Implement batch processing
        # TODO: Add parallel processing option using multiprocessing
        # TODO: Handle memory management for large batches
        # TODO: Provide progress tracking
        pass
    
    def _preprocess_sections(self, sections):
        """Preprocess all sections and their clauses."""
        # TODO: Apply preprocessing to all clauses in all sections
        # TODO: Maintain section structure
        pass
    
    def _generate_embeddings(self, contract: ProcessedContract) -> ProcessedContract:
        """Generate embeddings for all clauses in the contract."""
        # TODO: Extract all clauses from sections
        # TODO: Generate embeddings using embedder
        # TODO: Update contract with embeddings
        pass
    
    def _store_vectors(self, contract: ProcessedContract):
        """Store contract vectors in database."""
        # TODO: Store all clause vectors
        # TODO: Include contract metadata
        # TODO: Handle storage errors gracefully
        pass
    
    def _generate_analysis(self, contract: ProcessedContract) -> Dict[str, Any]:
        """Generate comprehensive contract analysis."""
        analysis = {}
        
        try:
            # Generate summary
            analysis['summary'] = self.rag_generator.generate_summary(contract)
        except Exception as e:
            self.logger.warning(f"Summary generation failed: {e}")
            analysis['summary'] = "Summary generation unavailable"
        
        try:
            # Risk analysis
            analysis['risks'] = self.rag_generator.analyze_risks(contract)
        except Exception as e:
            self.logger.warning(f"Risk analysis failed: {e}")
            analysis['risks'] = []
        
        try:
            # Redline suggestions
            analysis['redlines'] = self.rag_generator.suggest_redlines(contract)
        except Exception as e:
            self.logger.warning(f"Redline suggestions failed: {e}")
            analysis['redlines'] = []
        
        # Key terms extraction (local processing)
        analysis['key_terms'] = self._extract_key_terms(contract)
        
        return analysis
    
    def _extract_key_terms(self, contract: ProcessedContract) -> Dict[str, Any]:
        """Extract key terms and provisions from contract."""
        key_terms = {
            'parties': [],
            'effective_dates': [],
            'payment_terms': [],
            'termination_conditions': [],
            'governing_law': [],
            'obligations': [],
            'conditions': []
        }
        
        # Extract from contract metadata
        if hasattr(contract.metadata, 'parties') and contract.metadata.parties:
            key_terms['parties'] = contract.metadata.parties
        
        # Extract from clauses
        for clause in contract.clauses:
            if clause.key_terms:
                for term in clause.key_terms:
                    if 'payment' in term.lower() or 'fee' in term.lower():
                        key_terms['payment_terms'].append(term)
                    elif 'terminate' in term.lower() or 'end' in term.lower():
                        key_terms['termination_conditions'].append(term)
                    elif 'law' in term.lower() or 'jurisdiction' in term.lower():
                        key_terms['governing_law'].append(term)
            
            if clause.obligations:
                key_terms['obligations'].extend(clause.obligations)
            
            if clause.conditions:
                key_terms['conditions'].extend(clause.conditions)
        
        # Remove duplicates
        for key in key_terms:
            if isinstance(key_terms[key], list):
                key_terms[key] = list(set(key_terms[key]))
        
        return key_terms
    
    def _save_outputs(
        self, 
        contract: ProcessedContract, 
        analysis: Dict[str, Any], 
        output_dir: str
    ) -> Dict[str, str]:
        """Save all processing outputs to files."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        base_name = Path(contract.metadata.filename).stem
        
        # TODO: Save structured contract data
        contract_path = output_dir / f"{base_name}_structured.json"
        with open(contract_path, 'w') as f:
            json.dump(contract.dict(), f, indent=2, default=str)
        
        # TODO: Save analysis results
        analysis_path = output_dir / f"{base_name}_analysis.json"
        with open(analysis_path, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        # TODO: Save summary as text file
        summary_path = output_dir / f"{base_name}_summary.txt"
        with open(summary_path, 'w') as f:
            f.write(analysis.get('summary', ''))
        
        return {
            'contract': str(contract_path),
            'analysis': str(analysis_path),
            'summary': str(summary_path)
        }
    
    # Cloud integration placeholders
    def deploy_firebase_functions(self):
        """Deploy pipeline as Firebase Functions with Storage triggers."""
        # TODO: Deploy main processing function with Storage trigger
        # TODO: Deploy HTTP endpoints for manual processing
        # TODO: Deploy RAG query endpoints
        # TODO: Set up Firestore security rules
        # TODO: Configure Firebase Storage rules
        
        deployment_config = {
            'functions': [
                'process_uploaded_contract',  # Storage trigger
                'process_contract_api',       # HTTP endpoint
                'query_contract_api',         # RAG endpoint
                'batch_process_api'           # Batch processing
            ],
            'triggers': {
                'storage': 'contracts/',      # Storage bucket path
                'firestore': ['contracts']    # Firestore collections
            }
        }
        
        return deployment_config
    
    def setup_firebase_triggers(self):
        """Set up Firebase triggers for automated processing."""
        # TODO: Configure Storage triggers for PDF uploads
        # TODO: Set up Firestore triggers for status updates
        # TODO: Create Cloud Scheduler jobs for batch processing
        # TODO: Set up Pub/Sub for processing queues
        # TODO: Configure Firebase Auth for user management
        
        trigger_config = {
            'storage_trigger': {
                'bucket': settings.FIREBASE_STORAGE_BUCKET,
                'path': 'contracts/',
                'events': ['finalize']
            },
            'firestore_triggers': {
                'contracts': ['create', 'update'],
                'processing_jobs': ['create', 'update']
            },
            'scheduled_jobs': {
                'cleanup_temp_files': '0 2 * * *',  # Daily at 2 AM
                'batch_processing': '0 */6 * * *'   # Every 6 hours
            }
        }
        
        return trigger_config
