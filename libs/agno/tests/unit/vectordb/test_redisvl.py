"""Unit tests for RedisVL vector database integration."""

from typing import List
from unittest.mock import AsyncMock, Mock, patch

import pytest

from agno.document import Document
from agno.vectordb.distance import Distance
from agno.vectordb.redisvl import RedisVL
from agno.vectordb.search import SearchType


@pytest.fixture
def mock_redis_client():
    """Fixture to create a mock Redis client"""
    with patch("redis.Redis") as mock_redis_class:
        client = Mock()

        # Mock Redis operations
        client.ping.return_value = True
        client.keys.return_value = []
        client.get.return_value = None
        client.set.return_value = True
        client.delete.return_value = 1

        mock_redis_class.return_value = client
        yield client


@pytest.fixture
def mock_redisvl_index():
    """Fixture to create a mock RedisVL SearchIndex"""
    with patch("redisvl.index.SearchIndex") as mock_index_class:
        index = Mock()

        # Mock index operations
        index.exists.return_value = True
        index.create = Mock()
        index.delete = Mock()
        index.load = Mock()
        index.query.return_value = Mock(docs=[])
        index.search.return_value = []
        index.get.return_value = None

        mock_index_class.return_value = index
        yield index


@pytest.fixture
def mock_redisvl_schema():
    """Fixture to create a mock RedisVL IndexSchema"""
    with patch("redisvl.schema.IndexSchema") as mock_schema_class:
        schema = Mock()
        mock_schema_class.from_dict.return_value = schema
        yield schema


@pytest.fixture
def redisvl_db(mock_redis_client, mock_redisvl_index, mock_redisvl_schema, mock_embedder):
    """Fixture to create a RedisVL instance with mocked dependencies"""
    with patch("redisvl.index.SearchIndex"), patch("redisvl.schema.IndexSchema"), patch("redis.Redis"):
        db = RedisVL(collection="test_collection", embedder=mock_embedder, host="localhost", port=6379)

        # Set mocked components
        db._redis_client = mock_redis_client
        db._index = mock_redisvl_index
        db._schema = mock_redisvl_schema

        yield db


@pytest.fixture
def sample_documents() -> List[Document]:
    """Fixture to create sample documents"""
    return [
        Document(
            id="doc1",
            content="This is a test document about machine learning",
            meta_data={"topic": "AI", "type": "article"},
            name="ml_doc",
        ),
        Document(
            id="doc2",
            content="Python programming tutorial for beginners",
            meta_data={"topic": "programming", "type": "tutorial"},
            name="python_doc",
        ),
        Document(
            id="doc3",
            content="Redis vector database implementation guide",
            meta_data={"topic": "database", "type": "guide"},
            name="redis_doc",
        ),
    ]


class TestRedisVLBasicOperations:
    """Test basic RedisVL operations"""

    def test_initialization(self, mock_embedder):
        """Test RedisVL initialization"""
        db = RedisVL(
            collection="test_collection", embedder=mock_embedder, distance=Distance.cosine, host="localhost", port=6379
        )

        assert db.collection == "test_collection"
        assert db.embedder == mock_embedder
        assert db.distance == Distance.cosine
        assert db.host == "localhost"
        assert db.port == 6379
        assert db.search_type == SearchType.vector  # default

    def test_dimensions_property(self, redisvl_db, mock_embedder):
        """Test dimensions property"""
        mock_embedder.dimensions = 1536
        assert redisvl_db.dimensions == 1536

        # Test default when no embedder
        db_no_embedder = RedisVL(collection="test")
        assert db_no_embedder.dimensions == 1536  # default OpenAI dimension

    def test_distance_metric_mapping(self, redisvl_db):
        """Test distance metric conversion"""
        redisvl_db.distance = Distance.cosine
        assert redisvl_db._get_distance_metric() == "COSINE"

        redisvl_db.distance = Distance.l2
        assert redisvl_db._get_distance_metric() == "L2"

        redisvl_db.distance = Distance.max_inner_product
        assert redisvl_db._get_distance_metric() == "IP"


class TestRedisVLCRUDOperations:
    """Test CRUD operations"""

    def test_create_collection(self, redisvl_db, mock_redisvl_index):
        """Test creating a collection"""
        mock_redisvl_index.exists.return_value = False

        redisvl_db.create()
        mock_redisvl_index.create.assert_called_once()

    def test_create_collection_already_exists(self, redisvl_db, mock_redisvl_index):
        """Test creating a collection that already exists"""
        mock_redisvl_index.exists.return_value = True

        redisvl_db.create()
        mock_redisvl_index.create.assert_not_called()

    def test_exists(self, redisvl_db, mock_redisvl_index):
        """Test checking if collection exists"""
        mock_redisvl_index.exists.return_value = True
        assert redisvl_db.exists() is True

        mock_redisvl_index.exists.return_value = False
        assert redisvl_db.exists() is False

    def test_drop_collection(self, redisvl_db, mock_redisvl_index):
        """Test dropping a collection"""
        mock_redisvl_index.exists.return_value = True

        redisvl_db.drop()
        mock_redisvl_index.delete.assert_called_once_with(drop=True)

    def test_insert_documents(self, redisvl_db, sample_documents, mock_redisvl_index, mock_embedder):
        """Test inserting documents"""
        # Mock embedder to return embeddings
        mock_embedder.get_embedding.return_value = [0.1] * 1024

        # Mock exists to return False to ensure create is called
        mock_redisvl_index.exists.return_value = False

        redisvl_db.insert(sample_documents)

        # Verify create was called (to ensure index exists)
        mock_redisvl_index.create.assert_called()

        # Verify load was called with document data
        mock_redisvl_index.load.assert_called()

        # Check the call arguments
        call_args = mock_redisvl_index.load.call_args[0][0]
        assert len(call_args) == 3  # 3 documents
        assert call_args[0]["id"] == "doc1"
        assert call_args[0]["content"] == "This is a test document about machine learning"

    def test_insert_empty_documents(self, redisvl_db, mock_redisvl_index):
        """Test inserting empty document list"""
        redisvl_db.insert([])
        mock_redisvl_index.load.assert_not_called()

    def test_upsert_documents(self, redisvl_db, sample_documents):
        """Test upserting documents"""
        with patch.object(redisvl_db, "insert") as mock_insert:
            redisvl_db.upsert(sample_documents)
            mock_insert.assert_called_once_with(sample_documents, None)

    def test_upsert_available(self, redisvl_db):
        """Test upsert availability"""
        assert redisvl_db.upsert_available() is True


class TestRedisVLSearchOperations:
    """Test search operations"""

    def test_vector_search(self, redisvl_db, mock_redisvl_index, mock_embedder):
        """Test vector similarity search"""
        # Mock embedder and search results
        mock_embedder.get_embedding.return_value = [0.1] * 1024

        # Create mock search results
        mock_result = Mock()
        mock_result.__dict__ = {
            "id": "doc1",
            "name": "test_doc",
            "content": "test content",
            "meta_data": '{"topic": "test"}',
        }

        mock_query_result = Mock()
        mock_query_result.docs = [mock_result]
        mock_redisvl_index.query.return_value = mock_query_result

        results = redisvl_db.search("test query", limit=5, search_type=SearchType.vector)

        # Verify query was called
        mock_redisvl_index.query.assert_called_once()

        # Check results
        assert len(results) == 1
        assert results[0].id == "doc1"
        assert results[0].content == "test content"

    def test_vector_search_no_embedder(self, mock_redisvl_index, mock_redisvl_schema, mock_redis_client):
        """Test vector search without embedder"""
        db = RedisVL(collection="test", embedder=None)
        db._index = mock_redisvl_index
        db._schema = mock_redisvl_schema
        db._redis_client = mock_redis_client

        results = db.search("test query", search_type=SearchType.vector)
        assert results == []

    def test_keyword_search(self, redisvl_db, mock_redisvl_index):
        """Test keyword search"""
        # Mock search results
        mock_result = {"id": "doc1", "name": "test_doc", "content": "test content", "meta_data": "{}"}
        mock_redisvl_index.search.return_value = [mock_result]

        results = redisvl_db.search("test query", search_type=SearchType.keyword)

        # Verify search was called
        mock_redisvl_index.search.assert_called_once()
        assert len(results) == 1

    def test_hybrid_search(self, redisvl_db, mock_embedder):
        """Test hybrid search"""
        mock_embedder.get_embedding.return_value = [0.1] * 1024

        with (
            patch.object(redisvl_db, "_vector_search") as mock_vector,
            patch.object(redisvl_db, "_keyword_search") as mock_keyword,
        ):
            # Mock return values
            doc1 = Document(id="doc1", content="test1")
            doc2 = Document(id="doc2", content="test2")
            doc3 = Document(id="doc3", content="test3")

            mock_vector.return_value = [doc1, doc2]
            mock_keyword.return_value = [doc2, doc3]  # doc2 appears in both

            results = redisvl_db.search("test query", search_type=SearchType.hybrid)

            # Should deduplicate and return unique documents
            result_ids = [doc.id for doc in results]
            assert "doc1" in result_ids
            assert "doc2" in result_ids
            assert "doc3" in result_ids
            assert len(results) == 3  # No duplicates


class TestRedisVLDocumentOperations:
    """Test document-specific operations"""

    def test_doc_exists(self, redisvl_db, sample_documents, mock_redisvl_index):
        """Test document existence check"""
        # Test when document exists
        mock_redisvl_index.get.return_value = {"id": "doc1"}
        assert redisvl_db.doc_exists(sample_documents[0]) is True

        # Test when document doesn't exist
        mock_redisvl_index.get.return_value = None
        assert redisvl_db.doc_exists(sample_documents[0]) is False

    def test_name_exists(self, redisvl_db, mock_redisvl_index):
        """Test name existence check"""
        # Test when name exists
        mock_result = {"name": "test_name"}
        mock_redisvl_index.search.return_value = [mock_result]
        assert redisvl_db.name_exists("test_name") is True

        # Test when name doesn't exist
        mock_redisvl_index.search.return_value = []
        assert redisvl_db.name_exists("nonexistent") is False

    def test_get_count(self, redisvl_db, mock_redisvl_index):
        """Test getting document count"""
        mock_result = Mock()
        mock_result.total = 42
        mock_redisvl_index.search.return_value = mock_result
        mock_redisvl_index.exists.return_value = True

        count = redisvl_db.get_count()
        assert count == 42

    def test_delete_all_documents(self, redisvl_db):
        """Test deleting all documents"""
        with (
            patch.object(redisvl_db, "exists", return_value=True),
            patch.object(redisvl_db, "drop") as mock_drop,
            patch.object(redisvl_db, "create") as mock_create,
        ):
            result = redisvl_db.delete()
            assert result is True
            mock_drop.assert_called_once()
            mock_create.assert_called_once()


class TestRedisVLAsyncOperations:
    """Test async operations"""

    @pytest.mark.asyncio
    async def test_async_create(self, redisvl_db, mock_redisvl_index):
        """Test async collection creation"""
        mock_redisvl_index.exists.return_value = False
        mock_redisvl_index.create = AsyncMock()

        await redisvl_db.async_create()
        mock_redisvl_index.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_exists(self, redisvl_db, mock_redisvl_index):
        """Test async existence check"""
        mock_redisvl_index.exists = AsyncMock(return_value=True)

        result = await redisvl_db.async_exists()
        assert result is True

    @pytest.mark.asyncio
    async def test_async_insert(self, redisvl_db, sample_documents, mock_redisvl_index, mock_embedder):
        """Test async document insertion"""
        mock_embedder.get_embedding.return_value = [0.1] * 1024
        mock_redisvl_index.create = AsyncMock()

        # Mock async load if available
        mock_redisvl_index.aload = AsyncMock()

        await redisvl_db.async_insert(sample_documents)

        # Should try async load first
        if hasattr(mock_redisvl_index, "aload"):
            mock_redisvl_index.aload.assert_called()

    @pytest.mark.asyncio
    async def test_async_search(self, redisvl_db, mock_redisvl_index, mock_embedder):
        """Test async search"""
        mock_embedder.get_embedding.return_value = [0.1] * 1024
        mock_redisvl_index.query = AsyncMock(return_value=Mock(docs=[]))

        await redisvl_db.async_search("test query")
        mock_redisvl_index.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_drop(self, redisvl_db, mock_redisvl_index):
        """Test async collection drop"""
        mock_redisvl_index.exists = AsyncMock(return_value=True)
        mock_redisvl_index.drop = AsyncMock()

        await redisvl_db.async_drop()
        mock_redisvl_index.drop.assert_called_once()


class TestRedisVLUtilityMethods:
    """Test utility methods"""

    def test_validate_document(self, redisvl_db, sample_documents):
        """Test document validation"""
        # Valid document
        assert redisvl_db._validate_document(sample_documents[0]) is True

        # Document without content
        invalid_doc = Document(id="test", content="", name="test")
        assert redisvl_db._validate_document(invalid_doc) is False

        # Document without ID
        invalid_doc2 = Document(id="", content="test content", name="test")
        assert redisvl_db._validate_document(invalid_doc2) is False

    def test_clean_document_content(self, redisvl_db):
        """Test document content cleaning"""
        # Test null byte removal
        content_with_nulls = "test\x00content"
        cleaned = redisvl_db._clean_document_content(content_with_nulls)
        assert "\x00" not in cleaned

        # Test whitespace normalization
        content_with_spaces = "test   content   with    spaces"
        cleaned = redisvl_db._clean_document_content(content_with_spaces)
        assert cleaned == "test content with spaces"

    def test_build_filter_expression(self, redisvl_db):
        """Test filter expression building"""
        filters = {"topic": "AI", "score": 0.8, "category": "tech"}

        expression = redisvl_db._build_filter_expression(filters)
        assert "@topic:AI" in expression
        assert "@score:[0.8 0.8]" in expression
        assert "@category:tech" in expression

    def test_close_connection(self, redisvl_db):
        """Test connection cleanup"""
        redisvl_db.close()
        assert redisvl_db._index is None
        assert redisvl_db._schema is None
        assert redisvl_db._redis_client is None


class TestRedisVLErrorHandling:
    """Test error handling scenarios"""

    def test_search_with_embedder_error(self, redisvl_db, mock_embedder):
        """Test search when embedder fails"""
        mock_embedder.get_embedding.return_value = None

        results = redisvl_db.search("test query", search_type=SearchType.vector)
        assert results == []

    def test_insert_with_index_error(self, redisvl_db, sample_documents, mock_redisvl_index, mock_embedder):
        """Test insert when index operation fails"""
        mock_embedder.get_embedding.return_value = [0.1] * 1024
        mock_redisvl_index.load.side_effect = Exception("Index error")

        with pytest.raises(Exception):
            redisvl_db.insert(sample_documents)

    def test_exists_with_connection_error(self, redisvl_db, mock_redisvl_index):
        """Test exists check with connection error"""
        mock_redisvl_index.exists.side_effect = Exception("Connection error")

        result = redisvl_db.exists()
        assert result is False  # Should return False on error
