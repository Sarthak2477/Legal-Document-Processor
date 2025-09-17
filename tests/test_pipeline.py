"""
Integration tests for the complete contract processing pipeline.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import json
from datetime import datetime
import sys

from pipeline.orchestrator import ContractPipeline
from pipeline.ocr_extractor import OCRExtractor
from pipeline.layout_parser import LayoutParser
from pipeline.preprocessor import ContractPreprocessor
from pipeline.embedder import ContractEmbedder
from models.contract import ProcessedContract


class PipelineTestLogger:
    """Custom logger to capture test output."""
    
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path
        self.logs = []
        
    def log(self, message):
        """Log a message to both console and file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        print(message)  # Still print to console
        
    def save_logs(self):
        """Save all logs to file."""
        with open(self.log_file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(self.logs))


# Global logger instance
test_logger = None


@pytest.fixture
def sample_pdf_path():
    """Path to sample PDF file in tests directory."""
    return str(Path(__file__).parent / "sample_legal_document.pdf")


@pytest.fixture
def pipeline():
    """Initialize contract pipeline for testing."""
    return ContractPipeline()


@pytest.fixture(scope="session", autouse=True)
def setup_test_logger():
    """Set up test logger for the session."""
    global test_logger
    log_file = Path(__file__).parent / f"pipeline_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    test_logger = PipelineTestLogger(log_file)
    test_logger.log("=" * 80)
    test_logger.log("CONTRACT PROCESSING PIPELINE TEST RESULTS")
    test_logger.log("=" * 80)
    test_logger.log(f"Test started at: {datetime.now()}")
    test_logger.log("")
    
    yield
    
    test_logger.log("")
    test_logger.log("=" * 80)
    test_logger.log(f"Test completed at: {datetime.now()}")
    test_logger.log("=" * 80)
    test_logger.save_logs()
    print(f"\nTest results saved to: {log_file}")


def test_ocr_extraction_step(sample_pdf_path):
    """Test OCR text extraction step."""
    if not os.path.exists(sample_pdf_path):
        pytest.skip("sample_legal_document.pdf not found in tests directory")
    
    test_logger.log("\n=== OCR EXTRACTION TEST ===")
    
    ocr_extractor = OCRExtractor()
    text, metadata = ocr_extractor.extract_text(sample_pdf_path)
    
    test_logger.log(f"Extracted text length: {len(text)} characters")
    test_logger.log(f"OCR method: {metadata.ocr_method}")
    test_logger.log(f"Confidence score: {metadata.confidence_score}")
    test_logger.log(f"Pages: {metadata.pages}")
    test_logger.log(f"First 200 characters: {text[:200]}...")
    
    assert isinstance(text, str)
    assert len(text) > 0
    assert metadata.filename == "sample_legal_document.pdf"


def test_layout_parsing_step(sample_pdf_path):
    """Test layout parsing step."""
    if not os.path.exists(sample_pdf_path):
        pytest.skip("sample_legal_document.pdf not found in tests directory")
    
    test_logger.log("\n=== LAYOUT PARSING TEST ===")
    
    # First extract text
    ocr_extractor = OCRExtractor()
    text, metadata = ocr_extractor.extract_text(sample_pdf_path)
    
    # Then parse layout
    layout_parser = LayoutParser(use_layoutlm=False)
    contract = layout_parser.parse_structure(text, metadata)
    
    test_logger.log(f"Sections found: {len(contract.sections)}")
    test_logger.log(f"Total clauses: {len(contract.clauses)}")
    
    for i, section in enumerate(contract.sections[:3]):  # Show first 3 sections
        test_logger.log(f"Section {i+1}: {section.title}")
        test_logger.log(f"  Type: {section.section_type}")
        test_logger.log(f"  Importance: {section.importance_score}")
        test_logger.log(f"  Clauses: {len(section.clauses)}")
        test_logger.log(f"  Has obligations: {section.contains_obligations}")
        test_logger.log(f"  Has conditions: {section.contains_conditions}")
    
    for i, clause in enumerate(contract.clauses[:3]):  # Show first 3 clauses
        test_logger.log(f"Clause {i+1}: {clause.text[:100]}...")
        test_logger.log(f"  Category: {clause.legal_category}")
        test_logger.log(f"  Risk: {clause.risk_level}")
        test_logger.log(f"  Key terms: {clause.key_terms}")
        test_logger.log(f"  Obligations: {len(clause.obligations)}")
        test_logger.log(f"  Conditions: {len(clause.conditions)}")
    
    assert isinstance(contract, ProcessedContract)
    assert len(contract.sections) > 0
    assert len(contract.clauses) > 0


def test_preprocessing_step(sample_pdf_path):
    """Test preprocessing and normalization step."""
    if not os.path.exists(sample_pdf_path):
        pytest.skip("sample_legal_document.pdf not found in tests directory")
    
    test_logger.log("\n=== PREPROCESSING TEST ===")
    
    # Get contract from layout parsing
    ocr_extractor = OCRExtractor()
    text, metadata = ocr_extractor.extract_text(sample_pdf_path)
    
    layout_parser = LayoutParser(use_layoutlm=False)
    contract = layout_parser.parse_structure(text, metadata)
    
    # Preprocess clauses
    preprocessor = ContractPreprocessor()
    processed_clauses = preprocessor.preprocess_clauses(contract.clauses)
    
    test_logger.log(f"Processed {len(processed_clauses)} clauses")
    
    for i, clause in enumerate(processed_clauses[:3]):  # Show first 3
        test_logger.log(f"Processed Clause {i+1}:")
        test_logger.log(f"  Text: {clause.text[:100]}...")
        test_logger.log(f"  Entities: {list(clause.entities.keys())}")
        test_logger.log(f"  Legal category: {clause.legal_category}")
        test_logger.log(f"  Risk level: {clause.risk_level}")
        test_logger.log(f"  Key terms: {clause.key_terms}")
        test_logger.log(f"  Obligations: {clause.obligations[:2] if clause.obligations else []}")
        test_logger.log(f"  Conditions: {clause.conditions[:2] if clause.conditions else []}")
    
    assert len(processed_clauses) == len(contract.clauses)
    assert all(clause.legal_category for clause in processed_clauses)


def test_embedding_step(sample_pdf_path):
    """Test embedding generation step."""
    if not os.path.exists(sample_pdf_path):
        pytest.skip("sample_legal_document.pdf not found in tests directory")
    
    test_logger.log("\n=== EMBEDDING GENERATION TEST ===")
    
    # Get processed clauses
    ocr_extractor = OCRExtractor()
    text, metadata = ocr_extractor.extract_text(sample_pdf_path)
    
    layout_parser = LayoutParser(use_layoutlm=False)
    contract = layout_parser.parse_structure(text, metadata)
    
    preprocessor = ContractPreprocessor()
    processed_clauses = preprocessor.preprocess_clauses(contract.clauses)
    
    # Generate embeddings
    embedder = ContractEmbedder()
    clauses_with_embeddings = embedder.generate_embeddings(processed_clauses)
    
    test_logger.log(f"Generated embeddings for {len(clauses_with_embeddings)} clauses")
    
    embedding_stats = []
    for clause in clauses_with_embeddings:
        if clause.embedding:
            embedding_stats.append(len(clause.embedding))
    
    if embedding_stats:
        test_logger.log(f"Embedding dimensions: {embedding_stats[0]}")
        test_logger.log(f"Clauses with embeddings: {len(embedding_stats)}")
        test_logger.log(f"Sample embedding values: {clauses_with_embeddings[0].embedding[:5]}...")
    
    assert all(clause.embedding for clause in clauses_with_embeddings)
    assert all(len(clause.embedding) > 0 for clause in clauses_with_embeddings)


@patch.dict(os.environ, {'SUPABASE_URL': 'test_url', 'SUPABASE_KEY': 'test_key'})
def test_vector_storage_step(sample_pdf_path):
    """Test vector storage step (mocked)."""
    if not os.path.exists(sample_pdf_path):
        pytest.skip("sample_legal_document.pdf not found in tests directory")
    
    test_logger.log("\n=== VECTOR STORAGE TEST (MOCKED) ===")
    
    # Get clauses with embeddings
    ocr_extractor = OCRExtractor()
    text, metadata = ocr_extractor.extract_text(sample_pdf_path)
    
    layout_parser = LayoutParser(use_layoutlm=False)
    contract = layout_parser.parse_structure(text, metadata)
    
    preprocessor = ContractPreprocessor()
    processed_clauses = preprocessor.preprocess_clauses(contract.clauses)
    
    embedder = ContractEmbedder()
    clauses_with_embeddings = embedder.generate_embeddings(processed_clauses)
    
    # Mock vector storage
    with patch.object(embedder, 'supabase') as mock_supabase:
        mock_supabase.table.return_value.insert.return_value.execute.return_value = None
        
        result = embedder.store_vectors(clauses_with_embeddings, "test_contract")
        
        test_logger.log(f"Vector storage result: {result}")
        test_logger.log(f"Stored {len(clauses_with_embeddings)} clause vectors")
        
        if mock_supabase.table.called:
            test_logger.log("Supabase storage method was called")
        
        # Test similarity search (mocked)
        mock_supabase.rpc.return_value.execute.return_value.data = [
            {"clause_id": "C1", "similarity": 0.85, "text": "Sample similar clause"}
        ]
        
        similar = embedder.search_similar_clauses("payment terms", limit=5)
        test_logger.log(f"Similar clauses found: {len(similar)}")
        if similar:
            test_logger.log(f"Sample result: {similar[0]}")
    
    assert result is True or result is False  # Should return boolean


def test_complete_pipeline_integration(sample_pdf_path):
    """Test complete pipeline integration."""
    if not os.path.exists(sample_pdf_path):
        pytest.skip("sample_legal_document.pdf not found in tests directory")
    
    test_logger.log("\n=== COMPLETE PIPELINE INTEGRATION TEST ===")
    
    # Mock external services
    with patch('pipeline.embedder.create_client') as mock_supabase_client:
        mock_client = Mock()
        mock_client.table.return_value.insert.return_value.execute.return_value = None
        mock_supabase_client.return_value = mock_client
        
        # Initialize pipeline
        pipeline = ContractPipeline()
        
        # Process contract
        result = pipeline.process_contract(sample_pdf_path)
        
        test_logger.log(f"Pipeline processing result: {result['success']}")
        
        if result['success']:
            contract = result['contract']
            
            test_logger.log("\n=== FINAL PROCESSING RESULTS ===")
            test_logger.log(f"Contract filename: {contract.metadata.filename}")
            test_logger.log(f"Total sections: {len(contract.sections)}")
            test_logger.log(f"Total clauses: {len(contract.clauses)}")
            test_logger.log(f"OCR method: {contract.metadata.ocr_method}")
            test_logger.log(f"Processing time: {result.get('processing_time', 'N/A')}")
            
            # Legal analysis summary
            risk_counts = {'low': 0, 'medium': 0, 'high': 0}
            category_counts = {}
            
            for clause in contract.clauses:
                if clause.risk_level:
                    risk_counts[clause.risk_level] = risk_counts.get(clause.risk_level, 0) + 1
                if clause.legal_category:
                    category_counts[clause.legal_category] = category_counts.get(clause.legal_category, 0) + 1
            
            test_logger.log("\n=== RISK ANALYSIS ===")
            test_logger.log(f"Low risk clauses: {risk_counts['low']}")
            test_logger.log(f"Medium risk clauses: {risk_counts['medium']}")
            test_logger.log(f"High risk clauses: {risk_counts['high']}")
            
            test_logger.log("\n=== LEGAL CATEGORIES ===")
            for category, count in sorted(category_counts.items()):
                test_logger.log(f"{category}: {count} clauses")
            
            # Section analysis
            test_logger.log("\n=== SECTION ANALYSIS ===")
            for section in contract.sections[:5]:  # Show first 5 sections
                test_logger.log(f"Section: {section.title}")
                test_logger.log(f"  Type: {section.section_type}")
                test_logger.log(f"  Importance: {section.importance_score:.2f}")
                test_logger.log(f"  Clauses: {len(section.clauses)}")
                test_logger.log(f"  Has obligations: {section.contains_obligations}")
                test_logger.log(f"  Has conditions: {section.contains_conditions}")
            
            # Sample high-risk clauses
            high_risk_clauses = [c for c in contract.clauses if c.risk_level == 'high']
            if high_risk_clauses:
                test_logger.log("\n=== HIGH RISK CLAUSES ===")
                for clause in high_risk_clauses[:3]:
                    test_logger.log(f"Clause: {clause.text[:150]}...")
                    test_logger.log(f"  Risk: {clause.risk_level}")
                    test_logger.log(f"  Category: {clause.legal_category}")
                    test_logger.log(f"  Key terms: {clause.key_terms}")
            
            # Key obligations
            all_obligations = []
            for clause in contract.clauses:
                all_obligations.extend(clause.obligations)
            
            if all_obligations:
                test_logger.log("\n=== KEY OBLIGATIONS ===")
                for obligation in all_obligations[:5]:
                    test_logger.log(f"- {obligation}")
            
            # Analysis results
            if 'analysis' in result:
                analysis = result['analysis']
                test_logger.log("\n=== ANALYSIS RESULTS ===")
                test_logger.log(f"Summary: {analysis.get('summary', 'N/A')[:200]}...")
                risks = analysis.get('risks', [])
                if risks is None:
                    risks = []
                test_logger.log(f"Risks identified: {len(risks)}")
                
                redlines = analysis.get('redlines', [])
                if redlines is None:
                    redlines = []
                test_logger.log(f"Redline suggestions: {len(redlines)}")
                
                key_terms = analysis.get('key_terms', {})
                test_logger.log(f"Key terms extracted:")
                for term_type, terms in key_terms.items():
                    if terms:
                        test_logger.log(f"  {term_type}: {len(terms)} items")
            
            assert isinstance(contract, ProcessedContract)
            assert len(contract.sections) > 0
            assert len(contract.clauses) > 0
        else:
            test_logger.log(f"Pipeline failed: {result.get('error', 'Unknown error')}")
            assert False, f"Pipeline processing failed: {result.get('error')}"