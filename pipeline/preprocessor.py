"""
Text preprocessing and clause normalization module.
"""
import re
import spacy
from typing import List, Dict, Any
from models.contract import Clause, ExtractedEntity
from pipeline.risk_assesment import RiskAssessor


class ContractPreprocessor:
    """Handles text preprocessing and entity extraction for contracts."""
    
    def __init__(self, spacy_model: str = "en_core_web_sm"):
        """Initialize preprocessor with spaCy model."""
        import logging
        self.logger = logging.getLogger(__name__)
        self.risk_assessor = RiskAssessor()
        
        try:
            self.nlp = spacy.load(spacy_model)
            self._add_legal_patterns()
        except OSError:
            self.nlp = None
            self.logger.warning(f"spaCy model '{spacy_model}' not found. Install with: python -m spacy download {spacy_model}")
            self.logger.warning("Preprocessing will continue with limited functionality")
    
    def preprocess_clauses(self, clauses: List[Clause]) -> List[Clause]:
        """
        Preprocess and normalize contract clauses.
        
        Args:
            clauses: List of raw clauses
            
        Returns:
            List of preprocessed clauses with entities
        """
        processed_clauses = []
        
        for clause in clauses:
            normalized_text = self._normalize_text(clause.text)
            entities = self._extract_entities(normalized_text)
            
            # Enhanced legal analysis
            legal_category = self._classify_legal_category(normalized_text)
            risk_level = self.risk_assessor.assess(normalized_text)
            key_terms = self._extract_key_terms(normalized_text)
            obligations = entities.get('OBLIGATIONS', [])
            conditions = entities.get('CONDITIONS', [])
            
            # Create new clause with updated data
            processed_clause = Clause(
                id=clause.id,
                text=normalized_text,
                clause_type=clause.clause_type,
                section=clause.section,
                subsection=clause.subsection,
                entities=entities,
                embedding=clause.embedding,
                page_number=clause.page_number,
                confidence_score=clause.confidence_score,
                metadata=clause.metadata,
                legal_category=legal_category,
                risk_level=risk_level,
                key_terms=key_terms,
                obligations=obligations,
                conditions=conditions
            )
            
            processed_clauses.append(processed_clause)
        
        return processed_clauses
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text by cleaning and standardizing format."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Standardize quotes
        text = re.sub(r'["""]', '"', text)
        # Replace curly single quotes with straight single quote
        text = re.sub(r"[‘’]", "'", text)
        # Replace curly double quotes with straight double quote
        text = re.sub(r"[“”]", '"', text)        
        # Fix common encoding issues
        text = text.replace('â€™', "'")
        text = text.replace('â€œ', '"')
        text = text.replace('â€\x9d', '"')
        
        # Standardize legal abbreviations
        text = re.sub(r'\b(Inc|Corp|LLC|Ltd)\.?\b', lambda m: m.group(1) + '.', text)
        
        # Normalize section references
        text = re.sub(r'\bSection\s+(\d+(?:\.\d+)*)', r'Section \1', text)
        text = re.sub(r'\bArticle\s+([IVX]+)', r'Article \1', text)
        
        return text
    
    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities using spaCy and custom patterns."""
        entities = {}
        
        if self.nlp:
            doc = self.nlp(text)
            
            # Extract standard entities
            for ent in doc.ents:
                if ent.label_ not in entities:
                    entities[ent.label_] = []
                if ent.text not in entities[ent.label_]:
                    entities[ent.label_].append(ent.text)
        
        # Extract legal-specific entities
        legal_entities = self._extract_legal_entities(text)
        for key, values in legal_entities.items():
            if key not in entities:
                entities[key] = []
            entities[key].extend([v for v in values if v not in entities[key]])
        
        return entities
    
    def _add_legal_patterns(self):
        """Add custom patterns for legal entity recognition."""
        if not self.nlp:
            return
        
        from spacy.matcher import Matcher
        self.matcher = Matcher(self.nlp.vocab)
        
        # Contract parties
        party_patterns = [
            [{"LOWER": {"IN": ["party", "licensor", "licensee", "contractor", "company", "client"]}},
             {"IS_ALPHA": True, "OP": "?"}],
            [{"TEXT": {"REGEX": r"^[A-Z][a-z]+\s+(Inc|Corp|LLC|Ltd)\.?$"}}]
        ]
        self.matcher.add("PARTY", party_patterns)
        
        # Section references
        section_patterns = [
            [{"LOWER": "section"}, {"IS_DIGIT": True}, {"TEXT": ".", "OP": "?"}, {"IS_DIGIT": True, "OP": "?"}],
            [{"LOWER": "article"}, {"TEXT": {"REGEX": r"^[IVX]+$"}}]
        ]
        self.matcher.add("SECTION_REF", section_patterns)
    
    def _extract_legal_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract legal-specific entities using regex patterns."""
        legal_entities = {}
        
        # Effective dates
        date_patterns = [
            r'effective\s+(?:as\s+of\s+)?([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'commencing\s+on\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'\b(\d{1,2}/\d{1,2}/\d{4})\b'
        ]
        
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        
        if dates:
            legal_entities['EFFECTIVE_DATE'] = dates
        
        # Obligations and duties
        obligation_patterns = [
            r'(\w+\s+(?:shall|must|will|agrees?\s+to)\s+[^.]+)',
            r'(\w+\s+(?:is|are)\s+(?:required|obligated)\s+to\s+[^.]+)',
            r'(\w+\s+(?:undertakes?|covenants?)\s+[^.]+)'
        ]
        
        obligations = []
        for pattern in obligation_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            obligations.extend([m.strip() for m in matches])
        
        if obligations:
            legal_entities['OBLIGATIONS'] = obligations
        
        # Conditions and contingencies
        condition_patterns = [
            r'(if\s+[^,]+,\s*[^.]+)',
            r'(provided\s+that\s+[^.]+)',
            r'(subject\s+to\s+[^.]+)',
            r'(unless\s+[^.]+)'
        ]
        
        conditions = []
        for pattern in condition_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            conditions.extend([m.strip() for m in matches])
        
        if conditions:
            legal_entities['CONDITIONS'] = conditions
        
        # Payment terms
        payment_patterns = [
            r'payment\s+(?:shall\s+be\s+)?(?:made\s+)?within\s+(\d+\s+days)',
            r'net\s+(\d+)\s+days',
            r'\$([\d,]+(?:\.\d{2})?)',
            r'(\d+)%\s+(?:interest|penalty)'
        ]
        
        payments = []
        for pattern in payment_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            payments.extend(matches)
        
        if payments:
            legal_entities['PAYMENT_TERMS'] = payments
        
        # Liability and damages
        liability_patterns = [
            r'(liable\s+for\s+[^.]+)',
            r'(damages\s+[^.]+)',
            r'(indemnif[yi]\s+[^.]+)',
            r'(limitation\s+of\s+liability\s+[^.]+)'
        ]
        
        liabilities = []
        for pattern in liability_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            liabilities.extend([m.strip() for m in matches])
        
        if liabilities:
            legal_entities['LIABILITY'] = liabilities
        
        # Governing law
        law_pattern = r'governed\s+by\s+(?:the\s+)?laws?\s+of\s+([A-Za-z\s]+)'
        laws = re.findall(law_pattern, text, re.IGNORECASE)
        if laws:
            legal_entities['GOVERNING_LAW'] = [law.strip() for law in laws]
        
        return legal_entities
    
    def _classify_legal_category(self, text: str) -> str:
        """Classify clause into granular legal categories."""
        categories = {
            # Payment & Financial
            'payment_terms': ['payment', 'pay', 'remuneration', 'compensation', 'fee', 'salary'],
            'payment_schedule': ['installment', 'monthly', 'quarterly', 'due date', 'payment schedule'],
            'late_payment': ['late payment', 'overdue', 'penalty', 'interest', 'default interest'],
            'invoice_billing': ['invoice', 'billing', 'statement', 'receipt'],
            
            # Contract Lifecycle
            'contract_formation': ['effective date', 'commencement', 'execution', 'signing'],
            'contract_duration': ['term', 'duration', 'period', 'validity'],
            'renewal_extension': ['renewal', 'extension', 'auto-renew', 'rollover'],
            'termination_general': ['terminate', 'termination', 'end', 'conclude'],
            'termination_cause': ['breach', 'default', 'violation', 'material breach'],
            'termination_convenience': ['convenience', 'without cause', 'at will'],
            
            # Risk & Liability
            'liability_general': ['liable', 'liability', 'responsible'],
            'liability_limitation': ['limitation of liability', 'cap', 'maximum liability'],
            'indemnification': ['indemnify', 'indemnification', 'hold harmless'],
            'insurance': ['insurance', 'coverage', 'policy', 'insure'],
            'damages': ['damages', 'loss', 'harm', 'injury', 'consequential'],
            
            # Intellectual Property
            'ip_ownership': ['ownership', 'title', 'proprietary', 'belong'],
            'ip_license': ['license', 'grant', 'permit', 'authorize'],
            'copyright': ['copyright', 'author', 'work', 'derivative'],
            'trademark': ['trademark', 'service mark', 'brand', 'logo'],
            'patent': ['patent', 'invention', 'patentable'],
            'trade_secrets': ['trade secret', 'confidential information', 'know-how'],
            
            # Confidentiality
            'confidentiality_general': ['confidential', 'confidentiality', 'non-disclosure'],
            'data_protection': ['data protection', 'privacy', 'personal data', 'gdpr'],
            'non_compete': ['non-compete', 'competition', 'restraint'],
            'non_solicitation': ['non-solicitation', 'solicit', 'employee', 'customer'],
            
            # Performance
            'performance_standards': ['performance', 'standard', 'quality', 'specification'],
            'delivery_terms': ['delivery', 'shipment', 'transport', 'logistics'],
            'acceptance_testing': ['acceptance', 'testing', 'inspection', 'approval'],
            'service_levels': ['service level', 'sla', 'uptime', 'availability'],
            
            # Dispute Resolution
            'dispute_general': ['dispute', 'disagreement', 'conflict'],
            'arbitration': ['arbitration', 'arbitrator', 'arbitral'],
            'mediation': ['mediation', 'mediator', 'mediate'],
            'litigation': ['litigation', 'court', 'lawsuit', 'legal action'],
            'jurisdiction_venue': ['jurisdiction', 'venue', 'forum', 'competent court'],
            
            # Legal & Compliance
            'governing_law': ['governing law', 'applicable law', 'laws of', 'governed by'],
            'regulatory_compliance': ['compliance', 'regulation', 'regulatory', 'statute'],
            'force_majeure': ['force majeure', 'act of nature', 'unforeseeable'],
            'severability': ['severability', 'severable', 'invalid', 'unenforceable'],
            
            # Assignment & Transfer
            'assignment_general': ['assign', 'assignment', 'transfer', 'delegate'],
            'assignment_restriction': ['not assign', 'no assignment', 'consent required'],
            'succession': ['succession', 'successor', 'heir', 'estate'],
            
            # Modification
            'amendment': ['amend', 'amendment', 'modify', 'modification'],
            'waiver': ['waiver', 'waive', 'relinquish', 'forego'],
            'entire_agreement': ['entire agreement', 'complete agreement', 'supersede'],
            
            # Warranties
            'warranty_general': ['warranty', 'warrant', 'guarantee', 'assure'],
            'warranty_disclaimer': ['disclaim', 'as is', 'no warranty'],
            'representations': ['represent', 'representation', 'state', 'affirm'],
        }
        
        text_lower = text.lower()
        category_scores = {}
        
        # Score categories based on keyword matches
        for category, keywords in categories.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    # Weight longer phrases more heavily
                    weight = len(keyword.split()) * 2
                    score += weight
            if score > 0:
                category_scores[category] = score
        
        if not category_scores:
            return 'general'
        
        # Return highest scoring category
        best_category = max(category_scores.items(), key=lambda x: x[1])[0]
        return best_category if category_scores[best_category] >= 2 else 'general'
    

    
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
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences with legal document awareness."""
        if not text:
            return []
        
        if self.nlp:
            doc = self.nlp(text)
            return [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        
        # Fallback regex-based sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        return [s.strip() for s in sentences if s.strip()]
