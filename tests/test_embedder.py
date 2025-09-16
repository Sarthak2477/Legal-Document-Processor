"""
Tests for embedder module.
"""
import os
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from pipeline.embedder import ContractEmbedder
from models.contract import Clause


# @pytest.fixture
# def sample_clauses():
#     return [
#         Clause(
#             id="C1",
#             text="Payment shall be made within 30 days.",
#             clause_type="payment"
#         ),
#         Clause(
#             id="C2", 
#             text="This agreement may be terminated with notice.",
#             clause_type="termination"
#         )
#     ]


# @pytest.fixture
# def mock_supabase():
#     mock = Mock()
#     mock.table.return_value.insert.return_value.execute.return_value = None
#     mock.table.return_value.select.return_value.in_.return_value.execute.return_value.data = []
#     mock.rpc.return_value.execute.return_value.data = []
#     return mock


# @pytest.fixture
# def embedder_no_db():
#     return ContractEmbedder()


# @pytest.fixture
# def embedder_with_db(mock_supabase):
#     with patch('pipeline.embedder.create_client', return_value=mock_supabase):
#         return ContractEmbedder(supabase_url="test", supabase_key="test")


# def test_init_without_supabase():
#     """Test embedder initialization without Supabase."""
#     embedder = ContractEmbedder()
#     assert embedder.supabase is None
#     assert embedder.model is not None


# @patch('pipeline.embedder.create_client')
# def test_init_with_supabase(mock_create_client):
#     """Test embedder initialization with Supabase."""
#     mock_client = Mock()
#     mock_create_client.return_value = mock_client
    
#     embedder = ContractEmbedder(supabase_url="test", supabase_key="test")
#     assert embedder.supabase is not None
#     mock_create_client.assert_called_once()


# def test_generate_embeddings_empty_list(embedder_no_db):
#     """Test embedding generation with empty clause list."""
#     result = embedder_no_db.generate_embeddings([])
#     assert result == []


# def test_generate_embeddings(embedder_no_db, sample_clauses):
#     """Test embedding generation for clauses."""
#     with patch.object(embedder_no_db.model, 'encode') as mock_encode:
#         mock_encode.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])
        
#         result = embedder_no_db.generate_embeddings(sample_clauses)
        
#         assert len(result) == 2
#         assert result[0].embedding == [0.1, 0.2]
#         assert result[1].embedding == [0.3, 0.4]
#         mock_encode.assert_called_once()


# def test_store_vectors_no_supabase(embedder_no_db, sample_clauses):
#     """Test vector storage without Supabase client."""
#     result = embedder_no_db.store_vectors(sample_clauses, "contract1")
#     assert result is False


# def test_store_vectors_success(embedder_with_db, sample_clauses, caplog):
#     """Test successful vector storage."""
#     # Add embeddings to clauses
#     sample_clauses[0].embedding = [0.1, 0.2]
#     sample_clauses[1].embedding = [0.3, 0.4]
    
#     print(f"\nStoring {len(sample_clauses)} clauses with embeddings")
#     print(f"Clause 1 embedding: {sample_clauses[0].embedding}")
#     print(f"Clause 2 embedding: {sample_clauses[1].embedding}")
    
#     result = embedder_with_db.store_vectors(sample_clauses, "contract1")
    
#     print(f"Store result: {result}")
#     print(f"Supabase table calls: {embedder_with_db.supabase.table.call_count}")
#     print(f"Insert calls: {embedder_with_db.supabase.table.return_value.insert.call_count}")
#     print(f"Execute calls: {embedder_with_db.supabase.table.return_value.insert.return_value.execute.call_count}")
#     print(f"Log messages: {[record.message for record in caplog.records]}")
    
#     # Check if insert was called with data
#     if embedder_with_db.supabase.table.return_value.insert.called:
#         call_args = embedder_with_db.supabase.table.return_value.insert.call_args
#         print(f"Insert called with: {call_args}")
    
#     assert result is True
#     embedder_with_db.supabase.table.assert_called_with("clause_vectors")
#     # Verify insert was actually called
#     embedder_with_db.supabase.table.return_value.insert.assert_called_once()


# def test_store_vectors_exception(embedder_with_db, sample_clauses, caplog):
#     """Test vector storage with exception."""
#     # Add embeddings to clauses so they will be processed
#     sample_clauses[0].embedding = [0.1, 0.2]
#     sample_clauses[1].embedding = [0.3, 0.4]
    
#     embedder_with_db.supabase.table.side_effect = Exception("DB error")
    
#     print(f"\nTesting exception with {len(sample_clauses)} clauses")
#     result = embedder_with_db.store_vectors(sample_clauses, "contract1")
    
#     print(f"Exception test result: {result}")
#     print(f"Log messages: {[record.message for record in caplog.records]}")
    
#     assert result is False


# def test_search_similar_clauses_no_supabase(embedder_no_db):
#     """Test similarity search without Supabase client."""
#     result = embedder_no_db.search_similar_clauses("test query")
#     assert result == []


# def test_search_similar_clauses_success(embedder_with_db):
#     """Test successful similarity search."""
#     mock_result = Mock()
#     mock_result.data = [{"clause_id": "C1", "similarity": 0.8}]
#     embedder_with_db.supabase.rpc.return_value.execute.return_value = mock_result
    
#     with patch.object(embedder_with_db.model, 'encode') as mock_encode:
#         mock_encode.return_value = np.array([[0.1, 0.2]])
        
#         result = embedder_with_db.search_similar_clauses("payment terms")
        
#         assert len(result) == 1
#         assert result[0]["clause_id"] == "C1"
#         embedder_with_db.supabase.rpc.assert_called_with(
#             "match_clauses",
#             {
#                 "query_embedding": [0.1, 0.2],
#                 "match_threshold": 0.7,
#                 "match_count": 10
#             }
#         )


# def test_search_similar_clauses_exception(embedder_with_db):
#     """Test similarity search with exception."""
#     embedder_with_db.supabase.rpc.side_effect = Exception("Search error")
    
#     result = embedder_with_db.search_similar_clauses("test query")
#     assert result == []


# def test_update_embeddings_no_supabase(embedder_no_db):
#     """Test embedding update without Supabase client."""
#     result = embedder_no_db.update_embeddings(["C1", "C2"])
#     assert result is False


# def test_update_embeddings_success(embedder_with_db):
#     """Test successful embedding update."""
#     mock_result = Mock()
#     mock_result.data = [
#         {"id": "1", "text": "Payment clause", "clause_id": "C1"},
#         {"id": "2", "text": "Termination clause", "clause_id": "C2"}
#     ]
#     embedder_with_db.supabase.table.return_value.select.return_value.in_.return_value.execute.return_value = mock_result
    
#     with patch.object(embedder_with_db.model, 'encode') as mock_encode:
#         mock_encode.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])
        
#         result = embedder_with_db.update_embeddings(["C1", "C2"])
        
#         assert result is True
#         assert embedder_with_db.supabase.table.return_value.update.call_count == 2


# def test_update_embeddings_no_data(embedder_with_db):
#     """Test embedding update with no data found."""
#     mock_result = Mock()
#     mock_result.data = []
#     embedder_with_db.supabase.table.return_value.select.return_value.in_.return_value.execute.return_value = mock_result
    
#     result = embedder_with_db.update_embeddings(["C1"])
#     assert result is False


# def test_setup_vector_table(embedder_with_db):
#     """Test vector table setup."""
#     # Setup is called during initialization
#     embedder_with_db.supabase.rpc.assert_called_with("setup_clause_vectors")


# @pytest.mark.parametrize("limit,threshold", [
#     (5, 0.8),
#     (20, 0.6),
#     (1, 0.9)
# ])
# def test_search_parameters(embedder_with_db, limit, threshold):
#     """Test search with different parameters."""
#     with patch.object(embedder_with_db.model, 'encode') as mock_encode:
#         mock_encode.return_value = np.array([[0.1, 0.2]])
        
#         embedder_with_db.search_similar_clauses(
#             "test", 
#             limit=limit, 
#             similarity_threshold=threshold
#         )
        
#         embedder_with_db.supabase.rpc.assert_called_with(
#             "match_clauses",
#             {
#                 "query_embedding": [0.1, 0.2],
#                 "match_threshold": threshold,
#                 "match_count": limit
#             }
#         )


# def test_store_vectors_empty_embeddings(embedder_with_db, caplog):
#     """Test storing clauses without embeddings."""
#     clauses = [Clause(id="C1", text="Test clause")]  # No embedding
    
#     print(f"\nTesting with clause without embedding: {clauses[0].embedding}")
#     result = embedder_with_db.store_vectors(clauses, "contract1")
    
#     print(f"Empty embeddings result: {result}")
#     print(f"Log messages: {[record.message for record in caplog.records]}")
    
#     assert result is True  # Should succeed but store nothing

@pytest.mark.skipif(
    not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_KEY"),
    reason="Supabase credentials not set"
)
def test_store_vectors_in_real_supabase():
    """
    Integration test to store vectors in real Supabase.
    Make sure SUPABASE_URL and SUPABASE_KEY are set as environment variables.
    WARNING: This will insert data into your real database!
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    print(f"\nSupabase URL: {supabase_url[:20] + '...' if supabase_url else None}")
    print(f"Supabase Key: {'***' if supabase_key else None}")
    
    # Skip if credentials not available
    if not supabase_url or not supabase_key:
        pytest.skip("SUPABASE_URL and SUPABASE_KEY environment variables not set")

    embedder = ContractEmbedder(
        supabase_url=supabase_url,
        supabase_key=supabase_key
    )
    
    print(f"Embedder supabase client: {embedder.supabase is not None}")

    clauses = [
        Clause(id="C1", text="Payment shall be made within 30 days.", clause_type="payment"),
        Clause(id="C2", text="This agreement may be terminated with notice.", clause_type="termination")
    ]

    # Generate embeddings
    clauses = embedder.generate_embeddings(clauses)
    print(f"Generated embeddings: {len([c for c in clauses if c.embedding])} clauses")

    # Store vectors
    result = embedder.store_vectors(clauses, contract_id="integration_test_contract")
    print(f"Store result: {result}")

    assert result is True
