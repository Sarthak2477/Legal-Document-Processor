"""
OCR and text extraction module for contract processing.
"""
import os
import io
import json
import logging
import requests
from typing import Tuple, Optional
from pathlib import Path
from datetime import datetime
import fitz  # PyMuPDF
import pytesseract
import pdfplumber
from PIL import Image
from google.cloud import documentai, firestore
from models.contract import ContractMetadata


class OCRExtractor:
    """Handles OCR and text extraction from PDF documents."""
    
    def __init__(self, tesseract_path: Optional[str] = None, 
                 gcp_project: Optional[str] = None,
                 gcp_region: str = "us",
                 doc_ai_processor_id: Optional[str] = None,
                 privacy_shield_url: Optional[str] = None):
        """Initialize OCR extractor with optional configuration paths."""
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        
        # Google Cloud Document AI configuration
        self.gcp_project = gcp_project or os.getenv("GCP_PROJECT", "graphic-nucleus-470014-i6")
        self.gcp_region = gcp_region or os.getenv("GCP_REGION", "us")
        self.doc_ai_processor_id = doc_ai_processor_id or os.getenv("DOC_AI_PROCESSOR_ID", "b9c81ca1e6e6b84d")
        self.privacy_shield_url = privacy_shield_url or os.getenv("PRIVACY_SHIELD_URL", 
            "https://privacy-shield-service-141718440544.us-central1.run.app/redact")
        
        # Initialize Google Cloud clients
        try:
            self.docai_client = documentai.DocumentProcessorServiceClient()
            self.firestore_client = firestore.Client()
            self.use_gcp = True
            self.logger = logging.getLogger(__name__)
            self.logger.info("Google Cloud Document AI initialized successfully")
        except Exception as e:
            self.logger = logging.getLogger(__name__)
            self.logger.warning(f"Failed to initialize Google Cloud services: {e}. Falling back to local OCR.")
            self.use_gcp = False
    
    def extract_text(self, file_path: str) -> Tuple[str, ContractMetadata]:
        """
        Main extraction method - determines best approach for PDF.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Tuple of (extracted_text, metadata)
        """
        # Try Google Cloud Document AI first if available
        if self.use_gcp:
            try:
                return self._extract_with_document_ai(file_path)
            except Exception as e:
                self.logger.warning(f"Document AI extraction failed: {e}. Falling back to local methods.")
        
        # Fallback to original logic
        if self._is_text_based_pdf(file_path):
            return self._extract_with_pdfplumber(file_path)
        else:
            return self._extract_with_ocr(file_path)
    
    def _extract_with_document_ai(self, file_path: str) -> Tuple[str, ContractMetadata]:
        """Extract text using Google Cloud Document AI."""
        try:
            # Read the file content
            with open(file_path, 'rb') as file:
                document_content = file.read()
            
            # Prepare Document AI request
            full_processor_name = self.docai_client.processor_path(
                self.gcp_project, self.gcp_region, self.doc_ai_processor_id
            )
            
            # Create the request
            raw_document = documentai.RawDocument(
                content=document_content,
                mime_type="application/pdf"
            )
            
            request = documentai.ProcessRequest(
                name=full_processor_name,
                raw_document=raw_document
            )
            
            # Process the document
            result = self.docai_client.process_document(request=request)
            extracted_text = result.document.text
            
            if not extracted_text:
                raise ValueError("Document AI returned no text.")
            
            self.logger.info("Document AI text extraction successful.")
            
            # Apply privacy shield redaction if configured
            sanitized_text = self._apply_privacy_shield(extracted_text)
            
            # Generate metadata
            metadata = self._extract_metadata(file_path)
            metadata.ocr_method = "document_ai"
            metadata.confidence_score = self._calculate_document_ai_confidence(result)
            
            return sanitized_text, metadata
            
        except Exception as e:
            self.logger.error(f"Document AI extraction failed: {e}")
            raise
    
    def _apply_privacy_shield(self, text: str) -> str:
        """Apply privacy shield redaction to extracted text."""
        try:
            response = requests.post(
                self.privacy_shield_url,
                headers={"Content-Type": "application/json"},
                data=json.dumps({"text": text}),
                timeout=30
            )
            response.raise_for_status()
            sanitized_json = response.json()
            
            sanitized_text = sanitized_json.get("sanitized_text", text)
            self.logger.info("Privacy shield redaction applied successfully.")
            return sanitized_text
            
        except Exception as e:
            self.logger.warning(f"Privacy shield redaction failed: {e}. Returning original text.")
            return text
    
    def _calculate_document_ai_confidence(self, result) -> float:
        """Calculate confidence score from Document AI result."""
        try:
            # Extract confidence from Document AI result if available
            if hasattr(result.document, 'pages'):
                confidences = []
                for page in result.document.pages:
                    if hasattr(page, 'tokens'):
                        for token in page.tokens:
                            if hasattr(token, 'text_anchor') and hasattr(token.text_anchor, 'confidence'):
                                confidences.append(token.text_anchor.confidence)
                
                if confidences:
                    return sum(confidences) / len(confidences)
            
            # Default confidence for Document AI
            return 0.95
        except Exception as e:
            self.logger.warning(f"Could not calculate confidence: {e}")
            return 0.90
    
    def _is_text_based_pdf(self, file_path: str) -> bool:
        """Check if PDF contains extractable text or needs OCR."""
        try:
            with pdfplumber.open(file_path) as pdf:
                # Check first few pages for text
                pages_to_check = min(3, len(pdf.pages))
                total_text = ""
                
                for i in range(pages_to_check):
                    page_text = pdf.pages[i].extract_text()
                    if page_text:
                        total_text += page_text
                
                # If we have substantial text, consider it text-based
                return len(total_text.strip()) > 100
        except Exception as e:
            self.logger.warning(f"Error checking PDF type: {e}")
            return False
    
    def _extract_with_pdfplumber(self, file_path: str) -> Tuple[str, ContractMetadata]:
        """Extract text from text-based PDFs using pdfplumber."""
        try:
            text_content = []
            
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
                    
                    # Extract tables if present
                    tables = page.extract_tables()
                    for table in tables:
                        # Convert table to text format
                        for row in table:
                            if row:
                                text_content.append(" | ".join([cell or "" for cell in row]))
            
            combined_text = "\n".join(text_content)
            metadata = self._extract_metadata(file_path)
            metadata.ocr_method = "pdfplumber"
            metadata.confidence_score = 0.98  # High confidence for text-based PDFs
            
            return combined_text, metadata
            
        except Exception as e:
            self.logger.error(f"PDFplumber extraction failed: {e}")
            raise
    
    def _extract_with_ocr(self, file_path: str) -> Tuple[str, ContractMetadata]:
        """Extract text from scanned PDFs using Tesseract OCR."""
        try:
            text_content = []
            confidences = []
            
            # Convert PDF to images
            pdf_document = fitz.open(file_path)
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document.load_page(page_num)
                # Convert to image
                mat = fitz.Matrix(2, 2)  # 2x zoom for better OCR
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("ppm")
                
                # Create PIL image
                image = Image.open(io.BytesIO(img_data))
                
                # Preprocess image
                processed_image = self._preprocess_image(image)
                
                # Run OCR with confidence data
                ocr_data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT)
                
                # Extract text and confidence
                page_text = pytesseract.image_to_string(processed_image)
                text_content.append(page_text)
                
                # Calculate average confidence for this page
                page_confidences = [int(conf) for conf in ocr_data['conf'] if int(conf) > 0]
                if page_confidences:
                    confidences.append(sum(page_confidences) / len(page_confidences) / 100.0)
            
            pdf_document.close()
            
            combined_text = "\n".join(text_content)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
            
            metadata = self._extract_metadata(file_path)
            metadata.ocr_method = "tesseract_ocr"
            metadata.confidence_score = avg_confidence
            
            return combined_text, metadata
            
        except Exception as e:
            self.logger.error(f"Tesseract OCR extraction failed: {e}")
            raise
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Apply preprocessing to improve OCR accuracy."""
        try:
            # Convert to grayscale
            if image.mode != 'L':
                image = image.convert('L')
            
            # Apply basic enhancement
            from PIL import ImageEnhance, ImageFilter
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            
            # Sharpen
            image = image.filter(ImageFilter.SHARPEN)
            
            # Apply median filter to reduce noise
            image = image.filter(ImageFilter.MedianFilter(size=3))
            
            return image
            
        except Exception as e:
            self.logger.warning(f"Image preprocessing failed: {e}. Using original image.")
            return image
    
    def _extract_metadata(self, file_path: str) -> ContractMetadata:
        """Extract metadata from PDF file."""
        try:
            file_stats = os.stat(file_path)
            
            # Get basic file info
            file_size = file_stats.st_size
            file_name = Path(file_path).name
            
            # Get PDF-specific metadata
            page_count = 0
            creation_date = None
            
            try:
                with fitz.open(file_path) as pdf:
                    page_count = pdf.page_count
                    metadata_dict = pdf.metadata
                    if metadata_dict.get('creationDate'):
                        creation_date = metadata_dict['creationDate']
            except Exception as e:
                self.logger.warning(f"Could not extract PDF metadata: {e}")
            
            return ContractMetadata(
                filename=file_name,
                file_path=file_path,
                file_size=file_size,
                pages=page_count,
                processing_date=datetime.now(),
                ocr_method="unknown"  # Will be set by calling method
            )
            
        except Exception as e:
            self.logger.error(f"Metadata extraction failed: {e}")
            # Return minimal metadata
            return ContractMetadata(
                filename=Path(file_path).name,
                file_path=file_path,
                file_size=0,
                pages=0,
                processing_date=datetime.now(),
                ocr_method="unknown"
            )