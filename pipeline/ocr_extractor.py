"""
OCR and text extraction module for contract processing.
"""
import os
import io
import json
import logging
import requests
from typing import Tuple, Optional, List
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
        
        # Validate and set privacy shield URL
        privacy_url = privacy_shield_url or os.getenv("PRIVACY_SHIELD_URL", 
            "https://privacy-shield-service-141718440544.us-central1.run.app/redact")
        self.privacy_shield_url = self._validate_privacy_shield_url(privacy_url)
        
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
    
    def _validate_privacy_shield_url(self, url: str) -> str:
        """Validate privacy shield URL to ensure it's from a trusted domain."""
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(url)
            # Only allow HTTPS URLs from trusted domains
            if parsed.scheme != 'https':
                raise ValueError("Privacy shield URL must use HTTPS")
            
            # Whitelist trusted domains
            trusted_domains = [
                'privacy-shield-service-141718440544.us-central1.run.app',
                'localhost',  # For development
                '127.0.0.1'   # For development
            ]
            
            if parsed.hostname not in trusted_domains:
                raise ValueError(f"Untrusted privacy shield domain: {parsed.hostname}")
            
            return url
        except Exception as e:
            self.logger.warning(f"Invalid privacy shield URL: {e}. Disabling privacy shield.")
            return None
    
    def _apply_privacy_shield(self, text: str) -> str:
        """Apply privacy shield redaction to extracted text."""
        if not self.privacy_shield_url:
            return text
            
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
        """Check if PDF contains extractable text or needs OCR with quality assessment."""
        try:
            with pdfplumber.open(file_path) as pdf:
                pages_to_check = min(5, len(pdf.pages))  # Check more pages
                total_text = ""
                text_quality_score = 0
                
                for i in range(pages_to_check):
                    page_text = pdf.pages[i].extract_text()
                    if page_text:
                        total_text += page_text
                        # Quality indicators: proper words, punctuation, structure
                        words = page_text.split()
                        if len(words) > 10:
                            text_quality_score += 1
                        if any(char in page_text for char in '.,;:'):
                            text_quality_score += 1
                        if any(word.istitle() for word in words[:10]):
                            text_quality_score += 1
                
                # Enhanced criteria for text-based detection
                has_substantial_text = len(total_text.strip()) > 200
                has_good_quality = text_quality_score >= pages_to_check * 2
                
                return has_substantial_text and has_good_quality
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
        """Extract text from scanned PDFs using enhanced OCR with fallback strategies."""
        try:
            text_content = []
            confidences = []
            low_quality_pages = []
            
            pdf_document = fitz.open(file_path)
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document.load_page(page_num)
                
                # Try multiple OCR strategies for better accuracy
                page_text, page_confidence = self._extract_page_with_fallback(page, page_num)
                
                text_content.append(page_text)
                confidences.append(page_confidence)
                
                # Track low-quality pages for potential re-processing
                if page_confidence < 0.6:
                    low_quality_pages.append(page_num)
            
            pdf_document.close()
            
            # Re-process low-quality pages with enhanced settings
            if low_quality_pages and len(low_quality_pages) < len(text_content) * 0.5:
                self.logger.info(f"Re-processing {len(low_quality_pages)} low-quality pages")
                text_content, confidences = self._reprocess_low_quality_pages(
                    file_path, text_content, confidences, low_quality_pages
                )
            
            combined_text = "\n".join(text_content)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
            
            metadata = self._extract_metadata(file_path)
            metadata.ocr_method = "enhanced_tesseract_ocr"
            metadata.confidence_score = avg_confidence
            
            return combined_text, metadata
            
        except Exception as e:
            self.logger.error(f"Enhanced OCR extraction failed: {e}")
            raise
    
    def _preprocess_image(self, image: Image.Image, enhancement_level: str = "standard") -> Image.Image:
        """Apply advanced preprocessing to improve OCR accuracy."""
        try:
            from PIL import ImageEnhance, ImageFilter, ImageOps
            import numpy as np
            
            # Convert to grayscale if needed
            if image.mode != 'L':
                image = image.convert('L')
            
            if enhancement_level == "aggressive":
                # Aggressive enhancement for low-quality scans
                # Increase contrast more significantly
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(1.5)
                
                # Enhance sharpness
                enhancer = ImageEnhance.Sharpness(image)
                image = enhancer.enhance(2.0)
                
                # Apply unsharp mask
                image = image.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
                
                # Noise reduction
                image = image.filter(ImageFilter.MedianFilter(size=3))
                
                # Auto-level for better contrast
                image = ImageOps.autocontrast(image)
                
            else:
                # Standard enhancement
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(1.2)
                
                image = image.filter(ImageFilter.SHARPEN)
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
    
    def _extract_page_with_fallback(self, page, page_num: int) -> Tuple[str, float]:
        """Extract text from a page using multiple OCR strategies."""
        try:
            # Strategy 1: Standard OCR
            mat = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("ppm")
            image = Image.open(io.BytesIO(img_data))
            
            processed_image = self._preprocess_image(image, "standard")
            
            # Get OCR data with confidence
            ocr_data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT)
            page_text = pytesseract.image_to_string(processed_image)
            
            # Calculate confidence
            page_confidences = [int(conf) for conf in ocr_data['conf'] if int(conf) > 0]
            confidence = sum(page_confidences) / len(page_confidences) / 100.0 if page_confidences else 0.0
            
            # If confidence is low, try aggressive enhancement
            if confidence < 0.7 and len(page_text.strip()) < 50:
                self.logger.debug(f"Low confidence on page {page_num}, trying aggressive enhancement")
                
                processed_image_aggressive = self._preprocess_image(image, "aggressive")
                page_text_aggressive = pytesseract.image_to_string(processed_image_aggressive)
                
                ocr_data_aggressive = pytesseract.image_to_data(processed_image_aggressive, output_type=pytesseract.Output.DICT)
                confidences_aggressive = [int(conf) for conf in ocr_data_aggressive['conf'] if int(conf) > 0]
                confidence_aggressive = sum(confidences_aggressive) / len(confidences_aggressive) / 100.0 if confidences_aggressive else 0.0
                
                # Use better result
                if confidence_aggressive > confidence or len(page_text_aggressive.strip()) > len(page_text.strip()):
                    return page_text_aggressive, confidence_aggressive
            
            return page_text, confidence
            
        except Exception as e:
            self.logger.warning(f"Page {page_num} OCR failed: {e}")
            return "", 0.0
    
    def _reprocess_low_quality_pages(self, file_path: str, text_content: List[str], 
                                   confidences: List[float], low_quality_pages: List[int]) -> Tuple[List[str], List[float]]:
        """Re-process pages with low OCR quality using enhanced methods."""
        try:
            pdf_document = fitz.open(file_path)
            
            for page_num in low_quality_pages:
                if page_num < len(text_content):
                    page = pdf_document.load_page(page_num)
                    
                    # Try higher resolution
                    mat = fitz.Matrix(3, 3)  # Higher zoom
                    pix = page.get_pixmap(matrix=mat)
                    img_data = pix.tobytes("ppm")
                    image = Image.open(io.BytesIO(img_data))
                    
                    # Apply aggressive preprocessing
                    processed_image = self._preprocess_image(image, "aggressive")
                    
                    # Try different OCR engine modes
                    for psm_mode in [6, 4, 3]:  # Different page segmentation modes
                        try:
                            custom_config = f'--oem 3 --psm {psm_mode}'
                            page_text = pytesseract.image_to_string(processed_image, config=custom_config)
                            
                            if len(page_text.strip()) > len(text_content[page_num].strip()):
                                text_content[page_num] = page_text
                                confidences[page_num] = 0.8  # Assume better quality
                                break
                        except:
                            continue
            
            pdf_document.close()
            return text_content, confidences
            
        except Exception as e:
            self.logger.warning(f"Re-processing failed: {e}")
            return text_content, confidences