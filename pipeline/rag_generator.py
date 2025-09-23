"""
RAG (Retrieval Augmented Generation) module for contract analysis and generation.
"""
import logging
import time
import re
from typing import List, Dict, Any, Optional
import os

try:
    from google import genai
except ImportError:
    # Mock class for testing when dependencies are not available
    class genai:
        class Client:
            def __init__(self, api_key=None):
                pass
            
            class models:
                @staticmethod
                def generate_content(model, contents):
                    class MockResponse:
                        text = f"Mock response: {contents[:100]}..."
                    return MockResponse()
from models.contract import Clause, ProcessedContract


class ContractRAGGenerator:
    """Handles retrieval augmented generation for contract analysis using Gemini AI."""
    
    def __init__(self):
        """Initialize RAG generator with Gemini AI."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize Gemini client with API key
        from config import settings
        api_key = settings.GEMINI_API_KEY
        if api_key:
            try:
                self.client = genai.Client(api_key=api_key)
            except Exception as e:
                self.logger.warning(f"Failed to initialize Gemini client: {e}")
                self.client = None
        else:
            self.logger.warning("GEMINI_API_KEY not found, using mock client")
            self.client = None
        
        # Initialize embedder
        from pipeline.embedder import ContractEmbedder
        self.embedder = ContractEmbedder(
            supabase_url=settings.SUPABASE_URL,
            supabase_key=settings.SUPABASE_KEY
        )
    
    def generate_summary(self, contract: ProcessedContract) -> str:
        """
        Generate plain-language summary of contract.
        
        Args:
            contract: Processed contract object
            
        Returns:
            Human-readable contract summary
        """
        # Extract key clauses for summary
        key_clauses = self._identify_key_clauses(contract)
        
        # Create prompt for LLM
        prompt = self._create_summary_prompt(key_clauses, contract.metadata)
        
        # Generate summary using Gemini
        summary = self._generate_with_llm(prompt)
        
        return summary
    
    def analyze_risks(self, contract: ProcessedContract) -> List[Dict[str, Any]]:
        """
        Analyze contract for potential risks and issues.
        
        Args:
            contract: Processed contract object
            
        Returns:
            List of identified risks with severity levels
        """
        risks = []
        
        # Define risk patterns with severity levels
        risk_patterns = {
            'high_liability': {
                'keywords': ['unlimited liability', 'consequential damages', 'punitive damages', 'all damages', 'any damages'],
                'severity': 'critical',
                'description': 'Unlimited or excessive liability exposure'
            },
            'payment_risks': {
                'keywords': ['net 90', 'net 120', 'payment on completion', 'no advance payment', 'late payment penalty'],
                'severity': 'high',
                'description': 'Unfavorable payment terms'
            },
            'termination_risks': {
                'keywords': ['terminate at will', 'no notice required', 'immediate termination', 'terminate without cause'],
                'severity': 'high',
                'description': 'Unfavorable termination conditions'
            },
            'ip_risks': {
                'keywords': ['assign all rights', 'work for hire', 'no ownership', 'exclusive license', 'perpetual license'],
                'severity': 'medium',
                'description': 'Intellectual property concerns'
            },
            'confidentiality_risks': {
                'keywords': ['perpetual confidentiality', 'no exceptions', 'broad definition', 'survives termination'],
                'severity': 'medium',
                'description': 'Overly broad confidentiality requirements'
            },
            'force_majeure_risks': {
                'keywords': ['no force majeure', 'limited force majeure', 'acts of god', 'unforeseen circumstances'],
                'severity': 'medium',
                'description': 'Insufficient force majeure protection'
            },
            'governing_law_risks': {
                'keywords': ['foreign jurisdiction', 'unfamiliar law', 'distant venue', 'international arbitration'],
                'severity': 'low',
                'description': 'Unfavorable governing law or jurisdiction'
            },
            'indemnification_risks': {
                'keywords': ['indemnify and hold harmless', 'defend and indemnify', 'third party claims', 'breach of warranty'],
                'severity': 'high',
                'description': 'Broad indemnification obligations'
            },
            'warranty_risks': {
                'keywords': ['no warranties', 'as is', 'disclaim all warranties', 'no representations'],
                'severity': 'medium',
                'description': 'Limited or no warranties provided'
            },
            'renewal_risks': {
                'keywords': ['automatic renewal', 'evergreen', 'no termination right', 'perpetual'],
                'severity': 'medium',
                'description': 'Automatic renewal or perpetual terms'
            }
        }
        
        # Analyze each clause for risks
        for clause in contract.clauses:
            clause_text_lower = clause.text.lower()
            clause_risks = []
            
            for risk_type, risk_info in risk_patterns.items():
                # Check for keyword matches
                keyword_matches = [keyword for keyword in risk_info['keywords'] 
                                 if keyword in clause_text_lower]
                
                if keyword_matches:
                    # Calculate risk score based on number of matches and clause characteristics
                    risk_score = len(keyword_matches) * 2
                    
                    # Additional scoring factors
                    if len(clause.text) > 500:  # Longer clauses often contain more complex terms
                        risk_score += 1
                    
                    if clause.clause_type and clause.clause_type.lower() in ['liability', 'indemnification', 'termination']:
                        risk_score += 2
                    
                    clause_risks.append({
                        'risk_type': risk_type,
                        'severity': risk_info['severity'],
                        'description': risk_info['description'],
                        'matched_keywords': keyword_matches,
                        'risk_score': risk_score,
                        'clause_id': clause.id,
                        'clause_text': clause.text[:300] + "..." if len(clause.text) > 300 else clause.text
                    })
            
            # Add clause-level risks to overall risks
            risks.extend(clause_risks)
        
        # Sort risks by severity and score
        severity_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        risks.sort(key=lambda x: (severity_order.get(x['severity'], 0), x['risk_score']), reverse=True)
        
        # Add overall risk assessment
        if risks:
            critical_count = sum(1 for r in risks if r['severity'] == 'critical')
            high_count = sum(1 for r in risks if r['severity'] == 'high')
            
            overall_risk_level = 'low'
            if critical_count > 0:
                overall_risk_level = 'critical'
            elif high_count >= 3:
                overall_risk_level = 'high'
            elif high_count >= 1 or len(risks) >= 5:
                overall_risk_level = 'medium'
            
            # Add summary risk assessment
            risks.insert(0, {
                'risk_type': 'overall_assessment',
                'severity': overall_risk_level,
                'description': f'Overall contract risk assessment: {overall_risk_level.upper()}',
                'details': {
                    'total_risks': len(risks),
                    'critical_risks': critical_count,
                    'high_risks': high_count,
                    'medium_risks': sum(1 for r in risks if r['severity'] == 'medium'),
                    'low_risks': sum(1 for r in risks if r['severity'] == 'low')
                },
                'recommendations': self._get_risk_recommendations(overall_risk_level, risks)
            })
        
        return risks
    
    def _get_risk_recommendations(self, risk_level: str, risks: List[Dict[str, Any]]) -> List[str]:
        """Generate risk mitigation recommendations based on identified risks."""
        recommendations = []
        
        if risk_level == 'critical':
            recommendations.extend([
                "URGENT: This contract contains critical risks that require immediate legal review",
                "Consider negotiating liability caps and exclusions",
                "Review termination and indemnification clauses carefully"
            ])
        elif risk_level == 'high':
            recommendations.extend([
                "High-risk contract - recommend legal review before signing",
                "Negotiate more favorable payment terms",
                "Add appropriate force majeure protections"
            ])
        elif risk_level == 'medium':
            recommendations.extend([
                "Moderate risk contract - consider minor modifications",
                "Review IP and confidentiality terms",
                "Ensure adequate termination rights"
            ])
        else:
            recommendations.append("Low-risk contract - standard review recommended")
        
        # Add specific recommendations based on risk types found
        risk_types = [r['risk_type'] for r in risks if r['risk_type'] != 'overall_assessment']
        
        if 'payment_risks' in risk_types:
            recommendations.append("Consider negotiating shorter payment terms and advance payments")
        
        if 'ip_risks' in risk_types:
            recommendations.append("Clarify intellectual property ownership and licensing terms")
        
        if 'confidentiality_risks' in risk_types:
            recommendations.append("Add exceptions for publicly available information in confidentiality clauses")
        
        return recommendations
    
    def suggest_redlines(self, contract: ProcessedContract) -> List[Dict[str, Any]]:
        """
        Suggest contract redlines and modifications.
        
        Args:
            contract: Processed contract object
            
        Returns:
            List of suggested modifications with rationale
        """
        redlines = []
        
        # Define redline patterns and suggestions
        redline_patterns = {
            'liability_caps': {
                'pattern': r'(unlimited|all|any)\s+(liability|damages)',
                'suggestion': 'Add liability cap: "Liability shall be limited to the total amount paid under this Agreement"',
                'rationale': 'Unlimited liability exposes the party to excessive financial risk',
                'priority': 'high'
            },
            'payment_terms': {
                'pattern': r'(net\s+90|net\s+120|payment\s+on\s+completion)',
                'suggestion': 'Improve payment terms: "Payment due within 30 days of invoice date"',
                'rationale': 'Shorter payment terms improve cash flow and reduce collection risk',
                'priority': 'medium'
            },
            'termination_notice': {
                'pattern': r'(terminate\s+at\s+will|immediate\s+termination|no\s+notice)',
                'suggestion': 'Add termination notice: "Either party may terminate with 30 days written notice"',
                'rationale': 'Adequate notice period allows for proper transition and planning',
                'priority': 'high'
            },
            'force_majeure': {
                'pattern': r'(no\s+force\s+majeure|limited\s+force\s+majeure)',
                'suggestion': 'Add force majeure clause: "Neither party shall be liable for delays due to circumstances beyond their control"',
                'rationale': 'Force majeure protection is essential for unforeseen circumstances',
                'priority': 'medium'
            },
            'intellectual_property': {
                'pattern': r'(assign\s+all\s+rights|work\s+for\s+hire)',
                'suggestion': 'Clarify IP ownership: "Each party retains ownership of their pre-existing intellectual property"',
                'rationale': 'Clear IP ownership prevents future disputes and protects existing assets',
                'priority': 'high'
            },
            'confidentiality_scope': {
                'pattern': r'(perpetual\s+confidentiality|no\s+exceptions)',
                'suggestion': 'Limit confidentiality scope: "Confidentiality obligations survive for 3 years after termination"',
                'rationale': 'Reasonable time limits prevent indefinite confidentiality obligations',
                'priority': 'medium'
            },
            'governing_law': {
                'pattern': r'(foreign\s+jurisdiction|unfamiliar\s+law)',
                'suggestion': 'Specify familiar jurisdiction: "This Agreement shall be governed by [State/Country] law"',
                'rationale': 'Familiar governing law reduces legal costs and complexity',
                'priority': 'low'
            },
            'warranty_disclaimers': {
                'pattern': r'(no\s+warranties|as\s+is|disclaim\s+all)',
                'suggestion': 'Add limited warranties: "Each party warrants that they have authority to enter this Agreement"',
                'rationale': 'Basic warranties provide essential protections without excessive liability',
                'priority': 'medium'
            },
            'indemnification_scope': {
                'pattern': r'(indemnify\s+and\s+hold\s+harmless|defend\s+and\s+indemnify)',
                'suggestion': 'Limit indemnification: "Each party shall indemnify the other only for their own negligence or misconduct"',
                'rationale': 'Limited indemnification prevents excessive liability exposure',
                'priority': 'high'
            },
            'renewal_terms': {
                'pattern': r'(automatic\s+renewal|evergreen|perpetual)',
                'suggestion': 'Add renewal control: "This Agreement may be renewed by mutual written agreement"',
                'rationale': 'Controlled renewal prevents unwanted automatic extensions',
                'priority': 'medium'
            }
        }
        
        # Analyze each clause for redline opportunities
        for clause in contract.clauses:
            clause_text = clause.text
            clause_redlines = []
            
            for redline_type, redline_info in redline_patterns.items():
                # Search for pattern matches
                matches = re.finditer(redline_info['pattern'], clause_text, re.IGNORECASE)
                
                for match in matches:
                    # Extract context around the match
                    start = max(0, match.start() - 50)
                    end = min(len(clause_text), match.end() + 50)
                    context = clause_text[start:end]
                    
                    clause_redlines.append({
                        'redline_type': redline_type,
                        'priority': redline_info['priority'],
                        'original_text': match.group(),
                        'context': context,
                        'suggestion': redline_info['suggestion'],
                        'rationale': redline_info['rationale'],
                        'clause_id': clause.id,
                        'clause_type': getattr(clause, 'clause_type', 'General'),
                        'position': match.start()
                    })
            
            # Add clause-level redlines to overall redlines
            redlines.extend(clause_redlines)
        
        # Sort redlines by priority and clause position
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        redlines.sort(key=lambda x: (priority_order.get(x['priority'], 0), x['position']), reverse=True)
        
        # Add overall redline summary
        if redlines:
            high_priority_count = sum(1 for r in redlines if r['priority'] == 'high')
            medium_priority_count = sum(1 for r in redlines if r['priority'] == 'medium')
            
            redlines.insert(0, {
                'redline_type': 'summary',
                'priority': 'high' if high_priority_count > 0 else 'medium' if medium_priority_count > 0 else 'low',
                'description': f'Contract redline summary: {len(redlines)} suggestions found',
                'details': {
                    'total_redlines': len(redlines),
                    'high_priority': high_priority_count,
                    'medium_priority': medium_priority_count,
                    'low_priority': sum(1 for r in redlines if r['priority'] == 'low')
                },
                'general_recommendations': self._get_redline_recommendations(redlines)
            })
        
        return redlines
    
    def _get_redline_recommendations(self, redlines: List[Dict[str, Any]]) -> List[str]:
        """Generate general redline recommendations based on identified issues."""
        recommendations = []
        
        redline_types = [r['redline_type'] for r in redlines if r['redline_type'] != 'summary']
        
        if 'liability_caps' in redline_types:
            recommendations.append("Consider adding liability caps to limit financial exposure")
        
        if 'payment_terms' in redline_types:
            recommendations.append("Negotiate more favorable payment terms for better cash flow")
        
        if 'termination_notice' in redline_types:
            recommendations.append("Add appropriate termination notice periods")
        
        if 'intellectual_property' in redline_types:
            recommendations.append("Clarify intellectual property ownership and licensing terms")
        
        if 'indemnification_scope' in redline_types:
            recommendations.append("Limit indemnification obligations to reasonable scope")
        
        if not recommendations:
            recommendations.append("Contract appears to have standard terms - minor review recommended")
        
        return recommendations
    
    def query_contract(self, question: str, contract_id: Optional[str] = None) -> str:
        """Answer questions using stored contract data."""
        try:
            # Get all stored contracts from local storage
            from pipeline.local_storage import DatabaseStorageManager
            storage_manager = DatabaseStorageManager()
            
            # Try semantic search first if embedder is available
            try:
                # Use semantic search to find relevant clauses
                search_results = self.embedder.search_similar_clauses(
                    query_text=question,
                    limit=3,
                    similarity_threshold=0.3
                )
                
                if search_results:
                    context_clauses = [result['text'] for result in search_results]
                    context = "\n\n".join(context_clauses)
                    self.logger.info(f"Using semantic search: found {len(context_clauses)} relevant clauses")
                else:
                    self.logger.info("Semantic search found no results, falling back to basic retrieval")
                    raise Exception("No semantic results")
                    
            except Exception as e:
                self.logger.warning(f"Semantic search failed: {e}, using fallback method")
                
                # Fallback: basic retrieval from database
                from config import settings
                from supabase import create_client
                
                supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                
                if contract_id:
                    result = supabase.table('contracts').select('data').eq('contract_id', contract_id).limit(1).execute()
                else:
                    result = supabase.table('contracts').select('data').limit(2).execute()
                
                if not result.data:
                    return "No contract data found. Please upload and process contracts first."
                
                context_clauses = []
                for contract_row in result.data:
                    contract_data = contract_row.get('data', {})
                    if contract_data.get('success') and contract_data.get('contract'):
                        contract_dict = contract_data['contract']
                        if isinstance(contract_dict, dict):
                            clauses_data = contract_dict.get('clauses', [])
                            for clause_dict in clauses_data[:3]:
                                if isinstance(clause_dict, dict):
                                    clause_text = clause_dict.get('text', '')
                                    if clause_text and len(clause_text) > 20:
                                        context_clauses.append(clause_text)
                                        if len(context_clauses) >= 3:
                                            break
                            if len(context_clauses) >= 3:
                                break
                
                if not context_clauses:
                    return "No contract clauses found. Please ensure the contract was processed successfully."
                
                context = "\n\n".join(context_clauses)
            
            # Create prompt
            prompt = f"The following are contextually relevant contract clauses found through semantic search based on your question:\n\n{context}\n\nQuestion: {question}\n\nAnswer based only on these relevant contract clauses above. If the answer cannot be found in these specific clauses, say 'Not found in the relevant contract clauses'."
            
            # Generate answer using Gemini
            return self._generate_with_llm(prompt)
            
        except Exception as e:
            self.logger.error(f"Query failed: {e}")
            return "I'm sorry, I couldn't process your question."
    
    def search_similar_contracts(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar contracts or clauses."""
        try:
            # Get all stored contracts from local storage
            from pipeline.local_storage import DatabaseStorageManager
            storage_manager = DatabaseStorageManager()
            
            all_data = storage_manager._load_data()
            results = []
            
            for contract_id, contract_info in all_data.items():
                processed_data = contract_info.get('processed_data', {})
                
                if processed_data.get('success') and processed_data.get('contract'):
                    contract_data = processed_data['contract']
                    
                    if isinstance(contract_data, dict):
                        clauses_data = contract_data.get('clauses', [])
                        
                        for clause_dict in clauses_data:
                            if isinstance(clause_dict, dict):
                                clause_text = clause_dict.get('text', '')
                                
                                # Simple keyword matching
                                if query.lower() in clause_text.lower():
                                    results.append({
                                        'contract_id': contract_id,
                                        'clause_id': clause_dict.get('id', ''),
                                        'text': clause_text,
                                        'similarity': 0.8  # Mock similarity score
                                    })
                                    
                                    if len(results) >= limit:
                                        return results
            
            return results
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []
    
    def answer_questions(self, question: str, contract: ProcessedContract = None, contract_id: str = None) -> str:
        """
        Answer questions using enhanced RAG with hybrid search.
        
        Args:
            question: User question
            contract: Processed contract object (optional)
            contract_id: Contract ID to search in database (optional)
            
        Returns:
            Answer based on contract content
        """
        try:
            if contract:
                # Use contract clauses directly
                relevant_clauses = self._retrieve_relevant_clauses(question, contract)
            elif contract_id:
                # Search specific contract in database
                results = self.embedder.search_similar_clauses(
                    query_text=question,
                    limit=5,
                    contract_id=contract_id,
                    use_hybrid=True
                )
                relevant_clauses = [Clause(id=r['clause_id'], text=r['text']) for r in results]
            else:
                # Search across all contracts
                results = self.embedder.search_similar_clauses(
                    query_text=question,
                    limit=5,
                    use_hybrid=True
                )
                relevant_clauses = [Clause(id=r['clause_id'], text=r['text']) for r in results]
            
            # Create context-aware prompt
            prompt = self._create_qa_prompt(question, relevant_clauses)
            
            # Generate answer using Gemini
            return self._generate_with_llm(prompt)
        except Exception as e:
            self.logger.error(f"Question answering failed: {e}")
            return "I'm sorry, I couldn't process your question at this time."
    
    def _identify_key_clauses(self, contract: ProcessedContract) -> List[Clause]:
        """Identify the most important clauses for summary generation."""
        key_clauses = []
        
        # Define importance criteria with keywords and weights
        importance_criteria = {
            'payment_terms': {
                'keywords': ['payment', 'fee', 'compensation', 'price', 'cost', 'invoice', 'billing', 'remuneration'],
                'weight': 10
            },
            'termination': {
                'keywords': ['termination', 'expiration', 'duration', 'term', 'end', 'conclude', 'expire'],
                'weight': 9
            },
            'governing_law': {
                'keywords': ['governing law', 'jurisdiction', 'legal', 'court', 'venue', 'disputes'],
                'weight': 8
            },
            'liability': {
                'keywords': ['liability', 'indemnification', 'damages', 'breach', 'default', 'remedy'],
                'weight': 9
            },
            'intellectual_property': {
                'keywords': ['intellectual property', 'confidentiality', 'privacy', 'proprietary', 'trade secret'],
                'weight': 8
            },
            'obligations': {
                'keywords': ['obligation', 'duty', 'responsibility', 'perform', 'deliver', 'provide'],
                'weight': 7
            },
            'conditions': {
                'keywords': ['condition', 'requirement', 'if', 'unless', 'provided that', 'subject to'],
                'weight': 6
            },
            'parties': {
                'keywords': ['party', 'parties', 'company', 'corporation', 'entity', 'individual'],
                'weight': 5
            }
        }
        
        for clause in contract.clauses:
            clause_text_lower = clause.text.lower()
            importance_score = 0
            
            # Calculate importance score based on keyword matches
            for category, criteria in importance_criteria.items():
                keyword_matches = sum(1 for keyword in criteria['keywords'] 
                                    if keyword in clause_text_lower)
                importance_score += keyword_matches * criteria['weight']
            
            # Additional scoring based on clause characteristics
            if len(clause.text) > 200:  # Longer clauses often contain more important details
                importance_score += 2
            
            if clause.clause_type and clause.clause_type.lower() in ['payment', 'termination', 'liability']:
                importance_score += 5
            
            if clause.risk_level and clause.risk_level in ['high', 'critical']:
                importance_score += 8
            
            # Add to key clauses if significant
            if importance_score > 5:
                key_clauses.append(clause)
        
        # Sort by text length (longer clauses often more important) and return top clauses
        key_clauses.sort(key=lambda x: len(x.text), reverse=True)
        return key_clauses[:15]  # Return top 15 most important clauses
    
    def _retrieve_relevant_clauses(
        self, 
        query: str, 
        contract: ProcessedContract,
        top_k: int = 5
    ) -> List[Clause]:
        """Retrieve most relevant clauses using hybrid search."""
        if not self.embedder.supabase:
            return contract.clauses[:top_k]  # Fallback to first clauses
        
        try:
            # Use hybrid search for better retrieval
            results = self.embedder.search_similar_clauses(
                query_text=query,
                limit=top_k,
                use_hybrid=True
            )
            
            # Convert results back to Clause objects
            relevant_clauses = []
            for result in results:
                clause = Clause(
                    id=result['clause_id'],
                    text=result['text'],
                    metadata=result.get('metadata', {})
                )
                relevant_clauses.append(clause)
            
            return relevant_clauses
        except Exception as e:
            self.logger.error(f"Failed to retrieve relevant clauses: {e}")
            return contract.clauses[:top_k]  # Fallback
    
    def _create_summary_prompt(
        self, 
        key_clauses: List[Clause], 
        metadata: Any
    ) -> str:
        """Create prompt for contract summary generation."""
        # Prepare contract information
        contract_info = f"""
Contract Information:
- File: {getattr(metadata, 'filename', 'Unknown')}
- Type: {getattr(metadata, 'contract_type', 'Unknown')}
- Parties: {', '.join(getattr(metadata, 'parties', [])) if getattr(metadata, 'parties', None) else 'Not specified'}
- Effective Date: {getattr(metadata, 'effective_date', 'Not specified')}
- Expiration Date: {getattr(metadata, 'expiration_date', 'Not specified')}
- Governing Law: {getattr(metadata, 'governing_law', 'Not specified')}
- Jurisdiction: {getattr(metadata, 'jurisdiction', 'Not specified')}
"""
        
        # Prepare key clauses text
        clauses_text = ""
        if key_clauses:
            for i, clause in enumerate(key_clauses[:10], 1):  # Limit to top 10 clauses
                clause_type = getattr(clause, 'legal_category', 'General') or 'General'
                clause_text = clause.text if clause.text else 'No text available'
                clauses_text += f"\nClause {i} ({clause_type}):\n{clause_text[:500]}{'...' if len(clause_text) > 500 else ''}\n"
        else:
            # Fallback: use all contract clauses if key clause identification fails
            all_clauses = []
            for section in contract.sections:
                all_clauses.extend(section.clauses)
            
            for i, clause in enumerate(all_clauses[:10], 1):
                clause_type = getattr(clause, 'legal_category', 'General') or 'General'
                clause_text = clause.text if clause.text else 'No text available'
                clauses_text += f"\nClause {i} ({clause_type}):\n{clause_text[:500]}{'...' if len(clause_text) > 500 else ''}\n"
        
        prompt = f"""
Analyze this contract and provide a clear, concise summary based ONLY on the actual contract clauses provided below.

Key Contract Clauses:
{clauses_text}

Provide a structured summary with these sections:

**Contract Overview**
Briefly describe what type of agreement this is and its main purpose.

**Key Terms**
- Payment: How much, when, and how payments are made
- Duration: How long the contract lasts and termination conditions
- Obligations: What each party must do

**Important Provisions**
- Liability and risk allocation
- Intellectual property rights
- Confidentiality requirements
- Dispute resolution

**Notable Terms**
Any unusual or important conditions worth highlighting.

Rules:
- Use simple, clear language
- Base your summary ONLY on the provided clauses
- If information is not in the clauses, state "Not specified in provided clauses"
- Keep each section brief and focused
- Avoid legal jargon
"""
        return prompt
    
    def _create_qa_prompt(self, question: str, clauses: List[Clause]) -> str:
        """Create prompt for question answering."""
        # Prepare context from relevant clauses
        context = ""
        for i, clause in enumerate(clauses[:5], 1):  # Limit to top 5 most relevant clauses
            clause_type = getattr(clause, 'clause_type', 'General')
            context += f"\nClause {i} ({clause_type}):\n{clause.text[:400]}{'...' if len(clause.text) > 400 else ''}\n"
        
        prompt = f"""
Answer this question based on the contract clauses provided:

Question: {question}

Contract Clauses:
{context}

Rules:
- Answer based ONLY on the provided clauses
- If information is not in the clauses, say "Not found in contract clauses"
- Be direct and concise
- Use simple language

Answer:
"""
        return prompt
    
    def _generate_with_llm(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate text using Gemini API with retry logic and error handling."""
        # Check if client is available
        if not self.client:
            return self._get_fallback_response(prompt)
        
        max_retries = 3
        retry_delay = 1
        
        # Validate and truncate prompt if too long
        if len(prompt) > 10000:
            self.logger.warning("Prompt too long, truncating to 10000 characters")
            prompt = prompt[:10000] + "\n\n[Prompt truncated...]"
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Gemini generation attempt {attempt + 1}/{max_retries}")
                
                # Generate response using Gemini
                response = self.client.models.generate_content(
                    model="gemini-2.0-flash-exp",
                    contents=prompt
                )
                
                # Validate response
                if not response.text or len(response.text.strip()) < 10:
                    raise ValueError("Gemini returned empty or too short response")
                
                # Clean up response
                response_text = response.text.strip()
                
                # Basic content filtering
                if any(blocked in response_text.lower() for blocked in ['error', 'failed', 'cannot process']):
                    self.logger.warning("Response contains error indicators, retrying...")
                    if attempt < max_retries - 1:
                        continue
                
                self.logger.info(f"Gemini generation successful, response length: {len(response_text)}")
                return response_text
                
            except Exception as e:
                self.logger.warning(f"Gemini generation attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = retry_delay * (2 ** attempt)
                    self.logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"All Gemini generation attempts failed: {e}")
                    return self._get_fallback_response(prompt)
        
        return "I'm sorry, I couldn't generate a response at this time. Please try again."
    
    def _get_fallback_response(self, prompt: str) -> str:
        """Provide a fallback response when LLM generation fails."""
        # Simple keyword-based fallback for common questions
        prompt_lower = prompt.lower()
        
        if 'summary' in prompt_lower or 'overview' in prompt_lower:
            return "I'm unable to generate a summary at this time. Please try again or contact support."
        elif 'risk' in prompt_lower or 'danger' in prompt_lower:
            return "Risk analysis is currently unavailable. Please try again later."
        elif 'question' in prompt_lower:
            return "I'm unable to answer your question at this time. Please try rephrasing or contact support."
        else:
            return "I'm sorry, I couldn't process your request at this time. Please try again."
    
    def negotiate_terms(
        self, 
        contract: ProcessedContract,
        negotiation_points: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate negotiation strategies and alternative language."""
        negotiation_strategies = []
        
        # Define negotiation templates for common points
        negotiation_templates = {
            'payment_terms': {
                'current_issues': ['net 90', 'net 120', 'payment on completion', 'no advance payment'],
                'alternatives': [
                    'Payment due within 30 days of invoice date',
                    '50% advance payment, 50% on completion',
                    'Payment due within 15 days for early payment discount',
                    'Monthly payment schedule with 2% early payment discount'
                ],
                'leverage_points': [
                    'Improved cash flow for both parties',
                    'Reduced collection risk',
                    'Industry standard payment terms',
                    'Early payment incentives'
                ]
            },
            'liability_limits': {
                'current_issues': ['unlimited liability', 'consequential damages', 'punitive damages'],
                'alternatives': [
                    'Liability limited to total contract value',
                    'Liability limited to 150% of contract value',
                    'Mutual liability caps with exceptions for gross negligence',
                    'Liability limited to insurance coverage amounts'
                ],
                'leverage_points': [
                    'Reasonable risk allocation',
                    'Industry standard practice',
                    'Insurance coverage limitations',
                    'Mutual protection for both parties'
                ]
            },
            'termination_rights': {
                'current_issues': ['terminate at will', 'no notice required', 'immediate termination'],
                'alternatives': [
                    '30 days written notice for convenience termination',
                    '60 days notice with cure period for material breach',
                    'Immediate termination only for material breach',
                    'Mutual termination rights with appropriate notice'
                ],
                'leverage_points': [
                    'Fair termination process',
                    'Adequate transition time',
                    'Protection against arbitrary termination',
                    'Industry standard notice periods'
                ]
            },
            'intellectual_property': {
                'current_issues': ['assign all rights', 'work for hire', 'exclusive license'],
                'alternatives': [
                    'Each party retains pre-existing IP ownership',
                    'Joint ownership of jointly developed IP',
                    'Non-exclusive license for necessary use',
                    'Clear IP ownership with appropriate licensing'
                ],
                'leverage_points': [
                    'Protection of existing IP assets',
                    'Clear ownership rights',
                    'Reasonable licensing terms',
                    'Mutual IP protection'
                ]
            },
            'confidentiality_scope': {
                'current_issues': ['perpetual confidentiality', 'no exceptions', 'broad definition'],
                'alternatives': [
                    'Confidentiality for 3 years after termination',
                    'Exceptions for publicly available information',
                    'Narrow definition of confidential information',
                    'Mutual confidentiality with reasonable scope'
                ],
                'leverage_points': [
                    'Reasonable time limitations',
                    'Practical business operations',
                    'Industry standard practices',
                    'Mutual confidentiality obligations'
                ]
            },
            'force_majeure': {
                'current_issues': ['no force majeure', 'limited force majeure'],
                'alternatives': [
                    'Standard force majeure clause with pandemic coverage',
                    'Mutual force majeure protection',
                    'Force majeure with notice requirements',
                    'Comprehensive force majeure clause'
                ],
                'leverage_points': [
                    'Protection against unforeseen circumstances',
                    'Industry standard protection',
                    'Mutual risk sharing',
                    'Business continuity planning'
                ]
            }
        }
        
        # Analyze each negotiation point
        for point in negotiation_points:
            point_lower = point.lower()
            strategy = {
                'negotiation_point': point,
                'priority': 'medium',
                'current_issues': [],
                'alternatives': [],
                'leverage_points': [],
                'recommended_approach': '',
                'risk_assessment': 'medium'
            }
            
            # Match negotiation point to templates
            for template_key, template_data in negotiation_templates.items():
                if any(issue in point_lower for issue in template_data['current_issues']):
                    strategy['current_issues'].extend(template_data['current_issues'])
                    strategy['alternatives'].extend(template_data['alternatives'])
                    strategy['leverage_points'].extend(template_data['leverage_points'])
                    strategy['priority'] = 'high' if template_key in ['liability_limits', 'termination_rights'] else 'medium'
                    break
            
            # If no template match, create generic strategy
            if not strategy['current_issues']:
                strategy['current_issues'] = [point]
                strategy['alternatives'] = [
                    f'Modify {point} to be more favorable',
                    f'Add exceptions to {point}',
                    f'Limit scope of {point}',
                    f'Make {point} mutual rather than one-sided'
                ]
                strategy['leverage_points'] = [
                    'Mutual benefit for both parties',
                    'Industry standard practice',
                    'Reasonable business terms',
                    'Fair risk allocation'
                ]
            
            # Generate recommended approach
            strategy['recommended_approach'] = self._generate_negotiation_approach(point, strategy)
            
            # Assess negotiation risk
            strategy['risk_assessment'] = self._assess_negotiation_risk(point, strategy)
            
            negotiation_strategies.append(strategy)
        
        # Sort by priority and add overall strategy
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        negotiation_strategies.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
        
        # Add overall negotiation strategy
        if negotiation_strategies:
            high_priority_count = sum(1 for s in negotiation_strategies if s['priority'] == 'high')
            
            negotiation_strategies.insert(0, {
                'negotiation_point': 'Overall Strategy',
                'priority': 'high' if high_priority_count > 0 else 'medium',
                'description': f'Overall negotiation strategy for {len(negotiation_points)} points',
                'recommended_approach': self._generate_overall_strategy(negotiation_strategies),
                'key_leverage_points': self._identify_key_leverage_points(negotiation_strategies),
                'negotiation_priorities': self._prioritize_negotiation_points(negotiation_strategies)
            })
        
        return negotiation_strategies
    
    def _generate_negotiation_approach(self, point: str, strategy: Dict[str, Any]) -> str:
        """Generate a specific negotiation approach for a given point."""
        if strategy['priority'] == 'high':
            return f"PRIORITY: Focus on {point} as it significantly impacts contract risk. Present alternatives with clear business justification and industry examples."
        elif strategy['priority'] == 'medium':
            return f"MODERATE: Address {point} during negotiations. Present alternatives as improvements that benefit both parties."
        else:
            return f"LOW: Consider {point} if other priorities are resolved. Present as minor improvement for mutual benefit."
    
    def _assess_negotiation_risk(self, point: str, strategy: Dict[str, Any]) -> str:
        """Assess the risk level of negotiating a specific point."""
        if strategy['priority'] == 'high':
            return 'high'
        elif len(strategy['alternatives']) > 3:
            return 'medium'
        else:
            return 'low'
    
    def _generate_overall_strategy(self, strategies: List[Dict[str, Any]]) -> str:
        """Generate an overall negotiation strategy."""
        high_priority_points = [s for s in strategies if s['priority'] == 'high']
        
        if high_priority_points:
            return f"Focus on {len(high_priority_points)} high-priority points first. Present alternatives with clear business justification. Be prepared to compromise on lower-priority items to secure high-priority changes."
        else:
            return "Address all points systematically. Present alternatives as improvements that benefit both parties. Focus on mutual benefit and industry standards."
    
    def _identify_key_leverage_points(self, strategies: List[Dict[str, Any]]) -> List[str]:
        """Identify key leverage points across all negotiation strategies."""
        leverage_points = []
        
        # Collect unique leverage points
        for strategy in strategies:
            leverage_points.extend(strategy.get('leverage_points', []))
        
        # Count frequency and return most common
        leverage_counts = {}
        for point in leverage_points:
            leverage_counts[point] = leverage_counts.get(point, 0) + 1
        
        # Return top leverage points
        sorted_leverage = sorted(leverage_counts.items(), key=lambda x: x[1], reverse=True)
        return [point for point, count in sorted_leverage[:5]]
    
    def _prioritize_negotiation_points(self, strategies: List[Dict[str, Any]]) -> List[str]:
        """Prioritize negotiation points based on importance and risk."""
        priorities = []
        
        for strategy in strategies:
            if strategy['priority'] == 'high':
                priorities.append(f"1. {strategy['negotiation_point']} (HIGH PRIORITY)")
            elif strategy['priority'] == 'medium':
                priorities.append(f"2. {strategy['negotiation_point']} (MEDIUM PRIORITY)")
            else:
                priorities.append(f"3. {strategy['negotiation_point']} (LOW PRIORITY)")
        
        return priorities


# Alias for backward compatibility
RAGGenerator = ContractRAGGenerator
