import json
from typing import Any, Dict, List, Optional

try:
    import numpy as np
    import redis
    from redisvl.index import SearchIndex
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
    """RedisVL vector database implementation for Agno."""

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
            search_type (SearchType): Type of search to perform
            vector_index (str): Vector index type ('hnsw' or 'flat')
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
        self.search_type = search_type
        self.vector_index = vector_index
        self.hybrid_alpha = hybrid_alpha

        # Initialize schema and index as None - they'll be created lazily
        self._schema: Optional[IndexSchema] = None
        self._index: Optional[SearchIndex] = None
        self._redis_client: Optional[redis.Redis] = None

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
    def schema(self) -> IndexSchema:
        """Get or create the RedisVL IndexSchema."""
        if self._schema is None:
            log_debug("Creating RedisVL IndexSchema")

            # Create schema with proper configuration
            schema_dict = {
                "index": {"name": self.collection, "prefix": f"{self.collection}:", "storage_type": "hash"},
                "fields": [
                    {"name": "id", "type": "tag"},
                    {"name": "name", "type": "text"},
                    {"name": "content", "type": "text"},
                    {"name": "meta_data", "type": "text"},
                    {
                        "name": "embedding",
                        "type": "vector",
                        "attrs": {
                            "dims": self.dimensions,
                            "distance_metric": self._get_distance_metric(),
                            "algorithm": "HNSW",
                            "datatype": "FLOAT32",
                        },
                    },
                ],
            }

            self._schema = IndexSchema.from_dict(schema_dict)
            log_debug(f"Created schema: {self._schema}")

        return self._schema

    @property
    def index(self) -> SearchIndex:
        """Get or create the RedisVL SearchIndex."""
        if self._index is None:
            log_debug("Creating RedisVL SearchIndex")
            self._index = SearchIndex(schema=self.schema, redis_client=self.redis_client)
        return self._index

    def _get_distance_metric(self) -> str:
        """Convert Distance enum to RedisVL distance metric."""
        distance_mapping = {Distance.cosine: "COSINE", Distance.l2: "L2", Distance.max_inner_product: "IP"}
        return distance_mapping.get(self.distance, "COSINE")

    def _format_embedding(self, embedding):
        """Convert embedding to proper format for RedisVL.

        For Hash storage (which Agno uses), RedisVL expects embeddings as byte strings.
        For JSON storage, RedisVL expects embeddings as lists of floats.
        """
        if embedding is None:
            return None

        # Since we use Hash storage, convert to byte strings
        if isinstance(embedding, list):
            return np.array(embedding, dtype=np.float32).tobytes()
        elif isinstance(embedding, np.ndarray):
            return embedding.astype(np.float32).tobytes()
        else:
            # Try to convert to numpy array then bytes
            try:
                return np.array(embedding, dtype=np.float32).tobytes()
            except Exception:
                log_debug(f"Could not convert embedding of type {type(embedding)} to bytes")
                return None

    @property
    def dimensions(self) -> int:
        """Get embedding dimensions from embedder."""
        if self.embedder and self.embedder.dimensions:
            return self.embedder.dimensions
        return 1536  # Default OpenAI embedding dimension

    def create(self) -> None:
        """Create the index if it doesn't exist."""
        if not self.exists():
            log_debug(f"Creating index: {self.collection}")
            self.index.create()
        else:
            log_debug(f"Index {self.collection} already exists")

    async def async_create(self) -> None:
        """Create the index asynchronously if it doesn't exist."""
        if not await self.async_exists():
            log_debug(f"Creating index asynchronously: {self.collection}")
            # RedisVL's create() method is not async, so we call it synchronously
            self.index.create()
        else:
            log_debug(f"Index {self.collection} already exists")

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
            return await self.index.exists()
        except Exception:
            return False

    def doc_exists(self, document: Document) -> bool:
        """Check if a document exists in the index."""
        try:
            return bool(self.index.get(document.id))
        except Exception:
            return False

    async def async_doc_exists(self, document: Document) -> bool:
        """Check if a document exists in the index asynchronously."""
        try:
            return bool(await self.index.get(document.id))
        except Exception:
            return False

    def name_exists(self, name: str) -> bool:
        """Check if a document with given name exists."""
        try:
            # Use text search to find documents by name
            results = self.index.search(name, return_fields=["name"])
            return bool(results and any(r.get("name") == name for r in results))
        except Exception:
            return False

    async def async_name_exists(self, name: str) -> bool:
        """Check if a document with given name exists asynchronously."""
        try:
            results = await self.index.search(name, return_fields=["name"])
            return bool(results and any(r.get("name") == name for r in results))
        except Exception:
            return False

    def insert(
        self, documents: List[Document], filters: Optional[Dict[str, Any]] = None, batch_size: int = 100
    ) -> None:
        """Insert documents into the index.

        Args:
            documents (List[Document]): List of documents to insert
            filters (Optional[Dict[str, Any]]): Optional filters to apply to documents
            batch_size (int): Number of documents to insert in each batch
        """
        if not documents:
            return

        # Ensure index exists
        self.create()

        # Process documents in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            batch_data = []

            for doc in batch:
                # Get embedding if not already present
                if doc.embedding is None and self.embedder:
                    doc.embedding = self.embedder.get_embedding(doc.content)

                # Skip documents without embeddings if no embedder is configured
                if doc.embedding is None:
                    log_debug(f"Skipping document {doc.id} - no embedding available and no embedder configured")
                    continue

                # Prepare document data for RedisVL
                doc_data = {
                    "id": doc.id,
                    "name": doc.name or doc.id,
                    "content": doc.content,
                    "meta_data": json.dumps(doc.meta_data) if doc.meta_data else "{}",
                    "embedding": self._format_embedding(doc.embedding),
                }
                batch_data.append(doc_data)

            # Insert batch using RedisVL
            try:
                if batch_data:  # Only insert if we have data
                    self.index.load(batch_data)
                    log_debug(f"Inserted batch of {len(batch_data)} documents")
            except Exception as e:
                log_debug(f"Error inserting batch: {e}")
                raise

    async def async_insert(
        self, documents: List[Document], filters: Optional[Dict[str, Any]] = None, batch_size: int = 100
    ) -> None:
        """Insert documents asynchronously.

        Args:
            documents (List[Document]): List of documents to insert
            filters (Optional[Dict[str, Any]]): Optional filters to apply to documents
            batch_size (int): Number of documents to insert in each batch
        """
        if not documents:
            return

        # Ensure index exists
        await self.async_create()

        # Process documents in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            batch_data = []

            for doc in batch:
                # Get embedding if not already present
                if doc.embedding is None and self.embedder:
                    doc.embedding = self.embedder.get_embedding(doc.content)

                # Skip documents without embeddings if no embedder is configured
                if doc.embedding is None:
                    log_debug(f"Skipping document {doc.id} - no embedding available and no embedder configured")
                    continue

                # Prepare document data for RedisVL
                doc_data = {
                    "id": doc.id,
                    "name": doc.name or doc.id,
                    "content": doc.content,
                    "meta_data": json.dumps(doc.meta_data) if doc.meta_data else "{}",
                    "embedding": self._format_embedding(doc.embedding),
                }
                batch_data.append(doc_data)

            # Insert batch using RedisVL
            try:
                if batch_data:  # Only insert if we have data
                    if hasattr(self.index, "aload"):
                        await self.index.aload(batch_data)
                    else:
                        self.index.load(batch_data)
                    log_debug(f"Inserted batch of {len(batch_data)} documents asynchronously")
            except Exception as e:
                log_debug(f"Error inserting batch asynchronously: {e}")
                # Try inserting documents one by one
                for data in batch_data:
                    try:
                        if hasattr(self.index, "aload"):
                            await self.index.aload([data])
                        else:
                            self.index.load([data])
                        log_debug(f"Inserted document asynchronously: {data['name']}")
                    except Exception as e:
                        log_debug(f"Error inserting document {data['name']} asynchronously: {e}")

    def upsert_available(self) -> bool:
        """Check if upsert operation is available."""
        return True

    def upsert(self, documents: List[Document], filters: Optional[Dict[str, Any]] = None) -> None:
        """Upsert (insert or update) documents in the index.

        RedisVL's add_document/add_documents handle upsert automatically.
        """
        self.insert(documents, filters)

    async def async_upsert(self, documents: List[Document], filters: Optional[Dict[str, Any]] = None) -> None:
        """Upsert documents asynchronously.

        RedisVL's add_document/add_documents handle upsert automatically.
        """
        await self.async_insert(documents, filters)

    def search(
        self,
        query: str,
        limit: int = 5,
        search_type: Optional[SearchType] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """Search for documents."""
        # Use instance search_type if not provided
        if search_type is None:
            search_type = self.search_type

        if search_type == SearchType.vector:
            return self._vector_search(query, limit, filters)
        elif search_type == SearchType.keyword:
            return self._keyword_search(query, limit, filters)
        else:  # hybrid search
            return self._hybrid_search(query, limit, filters)

    def _vector_search(self, query: str, limit: int, filters: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Perform vector similarity search."""
        if not self.embedder:
            log_debug("No embedder configured for vector search")
            return []

        query_embedding = self.embedder.get_embedding(query)
        if query_embedding is None:
            log_debug(f"Error getting embedding for query: {query}")
            return []

        try:
            # For VectorQuery, use the raw numpy array instead of bytes
            query_vector = np.array(query_embedding, dtype=np.float32)

            vector_query = VectorQuery(
                vector=query_vector,
                vector_field_name="embedding",
                return_fields=["id", "name", "content", "meta_data"],
                num_results=limit,
                filter_expression=self._build_filter_expression(filters) if filters else None,
            )

            results = self.index.query(vector_query)
            return self._process_search_results(results, query)
        except Exception as e:
            log_debug(f"Error during vector search: {e}")
            return []

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
            import traceback

            traceback.print_exc()
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
                vector_field_name="embedding",
                text=query,
                text_fields=["content", "name"],  # Fields to search in
                return_fields=["id", "name", "content", "meta_data", "vector_distance"],
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
        """Build RedisVL filter expression from filters dict."""
        expressions = []
        for key, value in filters.items():
            if isinstance(value, str):
                expressions.append(f"@{key}:{value}")
            elif isinstance(value, (int, float)):
                expressions.append(f"@{key}:[{value} {value}]")

        return " ".join(expressions) if expressions else ""

    async def async_search(
        self,
        query: str,
        limit: int = 5,
        search_type: Optional[SearchType] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """Search for similar documents asynchronously."""
        # Use instance search_type if not provided
        if search_type is None:
            search_type = self.search_type

        if search_type == SearchType.vector:
            if not self.embedder:
                log_debug("No embedder configured for vector search")
                return []

            query_embedding = self.embedder.get_embedding(query)
            if query_embedding is None:
                log_debug(f"Error getting embedding for query: {query}")
                return []

            # For VectorQuery, use the raw numpy array instead of bytes
            query_vector = np.array(query_embedding, dtype=np.float32)

            vector_query = VectorQuery(
                vector=query_vector,
                vector_field_name="embedding",
                return_fields=["id", "name", "content", "meta_data", "vector_distance"],
                num_results=limit,
                filter_expression=self._build_filter_expression(filters) if filters else None,
            )

            try:
                results = await self.index.query(vector_query)
                return self._process_search_results(results, query)
            except Exception as e:
                log_debug(f"Error in async vector search: {e}")
                return []
        else:
            # For keyword and hybrid search, use sync implementation for now
            # as RedisVL doesn't provide async text search yet
            return self.search(query, limit, search_type, filters)

    def drop(self) -> None:
        """Drop the index."""
        if self.exists():
            log_debug(f"Dropping index: {self.collection}")
            self.index.delete(drop=True)

    async def async_drop(self) -> None:
        """Drop the index asynchronously."""
        try:
            if await self.async_exists():
                log_debug(f"Dropping index asynchronously: {self.collection}")
                await self.index.drop()
        except Exception as e:
            log_debug(f"Error dropping index asynchronously: {str(e)}")

    def optimize(self) -> None:
        """Optimize the index.

        RedisVL handles optimization automatically, but we can force a reindex
        if needed.
        """
        try:
            if self.exists():
                log_debug(f"Optimizing index: {self.collection}")
                # Force reindex while keeping data
                self.index.create(overwrite=True, drop=False)
        except Exception as e:
            log_debug(f"Error optimizing index: {str(e)}")

    def delete(self) -> bool:
        """Delete all documents from the index.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self.exists():
                log_debug(f"Deleting all documents from index: {self.collection}")
                self.drop()
                self.create()
                return True
        except Exception as e:
            log_debug(f"Error deleting documents: {str(e)}")
        return False

    def get_count(self) -> int:
        """Get the number of documents in the index.

        Returns:
            int: Number of documents in the index
        """
        try:
            if self.exists():
                # Use FT.INFO to get document count directly
                info = self.redis_client.execute_command("FT.INFO", self.collection)
                # info is a list where 'num_docs' appears before its value
                for i, item in enumerate(info):
                    if isinstance(item, bytes) and item.decode("utf-8") == "num_docs":
                        return int(info[i + 1])
                    elif isinstance(item, str) and item == "num_docs":
                        return int(info[i + 1])
        except Exception as e:
            log_debug(f"Error getting document count: {str(e)}")
        return 0

    def _validate_document(self, document: Document) -> bool:
        """Validate a document before insertion.

        Args:
            document (Document): Document to validate

        Returns:
            bool: True if valid, False otherwise
        """
        if not document.content:
            log_debug(f"Document {document.id} has no content")
            return False

        if not document.id:
            log_debug("Document has no ID")
            return False

        return True

    def _clean_document_content(self, content: str) -> str:
        """Clean document content for storage.

        Args:
            content (str): Content to clean

        Returns:
            str: Cleaned content
        """
        # Remove null bytes
        content = content.replace("\x00", "\ufffd")

        # Remove excessive whitespace
        content = " ".join(content.split())

        return content

    def close(self) -> None:
        """Close the RedisVL connection."""
        self._index = None
        self._schema = None
        self._redis_client = None
