"""
Embeddings generation and vector storage module.
"""
import logging
from typing import List, Optional, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client
from models.contract import Clause


class ContractEmbedder:
    """Enhanced embeddings generator with multilingual support and validation."""
    
    def __init__(
        self, 
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        multilingual: bool = False
    ):
        """Initialize embedder with enhanced capabilities."""
        self.logger = logging.getLogger(__name__)
        self.multilingual = multilingual
        
        # Initialize primary model
        self.model = SentenceTransformer(model_name)
        
        # Initialize multilingual fallback models
        self.fallback_models = {}
        if multilingual:
            self._initialize_multilingual_models()
        
        # Language detection
        self.language_detector = None
        if multilingual:
            try:
                from langdetect import detect
                self.language_detector = detect
            except ImportError:
                self.logger.warning("langdetect not available. Install with: pip install langdetect")
        
        if supabase_url and supabase_key:
            self.supabase: Client = create_client(supabase_url, supabase_key)
            self._setup_vector_table()
        else:
            self.supabase = None
    
    def generate_embeddings(self, clauses: List[Clause]) -> List[Clause]:
        """
        Generate embeddings with multilingual support and quality validation.
        
        Args:
            clauses: List of clauses to embed
            
        Returns:
            List of clauses with embeddings added
        """
        if not clauses:
            return clauses
        
        # Group clauses by language if multilingual support is enabled
        if self.multilingual and self.language_detector:
            language_groups = self._group_by_language(clauses)
            
            for language, lang_clauses in language_groups.items():
                model = self._get_model_for_language(language)
                texts = [clause.text for clause in lang_clauses]
                
                embeddings = model.encode(
                    texts,
                    batch_size=32,
                    show_progress_bar=True,
                    convert_to_numpy=True,
                    normalize_embeddings=True  # Normalize for better similarity
                )
                
                for clause, embedding in zip(lang_clauses, embeddings):
                    clause.embedding = embedding.tolist()
                    # Add language metadata
                    if not clause.metadata:
                        clause.metadata = {}
                    clause.metadata['detected_language'] = language
        else:
            # Standard processing
            texts = [clause.text for clause in clauses]
            
            embeddings = self.model.encode(
                texts,
                batch_size=32,
                show_progress_bar=True,
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            
            for clause, embedding in zip(clauses, embeddings):
                clause.embedding = embedding.tolist()
        
        # Validate embedding quality
        self._validate_embeddings(clauses)
        
        return clauses
    
    def store_vectors(self, clauses: List[Clause], contract_id: str) -> bool:
        """
        Store clause vectors in Supabase with pgvector.
        
        Args:
            clauses: List of clauses with embeddings
            contract_id: Unique identifier for the contract
            
        Returns:
            Success status
        """
        if not self.supabase:
            self.logger.warning("Supabase client not initialized")
            return False
        
        try:
            data = []
            for clause in clauses:
                if clause.embedding:
                    data.append({
                        "contract_id": contract_id,
                        "clause_id": clause.id,
                        "text": clause.text,
                        "embedding": clause.embedding,
                        "metadata": {
                            "clause_type": clause.clause_type,
                            "section": clause.section,
                            "page_number": clause.page_number
                        }
                    })
            
            if data:
                self.supabase.table("clause_vectors").insert(data).execute()
                self.logger.info(f"Stored {len(data)} vectors for contract {contract_id}")
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to store vectors: {e}")
            return False
    
    def search_similar_clauses(
        self, 
        query_text: str, 
        limit: int = 10, 
        similarity_threshold: float = 0.7,
        contract_id: Optional[str] = None,
        legal_category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Enhanced search with filtering and validation.
        
        Args:
            query_text: Text to search for
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            contract_id: Filter by specific contract
            legal_category: Filter by legal category
            
        Returns:
            List of similar clauses with metadata and validation scores
        """
        if not self.supabase:
            self.logger.warning("Supabase client not initialized")
            return []
        
        try:
            # Detect language and use appropriate model
            detected_lang = 'en'
            if self.multilingual and self.language_detector:
                try:
                    detected_lang = self.language_detector(query_text)
                except:
                    detected_lang = 'en'
            
            model = self._get_model_for_language(detected_lang)
            query_embedding = model.encode([query_text], normalize_embeddings=True)[0].tolist()
            
            # Build search parameters
            search_params = {
                "query_embedding": query_embedding,
                "match_threshold": similarity_threshold,
                "match_count": limit
            }
            
            if contract_id:
                search_params["contract_filter"] = contract_id
            if legal_category:
                search_params["category_filter"] = legal_category
            
            result = self.supabase.rpc("match_clauses_enhanced", search_params).execute()
            
            if result.data:
                # Validate and enhance results
                validated_results = self._validate_search_results(query_text, result.data)
                return validated_results
            
            return []
        except Exception as e:
            self.logger.error(f"Enhanced search failed: {e}")
            # Fallback to basic search
            return self._basic_search_fallback(query_text, limit, similarity_threshold)
    
    def _setup_vector_table(self):
        """Set up pgvector table for storing clause embeddings."""
        try:
            # Create table and function for similarity search
            self.supabase.rpc("setup_clause_vectors").execute()
            self.logger.info("Vector table setup completed")
        except Exception as e:
            self.logger.warning(f"Vector table setup failed: {e}")
    
    def update_embeddings(self, clause_ids: List[str]) -> bool:
        """Update embeddings for specific clauses."""
        if not self.supabase:
            return False
        
        try:
            # Retrieve clauses
            result = self.supabase.table("clause_vectors").select("*").in_("clause_id", clause_ids).execute()
            
            if not result.data:
                return False
            
            # Regenerate embeddings
            texts = [row["text"] for row in result.data]
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            
            # Update in database
            for row, embedding in zip(result.data, embeddings):
                self.supabase.table("clause_vectors").update({
                    "embedding": embedding.tolist()
                }).eq("id", row["id"]).execute()
            
            return True
        except Exception as e:
            self.logger.error(f"Update failed: {e}")
            return False
    
    def _initialize_multilingual_models(self):
        """Initialize multilingual fallback models."""
        multilingual_models = {
            'es': 'sentence-transformers/distiluse-base-multilingual-cased',  # Spanish
            'fr': 'sentence-transformers/distiluse-base-multilingual-cased',  # French
            'de': 'sentence-transformers/distiluse-base-multilingual-cased',  # German
            'zh': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',  # Chinese
            'ja': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',  # Japanese
            'multilingual': 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'  # General multilingual
        }
        
        try:
            # Load multilingual model as fallback
            self.fallback_models['multilingual'] = SentenceTransformer(
                multilingual_models['multilingual']
            )
            self.logger.info("Multilingual model loaded successfully")
        except Exception as e:
            self.logger.warning(f"Failed to load multilingual model: {e}")
    
    def _group_by_language(self, clauses: List[Clause]) -> Dict[str, List[Clause]]:
        """Group clauses by detected language."""
        language_groups = {'en': []}  # Default to English
        
        for clause in clauses:
            try:
                detected_lang = self.language_detector(clause.text)
                if detected_lang not in language_groups:
                    language_groups[detected_lang] = []
                language_groups[detected_lang].append(clause)
            except:
                # Default to English if detection fails
                language_groups['en'].append(clause)
        
        return language_groups
    
    def _get_model_for_language(self, language: str) -> SentenceTransformer:
        """Get appropriate model for detected language."""
        if language == 'en' or not self.multilingual:
            return self.model
        
        # Use multilingual model for non-English languages
        if 'multilingual' in self.fallback_models:
            return self.fallback_models['multilingual']
        
        # Fallback to primary model
        return self.model
    
    def _validate_embeddings(self, clauses: List[Clause]):
        """Validate embedding quality and flag potential issues."""
        for clause in clauses:
            if clause.embedding:
                embedding_array = np.array(clause.embedding)
                
                # Check for zero embeddings
                if np.allclose(embedding_array, 0):
                    self.logger.warning(f"Zero embedding detected for clause {clause.id}")
                    if not clause.metadata:
                        clause.metadata = {}
                    clause.metadata['embedding_quality'] = 'poor'
                
                # Check embedding magnitude
                magnitude = np.linalg.norm(embedding_array)
                if magnitude < 0.1:
                    self.logger.warning(f"Low magnitude embedding for clause {clause.id}")
                    if not clause.metadata:
                        clause.metadata = {}
                    clause.metadata['embedding_quality'] = 'low'
                else:
                    if not clause.metadata:
                        clause.metadata = {}
                    clause.metadata['embedding_quality'] = 'good'
    
    def _validate_search_results(self, query_text: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and enhance search results with additional metrics."""
        validated_results = []
        
        for result in results:
            # Add semantic validation
            result_text = result.get('text', '')
            
            # Calculate additional similarity metrics
            lexical_similarity = self._calculate_lexical_similarity(query_text, result_text)
            result['lexical_similarity'] = lexical_similarity
            
            # Calculate length ratio
            length_ratio = min(len(query_text), len(result_text)) / max(len(query_text), len(result_text))
            result['length_ratio'] = length_ratio
            
            # Composite relevance score
            semantic_sim = result.get('similarity', 0)
            composite_score = (semantic_sim * 0.7) + (lexical_similarity * 0.2) + (length_ratio * 0.1)
            result['composite_relevance'] = composite_score
            
            validated_results.append(result)
        
        # Sort by composite relevance
        validated_results.sort(key=lambda x: x['composite_relevance'], reverse=True)
        
        return validated_results
    
    def _calculate_lexical_similarity(self, text1: str, text2: str) -> float:
        """Calculate lexical similarity using word overlap."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def _basic_search_fallback(self, query_text: str, limit: int, threshold: float) -> List[Dict[str, Any]]:
        """Fallback search method for when enhanced search fails."""
        try:
            query_embedding = self.model.encode([query_text])[0].tolist()
            
            result = self.supabase.rpc(
                "match_clauses",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": threshold,
                    "match_count": limit
                }
            ).execute()
            
            return result.data if result.data else []
        except Exception as e:
            self.logger.error(f"Fallback search also failed: {e}")
            return []
    
    def test_adversarial_queries(self, test_queries: List[str]) -> Dict[str, Any]:
        """Test embedding system with adversarial queries for robustness."""
        results = {
            'total_queries': len(test_queries),
            'successful_searches': 0,
            'failed_searches': 0,
            'average_results': 0,
            'quality_scores': []
        }
        
        for query in test_queries:
            try:
                search_results = self.search_similar_clauses(query, limit=5)
                if search_results:
                    results['successful_searches'] += 1
                    results['average_results'] += len(search_results)
                    
                    # Calculate quality score based on relevance
                    avg_relevance = sum(r.get('composite_relevance', 0) for r in search_results) / len(search_results)
                    results['quality_scores'].append(avg_relevance)
                else:
                    results['failed_searches'] += 1
            except Exception as e:
                results['failed_searches'] += 1
                self.logger.error(f"Adversarial query failed: {query} - {e}")
        
        if results['successful_searches'] > 0:
            results['average_results'] /= results['successful_searches']
            results['average_quality'] = sum(results['quality_scores']) / len(results['quality_scores'])
        
        return results


def test_embedding_storage(embedder, text: str):
    embedding = embedder.model.encode(text).tolist()
    response = embedder.supabase.table("embeddings").insert({
        "content": text,
        "embedding": embedding
    }).execute()

    if response.data:
        print("✅ Embedding stored successfully:", response.data)
    else:
        print("❌ Failed to store embedding:", response.error)

    return response


if __name__ == "__main__":
    embedder = ContractEmbedder(multilingual=True)
    test_embedding_storage(embedder, "This is a test clause for storage check.")
