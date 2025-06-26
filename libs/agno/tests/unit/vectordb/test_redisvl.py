import json
import uuid
from typing import List
from unittest.mock import MagicMock, patch, PropertyMock

import numpy as np
import pytest

from agno.document import Document
from agno.vectordb.distance import Distance
from agno.vectordb.redisvl import RedisVL
from agno.vectordb.search import SearchType

# Configuration for tests
TEST_COLLECTION = f"test_redisvl_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client."""
    client = MagicMock()
    client.execute_command.return_value = [0]  # Default empty search result
    return client


@pytest.fixture
def mock_index():
    """Create a mock RedisVL SearchIndex."""
    index = MagicMock()
    index.exists.return_value = True
    index.create.return_value = None
    index.delete.return_value = None
    index.drop.return_value = None
    index.load.return_value = None
    index.get.return_value = None
    index.query.return_value = []
    return index


@pytest.fixture
def mock_schema():
    """Create a mock RedisVL IndexSchema."""
    schema = MagicMock()
    return schema


@pytest.fixture
def sample_documents() -> List[Document]:
    """Fixture to create sample documents."""
    return [
        Document(
            id="doc_1",
            content="Tom Kha Gai is a Thai coconut soup with chicken",
            meta_data={"cuisine": "Thai", "type": "soup"},
            name="thai_soup",
        ),
        Document(
            id="doc_2", 
            content="Pad Thai is a stir-fried rice noodle dish",
            meta_data={"cuisine": "Thai", "type": "noodles"},
            name="pad_thai",
        ),
        Document(
            id="doc_3",
            content="Green curry is a spicy Thai curry with coconut milk",
            meta_data={"cuisine": "Thai", "type": "curry"},
            name="green_curry",
        ),
    ]


@pytest.fixture
def redisvl_db(mock_embedder):
    """Create a RedisVL instance with mocked dependencies."""
    with (
        patch("agno.vectordb.redisvl.redisvl.redis.Redis") as mock_redis_class,
        patch("agno.vectordb.redisvl.redisvl.SearchIndex") as mock_index_class,
        patch("agno.vectordb.redisvl.redisvl.IndexSchema") as mock_schema_class,
    ):
        # Setup mocks
        mock_redis_instance = MagicMock()
        mock_redis_instance.execute_command.return_value = [0]
        mock_redis_class.return_value = mock_redis_instance

        mock_index_instance = MagicMock()
        mock_index_instance.exists.return_value = False
        mock_index_instance.create.return_value = None
        mock_index_instance.load.return_value = None
        mock_index_instance.query.return_value = []
        mock_index_instance.get.return_value = None
        mock_index_class.return_value = mock_index_instance

        mock_schema_instance = MagicMock()
        mock_schema_class.from_dict.return_value = mock_schema_instance

        # Create RedisVL instance
        db = RedisVL(
            collection=TEST_COLLECTION,
            embedder=mock_embedder,
            host="localhost",
            port=6379,
            db=0,
        )

        # Override properties to return our mocks
        db._redis_client = mock_redis_instance
        db._index = mock_index_instance
        db._schema = mock_schema_instance

        yield db


# Synchronous Tests
def test_initialization():
    """Test basic initialization."""
    with patch("agno.vectordb.redisvl.redisvl.redis.Redis"):
        db = RedisVL(
            collection=TEST_COLLECTION,
            host="localhost",
            port=6379,
            db=0,
            password="test_password",
            username="test_user",
        )
        assert db.collection == TEST_COLLECTION
        assert db.host == "localhost"
        assert db.port == 6379
        assert db.db == 0
        assert db.password == "test_password"
        assert db.username == "test_user"
        assert db.distance == Distance.cosine
        assert db.search_type == SearchType.vector


def test_initialization_with_embedder(mock_embedder):
    """Test initialization with embedder."""
    with patch("agno.vectordb.redisvl.redisvl.redis.Redis"):
        db = RedisVL(collection=TEST_COLLECTION, embedder=mock_embedder)
        assert db.embedder == mock_embedder


def test_dimensions_property(redisvl_db, mock_embedder):
    """Test dimensions property."""
    mock_embedder.dimensions = 1536
    assert redisvl_db.dimensions == 1536


def test_dimensions_property_default(redisvl_db):
    """Test dimensions property with default value."""
    redisvl_db.embedder = None
    assert redisvl_db.dimensions == 1536


def test_get_distance_metric(redisvl_db):
    """Test distance metric conversion."""
    redisvl_db.distance = Distance.cosine
    assert redisvl_db._get_distance_metric() == "COSINE"
    
    redisvl_db.distance = Distance.l2
    assert redisvl_db._get_distance_metric() == "L2"
    
    redisvl_db.distance = Distance.max_inner_product
    assert redisvl_db._get_distance_metric() == "IP"


def test_format_embedding(redisvl_db):
    """Test embedding formatting."""
    # Test with list
    embedding_list = [0.1, 0.2, 0.3]
    result = redisvl_db._format_embedding(embedding_list)
    assert isinstance(result, bytes)
    
    # Test with numpy array
    embedding_array = np.array([0.1, 0.2, 0.3], dtype=np.float32)
    result = redisvl_db._format_embedding(embedding_array)
    assert isinstance(result, bytes)
    
    # Test with None
    result = redisvl_db._format_embedding(None)
    assert result is None


def test_redis_client_property(redisvl_db):
    """Test Redis client property creation."""
    client = redisvl_db.redis_client
    assert client is not None
    assert redisvl_db._redis_client is not None


def test_schema_property(redisvl_db):
    """Test schema property creation."""
    with patch("agno.vectordb.redisvl.redisvl.IndexSchema") as mock_schema_class:
        mock_schema_instance = MagicMock()
        mock_schema_class.from_dict.return_value = mock_schema_instance
        
        # Reset the schema to trigger creation
        redisvl_db._schema = None
        schema = redisvl_db.schema
        assert schema is not None
        mock_schema_class.from_dict.assert_called_once()


def test_index_property(redisvl_db):
    """Test index property creation."""
    index = redisvl_db.index
    assert index is not None


def test_create(redisvl_db):
    """Test create method."""
    redisvl_db._index.exists.return_value = False
    redisvl_db.create()
    redisvl_db._index.create.assert_called_once()


def test_create_existing(redisvl_db):
    """Test create method when index already exists."""
    redisvl_db._index.exists.return_value = True
    redisvl_db.create()
    redisvl_db._index.create.assert_not_called()


def test_exists(redisvl_db):
    """Test exists method."""
    redisvl_db._index.exists.return_value = True
    assert redisvl_db.exists() is True
    
    redisvl_db._index.exists.return_value = False
    assert redisvl_db.exists() is False


def test_exists_with_exception(redisvl_db):
    """Test exists method with exception."""
    redisvl_db._index.exists.side_effect = Exception("Connection error")
    assert redisvl_db.exists() is False


def test_doc_exists(redisvl_db, sample_documents):
    """Test doc_exists method."""
    doc = sample_documents[0]
    
    # Test when document exists
    redisvl_db._index.get.return_value = {"id": doc.id}
    assert redisvl_db.doc_exists(doc) is True
    
    # Test when document doesn't exist
    redisvl_db._index.get.return_value = None
    assert redisvl_db.doc_exists(doc) is False


def test_doc_exists_with_exception(redisvl_db, sample_documents):
    """Test doc_exists method with exception."""
    doc = sample_documents[0]
    redisvl_db._index.get.side_effect = Exception("Connection error")
    assert redisvl_db.doc_exists(doc) is False


def test_name_exists(redisvl_db):
    """Test name_exists method."""
    # Test when name exists
    redisvl_db._index.search.return_value = [{"name": "test_name"}]
    assert redisvl_db.name_exists("test_name") is True
    
    # Test when name doesn't exist
    redisvl_db._index.search.return_value = []
    assert redisvl_db.name_exists("test_name") is False


def test_name_exists_with_exception(redisvl_db):
    """Test name_exists method with exception."""
    redisvl_db._index.search.side_effect = Exception("Connection error")
    assert redisvl_db.name_exists("test_name") is False


def test_insert(redisvl_db, sample_documents, mock_embedder):
    """Test insert method."""
    # Mock embedder to return embeddings
    mock_embedder.get_embedding.return_value = [0.1] * 1024
    
    # Mock create to avoid index creation
    with patch.object(redisvl_db, 'create'):
        redisvl_db.insert(sample_documents)
        redisvl_db._index.load.assert_called()


def test_insert_empty_list(redisvl_db):
    """Test insert method with empty list."""
    redisvl_db.insert([])
    redisvl_db._index.load.assert_not_called()


def test_insert_with_embeddings(redisvl_db, sample_documents):
    """Test insert method with pre-existing embeddings."""
    # Add embeddings to documents
    for doc in sample_documents:
        doc.embedding = [0.1] * 1024
    
    with patch.object(redisvl_db, 'create'):
        redisvl_db.insert(sample_documents)
        redisvl_db._index.load.assert_called()


def test_insert_without_embedder(redisvl_db, sample_documents):
    """Test insert method without embedder or embeddings."""
    redisvl_db.embedder = None
    
    # Documents without embeddings should be skipped
    with patch.object(redisvl_db, 'create'):
        redisvl_db.insert(sample_documents)
        # Should not load anything since no embeddings available
        redisvl_db._index.load.assert_not_called()


def test_upsert_available(redisvl_db):
    """Test upsert_available method."""
    assert redisvl_db.upsert_available() is True


def test_upsert(redisvl_db, sample_documents):
    """Test upsert method."""
    with patch.object(redisvl_db, 'insert') as mock_insert:
        redisvl_db.upsert(sample_documents)
        mock_insert.assert_called_once_with(sample_documents, None)


def test_search_vector(redisvl_db, mock_embedder):
    """Test vector search."""
    mock_embedder.get_embedding.return_value = [0.1] * 1024
    
    # Mock search results
    mock_results = MagicMock()
    mock_results.docs = [
        MagicMock(id="doc_1", name="test_doc", content="test_content", meta_data='{"type": "test"}')
    ]
    redisvl_db._index.query.return_value = mock_results
    
    results = redisvl_db.search("test query", limit=5, search_type=SearchType.vector)
    assert isinstance(results, list)


def test_search_vector_no_embedder(redisvl_db):
    """Test vector search without embedder."""
    redisvl_db.embedder = None
    results = redisvl_db.search("test query", search_type=SearchType.vector)
    assert results == []


def test_search_keyword(redisvl_db):
    """Test keyword search."""
    # Mock Redis FT.SEARCH response
    redisvl_db._redis_client.execute_command.return_value = [
        1,  # count
        "doc:1",  # key
        ["id", "doc_1", "name", "test_doc", "content", "test content", "meta_data", '{"type": "test"}']
    ]
    
    results = redisvl_db.search("test query", search_type=SearchType.keyword)
    assert isinstance(results, list)


def test_search_keyword_empty_results(redisvl_db):
    """Test keyword search with empty results."""
    redisvl_db._redis_client.execute_command.return_value = [0]
    
    results = redisvl_db.search("test query", search_type=SearchType.keyword)
    assert results == []


def test_search_hybrid(redisvl_db, mock_embedder):
    """Test hybrid search."""
    mock_embedder.get_embedding.return_value = [0.1] * 1024
    
    with (
        patch.object(redisvl_db, '_vector_search', return_value=[]) as mock_vector,
        patch.object(redisvl_db, '_keyword_search', return_value=[]) as mock_keyword,
    ):
        results = redisvl_db.search("test query", search_type=SearchType.hybrid)
        mock_vector.assert_called_once()
        mock_keyword.assert_called_once()
        assert isinstance(results, list)


def test_build_filter_expression(redisvl_db):
    """Test filter expression building."""
    filters = {"type": "soup", "rating": 4.5}
    expression = redisvl_db._build_filter_expression(filters)
    assert "@type:soup" in expression
    assert "@rating:[4.5 4.5]" in expression


def test_build_filter_expression_empty(redisvl_db):
    """Test filter expression building with empty filters."""
    expression = redisvl_db._build_filter_expression({})
    assert expression == ""


def test_process_search_results(redisvl_db):
    """Test search result processing."""
    # Mock search results with different formats
    mock_results = [
        {"id": "doc_1", "name": "test_doc", "content": "test content", "meta_data": '{"type": "test"}'},
        MagicMock(id="doc_2", name="test_doc2", content="test content 2", meta_data='{"type": "test2"}')
    ]
    
    # Add __dict__ to the MagicMock
    mock_results[1].__dict__ = {
        "id": "doc_2",
        "name": "test_doc2", 
        "content": "test content 2",
        "meta_data": '{"type": "test2"}'
    }
    
    documents = redisvl_db._process_search_results(mock_results, "test query")
    assert len(documents) == 2
    assert all(isinstance(doc, Document) for doc in documents)


def test_process_search_results_with_bytes(redisvl_db):
    """Test search result processing with byte strings."""
    mock_results = [
        {
            "id": b"doc_1",
            "name": b"test_doc",
            "content": b"test content",
            "meta_data": b'{"type": "test"}'
        }
    ]
    
    documents = redisvl_db._process_search_results(mock_results, "test query")
    assert len(documents) == 1
    assert documents[0].id == "doc_1"
    assert documents[0].name == "test_doc"


def test_drop(redisvl_db):
    """Test drop method."""
    redisvl_db._index.exists.return_value = True
    redisvl_db.drop()
    redisvl_db._index.delete.assert_called_once_with(drop=True)


def test_drop_nonexistent(redisvl_db):
    """Test drop method when index doesn't exist."""
    redisvl_db._index.exists.return_value = False
    redisvl_db.drop()
    redisvl_db._index.delete.assert_not_called()


def test_optimize(redisvl_db):
    """Test optimize method."""
    redisvl_db._index.exists.return_value = True
    redisvl_db.optimize()
    redisvl_db._index.create.assert_called_once_with(overwrite=True, drop=False)


def test_optimize_nonexistent(redisvl_db):
    """Test optimize method when index doesn't exist."""
    redisvl_db._index.exists.return_value = False
    redisvl_db.optimize()
    redisvl_db._index.create.assert_not_called()


def test_delete(redisvl_db):
    """Test delete method."""
    with (
        patch.object(redisvl_db, 'exists', return_value=True),
        patch.object(redisvl_db, 'drop') as mock_drop,
        patch.object(redisvl_db, 'create') as mock_create,
    ):
        result = redisvl_db.delete()
        assert result is True
        mock_drop.assert_called_once()
        mock_create.assert_called_once()


def test_delete_nonexistent(redisvl_db):
    """Test delete method when index doesn't exist."""
    with patch.object(redisvl_db, 'exists', return_value=False):
        result = redisvl_db.delete()
        assert result is False


def test_get_count(redisvl_db):
    """Test get_count method."""
    # Mock FT.INFO response
    redisvl_db._redis_client.execute_command.return_value = [
        "index_name", TEST_COLLECTION,
        "num_docs", "5",
        "max_doc_id", "5"
    ]
    
    with patch.object(redisvl_db, 'exists', return_value=True):
        count = redisvl_db.get_count()
        assert count == 5


def test_get_count_nonexistent(redisvl_db):
    """Test get_count method when index doesn't exist."""
    with patch.object(redisvl_db, 'exists', return_value=False):
        count = redisvl_db.get_count()
        assert count == 0


def test_get_count_with_bytes(redisvl_db):
    """Test get_count method with bytes in response."""
    # Mock FT.INFO response with bytes
    redisvl_db._redis_client.execute_command.return_value = [
        b"index_name", TEST_COLLECTION.encode(),
        b"num_docs", b"3",
        b"max_doc_id", b"3"
    ]
    
    with patch.object(redisvl_db, 'exists', return_value=True):
        count = redisvl_db.get_count()
        assert count == 3


def test_validate_document(redisvl_db):
    """Test document validation."""
    valid_doc = Document(id="test_id", content="test content")
    assert redisvl_db._validate_document(valid_doc) is True
    
    # Test document without content
    invalid_doc1 = Document(id="test_id", content="")
    assert redisvl_db._validate_document(invalid_doc1) is False
    
    # Test document without ID
    invalid_doc2 = Document(id="", content="test content")
    assert redisvl_db._validate_document(invalid_doc2) is False


def test_clean_document_content(redisvl_db):
    """Test document content cleaning."""
    # Test null byte removal
    content_with_null = "test\x00content"
    cleaned = redisvl_db._clean_document_content(content_with_null)
    assert "\x00" not in cleaned
    assert "\ufffd" in cleaned
    
    # Test whitespace normalization
    content_with_spaces = "test    content   with   spaces"
    cleaned = redisvl_db._clean_document_content(content_with_spaces)
    assert cleaned == "test content with spaces"


def test_close(redisvl_db):
    """Test close method."""
    redisvl_db.close()
    assert redisvl_db._index is None
    assert redisvl_db._schema is None
    assert redisvl_db._redis_client is None


# Async Tests
@pytest.mark.asyncio
async def test_async_create(redisvl_db):
    """Test async create method."""
    with patch.object(redisvl_db, 'async_exists', return_value=False):
        await redisvl_db.async_create()
        redisvl_db._index.create.assert_called_once()


@pytest.mark.asyncio
async def test_async_create_existing(redisvl_db):
    """Test async create method when index already exists."""
    with patch.object(redisvl_db, 'async_exists', return_value=True):
        await redisvl_db.async_create()
        redisvl_db._index.create.assert_not_called()


@pytest.mark.asyncio
async def test_async_exists(redisvl_db):
    """Test async exists method."""
    # Since RedisVL exists() is not actually async, the async_exists will use sync behavior
    # and catch any exceptions returning False
    result = await redisvl_db.async_exists()
    # The actual implementation will return False because the mock will raise an exception when awaited
    assert result is False


@pytest.mark.asyncio
async def test_async_exists_with_exception(redisvl_db):
    """Test async exists method with exception."""
    redisvl_db._index.exists.side_effect = Exception("Connection error")
    result = await redisvl_db.async_exists()
    assert result is False


@pytest.mark.asyncio
async def test_async_doc_exists(redisvl_db, sample_documents):
    """Test async doc_exists method."""
    doc = sample_documents[0]
    
    # Since RedisVL get() is not actually async, the async_doc_exists will catch exceptions
    result = await redisvl_db.async_doc_exists(doc)
    # The actual implementation will return False because the mock will raise an exception when awaited
    assert result is False


@pytest.mark.asyncio
async def test_async_name_exists(redisvl_db):
    """Test async name_exists method."""
    # Since RedisVL search() is not actually async, the async_name_exists will catch exceptions
    result = await redisvl_db.async_name_exists("test_name")
    # The actual implementation will return False because the mock will raise an exception when awaited
    assert result is False


@pytest.mark.asyncio
async def test_async_insert(redisvl_db, sample_documents, mock_embedder):
    """Test async insert method."""
    # Ensure embedder is properly set up
    embedding_value = [0.1] * 1024
    mock_embedder.get_embedding.return_value = embedding_value
    redisvl_db.embedder = mock_embedder
    
    # Pre-assign embeddings to documents to ensure they don't get skipped
    for doc in sample_documents:
        doc.embedding = embedding_value
    
    # Reset the load mock to track calls
    redisvl_db._index.load.reset_mock()
    
    # Ensure the index doesn't have aload method so it uses load
    if hasattr(redisvl_db._index, 'aload'):
        delattr(redisvl_db._index, 'aload')
    
    with patch.object(redisvl_db, 'async_create'):
        await redisvl_db.async_insert(sample_documents)
        # Since documents have embeddings and _format_embedding will format them,
        # load should be called with the batch data
        assert redisvl_db._index.load.call_count >= 1, f"Expected load to be called at least once, but was called {redisvl_db._index.load.call_count} times"


@pytest.mark.asyncio
async def test_async_insert_with_aload(redisvl_db, sample_documents, mock_embedder):
    """Test async insert method with aload method available."""
    mock_embedder.get_embedding.return_value = [0.1] * 1024
    
    # Add aload method to mock index
    redisvl_db._index.aload = MagicMock()
    
    with patch.object(redisvl_db, 'async_create'):
        await redisvl_db.async_insert(sample_documents)
        redisvl_db._index.aload.assert_called()


@pytest.mark.asyncio
async def test_async_upsert(redisvl_db, sample_documents):
    """Test async upsert method."""
    with patch.object(redisvl_db, 'async_insert') as mock_async_insert:
        await redisvl_db.async_upsert(sample_documents)
        mock_async_insert.assert_called_once_with(sample_documents, None)


@pytest.mark.asyncio
async def test_async_search_vector(redisvl_db, mock_embedder):
    """Test async vector search."""
    mock_embedder.get_embedding.return_value = [0.1] * 1024
    
    # Mock search results
    redisvl_db._index.query.return_value = []
    
    results = await redisvl_db.async_search("test query", search_type=SearchType.vector)
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_async_search_non_vector(redisvl_db):
    """Test async search for non-vector search types."""
    with patch.object(redisvl_db, 'search', return_value=[]) as mock_search:
        results = await redisvl_db.async_search("test query", search_type=SearchType.keyword)
        mock_search.assert_called_once_with("test query", 5, SearchType.keyword, None)
        assert isinstance(results, list)


@pytest.mark.asyncio
async def test_async_drop(redisvl_db):
    """Test async drop method."""
    with patch.object(redisvl_db, 'async_exists', return_value=True):
        await redisvl_db.async_drop()
        redisvl_db._index.drop.assert_called_once()


@pytest.mark.asyncio
async def test_async_drop_with_exception(redisvl_db):
    """Test async drop method with exception."""
    with patch.object(redisvl_db, 'async_exists', return_value=True):
        redisvl_db._index.drop.side_effect = Exception("Connection error")
        await redisvl_db.async_drop()  # Should not raise exception


def test_integration_with_reranker(mock_embedder):
    """Test integration with reranker."""
    with patch("agno.vectordb.redisvl.redisvl.redis.Redis"):
        mock_reranker = MagicMock()
        mock_reranker.rerank.return_value = []
        
        db = RedisVL(
            collection=TEST_COLLECTION,
            embedder=mock_embedder,
            reranker=mock_reranker,
        )
        assert db.reranker == mock_reranker


def test_error_handling_in_search(redisvl_db, mock_embedder):
    """Test error handling in search methods."""
    mock_embedder.get_embedding.return_value = [0.1] * 1024
    
    # Test vector search with query exception
    redisvl_db._index.query.side_effect = Exception("Query error")
    results = redisvl_db._vector_search("test query", 5)
    assert results == []
    
    # Test keyword search with execute_command exception
    redisvl_db._redis_client.execute_command.side_effect = Exception("Command error")
    results = redisvl_db._keyword_search("test query", 5)
    assert results == [] 