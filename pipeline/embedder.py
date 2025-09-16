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
    """Generates embeddings for contract clauses and manages vector storage."""
    
    def __init__(
        self, 
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None
    ):
        """Initialize embedder with sentence transformer model and database."""
        self.logger = logging.getLogger(__name__)
        self.model = SentenceTransformer(model_name)
        
        if supabase_url and supabase_key:
            self.supabase: Client = create_client(supabase_url, supabase_key)
            self._setup_vector_table()
        else:
            self.supabase = None
    
    def generate_embeddings(self, clauses: List[Clause]) -> List[Clause]:
        """
        Generate embeddings for contract clauses.
        
        Args:
            clauses: List of clauses to embed
            
        Returns:
            List of clauses with embeddings added
        """
        if not clauses:
            return clauses
            
        texts = [clause.text for clause in clauses]
        
        embeddings = self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        for clause, embedding in zip(clauses, embeddings):
            clause.embedding = embedding.tolist()
        
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
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for similar clauses using vector similarity.
        
        Args:
            query_text: Text to search for
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of similar clauses with metadata
        """
        if not self.supabase:
            self.logger.warning("Supabase client not initialized")
            return []
        
        try:
            query_embedding = self.model.encode([query_text])[0].tolist()
            
            result = self.supabase.rpc(
                "match_clauses",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": similarity_threshold,
                    "match_count": limit
                }
            ).execute()
            
            return result.data if result.data else []
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []
    
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
    embedder = ContractEmbedder()  # uses your __init__ setup
    test_embedding_storage(embedder, "This is a test clause for storage check.")
