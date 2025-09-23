"""
Tests for layout parser module.
"""
import pytest
from unittest.mock import Mock, patch
from PIL import Image
import numpy as np

from pipeline.layout_parser import LayoutParser
from models.contract import ContractMetadata, ProcessedContract
from datetime import datetime


@pytest.fixture
def sample_contract_text():
    return """
    ARTICLE I. DEFINITIONS
    
    1. Payment Terms
    The Company shall pay the Contractor within 30 days.
    
    2. Termination Clause
    Either party may terminate this agreement with 30 days notice.
    
    WHEREAS, the parties agree to the following terms;
    
    "Confidential Information" means any proprietary data.
    """


@pytest.fixture
def sample_metadata():
    return ContractMetadata(
        filename="test.pdf",
        file_path="/test/test.pdf",
        file_size=1024,
        pages=1,
        processing_date=datetime.now(),
        ocr_method="tesseract"
    )


@pytest.fixture
def layout_parser():
    return LayoutParser(use_layoutlm=False)


def test_parse_structure_basic(layout_parser, sample_contract_text, sample_metadata):
    """Test basic structure parsing."""
    result = layout_parser.parse_structure(sample_contract_text, sample_metadata)
    
    assert isinstance(result, ProcessedContract)
    assert len(result.sections) > 0
    assert len(result.clauses) > 0
    
    # Test that clauses have legal analysis fields
    for clause in result.clauses:
        assert clause.legal_category is not None
        assert clause.risk_level is not None
        assert isinstance(clause.key_terms, list)
        assert isinstance(clause.obligations, list)
        assert isinstance(clause.conditions, list)


def test_extract_sections(layout_parser, sample_contract_text):
    """Test section extraction."""
    sections = layout_parser._extract_sections_enhanced(sample_contract_text)
    
    assert len(sections) >= 1
    # Check that sections have required fields including new legal fields
    for section in sections:
        assert hasattr(section, 'title')
        assert hasattr(section, 'text')
        assert hasattr(section, 'section_type')
        assert hasattr(section, 'importance_score')
        assert hasattr(section, 'contains_obligations')
        assert hasattr(section, 'contains_conditions')


def test_extract_clauses(layout_parser):
    """Test clause extraction."""
    text = "1. Payment shall be made within 30 days. 2. Termination requires notice."
    clauses = layout_parser._extract_clauses_enhanced(text, "S1")
    
    assert len(clauses) >= 1
    assert all(clause.text for clause in clauses)
    # Test new legal fields are populated
    for clause in clauses:
        assert hasattr(clause, 'legal_category')
        assert hasattr(clause, 'risk_level')
        assert hasattr(clause, 'key_terms')
        assert hasattr(clause, 'obligations')
        assert hasattr(clause, 'conditions')


def test_clause_classification(layout_parser):
    """Test clause type classification."""
    payment_text = "Payment shall be made monthly to the contractor."
    clause_type = layout_parser._determine_clause_type(payment_text)
    
    assert clause_type == "payment"


def test_legal_patterns(layout_parser):
    """Test legal pattern matching."""
    text = "WHEREAS, the parties agree to these terms."
    clauses = layout_parser._extract_by_patterns(text)
    
    assert len(clauses) > 0


def test_valid_clause_detection(layout_parser):
    """Test clause validation."""
    valid_clause = "The contractor shall complete work by deadline."
    invalid_clause = "abc"
    
    assert layout_parser._is_valid_clause(valid_clause)
    assert not layout_parser._is_valid_clause(invalid_clause)


@patch('pipeline.layout_parser.spacy.load')
def test_spacy_fallback(mock_spacy_load, layout_parser):
    """Test spaCy model loading fallback."""
    mock_spacy_load.side_effect = OSError("Model not found")
    
    parser = LayoutParser(use_layoutlm=False)
    assert parser.nlp is None


def test_clause_cleaning(layout_parser):
    """Test clause text cleaning."""
    dirty_text = "  1.2.3   This is a   clause   "
    clean_text = layout_parser._clean_clause_text(dirty_text)
    
    assert clean_text.strip() == "This is a clause."


def test_duplicate_clause_removal(layout_parser):
    """Test duplicate clause removal."""
    clauses = [
        "Payment terms are 30 days.",
        "Payment terms are 30 days.",  # Exact duplicate
        "Termination requires notice."
    ]
    
    unique = layout_parser._merge_duplicate_clauses(clauses)
    assert len(unique) == 2


def test_risk_assessment(layout_parser):
    """Test risk level assessment."""
    high_risk_text = "unlimited liability for all damages"
    medium_risk_text = "indemnification required"
    low_risk_text = "standard payment terms"
    
    assert layout_parser._assess_risk_level(high_risk_text) == 'high'
    assert layout_parser._assess_risk_level(medium_risk_text) == 'medium'
    assert layout_parser._assess_risk_level(low_risk_text) == 'low'


def test_key_terms_extraction(layout_parser):
    """Test key terms extraction."""
    text = "Payment of $10,000 within 30 days at 5% interest"
    terms = layout_parser._extract_key_terms(text)
    
    assert '$10,000' in terms
    assert '30 days' in terms
    assert '5%' in terms


def test_obligations_extraction(layout_parser):
    """Test obligations extraction."""
    text = "Company shall provide services. Client must pay fees."
    obligations = layout_parser._extract_obligations(text)
    
    assert len(obligations) >= 1
    assert any('shall provide' in ob.lower() for ob in obligations)


def test_conditions_extraction(layout_parser):
    """Test conditions extraction."""
    text = "If payment is late, then penalty applies. Provided that notice is given."
    conditions = layout_parser._extract_conditions(text)
    
    assert len(conditions) >= 1
    assert any('if payment' in cond.lower() for cond in conditions)


def test_section_classification(layout_parser):
    """Test section type classification."""
    assert layout_parser._classify_section_type("DEFINITIONS") == 'definitions'
    assert layout_parser._classify_section_type("Payment Terms") == 'terms'  # 'term' matches first
    assert layout_parser._classify_section_type("Payment Schedule") == 'payment'
    assert layout_parser._classify_section_type("General Provisions") == 'general'


def test_section_importance_scoring(layout_parser):
    """Test section importance scoring."""
    important_text = "payment termination liability breach indemnification"
    unimportant_text = "general provisions miscellaneous"
    
    important_score = layout_parser._calculate_section_importance(important_text)
    unimportant_score = layout_parser._calculate_section_importance(unimportant_text)
    
    assert important_score > unimportant_score
    assert 0 <= important_score <= 1
    assert 0 <= unimportant_score <= 1


@pytest.mark.parametrize("text,expected_type", [
    ("Payment shall be made monthly", "payment"),
    ("This agreement may be terminated", "termination"),
    ("Confidential information must be protected", "confidentiality"),
    ("General contract clause", "general")
])
def test_clause_type_detection(layout_parser, text, expected_type):
    """Test clause type detection with various inputs."""
    result = layout_parser._determine_clause_type(text)
    assert result == expected_type


def test_layoutlm_disabled():
    """Test parser with LayoutLM disabled."""
    parser = LayoutParser(use_layoutlm=False)
    assert not parser.use_layoutlm
    assert not hasattr(parser, 'processor')


@patch('pipeline.layout_parser.AutoTokenizer')
@patch('pipeline.layout_parser.LayoutLMv3Processor')
@patch('pipeline.layout_parser.LayoutLMv3ForTokenClassification')
def test_layoutlm_integration(mock_model, mock_processor, mock_tokenizer, sample_metadata):
    """Test LayoutLM integration when enabled."""
    # Mock the processor and model properly
    mock_processor.from_pretrained.return_value = Mock()
    mock_model.from_pretrained.return_value = Mock()
    mock_tokenizer.from_pretrained.return_value = Mock()
    
    with patch('torch.cuda.is_available', return_value=False):
        parser = LayoutParser(use_layoutlm=True)
        
        # Mock image
        image = Image.new('RGB', (100, 100), color='white')
        
        # Test with mocked model
        result = parser.parse_structure("Test text", sample_metadata, image)
        assert isinstance(result, ProcessedContract)
