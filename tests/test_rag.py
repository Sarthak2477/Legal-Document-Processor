"""
Pytest tests for RAG generator functionality.
"""
import pytest
import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup logging to file
log_file = Path(__file__).parent / f"test_rag_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from pipeline.rag_generator import RAGGenerator
from models.contract import ProcessedContract, ContractSection, Clause
from datetime import datetime


@pytest.fixture
def rag_generator():
    """Create RAG generator instance for testing."""
    logger.info("Creating RAG generator instance for testing")
    # Set mock API key for testing if not set
    if not os.getenv("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = "test_key"
        logger.info("Using mock API key for testing")
    return RAGGenerator()


@pytest.fixture
def sample_contract():
    """Create sample contract for testing."""
    clauses = [
        Clause(
            id="clause_1",
            text="This Agreement shall be governed by the laws of California. Any disputes shall be subject to binding arbitration.",
            legal_category="governing_law",
            risk_level="medium"
        ),
        Clause(
            id="clause_2", 
            text="The Company shall indemnify and hold harmless the Client from any liability, damages, or costs arising from breach.",
            legal_category="liability",
            risk_level="high"
        ),
        Clause(
            id="clause_3",
            text="Either party may terminate this Agreement with thirty (30) days written notice.",
            legal_category="termination",
            risk_level="low"
        )
    ]
    
    section = ContractSection(
        id="section_1",
        title="General Terms", 
        text="General terms and conditions",
        level=1, 
        clauses=clauses
    )
    
    from models.contract import ContractMetadata
    
    metadata = ContractMetadata(
        filename="test.pdf",
        file_path="/test/test.pdf",
        file_size=1024,
        pages=5,
        processing_date=datetime.now(),
        ocr_method="test"
    )
    
    return ProcessedContract(
        metadata=metadata,
        sections=[section],
        entities=[],
        processing_stats={"total_clauses": 3}
    )


def test_gemini_connection():
    """Test Gemini API connection."""
    logger.info("=== Testing Gemini API Connection ===")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not set - skipping test")
        pytest.skip("GEMINI_API_KEY not set")
    
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents="Test"
        )
        logger.info(f"Gemini response: {response.text}")
        assert response.text is not None
        logger.info("✅ Gemini connection successful")
    except ImportError:
        logger.warning("Google GenAI not available")
        pytest.skip("Google GenAI not available")
    except Exception as e:
        logger.error(f"❌ Gemini connection failed: {e}")
        pytest.fail(f"Gemini connection failed: {e}")


def test_rag_generator_init(rag_generator):
    """Test RAG generator initialization."""
    logger.info("=== Testing RAG Generator Initialization ===")
    assert rag_generator is not None
    assert hasattr(rag_generator, 'client')
    assert hasattr(rag_generator, 'embedder')
    logger.info("✅ RAG generator initialized successfully")


def test_query_contract(rag_generator):
    """Test contract query functionality."""
    logger.info("=== Testing Contract Query ===")
    question = "What is confidential information?"
    logger.info(f"Query: {question}")
    result = rag_generator.query_contract("contract_training", question)
    logger.info(f"Result: {result[:200]}...")
    assert isinstance(result, str)
    assert len(result) > 0
    logger.info("✅ Contract query successful")


def test_generate_summary(rag_generator, sample_contract):
    """Test summary generation."""
    logger.info("=== Testing Summary Generation ===")
    summary = rag_generator.generate_summary(sample_contract)
    logger.info(f"Generated summary: {summary}")
    assert isinstance(summary, str)
    assert len(summary) > 0
    logger.info("✅ Summary generation successful")


def test_analyze_risks(rag_generator, sample_contract):
    """Test risk analysis."""
    logger.info("=== Testing Risk Analysis ===")
    risks = rag_generator.analyze_risks(sample_contract)
    logger.info(f"Found {len(risks)} risks")
    for i, risk in enumerate(risks):
        logger.info(f"Risk {i+1}: {risk.get('risk_analysis', 'No analysis')[:100]}...")
    assert isinstance(risks, list)
    # Should find at least one risk (liability clause)
    assert len(risks) >= 1
    if risks:
        assert 'clause_id' in risks[0]
        assert 'risk_analysis' in risks[0]
    logger.info("✅ Risk analysis successful")


def test_search_similar_contracts(rag_generator):
    """Test similar contract search."""
    logger.info("=== Testing Similar Contract Search ===")
    query = "confidentiality agreement"
    logger.info(f"Search query: {query}")
    results = rag_generator.search_similar_contracts(query, limit=3)
    logger.info(f"Found {len(results)} similar contracts")
    for i, result in enumerate(results):
        logger.info(f"Result {i+1}: {result.get('text', 'No text')[:100]}...")
    assert isinstance(results, list)
    logger.info("✅ Similar contract search successful")


@pytest.mark.parametrize("question", [
    "What are the payment terms?",
    "Who are the parties?",
    "What is the termination clause?"
])
def test_multiple_queries(rag_generator, question):
    """Test multiple different queries."""
    logger.info(f"=== Testing Query: {question} ===")
    result = rag_generator.query_contract("contract_training", question)
    logger.info(f"Query result: {result[:150]}...")
    assert isinstance(result, str)
    assert len(result) > 0
    logger.info(f"✅ Query '{question}' successful")


def test_empty_query(rag_generator):
    """Test handling of empty queries."""
    logger.info("=== Testing Empty Query ===")
    result = rag_generator.query_contract("contract_training", "")
    logger.info(f"Empty query result: {result}")
    assert isinstance(result, str)
    logger.info("✅ Empty query handled successfully")


def test_nonexistent_contract(rag_generator):
    """Test query on non-existent contract."""
    logger.info("=== Testing Non-existent Contract Query ===")
    result = rag_generator.query_contract("nonexistent_contract", "What is this?")
    logger.info(f"Non-existent contract result: {result}")
    assert isinstance(result, str)
    logger.info("✅ Non-existent contract query handled successfully")


if __name__ == "__main__":
    logger.info(f"Starting RAG tests - Results will be saved to: {log_file}")
    pytest.main([__file__, "-v"])
    logger.info(f"Test results saved to: {log_file}")
    print(f"\n📄 Test results saved to: {log_file}")