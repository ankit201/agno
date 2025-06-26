"""Unit tests for RedisVL vector database integration."""

from typing import List
<<<<<<< HEAD
from unittest.mock import AsyncMock, Mock, patch
=======
from unittest.mock import Mock, patch, AsyncMock
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53

import pytest

from agno.document import Document
<<<<<<< HEAD
from agno.vectordb.distance import Distance
from agno.vectordb.redisvl import RedisVL
from agno.vectordb.search import SearchType
=======
from agno.vectordb.redisvl import RedisVL
from agno.vectordb.search import SearchType
from agno.vectordb.distance import Distance
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53


@pytest.fixture
def mock_redis_client():
    """Fixture to create a mock Redis client"""
    with patch("redis.Redis") as mock_redis_class:
        client = Mock()
<<<<<<< HEAD

=======
        
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
        # Mock Redis operations
        client.ping.return_value = True
        client.keys.return_value = []
        client.get.return_value = None
        client.set.return_value = True
        client.delete.return_value = 1
<<<<<<< HEAD

=======
        
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
        mock_redis_class.return_value = client
        yield client


@pytest.fixture
def mock_redisvl_index():
    """Fixture to create a mock RedisVL SearchIndex"""
    with patch("redisvl.index.SearchIndex") as mock_index_class:
        index = Mock()
<<<<<<< HEAD

=======
        
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
        # Mock index operations
        index.exists.return_value = True
        index.create = Mock()
        index.delete = Mock()
        index.load = Mock()
        index.query.return_value = Mock(docs=[])
        index.search.return_value = []
        index.get.return_value = None
<<<<<<< HEAD

=======
        
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
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
<<<<<<< HEAD
    with patch("redisvl.index.SearchIndex"), patch("redisvl.schema.IndexSchema"), patch("redis.Redis"):
        db = RedisVL(collection="test_collection", embedder=mock_embedder, host="localhost", port=6379)

=======
    with patch("redisvl.index.SearchIndex"), \
         patch("redisvl.schema.IndexSchema"), \
         patch("redis.Redis"):
        
        db = RedisVL(
            collection="test_collection",
            embedder=mock_embedder,
            host="localhost",
            port=6379
        )
        
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
        # Set mocked components
        db._redis_client = mock_redis_client
        db._index = mock_redisvl_index
        db._schema = mock_redisvl_schema
<<<<<<< HEAD

=======
        
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
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
<<<<<<< HEAD
            id="doc2",
=======
            id="doc2", 
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
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
<<<<<<< HEAD

    def test_initialization(self, mock_embedder):
        """Test RedisVL initialization"""
        db = RedisVL(
            collection="test_collection", embedder=mock_embedder, distance=Distance.cosine, host="localhost", port=6379
        )

=======
    
    def test_initialization(self, mock_embedder):
        """Test RedisVL initialization"""
        db = RedisVL(
            collection="test_collection",
            embedder=mock_embedder,
            distance=Distance.cosine,
            host="localhost",
            port=6379
        )
        
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
        assert db.collection == "test_collection"
        assert db.embedder == mock_embedder
        assert db.distance == Distance.cosine
        assert db.host == "localhost"
        assert db.port == 6379
        assert db.search_type == SearchType.vector  # default
<<<<<<< HEAD

=======
    
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
    def test_dimensions_property(self, redisvl_db, mock_embedder):
        """Test dimensions property"""
        mock_embedder.dimensions = 1536
        assert redisvl_db.dimensions == 1536
<<<<<<< HEAD

=======
        
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
        # Test default when no embedder
        db_no_embedder = RedisVL(collection="test")
        assert db_no_embedder.dimensions == 1536  # default OpenAI dimension

    def test_distance_metric_mapping(self, redisvl_db):
        """Test distance metric conversion"""
        redisvl_db.distance = Distance.cosine
        assert redisvl_db._get_distance_metric() == "COSINE"
<<<<<<< HEAD

        redisvl_db.distance = Distance.l2
        assert redisvl_db._get_distance_metric() == "L2"

=======
        
        redisvl_db.distance = Distance.l2
        assert redisvl_db._get_distance_metric() == "L2"
        
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
        redisvl_db.distance = Distance.max_inner_product
        assert redisvl_db._get_distance_metric() == "IP"


class TestRedisVLCRUDOperations:
    """Test CRUD operations"""
<<<<<<< HEAD

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

=======
    
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
    
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
    def test_exists(self, redisvl_db, mock_redisvl_index):
        """Test checking if collection exists"""
        mock_redisvl_index.exists.return_value = True
        assert redisvl_db.exists() is True
<<<<<<< HEAD

        mock_redisvl_index.exists.return_value = False
        assert redisvl_db.exists() is False

    def test_drop_collection(self, redisvl_db, mock_redisvl_index):
        """Test dropping a collection"""
        mock_redisvl_index.exists.return_value = True

        redisvl_db.drop()
        mock_redisvl_index.delete.assert_called_once_with(drop=True)

=======
        
        mock_redisvl_index.exists.return_value = False
        assert redisvl_db.exists() is False
    
    def test_drop_collection(self, redisvl_db, mock_redisvl_index):
        """Test dropping a collection"""
        mock_redisvl_index.exists.return_value = True
        
        redisvl_db.drop()
        mock_redisvl_index.delete.assert_called_once_with(drop=True)
    
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
    def test_insert_documents(self, redisvl_db, sample_documents, mock_redisvl_index, mock_embedder):
        """Test inserting documents"""
        # Mock embedder to return embeddings
        mock_embedder.get_embedding.return_value = [0.1] * 1024
<<<<<<< HEAD

        # Mock exists to return False to ensure create is called
        mock_redisvl_index.exists.return_value = False

        redisvl_db.insert(sample_documents)

        # Verify create was called (to ensure index exists)
        mock_redisvl_index.create.assert_called()

        # Verify load was called with document data
        mock_redisvl_index.load.assert_called()

=======
        
        # Mock exists to return False to ensure create is called
        mock_redisvl_index.exists.return_value = False
        
        redisvl_db.insert(sample_documents)
        
        # Verify create was called (to ensure index exists)
        mock_redisvl_index.create.assert_called()
        
        # Verify load was called with document data
        mock_redisvl_index.load.assert_called()
        
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
        # Check the call arguments
        call_args = mock_redisvl_index.load.call_args[0][0]
        assert len(call_args) == 3  # 3 documents
        assert call_args[0]["id"] == "doc1"
        assert call_args[0]["content"] == "This is a test document about machine learning"
<<<<<<< HEAD

=======
    
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
    def test_insert_empty_documents(self, redisvl_db, mock_redisvl_index):
        """Test inserting empty document list"""
        redisvl_db.insert([])
        mock_redisvl_index.load.assert_not_called()
<<<<<<< HEAD

    def test_upsert_documents(self, redisvl_db, sample_documents):
        """Test upserting documents"""
        with patch.object(redisvl_db, "insert") as mock_insert:
            redisvl_db.upsert(sample_documents)
            mock_insert.assert_called_once_with(sample_documents, None)

=======
    
    def test_upsert_documents(self, redisvl_db, sample_documents):
        """Test upserting documents"""
        with patch.object(redisvl_db, 'insert') as mock_insert:
            redisvl_db.upsert(sample_documents)
            mock_insert.assert_called_once_with(sample_documents, None)
    
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
    def test_upsert_available(self, redisvl_db):
        """Test upsert availability"""
        assert redisvl_db.upsert_available() is True


class TestRedisVLSearchOperations:
    """Test search operations"""
<<<<<<< HEAD

=======
    
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
    def test_vector_search(self, redisvl_db, mock_redisvl_index, mock_embedder):
        """Test vector similarity search"""
        # Mock embedder and search results
        mock_embedder.get_embedding.return_value = [0.1] * 1024
<<<<<<< HEAD

=======
        
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
        # Create mock search results
        mock_result = Mock()
        mock_result.__dict__ = {
            "id": "doc1",
            "name": "test_doc",
            "content": "test content",
<<<<<<< HEAD
            "meta_data": '{"topic": "test"}',
        }

        mock_query_result = Mock()
        mock_query_result.docs = [mock_result]
        mock_redisvl_index.query.return_value = mock_query_result

        results = redisvl_db.search("test query", limit=5, search_type=SearchType.vector)

        # Verify query was called
        mock_redisvl_index.query.assert_called_once()

=======
            "meta_data": '{"topic": "test"}'
        }
        
        mock_query_result = Mock()
        mock_query_result.docs = [mock_result]
        mock_redisvl_index.query.return_value = mock_query_result
        
        results = redisvl_db.search("test query", limit=5, search_type=SearchType.vector)
        
        # Verify query was called
        mock_redisvl_index.query.assert_called_once()
        
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
        # Check results
        assert len(results) == 1
        assert results[0].id == "doc1"
        assert results[0].content == "test content"
<<<<<<< HEAD

=======
    
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
    def test_vector_search_no_embedder(self, mock_redisvl_index, mock_redisvl_schema, mock_redis_client):
        """Test vector search without embedder"""
        db = RedisVL(collection="test", embedder=None)
        db._index = mock_redisvl_index
        db._schema = mock_redisvl_schema
        db._redis_client = mock_redis_client
<<<<<<< HEAD

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
=======
        
        results = db.search("test query", search_type=SearchType.vector)
        assert results == []
    
    def test_keyword_search(self, redisvl_db, mock_redisvl_index):
        """Test keyword search"""
        # Mock search results
        mock_result = {
            "id": "doc1",
            "name": "test_doc", 
            "content": "test content",
            "meta_data": "{}"
        }
        mock_redisvl_index.search.return_value = [mock_result]
        
        results = redisvl_db.search("test query", search_type=SearchType.keyword)
        
        # Verify search was called
        mock_redisvl_index.search.assert_called_once()
        assert len(results) == 1
    
    def test_hybrid_search(self, redisvl_db, mock_embedder):
        """Test hybrid search"""
        mock_embedder.get_embedding.return_value = [0.1] * 1024
        
        with patch.object(redisvl_db, '_vector_search') as mock_vector, \
             patch.object(redisvl_db, '_keyword_search') as mock_keyword:
            
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
            # Mock return values
            doc1 = Document(id="doc1", content="test1")
            doc2 = Document(id="doc2", content="test2")
            doc3 = Document(id="doc3", content="test3")
<<<<<<< HEAD

            mock_vector.return_value = [doc1, doc2]
            mock_keyword.return_value = [doc2, doc3]  # doc2 appears in both

            results = redisvl_db.search("test query", search_type=SearchType.hybrid)

            # Should deduplicate and return unique documents
            result_ids = [doc.id for doc in results]
            assert "doc1" in result_ids
            assert "doc2" in result_ids
=======
            
            mock_vector.return_value = [doc1, doc2]
            mock_keyword.return_value = [doc2, doc3]  # doc2 appears in both
            
            results = redisvl_db.search("test query", search_type=SearchType.hybrid)
            
            # Should deduplicate and return unique documents
            result_ids = [doc.id for doc in results]
            assert "doc1" in result_ids
            assert "doc2" in result_ids  
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
            assert "doc3" in result_ids
            assert len(results) == 3  # No duplicates


class TestRedisVLDocumentOperations:
    """Test document-specific operations"""
<<<<<<< HEAD

=======
    
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
    def test_doc_exists(self, redisvl_db, sample_documents, mock_redisvl_index):
        """Test document existence check"""
        # Test when document exists
        mock_redisvl_index.get.return_value = {"id": "doc1"}
        assert redisvl_db.doc_exists(sample_documents[0]) is True
<<<<<<< HEAD

        # Test when document doesn't exist
        mock_redisvl_index.get.return_value = None
        assert redisvl_db.doc_exists(sample_documents[0]) is False

=======
        
        # Test when document doesn't exist
        mock_redisvl_index.get.return_value = None
        assert redisvl_db.doc_exists(sample_documents[0]) is False
    
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
    def test_name_exists(self, redisvl_db, mock_redisvl_index):
        """Test name existence check"""
        # Test when name exists
        mock_result = {"name": "test_name"}
        mock_redisvl_index.search.return_value = [mock_result]
        assert redisvl_db.name_exists("test_name") is True
<<<<<<< HEAD

        # Test when name doesn't exist
        mock_redisvl_index.search.return_value = []
        assert redisvl_db.name_exists("nonexistent") is False

=======
        
        # Test when name doesn't exist
        mock_redisvl_index.search.return_value = []
        assert redisvl_db.name_exists("nonexistent") is False
    
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
    def test_get_count(self, redisvl_db, mock_redisvl_index):
        """Test getting document count"""
        mock_result = Mock()
        mock_result.total = 42
        mock_redisvl_index.search.return_value = mock_result
        mock_redisvl_index.exists.return_value = True
<<<<<<< HEAD

        count = redisvl_db.get_count()
        assert count == 42

    def test_delete_all_documents(self, redisvl_db):
        """Test deleting all documents"""
        with (
            patch.object(redisvl_db, "exists", return_value=True),
            patch.object(redisvl_db, "drop") as mock_drop,
            patch.object(redisvl_db, "create") as mock_create,
        ):
=======
        
        count = redisvl_db.get_count()
        assert count == 42
    
    def test_delete_all_documents(self, redisvl_db):
        """Test deleting all documents"""
        with patch.object(redisvl_db, 'exists', return_value=True), \
             patch.object(redisvl_db, 'drop') as mock_drop, \
             patch.object(redisvl_db, 'create') as mock_create:
            
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
            result = redisvl_db.delete()
            assert result is True
            mock_drop.assert_called_once()
            mock_create.assert_called_once()


class TestRedisVLAsyncOperations:
    """Test async operations"""
<<<<<<< HEAD

=======
    
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
    @pytest.mark.asyncio
    async def test_async_create(self, redisvl_db, mock_redisvl_index):
        """Test async collection creation"""
        mock_redisvl_index.exists.return_value = False
        mock_redisvl_index.create = AsyncMock()
<<<<<<< HEAD

        await redisvl_db.async_create()
        mock_redisvl_index.create.assert_called_once()

=======
        
        await redisvl_db.async_create()
        mock_redisvl_index.create.assert_called_once()
    
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
    @pytest.mark.asyncio
    async def test_async_exists(self, redisvl_db, mock_redisvl_index):
        """Test async existence check"""
        mock_redisvl_index.exists = AsyncMock(return_value=True)
<<<<<<< HEAD

        result = await redisvl_db.async_exists()
        assert result is True

=======
        
        result = await redisvl_db.async_exists()
        assert result is True
    
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
    @pytest.mark.asyncio
    async def test_async_insert(self, redisvl_db, sample_documents, mock_redisvl_index, mock_embedder):
        """Test async document insertion"""
        mock_embedder.get_embedding.return_value = [0.1] * 1024
        mock_redisvl_index.create = AsyncMock()
<<<<<<< HEAD

        # Mock async load if available
        mock_redisvl_index.aload = AsyncMock()

        await redisvl_db.async_insert(sample_documents)

        # Should try async load first
        if hasattr(mock_redisvl_index, "aload"):
            mock_redisvl_index.aload.assert_called()

=======
        
        # Mock async load if available
        mock_redisvl_index.aload = AsyncMock()
        
        await redisvl_db.async_insert(sample_documents)
        
        # Should try async load first
        if hasattr(mock_redisvl_index, 'aload'):
            mock_redisvl_index.aload.assert_called()
    
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
    @pytest.mark.asyncio
    async def test_async_search(self, redisvl_db, mock_redisvl_index, mock_embedder):
        """Test async search"""
        mock_embedder.get_embedding.return_value = [0.1] * 1024
        mock_redisvl_index.query = AsyncMock(return_value=Mock(docs=[]))
<<<<<<< HEAD

        await redisvl_db.async_search("test query")
        mock_redisvl_index.query.assert_called_once()

=======
        
        results = await redisvl_db.async_search("test query")
        mock_redisvl_index.query.assert_called_once()
    
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
    @pytest.mark.asyncio
    async def test_async_drop(self, redisvl_db, mock_redisvl_index):
        """Test async collection drop"""
        mock_redisvl_index.exists = AsyncMock(return_value=True)
        mock_redisvl_index.drop = AsyncMock()
<<<<<<< HEAD

=======
        
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
        await redisvl_db.async_drop()
        mock_redisvl_index.drop.assert_called_once()


class TestRedisVLUtilityMethods:
    """Test utility methods"""
<<<<<<< HEAD

=======
    
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
    def test_validate_document(self, redisvl_db, sample_documents):
        """Test document validation"""
        # Valid document
        assert redisvl_db._validate_document(sample_documents[0]) is True
<<<<<<< HEAD

        # Document without content
        invalid_doc = Document(id="test", content="", name="test")
        assert redisvl_db._validate_document(invalid_doc) is False

        # Document without ID
        invalid_doc2 = Document(id="", content="test content", name="test")
        assert redisvl_db._validate_document(invalid_doc2) is False

=======
        
        # Document without content
        invalid_doc = Document(id="test", content="", name="test")
        assert redisvl_db._validate_document(invalid_doc) is False
        
        # Document without ID
        invalid_doc2 = Document(id="", content="test content", name="test")
        assert redisvl_db._validate_document(invalid_doc2) is False
    
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
    def test_clean_document_content(self, redisvl_db):
        """Test document content cleaning"""
        # Test null byte removal
        content_with_nulls = "test\x00content"
        cleaned = redisvl_db._clean_document_content(content_with_nulls)
        assert "\x00" not in cleaned
<<<<<<< HEAD

=======
        
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
        # Test whitespace normalization
        content_with_spaces = "test   content   with    spaces"
        cleaned = redisvl_db._clean_document_content(content_with_spaces)
        assert cleaned == "test content with spaces"
<<<<<<< HEAD

    def test_build_filter_expression(self, redisvl_db):
        """Test filter expression building"""
        filters = {"topic": "AI", "score": 0.8, "category": "tech"}

=======
    
    def test_build_filter_expression(self, redisvl_db):
        """Test filter expression building"""
        filters = {
            "topic": "AI",
            "score": 0.8,
            "category": "tech"
        }
        
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
        expression = redisvl_db._build_filter_expression(filters)
        assert "@topic:AI" in expression
        assert "@score:[0.8 0.8]" in expression
        assert "@category:tech" in expression
<<<<<<< HEAD

=======
    
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
    def test_close_connection(self, redisvl_db):
        """Test connection cleanup"""
        redisvl_db.close()
        assert redisvl_db._index is None
        assert redisvl_db._schema is None
        assert redisvl_db._redis_client is None


class TestRedisVLErrorHandling:
    """Test error handling scenarios"""
<<<<<<< HEAD

    def test_search_with_embedder_error(self, redisvl_db, mock_embedder):
        """Test search when embedder fails"""
        mock_embedder.get_embedding.return_value = None

        results = redisvl_db.search("test query", search_type=SearchType.vector)
        assert results == []

=======
    
    def test_search_with_embedder_error(self, redisvl_db, mock_embedder):
        """Test search when embedder fails"""
        mock_embedder.get_embedding.return_value = None
        
        results = redisvl_db.search("test query", search_type=SearchType.vector)
        assert results == []
    
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
    def test_insert_with_index_error(self, redisvl_db, sample_documents, mock_redisvl_index, mock_embedder):
        """Test insert when index operation fails"""
        mock_embedder.get_embedding.return_value = [0.1] * 1024
        mock_redisvl_index.load.side_effect = Exception("Index error")
<<<<<<< HEAD

        with pytest.raises(Exception):
            redisvl_db.insert(sample_documents)

    def test_exists_with_connection_error(self, redisvl_db, mock_redisvl_index):
        """Test exists check with connection error"""
        mock_redisvl_index.exists.side_effect = Exception("Connection error")

        result = redisvl_db.exists()
        assert result is False  # Should return False on error
=======
        
        with pytest.raises(Exception):
            redisvl_db.insert(sample_documents)
    
    def test_exists_with_connection_error(self, redisvl_db, mock_redisvl_index):
        """Test exists check with connection error"""
        mock_redisvl_index.exists.side_effect = Exception("Connection error")
        
        result = redisvl_db.exists()
        assert result is False  # Should return False on error 
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
