"""
Layout and semantic parsing module for contract structure analysis.
Optimized for legal documents with LayoutLMv3 integration.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
import re
from dataclasses import dataclass
import spacy
try:
    from transformers import (
        LayoutLMv3ForTokenClassification, 
        LayoutLMv3Processor,
        AutoTokenizer
    )
    from PIL import Image
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    # Mock classes for deployment
    class LayoutLMv3ForTokenClassification:
        def __init__(self, *args, **kwargs): pass
        @classmethod
        def from_pretrained(cls, *args, **kwargs): return cls()
        def to(self, device): return self
        def eval(self): return self
    
    class LayoutLMv3Processor:
        def __init__(self, *args, **kwargs): pass
        @classmethod
        def from_pretrained(cls, *args, **kwargs): return cls()
        def __call__(self, *args, **kwargs): return {"input_ids": [[0]]}
    
    class AutoTokenizer:
        @staticmethod
        def from_pretrained(*args, **kwargs): return None
        def convert_ids_to_tokens(self, ids): return ["[UNK]"] * len(ids)
    
    try:
        from PIL import Image
    except ImportError:
        Image = None
    
    class torch:
        class device:
            def __init__(self, name): pass
        @staticmethod
        def cuda_is_available(): return False
        class no_grad:
            def __enter__(self): return self
            def __exit__(self, *args): pass
        class nn:
            class functional:
                @staticmethod
                def softmax(x, dim): return x
    
    TRANSFORMERS_AVAILABLE = False
import numpy as np
from models.contract import ProcessedContract, ContractSection, Clause
from pipeline.risk_assesment import RiskAssessor


@dataclass
class ClausePattern:
    """Legal clause pattern definitions."""
    name: str
    pattern: re.Pattern
    priority: int
    clause_type: str


class LayoutParser:
    """
    Advanced layout parser with LayoutLMv3 integration for legal documents.
    Optimized for contract structure analysis and clause extraction.
    """

    def __init__(self, use_layoutlm: bool = True, model_name: str = "microsoft/layoutlmv3-base"):
        """Initialize enhanced layout parser with LayoutLMv3 integration."""
        self.use_layoutlm = use_layoutlm
        self.model_name = model_name
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.nlp = self._load_spacy_model()
        self.legal_patterns = self._initialize_legal_patterns()
        self.clause_keywords = self._initialize_clause_keywords()
        self.risk_assessor = RiskAssessor()
        
        if use_layoutlm:
            self._load_layoutlm_model()

    def _load_spacy_model(self) -> spacy.Language:
        """Load spaCy model for linguistic analysis."""
        try:
            return spacy.load("en_core_web_sm")
        except OSError:
            self.logger.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            return None

    def _initialize_legal_patterns(self) -> List[ClausePattern]:
        """Initialize legal document patterns for clause detection."""
        patterns = [
            # Standard numbered clauses
            ClausePattern(
                "numbered_clause",
                re.compile(r'^\s*(\d+)\.\s+(.+?)(?=^\s*\d+\.\s|\Z)', re.MULTILINE | re.DOTALL),
                1,
                "numbered"
            ),
            # Sub-numbered clauses (1.1, 1.2, etc.)
            ClausePattern(
                "sub_numbered",
                re.compile(r'^\s*(\d+\.\d+)\s+(.+?)(?=^\s*\d+\.\d+\s|\Z)', re.MULTILINE | re.DOTALL),
                2,
                "sub_numbered"
            ),
            # Lettered clauses (a), (b), etc.
            ClausePattern(
                "lettered",
                re.compile(r'^\s*\(([a-z])\)\s+(.+?)(?=^\s*\([a-z]\)\s|\Z)', re.MULTILINE | re.DOTALL),
                3,
                "lettered"
            ),
            # Roman numeral clauses
            ClausePattern(
                "roman",
                re.compile(r'^\s*([IVXLCDM]+)\.\s+(.+?)(?=^\s*[IVXLCDM]+\.\s|\Z)', re.MULTILINE | re.DOTALL),
                4,
                "roman"
            ),
            # Whereas clauses
            ClausePattern(
                "whereas",
                re.compile(r'\bWHEREAS,?\s+(.+?)(?=\bWHEREAS\b|\bNOW,?\s+THEREFORE\b|\Z)', re.IGNORECASE | re.DOTALL),
                5,
                "recital"
            ),
            # Definitions
            ClausePattern(
                "definition",
                re.compile(r'"([^"]+)"\s+(?:means|shall mean|is defined as)\s+(.+?)(?=\.|;|\n\n)', re.IGNORECASE),
                6,
                "definition"
            ),
            # Standard contract clauses
            ClausePattern(
                "termination",
                re.compile(r'((?:Termination|Term)\s+[^.]*\.(?:[^.]*\.)*)', re.IGNORECASE),
                7,
                "termination"
            ),
        ]
        return patterns

    def _initialize_clause_keywords(self) -> Dict[str, List[str]]:
        """Initialize keywords for clause type classification."""
        return {
            "payment": ["payment", "compensation", "remuneration", "fee", "salary", "invoice"],
            "termination": ["terminate", "termination", "expire", "expiry", "end", "conclude"],
            "liability": ["liable", "liability", "responsible", "responsibility", "damages", "loss"],
            "confidentiality": ["confidential", "confidentiality", "non-disclosure", "proprietary", "trade secret"],
            "intellectual_property": ["copyright", "trademark", "patent", "intellectual property", "ip", "proprietary"],
            "dispute_resolution": ["dispute", "arbitration", "mediation", "litigation", "court", "jurisdiction"],
            "force_majeure": ["force majeure", "act of god", "unforeseeable", "beyond control"],
            "governing_law": ["governing law", "jurisdiction", "applicable law", "laws of"],
            "assignment": ["assign", "assignment", "transfer", "delegate", "succession"],
            "amendment": ["amend", "amendment", "modify", "modification", "change", "alter"],
        }

    def parse_structure(self, raw_text: str, metadata: Any, document_image: Optional[Image.Image] = None) -> ProcessedContract:
        """
        Parse document structure with enhanced legal clause extraction.

        Args:
            raw_text: Raw extracted text
            metadata: Document metadata
            document_image: Optional PIL Image for LayoutLMv3 processing

        Returns:
            Structured contract with enhanced sections and clauses
        """
        # Enhanced section extraction
        sections = self._extract_sections_enhanced(raw_text)
        
        # Process with LayoutLMv3 if available
        if self.use_layoutlm and document_image:
            layout_analysis = self._analyze_with_layoutlm(raw_text, document_image)
            sections = self._merge_layout_analysis(sections, layout_analysis)

        # Enhanced clause extraction for each section
        all_clauses: List[Clause] = []
        for section in sections:
            clauses = self._extract_clauses_enhanced(section.text, section.id)
            section.clauses = clauses
            # Update section flags based on clauses
            section.contains_obligations = any(clause.obligations for clause in clauses)
            section.contains_conditions = any(clause.conditions for clause in clauses)
            all_clauses.extend(clauses)

        # Post-process and classify clauses
        all_clauses = self._classify_clauses(all_clauses)
        all_clauses = self._merge_related_clauses(all_clauses)

        return ProcessedContract(
            metadata=metadata,
            sections=sections,
            clauses=all_clauses
        )

    def _extract_sections_enhanced(self, text: str) -> List[ContractSection]:
        """Enhanced section extraction with legal document patterns."""
        sections: List[ContractSection] = []
        
        # Enhanced heading patterns for legal documents
        legal_heading_patterns = [
            # Article/Section patterns
            re.compile(r'^(ARTICLE|SECTION)\s+([IVXLCDM]+|\d+)[\.\s]+(.+?)$', re.MULTILINE | re.IGNORECASE),
            # Standard numbered headings
            re.compile(r'^\s*(\d+)\.?\s+([A-Z][A-Za-z\s]+)\.?\s*$', re.MULTILINE),
            # Lettered headings
            re.compile(r'^\s*([A-Z])\.?\s+([A-Z][A-Za-z\s]+)\.?\s*$', re.MULTILINE),
            # All caps headings
            re.compile(r'^([A-Z][A-Z\s]{3,})\.?\s*$', re.MULTILINE),
            # Recital sections
            re.compile(r'^(RECITALS?|BACKGROUND|PREAMBLE)\s*$', re.MULTILINE | re.IGNORECASE),
        ]

        # Find all potential section breaks
        section_breaks = []
        for pattern in legal_heading_patterns:
            for match in pattern.finditer(text):
                section_breaks.append({
                    'start': match.start(),
                    'end': match.end(),
                    'title': match.group(0).strip(),
                    'pattern_type': pattern.pattern
                })

        # Sort by position and create sections
        section_breaks.sort(key=lambda x: x['start'])
        
        if not section_breaks:
            # Intelligent fallback: split by paragraph patterns
            return self._fallback_section_extraction(text)

        # Create hierarchical sections with semantic grouping
        sections = self._create_hierarchical_sections(text, section_breaks)
        
        # Apply semantic grouping
        sections = self._apply_semantic_grouping(sections)
        
        return sections

    def _extract_clauses_enhanced(self, text: str, section_id: str) -> List[Clause]:
        """Enhanced clause extraction using multiple strategies."""
        clauses: List[Clause] = []
        clause_id = 1

        # Strategy 1: Pattern-based extraction
        pattern_clauses = self._extract_by_patterns(text)
        
        # Strategy 2: Sentence-based extraction with legal awareness
        sentence_clauses = self._extract_by_sentences(text)
        
        # Strategy 3: Paragraph-based extraction
        paragraph_clauses = self._extract_by_paragraphs(text)

        # Merge and deduplicate clauses
        all_candidate_clauses = pattern_clauses + sentence_clauses + paragraph_clauses
        merged_clauses = self._merge_duplicate_clauses(all_candidate_clauses)

        # Create final clause objects
        for clause_text in merged_clauses:
            if self._is_valid_clause(clause_text):
                clause = Clause(
                    id=f"{section_id}_C{clause_id}",
                    text=self._clean_clause_text(clause_text),
                    legal_category=self._determine_clause_type(clause_text),
                    risk_level=self.risk_assessor.assess(clause_text),
                    key_terms=self._extract_key_terms(clause_text),
                    obligations=self._extract_obligations(clause_text),
                    conditions=self._extract_conditions(clause_text),
                    metadata={
                        "length": len(clause_text),
                        "source": "enhanced_extraction",
                        "section_id": section_id,
                        "word_count": len(clause_text.split()),
                        "sentence_count": len(re.split(r'[.!?]+', clause_text))
                    }
                )
                clauses.append(clause)
                clause_id += 1

        return clauses

    def _extract_by_patterns(self, text: str) -> List[str]:
        """Extract clauses using legal document patterns."""
        clauses = []
        
        for pattern_def in self.legal_patterns:
            matches = pattern_def.pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    clause_text = ' '.join(str(m) for m in match if m)
                else:
                    clause_text = str(match)
                
                if len(clause_text.strip()) > 10:  # Minimum clause length
                    clauses.append(clause_text.strip())
        
        return clauses

    def _extract_by_sentences(self, text: str) -> List[str]:
        """Extract clauses by intelligent sentence grouping."""
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        clauses = []
        current_clause = []
        
        for sent in doc.sents:
            sent_text = sent.text.strip()
            
            # Group sentences that form logical clauses
            if self._is_clause_boundary(sent_text, current_clause):
                if current_clause:
                    clauses.append(' '.join(current_clause))
                current_clause = [sent_text]
            else:
                current_clause.append(sent_text)
        
        # Add final clause
        if current_clause:
            clauses.append(' '.join(current_clause))
        
        return clauses

    def _extract_by_paragraphs(self, text: str) -> List[str]:
        """Extract clauses by paragraph analysis."""
        paragraphs = re.split(r'\n\s*\n', text)
        clauses = []
        
        for para in paragraphs:
            para = para.strip()
            if len(para) > 20 and self._contains_legal_content(para):
                # Split long paragraphs by legal markers
                sub_clauses = re.split(
                    r'(?=\b(?:provided that|provided,|however,|notwithstanding|subject to)\b)',
                    para,
                    flags=re.IGNORECASE
                )
                clauses.extend([sc.strip() for sc in sub_clauses if sc.strip()])
        
        return clauses

    def _is_clause_boundary(self, sentence: str, current_clause: List[str]) -> bool:
        """Determine if a sentence starts a new clause."""
        boundary_indicators = [
            r'^\s*\d+\.',  # Numbered clauses
            r'^\s*\([a-z]\)',  # Lettered clauses
            r'^\s*[IVXLCDM]+\.',  # Roman numerals
            r'^\s*(?:WHEREAS|NOW THEREFORE|PROVIDED|SUBJECT TO)',  # Legal terms
        ]
        
        for pattern in boundary_indicators:
            if re.match(pattern, sentence, re.IGNORECASE):
                return True
        
        return len(current_clause) > 3  # Max sentences per clause

    def _contains_legal_content(self, text: str) -> bool:
        """Check if text contains legal content indicators."""
        legal_indicators = [
            r'\b(?:shall|will|must|may not|agree|covenant|warrant|represent)\b',
            r'\b(?:party|parties|agreement|contract|terms|conditions)\b',
            r'\b(?:liable|liability|damages|breach|violation|default)\b',
            r'\b(?:terminate|termination|expire|effective|binding)\b',
        ]
        
        for pattern in legal_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def _is_valid_clause(self, text: str) -> bool:
        """Validate if extracted text constitutes a valid legal clause."""
        text = text.strip()
        
        # Minimum length check
        if len(text) < 15 or len(text.split()) < 3:
            return False
        
        # Must contain at least one verb or legal term
        has_verb = bool(re.search(r'\b(?:is|are|shall|will|must|may|can|should)\b', text, re.IGNORECASE))
        has_legal_term = self._contains_legal_content(text)
        
        return has_verb or has_legal_term

    def _clean_clause_text(self, text: str) -> str:
        """Clean and normalize clause text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading numbering if it's just formatting
        text = re.sub(r'^\s*[\d\.\(\)a-z]+\s*', '', text, flags=re.IGNORECASE)
        
        # Ensure proper sentence ending
        text = text.strip()
        if text and not text[-1] in '.!?':
            text += '.'
            
        return text

    def _classify_clauses(self, clauses: List[Clause]) -> List[Clause]:
        """Classify clauses by legal type using keyword matching."""
        for clause in clauses:
            if not clause.legal_category:
                clause.legal_category = self._determine_clause_type(clause.text)
            clause.metadata["legal_keywords"] = self._extract_legal_keywords(clause.text)
        
        return clauses

    def _determine_clause_type(self, text: str) -> str:
        """Determine the legal type of a clause."""
        text_lower = text.lower()
        type_scores = {}
        
        for clause_type, keywords in self.clause_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                type_scores[clause_type] = score
        
        if type_scores:
            return max(type_scores.items(), key=lambda x: x[1])[0]
        
        return "general"

    def _extract_legal_keywords(self, text: str) -> List[str]:
        """Extract legal keywords from clause text."""
        all_keywords = []
        for keywords in self.clause_keywords.values():
            all_keywords.extend(keywords)
        
        found_keywords = []
        text_lower = text.lower()
        
        for keyword in all_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword)
        
        return found_keywords

    def _merge_duplicate_clauses(self, clauses: List[str]) -> List[str]:
        """Remove duplicate and highly similar clauses with improved logic."""
        unique_clauses = []
        
        for clause in clauses:
            clause_clean = re.sub(r'\W+', '', clause.lower())
            
            # Skip very short clauses
            if len(clause_clean) < 20:
                continue
                
            is_duplicate = False
            for existing in unique_clauses:
                existing_clean = re.sub(r'\W+', '', existing.lower())
                
                # More conservative similarity check
                similarity = len(set(clause_clean) & set(existing_clean)) / max(len(clause_clean), len(existing_clean))
                
                # Only merge if very similar AND one is a clear substring
                if (similarity > 0.95 and 
                    (len(clause_clean) < len(existing_clean) * 0.6 or 
                    len(existing_clean) < len(clause_clean) * 0.6)):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_clauses.append(clause)
        
        return unique_clauses

    def _merge_related_clauses(self, clauses: List[Clause]) -> List[Clause]:
        """Merge clauses that should be combined based on legal logic."""
        # This is a simplified version - in practice, this would be more sophisticated
        merged = []
        i = 0
        
        while i < len(clauses):
            current = clauses[i]
            
            # Check if next clause continues this one
            if (i + 1 < len(clauses) and 
                self._should_merge_clauses(current, clauses[i + 1])):
                
                # Merge the clauses
                merged_text = current.text + " " + clauses[i + 1].text
                merged_clause = Clause(
                    id=current.id,
                    text=merged_text,
                    metadata={
                        **current.metadata,
                        "merged": True,
                        "merged_with": clauses[i + 1].id
                    }
                )
                merged.append(merged_clause)
                i += 2  # Skip next clause as it's merged
            else:
                merged.append(current)
                i += 1
        
        return merged

    def _should_merge_clauses(self, clause1: Clause, clause2: Clause) -> bool:
        """Determine if two clauses should be merged."""
        # Don't merge if either clause is too long
        if len(clause1.text) > 500 or len(clause2.text) > 500:
            return False
        
        # Check for continuation patterns
        continuation_patterns = [
            r'\bprovided that\b',
            r'\bhowever\b',
            r'\bnotwithstanding\b',
            r'\bsubject to\b',
            r'\bunless\b',
            r'\bexcept\b'
        ]
        
        for pattern in continuation_patterns:
            if re.search(pattern, clause2.text, re.IGNORECASE):
                return True
        
        return False

    # LayoutLMv3 Integration
    def _load_layoutlm_model(self):
        """Load and initialize LayoutLMv3 model for semantic parsing."""
        try:
            self.processor = LayoutLMv3Processor.from_pretrained(self.model_name)
            self.model = LayoutLMv3ForTokenClassification.from_pretrained(self.model_name)
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            # Set device
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.model.to(self.device)
            self.model.eval()
            
            self.logger.info(f"LayoutLMv3 model loaded successfully on {self.device}")
        except Exception as e:
            self.logger.error(f"Failed to load LayoutLMv3 model: {e}")
            self.use_layoutlm = False

    def _analyze_with_layoutlm(self, text: str, image: Image.Image) -> Dict[str, Any]:
        """Use LayoutLMv3 for advanced semantic analysis."""
        if not hasattr(self, 'processor'):
            return {"status": "model not loaded"}
        
        try:
            # Prepare inputs
            encoding = self.processor(image, text, return_tensors="pt")
            encoding = {k: v.to(self.device) for k, v in encoding.items()}
            
            # Run inference
            with torch.no_grad():
                outputs = self.model(**encoding)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                predicted_class_ids = predictions.argmax(dim=-1).squeeze().tolist()
            
            # Process results
            tokens = self.tokenizer.convert_ids_to_tokens(encoding["input_ids"].squeeze().tolist())
            
            # Group tokens by predicted labels
            layout_elements = self._group_layout_elements(tokens, predicted_class_ids)
            
            return {
                "status": "success",
                "layout_elements": layout_elements,
                "confidence_scores": predictions.max(dim=-1)[0].squeeze().tolist()
            }
            
        except Exception as e:
            self.logger.error(f"LayoutLMv3 analysis failed: {e}")
            return {"status": "error", "error": str(e)}

    def _group_layout_elements(self, tokens: List[str], predictions: List[int]) -> Dict[str, List[str]]:
        """Group tokens by their predicted layout element types."""
        # Define label mapping (this would come from your specific model)
        label_map = {
            0: "other",
            1: "title",
            2: "text", 
            3: "header",
            4: "list",
            5: "table",
            6: "figure"
        }
        
        grouped = {}
        current_element = None
        current_tokens = []
        
        for token, pred in zip(tokens, predictions):
            label = label_map.get(pred, "other")
            
            if label != current_element:
                if current_element and current_tokens:
                    if current_element not in grouped:
                        grouped[current_element] = []
                    grouped[current_element].append(' '.join(current_tokens))
                
                current_element = label
                current_tokens = [token]
            else:
                current_tokens.append(token)
        
        # Add final group
        if current_element and current_tokens:
            if current_element not in grouped:
                grouped[current_element] = []
            grouped[current_element].append(' '.join(current_tokens))
        
        return grouped

    def _merge_layout_analysis(self, sections: List[ContractSection], layout_analysis: Dict[str, Any]) -> List[ContractSection]:
        """Merge LayoutLMv3 analysis results with extracted sections."""
        if layout_analysis.get("status") != "success":
            return sections
        
        layout_elements = layout_analysis.get("layout_elements", {})
        
        # Enhance sections with layout information
        for section in sections:
            section.metadata = getattr(section, 'metadata', {})
            
            # Add layout element information
            for element_type, elements in layout_elements.items():
                matching_elements = []
                for element_text in elements:
                    if self._text_similarity(section.text, element_text) > 0.5:
                        matching_elements.append(element_text)
                
                if matching_elements:
                    section.metadata[f"layout_{element_type}"] = matching_elements
        
        return sections

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity score."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0

    # Table and heading detection enhancements
    def _detect_headings(self, text: str) -> List[Dict[str, Any]]:
        """Enhanced heading detection for legal documents."""
        headings = []
        
        # Legal document heading patterns
        patterns = [
            (r'^\s*(ARTICLE|SECTION)\s+([IVXLCDM]+|\d+)[\.\s]+(.+?)$', "article"),
            (r'^\s*(\d+)\.?\s+([A-Z][A-Za-z\s]+)\.?\s*$', "numbered"),
            (r'^\s*([A-Z])\.?\s+([A-Z][A-Za-z\s]+)\.?\s*$', "lettered"),
            (r'^([A-Z][A-Z\s]{3,})\.?\s*$', "title"),
        ]
        
        for pattern, heading_type in patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                headings.append({
                    "text": match.group(0).strip(),
                    "position": match.start(),
                    "type": heading_type,
                    "level": self._determine_heading_level(match.group(0))
                })
        
        return sorted(headings, key=lambda x: x["position"])

    def _determine_heading_level(self, heading: str) -> int:
        """Determine hierarchical level of heading."""
        if re.match(r'^\s*(ARTICLE|SECTION)', heading, re.IGNORECASE):
            return 1
        elif re.match(r'^\s*\d+\.', heading):
            return 2
        elif re.match(r'^\s*[A-Z]\.', heading):
            return 3
        elif heading.isupper():
            return 1
        else:
            return 4

    def _extract_tables(self, text: str) -> List[Dict[str, Any]]:
        """Enhanced table extraction for legal documents."""
        tables = []
        
        # Pattern for table-like structures
        table_patterns = [
            # Aligned columns with multiple spaces or tabs
            r'(\S+(?:\s{2,}|\t+)\S+(?:\s{2,}|\t+)\S+.*\n)+',
            # Pipe-separated values
            r'(\|[^|\n]*\|.*\n)+',
            # Multiple lines with consistent formatting
            r'(^\s*\w+:\s*\S.*\n){3,}'
        ]
        
        for i, pattern in enumerate(table_patterns):
            for match in re.finditer(pattern, text, re.MULTILINE):
                table_text = match.group(0).strip()
                if len(table_text) > 50:  # Minimum table size
                    tables.append({
                        "id": f"table_{len(tables)+1}",
                        "text": table_text,
                        "position": match.start(),
                        "pattern_type": i,
                        "rows": len(table_text.split('\n')),
                        "estimated_columns": self._estimate_columns(table_text)
                    })
        
        return tables

    def _estimate_columns(self, table_text: str) -> int:
        """Estimate number of columns in table text."""
        lines = table_text.split('\n')
        if not lines:
            return 0
        
        # Count separators in first non-empty line
        first_line = next((line for line in lines if line.strip()), "")
        
        # Count different types of separators
        pipe_count = first_line.count('|')
        tab_count = first_line.count('\t')
        multi_space_count = len(re.findall(r'\s{2,}', first_line))
        
        return max(pipe_count - 1, tab_count, multi_space_count) if any([pipe_count, tab_count, multi_space_count]) else 1
    

    
    def _extract_key_terms(self, text: str) -> List[str]:
        """Extract key legal terms from clause."""
        patterns = [
            r'\$[\d,]+(?:\.\d{2})?',  # Money
            r'\d+\s+(?:days?|months?|years?)',  # Time periods
            r'\d+%'  # Percentages
        ]
        
        terms = []
        for pattern in patterns:
            terms.extend(re.findall(pattern, text))
        return list(set(terms))
    
    def _extract_obligations(self, text: str) -> List[str]:
        """Extract obligations from clause text."""
        patterns = [
            r'(\w+\s+(?:shall|must|will|agrees?\s+to)\s+[^.]+)',
            r'(\w+\s+(?:is|are)\s+(?:required|obligated)\s+to\s+[^.]+)'
        ]
        
        obligations = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            obligations.extend([m.strip() for m in matches])
        return obligations
    
    def _extract_conditions(self, text: str) -> List[str]:
        """Extract conditions from clause text."""
        patterns = [
            r'(if\s+[^,]+,\s*[^.]+)',
            r'(provided\s+that\s+[^.]+)',
            r'(subject\s+to\s+[^.]+)',
            r'(unless\s+[^.]+)'
        ]
        
        conditions = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            conditions.extend([m.strip() for m in matches])
        return conditions
    
    def _classify_section_type(self, title: str) -> str:
        """Classify section type based on title."""
        title_lower = title.lower()
        if 'definition' in title_lower:
            return 'definitions'
        elif 'term' in title_lower:
            return 'terms'
        elif 'obligation' in title_lower or 'duties' in title_lower:
            return 'obligations'
        elif 'payment' in title_lower:
            return 'payment'
        elif 'termination' in title_lower:
            return 'termination'
        return 'general'
    
    def _calculate_section_importance(self, text: str) -> float:
        """Calculate comprehensive importance score for section."""
        # Critical importance keywords (high weight)
        critical_keywords = {
            'liability': 10, 'indemnification': 10, 'damages': 8,
            'termination': 9, 'breach': 8, 'default': 8,
            'payment': 7, 'compensation': 6, 'fee': 5,
            'confidential': 7, 'proprietary': 6, 'trade secret': 8,
            'intellectual property': 9, 'copyright': 6, 'patent': 6,
            'governing law': 5, 'jurisdiction': 5, 'dispute': 6,
            'force majeure': 4, 'assignment': 4, 'amendment': 3
        }
        
        # Moderate importance keywords (medium weight)
        moderate_keywords = {
            'performance': 4, 'delivery': 4, 'service': 3,
            'warranty': 5, 'representation': 4, 'compliance': 5,
            'insurance': 4, 'notice': 2, 'consent': 3,
            'approval': 3, 'standard': 2, 'requirement': 3
        }
        
        text_lower = text.lower()
        total_score = 0
        max_possible_score = 0
        
        # Calculate weighted score
        for keyword, weight in critical_keywords.items():
            max_possible_score += weight
            if keyword in text_lower:
                # Count occurrences for repeated emphasis
                occurrences = text_lower.count(keyword)
                total_score += weight * min(occurrences, 3)  # Cap at 3x weight
        
        for keyword, weight in moderate_keywords.items():
            max_possible_score += weight
            if keyword in text_lower:
                occurrences = text_lower.count(keyword)
                total_score += weight * min(occurrences, 2)  # Cap at 2x weight
        
        # Consider section length (longer sections might be more important)
        length_factor = min(len(text) / 1000, 2.0)  # Cap at 2x multiplier
        total_score *= (1 + length_factor * 0.1)  # Small boost for length
        
        # Normalize to 0-1 scale
        normalized_score = min(total_score / (max_possible_score * 0.3), 1.0)
        
        return normalized_score
    
    def _fallback_section_extraction(self, text: str) -> List[ContractSection]:
        """Intelligent fallback when no clear headings are found."""
        # Split by double line breaks and analyze content
        paragraphs = re.split(r'\n\s*\n', text)
        sections = []
        current_section_text = ""
        section_count = 1
        
        for para in paragraphs:
            para = para.strip()
            if len(para) < 20:  # Skip very short paragraphs
                continue
            
            # Check if paragraph looks like a section start
            if self._is_section_start(para):
                # Save previous section if exists
                if current_section_text:
                    section = ContractSection(
                        id=f"S{section_count}",
                        title=f"Section {section_count}",
                        text=current_section_text.strip(),
                        clauses=[],
                        section_type=self._classify_section_type(current_section_text[:100]),
                        importance_score=self._calculate_section_importance(current_section_text)
                    )
                    sections.append(section)
                    section_count += 1
                
                current_section_text = para
            else:
                current_section_text += "\n\n" + para
        
        # Add final section
        if current_section_text:
            section = ContractSection(
                id=f"S{section_count}",
                title=f"Section {section_count}",
                text=current_section_text.strip(),
                clauses=[],
                section_type=self._classify_section_type(current_section_text[:100]),
                importance_score=self._calculate_section_importance(current_section_text)
            )
            sections.append(section)
        
        return sections if sections else [ContractSection(id="S1", title="Complete Document", text=text, clauses=[])]
    
    def _is_section_start(self, paragraph: str) -> bool:
        """Determine if a paragraph likely starts a new section."""
        # Check for section indicators
        section_indicators = [
            r'^\d+\.',  # Numbered
            r'^[A-Z]\.',  # Lettered
            r'^[IVXLCDM]+\.',  # Roman numerals
            r'^(WHEREAS|NOW THEREFORE|PROVIDED|SUBJECT TO)',  # Legal terms
            r'^[A-Z][A-Z\s]{5,}$',  # All caps titles
        ]
        
        for pattern in section_indicators:
            if re.match(pattern, paragraph.strip(), re.IGNORECASE):
                return True
        
        # Check if it's a short paragraph that looks like a title
        if len(paragraph) < 100 and paragraph.isupper():
            return True
        
        return False
    
    def _create_hierarchical_sections(self, text: str, section_breaks: List[Dict]) -> List[ContractSection]:
        """Create sections with proper hierarchical relationships."""
        sections = []
        
        for i, break_info in enumerate(section_breaks):
            start = break_info['start']
            end = section_breaks[i + 1]['start'] if i + 1 < len(section_breaks) else len(text)
            
            section_text = text[start:end].strip()
            section_id = f"S{i+1}"
            
            # Determine parent section for hierarchy
            parent_id = None
            level = break_info.get('level', 1)
            if level > 1:
                # Find parent section (previous section with lower level)
                for j in range(i-1, -1, -1):
                    if section_breaks[j].get('level', 1) < level:
                        parent_id = f"S{j+1}"
                        break
            
            section = ContractSection(
                id=section_id,
                title=break_info['title'],
                text=section_text,
                clauses=[],
                level=level,
                section_type=self._classify_section_type(break_info['title']),
                importance_score=self._calculate_section_importance(section_text)
            )
            
            # Add hierarchy metadata
            if not section.metadata:
                section.metadata = {}
            section.metadata['parent_section'] = parent_id
            section.metadata['hierarchy_level'] = level
            
            sections.append(section)
        
        return sections
    
    def _apply_semantic_grouping(self, sections: List[ContractSection]) -> List[ContractSection]:
        """Apply semantic grouping to related sections."""
        # Define semantic groups
        semantic_groups = {
            'contract_formation': ['recital', 'background', 'preamble', 'whereas', 'parties'],
            'definitions': ['definition', 'interpretation', 'meaning'],
            'core_terms': ['scope', 'work', 'service', 'deliverable', 'performance'],
            'financial': ['payment', 'fee', 'cost', 'price', 'compensation', 'invoice'],
            'legal_compliance': ['law', 'regulation', 'compliance', 'jurisdiction', 'governing'],
            'risk_management': ['liability', 'insurance', 'indemnification', 'limitation'],
            'ip_confidentiality': ['intellectual', 'property', 'confidential', 'proprietary', 'trade secret'],
            'contract_management': ['term', 'duration', 'renewal', 'termination', 'amendment'],
            'dispute_resolution': ['dispute', 'arbitration', 'mediation', 'litigation'],
            'miscellaneous': ['general', 'miscellaneous', 'other', 'additional']
        }
        
        # Assign semantic groups to sections
        for section in sections:
            section_title_lower = section.title.lower()
            section_text_lower = section.text[:200].lower()  # First 200 chars
            
            best_group = 'miscellaneous'
            best_score = 0
            
            for group_name, keywords in semantic_groups.items():
                score = 0
                for keyword in keywords:
                    if keyword in section_title_lower:
                        score += 3  # Title matches are weighted more
                    if keyword in section_text_lower:
                        score += 1
                
                if score > best_score:
                    best_score = score
                    best_group = group_name
            
            if not section.metadata:
                section.metadata = {}
            section.metadata['semantic_group'] = best_group
            section.metadata['semantic_score'] = best_score
        
        return sections
