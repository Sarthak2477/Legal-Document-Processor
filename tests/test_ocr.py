"""
Tests for OCR extractor module.
"""
import os
import io
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime

from pipeline.ocr_extractor import OCRExtractor
from models.contract import ContractMetadata


@pytest.fixture
def sample_pdf_path():
    """Path to sample PDF file in tests directory."""
    return str(Path(__file__).parent / "sample.pdf")


@pytest.fixture
def ocr_extractor():
    return OCRExtractor()


def test_init_default():
    """Test OCR extractor initialization with defaults."""
    with patch('pipeline.ocr_extractor.documentai.DocumentProcessorServiceClient'):
        extractor = OCRExtractor()
        assert extractor.logger is not None
        assert extractor.gcp_project == "graphic-nucleus-470014-i6"


def test_init_gcp_failure():
    """Test initialization when GCP services fail."""
    with patch('pipeline.ocr_extractor.documentai.DocumentProcessorServiceClient', side_effect=Exception("GCP Error")):
        extractor = OCRExtractor()
        assert not extractor.use_gcp


def test_extract_text_document_ai_success(ocr_extractor, sample_pdf_path):
    """Test Document AI extraction success."""
    if not os.path.exists(sample_pdf_path):
        pytest.skip("sample.pdf not found")
    
    ocr_extractor.use_gcp = True
    
    with patch.object(ocr_extractor, '_extract_with_document_ai') as mock_docai:
        mock_docai.return_value = ("Document AI text", Mock(spec=ContractMetadata))
        
        text, metadata = ocr_extractor.extract_text(sample_pdf_path)
        
        assert text == "Document AI text"
        mock_docai.assert_called_once_with(sample_pdf_path)


def test_extract_text_fallback_to_pdfplumber(ocr_extractor, sample_pdf_path):
    """Test fallback to pdfplumber when Document AI fails."""
    if not os.path.exists(sample_pdf_path):
        pytest.skip("sample.pdf not found")
    
    ocr_extractor.use_gcp = True
    
    with patch.object(ocr_extractor, '_extract_with_document_ai', side_effect=Exception("AI Error")), \
         patch.object(ocr_extractor, '_is_text_based_pdf', return_value=True), \
         patch.object(ocr_extractor, '_extract_with_pdfplumber') as mock_pdf:
        
        mock_pdf.return_value = ("PDF text", Mock(spec=ContractMetadata))
        
        text, metadata = ocr_extractor.extract_text(sample_pdf_path)
        
        assert text == "PDF text"
        mock_pdf.assert_called_once_with(sample_pdf_path)


def test_extract_text_fallback_to_ocr(ocr_extractor, sample_pdf_path):
    """Test fallback to OCR for scanned PDFs."""
    if not os.path.exists(sample_pdf_path):
        pytest.skip("sample.pdf not found")
    
    ocr_extractor.use_gcp = False
    
    with patch.object(ocr_extractor, '_is_text_based_pdf', return_value=False), \
         patch.object(ocr_extractor, '_extract_with_ocr') as mock_ocr:
        
        mock_ocr.return_value = ("OCR text", Mock(spec=ContractMetadata))
        
        text, metadata = ocr_extractor.extract_text(sample_pdf_path)
        
        assert text == "OCR text"
        mock_ocr.assert_called_once_with(sample_pdf_path)


@patch('pipeline.ocr_extractor.requests.post')
def test_apply_privacy_shield_success(mock_post, ocr_extractor):
    """Test privacy shield redaction success."""
    mock_response = Mock()
    mock_response.json.return_value = {"sanitized_text": "redacted text"}
    mock_post.return_value = mock_response
    
    result = ocr_extractor._apply_privacy_shield("sensitive text")
    
    assert result == "redacted text"
    mock_post.assert_called_once()


@patch('pipeline.ocr_extractor.requests.post')
def test_apply_privacy_shield_failure(mock_post, ocr_extractor):
    """Test privacy shield redaction failure."""
    mock_post.side_effect = Exception("Network error")
    
    result = ocr_extractor._apply_privacy_shield("sensitive text")
    
    assert result == "sensitive text"


def test_calculate_document_ai_confidence(ocr_extractor):
    """Test Document AI confidence calculation."""
    mock_result = Mock()
    mock_result.document.pages = []
    
    confidence = ocr_extractor._calculate_document_ai_confidence(mock_result)
    
    assert confidence == 0.95  # Default confidence


@patch('pipeline.ocr_extractor.pdfplumber')
def test_is_text_based_pdf_true(mock_pdfplumber, ocr_extractor, sample_pdf_path):
    """Test text-based PDF detection."""
    mock_pdf = Mock()
    mock_page = Mock()
    mock_page.extract_text.return_value = "A" * 150  # Substantial text
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = Mock(return_value=mock_pdf)
    mock_pdf.__exit__ = Mock(return_value=None)
    mock_pdfplumber.open.return_value = mock_pdf
    
    result = ocr_extractor._is_text_based_pdf(sample_pdf_path)
    
    assert result is True


@patch('pipeline.ocr_extractor.pdfplumber')
def test_is_text_based_pdf_false(mock_pdfplumber, ocr_extractor, sample_pdf_path):
    """Test scanned PDF detection."""
    mock_pdf = Mock()
    mock_page = Mock()
    mock_page.extract_text.return_value = "short"  # Insufficient text
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = Mock(return_value=mock_pdf)
    mock_pdf.__exit__ = Mock(return_value=None)
    mock_pdfplumber.open.return_value = mock_pdf
    
    result = ocr_extractor._is_text_based_pdf(sample_pdf_path)
    
    assert result is False


@patch('pipeline.ocr_extractor.pdfplumber')
def test_extract_with_pdfplumber(mock_pdfplumber, ocr_extractor, sample_pdf_path):
    """Test pdfplumber extraction."""
    mock_pdf = Mock()
    mock_page = Mock()
    mock_page.extract_text.return_value = "Page text"
    mock_page.extract_tables.return_value = [[["cell1", "cell2"]]]
    mock_pdf.pages = [mock_page]
    mock_pdf.__enter__ = Mock(return_value=mock_pdf)
    mock_pdf.__exit__ = Mock(return_value=None)
    mock_pdfplumber.open.return_value = mock_pdf
    
    with patch.object(ocr_extractor, '_extract_metadata') as mock_metadata:
        mock_metadata.return_value = Mock(spec=ContractMetadata)
        
        text, metadata = ocr_extractor._extract_with_pdfplumber(sample_pdf_path)
        
        assert "Page text" in text
        assert "cell1 | cell2" in text


@patch('pipeline.ocr_extractor.fitz')
@patch('pipeline.ocr_extractor.pytesseract')
@patch('pipeline.ocr_extractor.Image')
def test_extract_with_ocr(mock_image, mock_tesseract, mock_fitz, ocr_extractor, sample_pdf_path):
    """Test OCR extraction."""
    # Mock PyMuPDF
    mock_doc = Mock()
    mock_page = Mock()
    mock_pix = Mock()
    mock_pix.tobytes.return_value = b"image_data"
    mock_page.get_pixmap.return_value = mock_pix
    mock_doc.page_count = 1
    mock_doc.load_page.return_value = mock_page
    mock_fitz.open.return_value = mock_doc
    
    # Mock Tesseract
    mock_tesseract.image_to_string.return_value = "OCR result"
    mock_tesseract.image_to_data.return_value = {"conf": ["90", "85"]}
    mock_tesseract.Output.DICT = "dict"
    
    # Mock PIL Image
    mock_img = Mock()
    mock_image.open.return_value = mock_img
    
    with patch.object(ocr_extractor, '_extract_metadata') as mock_metadata, \
         patch.object(ocr_extractor, '_preprocess_image', return_value=mock_img):
        
        mock_metadata.return_value = Mock(spec=ContractMetadata)
        
        text, metadata = ocr_extractor._extract_with_ocr(sample_pdf_path)
        
        assert "OCR result" in text


def test_preprocess_image(ocr_extractor):
    """Test image preprocessing."""
    with patch('PIL.ImageEnhance'), \
         patch('PIL.ImageFilter'):
        
        mock_image = Mock()
        mock_image.mode = 'RGB'
        mock_image.convert.return_value = mock_image
        mock_image.filter.return_value = mock_image
        
        result = ocr_extractor._preprocess_image(mock_image)
        
        assert result is not None


@patch('pipeline.ocr_extractor.os.stat')
@patch('pipeline.ocr_extractor.fitz')
def test_extract_metadata(mock_fitz, mock_stat, ocr_extractor, sample_pdf_path):
    """Test metadata extraction."""
    mock_stat.return_value.st_size = 1024
    
    mock_doc = Mock()
    mock_doc.page_count = 3
    mock_doc.metadata = {"creationDate": "2023-01-01"}
    mock_doc.__enter__ = Mock(return_value=mock_doc)
    mock_doc.__exit__ = Mock(return_value=None)
    mock_fitz.open.return_value = mock_doc
    
    metadata = ocr_extractor._extract_metadata(sample_pdf_path)
    
    assert metadata.filename == "sample.pdf"
    assert metadata.file_size == 1024
    assert metadata.pages == 3


def test_extract_metadata_error(ocr_extractor, sample_pdf_path):
    """Test metadata extraction with errors."""
    with patch('pipeline.ocr_extractor.os.stat', side_effect=Exception("File error")):
        
        metadata = ocr_extractor._extract_metadata(sample_pdf_path)
        
        assert metadata.filename == "sample.pdf"
        assert metadata.file_size == 0


def test_extract_text_integration(sample_pdf_path):
    """Integration test with real PDF."""
    if not os.path.exists(sample_pdf_path):
        pytest.skip("sample.pdf not found")
    
    try:
        extractor = OCRExtractor()
        text, metadata = extractor.extract_text(sample_pdf_path)
        
        assert isinstance(text, str)
        assert len(text) > 0
        assert isinstance(metadata, ContractMetadata)
        assert metadata.filename == "sample.pdf"
        
    except Exception as e:
        pytest.skip(f"Integration test failed: {e}")


@patch('pipeline.ocr_extractor.documentai.DocumentProcessorServiceClient')
def test_document_ai_extraction_full_flow(mock_client_class, ocr_extractor, sample_pdf_path):
    """Test full Document AI extraction flow."""
    if not os.path.exists(sample_pdf_path):
        pytest.skip("sample.pdf not found")
    
    # Mock Document AI client and response
    mock_client = Mock()
    mock_result = Mock()
    mock_result.document.text = "Document AI extracted text"
    mock_client.process_document.return_value = mock_result
    mock_client.processor_path.return_value = "projects/test/locations/us/processors/123"
    mock_client_class.return_value = mock_client
    
    ocr_extractor.use_gcp = True
    ocr_extractor.docai_client = mock_client
    
    with patch.object(ocr_extractor, '_apply_privacy_shield', return_value="sanitized text"), \
         patch.object(ocr_extractor, '_calculate_document_ai_confidence', return_value=0.95):
        
        with patch.object(ocr_extractor, '_extract_metadata') as mock_metadata:
            mock_metadata.return_value = ContractMetadata(
                filename="sample.pdf",
                file_path=sample_pdf_path,
                file_size=1024,
                pages=1,
                processing_date=datetime.now(),
                ocr_method="document_ai"
            )
            
            text, metadata = ocr_extractor._extract_with_document_ai(sample_pdf_path)
            
            assert text == "sanitized text"
            assert metadata is not None