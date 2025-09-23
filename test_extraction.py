#!/usr/bin/env python3
"""
Quick test to see what's being extracted from contracts.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.ocr_extractor import OCRExtractor
from pipeline.layout_parser import LayoutParser

def test_extraction(file_path):
    """Test what gets extracted from a contract."""
    print(f"Testing extraction from: {file_path}")
    
    # Test OCR extraction
    print("\n=== OCR EXTRACTION ===")
    try:
        extractor = OCRExtractor()
        raw_text, metadata = extractor.extract_text(file_path)
        print(f"Raw text length: {len(raw_text)}")
        print(f"First 500 chars: {raw_text[:500]}")
        print(f"OCR method: {metadata.ocr_method}")
        print(f"Confidence: {metadata.confidence_score}")
    except Exception as e:
        print(f"OCR extraction failed: {e}")
        return
    
    # Test layout parsing
    print("\n=== LAYOUT PARSING ===")
    try:
        parser = LayoutParser(use_layoutlm=False)
        contract = parser.parse_structure(raw_text, metadata)
        print(f"Sections found: {len(contract.sections)}")
        print(f"Total clauses: {len(contract.clauses)}")
        
        if contract.clauses:
            print(f"First clause text: {contract.clauses[0].text[:200]}")
        else:
            print("No clauses extracted!")
            
    except Exception as e:
        print(f"Layout parsing failed: {e}")

if __name__ == "__main__":
    # Test with a sample file
    test_file = "uploads/sample.pdf"  # Replace with actual file path
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    
    if os.path.exists(test_file):
        test_extraction(test_file)
    else:
        print(f"File not found: {test_file}")
        print("Usage: python test_extraction.py <path_to_pdf>")