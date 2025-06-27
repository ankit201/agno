import json
from typing import Any, Dict, List, Optional, Union

try:
    import numpy as np
    import redis
    import redis.asyncio as aioredis
    from redisvl.index import SearchIndex, AsyncSearchIndex
    from redisvl.query import VectorQuery, HybridQuery
    from redisvl.schema import IndexSchema
except ImportError:
    raise ImportError("Please install redisvl: pip install redisvl")

from agno.document import Document
from agno.embedder.base import Embedder
from agno.reranker.base import Reranker
from agno.utils.log import log_debug
from agno.vectordb.base import VectorDb
from agno.vectordb.distance import Distance
from agno.vectordb.search import SearchType


class RedisVL(VectorDb):
    """RedisVL vector database implementation for Agno.
    
    Note: This implementation supports only vector and hybrid search as these are
    the native search types supported by RedisVL. Keyword-only search is not 
    natively supported by RedisVL.
    """

    def __init__(
        self,
        collection: str = "agno_collection",
        embedder: Optional[Embedder] = None,
        distance: Distance = Distance.cosine,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        username: Optional[str] = None,
        reranker: Optional[Reranker] = None,
        search_type: SearchType = SearchType.vector,
        vector_index: str = "hnsw",  # 'hnsw' or 'flat'
        hybrid_alpha: float = 0.6,  # Balance for hybrid search (0.0=text only, 1.0=vector only)
        # Schema configuration options
        schema_dict: Optional[Dict[str, Any]] = None,
        schema_yaml_path: Optional[str] = None,
        storage_type: str = "hash",  # 'hash' or 'json'
        vector_field_name: str = "embedding",
        vector_datatype: str = "FLOAT32",  # FLOAT32, FLOAT64, FLOAT16, BFLOAT16
        # HNSW specific parameters
        hnsw_m: int = 16,
        hnsw_ef_construction: int = 200,
        hnsw_ef_runtime: int = 10,
        hnsw_epsilon: float = 0.01,
        # Additional fields configuration
        additional_fields: Optional[List[Dict[str, Any]]] = None,
        # Key configuration
        key_prefix: Optional[str] = None,
        key_separator: str = ":",
        **kwargs,
    ):
        """Initialize RedisVL vector database.

        Args:
            collection (str): Name of the Redis collection/index
            embedder (Optional[Embedder]): Optional embedder for automatic vector generation
            distance (Distance): Distance metric (default: cosine)
            host (str): Redis host
            port (int): Redis port
            db (int): Redis database
            password (Optional[str]): Redis password
            username (Optional[str]): Redis username
            reranker (Optional[Reranker]): Optional reranker for search results
            search_type (SearchType): Type of search to perform (vector or hybrid only)
            vector_index (str): Vector index type ('hnsw' or 'flat')
            hybrid_alpha (float): Balance for hybrid search (0.0=text only, 1.0=vector only)
            schema_dict (Optional[Dict]): Custom schema dictionary following RedisVL format
            schema_yaml_path (Optional[str]): Path to YAML schema file
            storage_type (str): Storage type ('hash' or 'json')
            vector_field_name (str): Name of the vector field
            vector_datatype (str): Vector data type (FLOAT32, FLOAT64, FLOAT16, BFLOAT16)
            hnsw_m (int): HNSW M parameter for max connections per node
            hnsw_ef_construction (int): HNSW ef_construction parameter
            hnsw_ef_runtime (int): HNSW ef_runtime parameter
            hnsw_epsilon (float): HNSW epsilon parameter for range queries
            additional_fields (Optional[List[Dict]]): Additional fields to include in schema
            key_prefix (Optional[str]): Custom key prefix (defaults to collection name)
            key_separator (str): Key separator character
            **kwargs: Additional arguments passed to RedisVL
        """
        self.collection = collection
        self.embedder = embedder
        self.distance = distance
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.username = username
        self._connection_kwargs = kwargs
        self.reranker = reranker
        
        # Validate search type - only vector and hybrid are natively supported
        if search_type == SearchType.keyword:
            log_debug("Warning: Keyword search is not natively supported by RedisVL. Using hybrid search instead.")
            self.search_type = SearchType.hybrid
        else:
            self.search_type = search_type
            
        self.vector_index = vector_index.upper()
        self.hybrid_alpha = hybrid_alpha

        # Schema configuration
        self.schema_dict = schema_dict
        self.schema_yaml_path = schema_yaml_path
        self.storage_type = storage_type.lower()
        self.vector_field_name = vector_field_name
        self.vector_datatype = vector_datatype.upper()
        
        # HNSW parameters
        self.hnsw_m = hnsw_m
        self.hnsw_ef_construction = hnsw_ef_construction
        self.hnsw_ef_runtime = hnsw_ef_runtime
        self.hnsw_epsilon = hnsw_epsilon
        
        # Additional configuration
        self.additional_fields = additional_fields or []
        self.key_prefix = key_prefix or f"{collection}"
        self.key_separator = key_separator
        
        # Redis VL actually uses :: as the default separator, regardless of what we specify
        self._actual_key_separator = "::"

        # Initialize schema and indexes as None - they'll be created lazily
        self._schema: Optional[IndexSchema] = None
        self._index: Optional[SearchIndex] = None
        self._async_index: Optional[AsyncSearchIndex] = None
        self._redis_client: Optional[redis.Redis] = None
        self._async_redis_client: Optional[aioredis.Redis] = None

    @property
    def redis_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if self._redis_client is None:
            log_debug("Creating Redis client")
            self._redis_client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                username=self.username,
                decode_responses=False,  # Don't decode responses to handle binary vector data
                **self._connection_kwargs,
            )
        return self._redis_client

    @property
    async def async_redis_client(self) -> aioredis.Redis:
        """Get or create async Redis client."""
        if self._async_redis_client is None:
            self._async_redis_client = aioredis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                username=self.username,
                decode_responses=False,
                **self._connection_kwargs,
            )
        return self._async_redis_client

    @property
    def schema(self) -> IndexSchema:
        """Get or create the RedisVL IndexSchema."""
        if self._schema is None:
            # If custom schema is provided, use it
            if self.schema_dict:
                self._schema = IndexSchema.from_dict(self.schema_dict)
                return self._schema
            
            if self.schema_yaml_path:
                self._schema = IndexSchema.from_yaml(self.schema_yaml_path)
                return self._schema

            # Create default schema with proper configuration
            schema_dict = self._build_default_schema()
            self._schema = IndexSchema.from_dict(schema_dict)

        return self._schema

    def _build_default_schema(self) -> Dict[str, Any]:
        """Build the default schema dictionary following RedisVL standards."""
        # Base schema structure
        schema_dict = {
            "index": {
                "name": self.collection,
                "prefix": f"{self.key_prefix}{self.key_separator}",
                "storage_type": self.storage_type,
            },
            "fields": []
        }

        # Add default document fields
        default_fields = [
            {"name": "id", "type": "tag"},
            {"name": "name", "type": "text"},
            {"name": "content", "type": "text"},
            {"name": "meta_data", "type": "text"},
        ]
        
        # Add vector field with proper configuration
        vector_field = {
            "name": self.vector_field_name,
            "type": "vector",
            "attrs": {
                "dims": self.dimensions,
                "distance_metric": self._get_distance_metric(),
                "algorithm": self.vector_index,
                "datatype": self.vector_datatype,
            }
        }

        # Add HNSW-specific parameters if using HNSW
        if self.vector_index == "HNSW":
            vector_field["attrs"].update({
                "m": self.hnsw_m,
                "ef_construction": self.hnsw_ef_construction,
                "ef_runtime": self.hnsw_ef_runtime,
                "epsilon": self.hnsw_epsilon,
            })

        # Combine all fields
        schema_dict["fields"] = default_fields + [vector_field] + self.additional_fields

        return schema_dict

    @property
    def index(self) -> SearchIndex:
        """Get or create the RedisVL SearchIndex."""
        if self._index is None:
            self._index = SearchIndex(schema=self.schema, redis_client=self.redis_client)
        return self._index

    async def get_async_index(self) -> AsyncSearchIndex:
        """Get or create the async RedisVL SearchIndex."""
        if self._async_index is None:
            async_client = await self.async_redis_client
            self._async_index = AsyncSearchIndex(schema=self.schema, redis_client=async_client)
        return self._async_index

    def _get_distance_metric(self) -> str:
        """Convert Agno Distance enum to RedisVL distance metric."""
        distance_map = {
            Distance.cosine: "cosine",
            Distance.l2: "l2",
            Distance.max_inner_product: "ip",  # Inner product
        }
        return distance_map.get(self.distance, "cosine")

    def _format_embedding(self, embedding):
        """Format embedding for RedisVL storage."""
        if embedding is None:
            return None

        # Convert to numpy array and then to bytes for Redis storage
        if isinstance(embedding, list):
            embedding = np.array(embedding, dtype=np.float32)
        elif isinstance(embedding, np.ndarray):
            embedding = embedding.astype(np.float32)

        # Convert to bytes for Redis storage
        return embedding.tobytes()

    def _get_numpy_dtype(self):
        """Get numpy dtype based on vector_datatype."""
        dtype_map = {
            "FLOAT32": np.float32,
            "FLOAT64": np.float64,
            "FLOAT16": np.float16,
            "BFLOAT16": np.float32,  # Use float32 as fallback for bfloat16
        }
        return dtype_map.get(self.vector_datatype, np.float32)

    @property
    def dimensions(self) -> int:
        """Get the dimensions of the embeddings."""
        if self.embedder:
            return self.embedder.dimensions
        # Default dimension if no embedder is set
        return 1536

    def create(self) -> None:
        """Create the search index."""
        self.index.create(overwrite=True)

    async def async_create(self) -> None:
        """Create the search index asynchronously."""
        async_index = await self.get_async_index()
        await async_index.create(overwrite=True)

    def exists(self) -> bool:
        """Check if the index exists."""
        try:
            return self.index.exists()
        except Exception as e:
            log_debug(f"Error checking if index exists: {e}")
            return False

    async def async_exists(self) -> bool:
        """Check if the index exists asynchronously."""
        try:
            async_index = await self.get_async_index()
            return await async_index.exists()
        except Exception as e:
            log_debug(f"Error checking if index exists: {e}")
            return False

    def doc_exists(self, document: Document) -> bool:
        """Check if a document exists in the database."""
        try:
            key = f"{self.key_prefix}{self._actual_key_separator}{document.id}"
            return self.redis_client.exists(key) > 0
        except Exception as e:
            log_debug(f"Error checking if document exists: {e}")
            return False

    async def async_doc_exists(self, document: Document) -> bool:
        """Check if a document exists in the database asynchronously."""
        try:
            async_client = await self.async_redis_client
            key = f"{self.key_prefix}{self._actual_key_separator}{document.id}"
            result = await async_client.exists(key)
            return result > 0
        except Exception as e:
            log_debug(f"Error checking if document exists: {e}")
            return False

    def name_exists(self, name: str) -> bool:
        """Check if a document with the given name exists."""
        try:
            # Search for documents with the given name
            results = self.redis_client.execute_command(
                "FT.SEARCH", self.collection, f"@name:{name}", "LIMIT", "0", "1"
            )
            return len(results) > 1  # First element is count
        except Exception:
            return False

    async def async_name_exists(self, name: str) -> bool:
        """Check if a document with the given name exists asynchronously."""
        try:
            async_client = await self.async_redis_client
            results = await async_client.execute_command(
                "FT.SEARCH", self.collection, f"@name:{name}", "LIMIT", "0", "1"
            )
            return len(results) > 1  # First element is count
        except Exception:
            return False

    def insert(
        self, documents: List[Document], filters: Optional[Dict[str, Any]] = None, batch_size: int = 100
    ) -> None:
        """Insert documents into the database."""
        if not documents:
            return

        # Prepare data for bulk insertion
        data_to_insert = []
        for doc in documents:
            if not self._validate_document(doc):
                continue

            # Get or generate embedding
            embedding = doc.embedding
            if embedding is None and self.embedder:
                embedding = self.embedder.get_embedding(doc.content)

            # Convert embedding to the format expected by RedisVL 
            if embedding is not None:
                # Convert to numpy array with correct dtype, then to bytes
                embedding = self._format_embedding(embedding)

            # Prepare document data
            doc_data = {
                "id": doc.id,
                "name": doc.name or doc.id,
                "content": self._clean_document_content(doc.content),
                "meta_data": json.dumps(doc.meta_data or {}),
                self.vector_field_name: embedding,
            }

            data_to_insert.append(doc_data)

        # Insert in batches
        for i in range(0, len(data_to_insert), batch_size):
            batch = data_to_insert[i : i + batch_size]
            try:
                if batch:  # Only insert if we have data
                    self.index.load(batch)
                    log_debug(f"Inserted batch of {len(batch)} documents")
            except Exception as e:
                log_debug(f"Error inserting batch: {e}")

    async def async_insert(
        self, documents: List[Document], filters: Optional[Dict[str, Any]] = None, batch_size: int = 100
    ) -> None:
        """Insert documents into the database asynchronously."""
        if not documents:
            return

        # Prepare data for bulk insertion
        data_to_insert = []
        for doc in documents:
            if not self._validate_document(doc):
                continue

            # Get or generate embedding
            embedding = doc.embedding
            if embedding is None and self.embedder:
                embedding = self.embedder.get_embedding(doc.content)

            # Convert embedding to the format expected by RedisVL
            if embedding is not None:
                embedding = self._format_embedding(embedding)

            # Prepare document data
            doc_data = {
                "id": doc.id,
                "name": doc.name or doc.id,
                "content": self._clean_document_content(doc.content),
                "meta_data": json.dumps(doc.meta_data or {}),
                self.vector_field_name: embedding,
            }

            data_to_insert.append(doc_data)

        # Insert in batches
        async_index = await self.get_async_index()
        for i in range(0, len(data_to_insert), batch_size):
            batch = data_to_insert[i : i + batch_size]
            try:
                if batch:  # Only insert if we have data
                    if hasattr(async_index, "aload"):
                        await async_index.aload(batch)
                    else:
                        async_index.load(batch)
                    log_debug(f"Inserted batch of {len(batch)} documents asynchronously")
            except Exception as e:
                log_debug(f"Error inserting batch asynchronously: {e}")

    def upsert_available(self) -> bool:
        """Check if upsert is available."""
        return True

    def upsert(self, documents: List[Document], filters: Optional[Dict[str, Any]] = None) -> None:
        """Upsert documents (insert or update)."""
        # RedisVL's load method handles upserts by default
        self.insert(documents, filters)

    async def async_upsert(self, documents: List[Document], filters: Optional[Dict[str, Any]] = None) -> None:
        """Upsert documents asynchronously."""
        await self.async_insert(documents, filters)

    def search(
        self,
        query: str,
        limit: int = 5,
        search_type: Optional[SearchType] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """Search for documents using the specified search type.
        
        Note: Only vector and hybrid search are supported natively by RedisVL.
        Keyword search requests will be converted to hybrid search.
        """
        effective_search_type = search_type or self.search_type

        if effective_search_type == SearchType.vector:
            return self._vector_search(query, limit, filters)
        elif effective_search_type in (SearchType.hybrid, SearchType.keyword):
            if effective_search_type == SearchType.keyword:
                log_debug("Keyword search not natively supported. Using hybrid search instead.")
            return self._hybrid_search(query, limit, filters)
        else:
            log_debug(f"Unsupported search type: {effective_search_type}. Using vector search.")
            return self._vector_search(query, limit, filters)

    def _vector_search(self, query: str, limit: int, filters: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Perform vector-based search using RedisVL's native VectorQuery."""
        try:
            if not self.embedder:
                log_debug("No embedder configured for vector search")
                return []

            # Get embedding for the query
            query_embedding = self.embedder.get_embedding(query)
            if query_embedding is None:
                log_debug(f"Error getting embedding for query: {query}")
                return []

            # For VectorQuery, use the raw numpy array instead of bytes
            query_vector = np.array(query_embedding, dtype=np.float32)

            # Create VectorQuery
            vector_query = VectorQuery(
                vector=query_vector,
                vector_field_name=self.vector_field_name,
                return_fields=["id", "name", "content", "meta_data"],
                num_results=limit,
                filter_expression=self._build_filter_expression(filters) if filters else None,
            )

            # Execute the query
            results = self.index.query(vector_query)
            return self._process_search_results(results, query)

        except Exception as e:
            log_debug(f"Error during vector search: {e}")
            return []

    def _hybrid_search(self, query: str, limit: int, filters: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Perform hybrid search using RedisVL's native HybridQuery."""
        try:
            if not self.embedder:
                log_debug("No embedder configured for hybrid search")
                return self._keyword_search(query, limit, filters)

            # Get embedding for the query
            query_embedding = self.embedder.get_embedding(query)
            if query_embedding is None:
                log_debug(f"Error getting embedding for query: {query}")
                return self._keyword_search(query, limit, filters)

            # Convert to numpy array
            query_vector = np.array(query_embedding, dtype=np.float32)

            # Create HybridQuery with both vector and text components
            hybrid_query = HybridQuery(
                vector=query_vector,
                vector_field_name=self.vector_field_name,
                text=query,
                text_fields=["content", "name"],  # Fields to search in
                return_fields=["id", "name", "content", "meta_data"],
                num_results=limit,
                filter_expression=self._build_filter_expression(filters) if filters else None,
                alpha=self.hybrid_alpha,  # Use configured balance between vector and text search
            )

            # Execute the hybrid query
            results = self.index.query(hybrid_query)
            return self._process_search_results(results, query)

        except Exception as e:
            log_debug(f"Error in hybrid search: {e}")
            # Fallback to the original implementation if HybridQuery fails
            return self._fallback_hybrid_search(query, limit, filters)

    def _keyword_search(self, query: str, limit: int, filters: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Perform keyword-based search."""
        try:
            # For keyword search, use Redis search syntax
            # Use a more flexible search pattern
            if query == "*":
                search_query = "*"
            else:
                # Search in content and name fields
                search_query = f"@content:{query}|@name:{query}"

            # Use direct Redis FT.SEARCH command to avoid encoding issues
            raw_results = self.redis_client.execute_command(
                "FT.SEARCH",
                self.collection,
                search_query,
                "RETURN",
                "4",
                "id",
                "name",
                "content",
                "meta_data",
                "LIMIT",
                "0",
                str(limit),
            )

            # Process raw results
            documents = []
            if len(raw_results) > 1:  # First element is count
                # Results come in pairs: [key, [field1, value1, field2, value2, ...]]
                for i in range(1, len(raw_results), 2):
                    # key = raw_results[i]  # Not used, skip assignment
                    fields = raw_results[i + 1] if i + 1 < len(raw_results) else []

                    # Convert fields list to dict
                    field_dict = {}
                    for j in range(0, len(fields), 2):
                        field_name = fields[j]
                        field_value = fields[j + 1] if j + 1 < len(fields) else ""

                        # Decode bytes to string
                        if isinstance(field_name, bytes):
                            field_name = field_name.decode("utf-8")
                        if isinstance(field_value, bytes):
                            field_value = field_value.decode("utf-8")

                        field_dict[field_name] = field_value

                    # Create Document
                    doc_id = field_dict.get("id", "")
                    name = field_dict.get("name", doc_id)
                    content = field_dict.get("content", "")
                    meta_data_str = field_dict.get("meta_data", "{}")

                    try:
                        meta_data = json.loads(meta_data_str) if meta_data_str else {}
                    except json.JSONDecodeError:
                        meta_data = {}

                    doc = Document(id=doc_id, name=name, content=content, meta_data=meta_data)
                    documents.append(doc)

            return documents
        except Exception as e:
            log_debug(f"Error in keyword search: {str(e)}")
            return []

    def _fallback_hybrid_search(self, query: str, limit: int, filters: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Fallback hybrid search implementation."""
        # Get vector search results
        vector_results = self._vector_search(query, limit, filters)

        # Get keyword search results
        keyword_results = self._keyword_search(query, limit, filters)

        # Combine and deduplicate results
        seen_ids = set()
        combined_results = []

        for doc in vector_results + keyword_results:
            if doc.id not in seen_ids:
                seen_ids.add(doc.id)
                combined_results.append(doc)

        # Apply reranking if available
        if self.reranker:
            combined_results = self.reranker.rerank(query=query, documents=combined_results)

        return combined_results[:limit]

    def _process_search_results(self, results: List[Dict[str, Any]], query: str) -> List[Document]:
        """Process search results into Document objects."""
        documents = []

        # Handle different result formats from RedisVL
        if hasattr(results, "docs"):
            # If results is a SearchResult object
            result_docs = results.docs
        elif isinstance(results, list):
            # If results is already a list
            result_docs = results
        else:
            # If results is some other format, try to convert
            try:
                result_docs = list(results)
            except Exception as e:
                log_debug(f"Unable to process search results format: {type(results)}, error: {e}")
                return []

        for result in result_docs:
            try:
                # Handle different result formats
                if hasattr(result, "__dict__"):
                    result_dict = result.__dict__
                elif isinstance(result, dict):
                    result_dict = result
                else:
                    log_debug(f"Unexpected result format: {type(result)}")
                    continue

                # Extract document data - decode bytes to strings if needed
                doc_id = result_dict.get("id", "")
                if isinstance(doc_id, bytes):
                    doc_id = doc_id.decode("utf-8")

                name = result_dict.get("name", doc_id)
                if isinstance(name, bytes):
                    name = name.decode("utf-8")

                content = result_dict.get("content", "")
                if isinstance(content, bytes):
                    content = content.decode("utf-8")

                meta_data_str = result_dict.get("meta_data", "{}")
                if isinstance(meta_data_str, bytes):
                    meta_data_str = meta_data_str.decode("utf-8")

                # Parse metadata
                try:
                    meta_data = json.loads(meta_data_str) if meta_data_str else {}
                except json.JSONDecodeError:
                    meta_data = {}

                # Create Document object
                doc = Document(id=doc_id, name=name, content=content, meta_data=meta_data)
                documents.append(doc)

            except Exception as e:
                log_debug(f"Error processing search result: {e}")
                continue

        if self.reranker and documents:
            documents = self.reranker.rerank(query=query, documents=documents)

        return documents

    def _build_filter_expression(self, filters: Dict[str, Any]) -> str:
        """Build filter expression for RedisVL queries."""
        if not filters:
            return ""

        # Simple filter implementation - can be extended
        filter_parts = []
        for key, value in filters.items():
            if isinstance(value, str):
                filter_parts.append(f"@{key}:{value}")
            elif isinstance(value, (int, float)):
                filter_parts.append(f"@{key}:[{value} {value}]")

        return " ".join(filter_parts)

    async def async_search(
        self,
        query: str,
        limit: int = 5,
        search_type: Optional[SearchType] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """Search for documents asynchronously."""
        effective_search_type = search_type or self.search_type

        if effective_search_type == SearchType.vector:
            return await self._async_vector_search(query, limit, filters)
        elif effective_search_type in (SearchType.hybrid, SearchType.keyword):
            if effective_search_type == SearchType.keyword:
                log_debug("Keyword search not natively supported. Using hybrid search instead.")
            return await self._async_hybrid_search(query, limit, filters)
        else:
            log_debug(f"Unsupported search type: {effective_search_type}. Using vector search.")
            return await self._async_vector_search(query, limit, filters)

    async def _async_vector_search(self, query: str, limit: int, filters: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Perform async vector-based search using RedisVL's native VectorQuery."""
        try:
            if not self.embedder:
                log_debug("No embedder configured for vector search")
                return []

            # Get embedding for the query
            query_embedding = self.embedder.get_embedding(query)
            if query_embedding is None:
                log_debug(f"Error getting embedding for query: {query}")
                return []

            # Convert to numpy array
            query_vector = np.array(query_embedding, dtype=self._get_numpy_dtype())

            # Create VectorQuery
            vector_query = VectorQuery(
                vector=query_vector,
                vector_field_name=self.vector_field_name,
                return_fields=["id", "name", "content", "meta_data"],
                num_results=limit,
                filter_expression=self._build_filter_expression(filters) if filters else None,
            )

            # Execute the query
            async_index = await self.get_async_index()
            results = await async_index.query(vector_query)
            return self._process_search_results(results, query)

        except Exception as e:
            log_debug(f"Error during async vector search: {e}")
            return []

    async def _async_hybrid_search(self, query: str, limit: int, filters: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Perform async hybrid search using RedisVL's native HybridQuery."""
        try:
            if not self.embedder:
                log_debug("No embedder configured for hybrid search")
                return []

            # Get embedding for the query
            query_embedding = self.embedder.get_embedding(query)
            if query_embedding is None:
                log_debug(f"Error getting embedding for query: {query}")
                return []

            # Convert to numpy array
            query_vector = np.array(query_embedding, dtype=self._get_numpy_dtype())

            # Create HybridQuery with both vector and text components
            hybrid_query = HybridQuery(
                vector=query_vector,
                vector_field_name=self.vector_field_name,
                text=query,
                text_field_name="content",  # Primary text field for search
                return_fields=["id", "name", "content", "meta_data"],
                num_results=limit,
                filter_expression=self._build_filter_expression(filters) if filters else None,
                alpha=self.hybrid_alpha,  # Use configured balance between vector and text search
            )

            # Execute the hybrid query
            async_index = await self.get_async_index()
            results = await async_index.query(hybrid_query)
            return self._process_search_results(results, query)

        except Exception as e:
            log_debug(f"Error in async hybrid search: {e}")
            return []

    def drop(self) -> None:
        """Drop the search index."""
        try:
            self.index.delete(drop=True)
        except Exception as e:
            log_debug(f"Error dropping index: {e}")

    async def async_drop(self) -> None:
        """Drop the search index asynchronously."""
        try:
            async_index = await self.get_async_index()
            await async_index.delete(drop=True)
        except Exception as e:
            log_debug(f"Error dropping index: {e}")

    def optimize(self) -> None:
        """Optimize the database."""
        # RedisVL doesn't provide explicit optimization methods
        # The index is automatically optimized by Redis
        log_debug("Index optimization is handled automatically by Redis")

    def delete(self) -> bool:
        """Delete the database."""
        try:
            self.drop()
            return True
        except Exception as e:
            log_debug(f"Error deleting database: {e}")
            return False

    def get_count(self) -> int:
        """Get the number of documents in the database."""
        try:
            info = self.index.info()
            return int(info.get("num_docs", 0))
        except Exception as e:
            log_debug(f"Error getting document count: {e}")
            return 0

    def _validate_document(self, document: Document) -> bool:
        """Validate a document before insertion."""
        if not document.id:
            log_debug("Document missing required 'id' field")
            return False

        if not document.content and not document.embedding:
            log_debug("Document missing both 'content' and 'embedding' fields")
            return False

        return True

    def _clean_document_content(self, content: str) -> str:
        """Clean document content for indexing."""
        if not content:
            return ""

        # Basic cleaning - remove excessive whitespace
        content = " ".join(content.split())

        # Limit content length to prevent issues
        max_length = 10000  # Adjust as needed
        if len(content) > max_length:
            content = content[:max_length]

        return content

    def close(self) -> None:
        """Close database connections."""
        if self._redis_client:
            self._redis_client.close()
            self._redis_client = None

        if self._async_redis_client:
            # Note: async client close should be awaited, but we can't do that here
            # Users should call async_close() for proper cleanup
            self._async_redis_client = None

    async def async_close(self) -> None:
        """Close database connections asynchronously."""
        if self._async_redis_client:
            await self._async_redis_client.close()
            self._async_redis_client = None

        if self._redis_client:
            self._redis_client.close()
            self._redis_client = None
