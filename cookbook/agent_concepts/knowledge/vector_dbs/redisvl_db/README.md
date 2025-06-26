# RedisVL Integration for Agno Agent Framework

A comprehensive RedisVL vector database integration for the Agno agent framework, providing powerful Redis-based vector search capabilities with full feature parity to other Agno vector database integrations.

## 🚀 Features

- **Full Vector Search**: Semantic search using embeddings with multiple distance metrics
- **Hybrid Search**: Combined vector and keyword search capabilities  
- **Async Support**: Full asynchronous operation support
- **Multiple Search Types**: Vector, keyword, and hybrid search modes
- **Flexible Configuration**: Support for different Redis configurations and embedding models
- **Quora Dataset Integration**: Special example demonstrating text question-answer search

## 📋 Prerequisites

1. **Redis Stack**: Install Redis with Search & Query capabilities:
   ```bash
   docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
   ```
   This also provides Redis Insight GUI at `http://localhost:8001`

2. **Python Environment**: Set up the development environment using Agno's dev setup:
   ```bash
   # Clone the repository (if not already done)
   git clone https://github.com/ankit201/agno.git
   cd agno
   
   # Create virtual environment and install dependencies
   ./scripts/dev_setup.sh
   
   # Activate the virtual environment
   source .venv/bin/activate
   
   # Install additional dependencies for RedisVL integration
   uv pip install pandas
   ```

3. **OpenAI API Key**: Set your API key:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

## 🛠️ Installation & Setup

The RedisVL integration is already included in the Agno framework. You can use it directly:

```python
from agno.vectordb.redisvl import RedisVL
from agno.embedder.openai import OpenAIEmbedder
```

## 📖 Usage Examples

### 1. Basic PDF Knowledge Base

```python
from agno.agent import Agent
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.vectordb.redisvl import RedisVL
from agno.embedder.openai import OpenAIEmbedder

# Create RedisVL vector store
vector_db = RedisVL(
    collection="recipes",
    host="localhost",
    port=6379,
    embedder=OpenAIEmbedder()
)

# Create knowledge base
knowledge_base = PDFUrlKnowledgeBase(
    urls=["https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"],
    vector_db=vector_db,
)

# Load and use
knowledge_base.load(recreate=False)
agent = Agent(knowledge=knowledge_base, show_tool_calls=True)
agent.print_response("How to make Thai curry?", markdown=True)
```

### 2. Hybrid Search (Vector + Keyword)

```python
from agno.vectordb.search import SearchType

vector_db = RedisVL(
    collection="recipes-hybrid",
    host="localhost", 
    port=6379,
    search_type=SearchType.hybrid,
    embedder=OpenAIEmbedder()
)

# This enables both semantic similarity and keyword matching
```

### 3. Asynchronous Operations

```python
import asyncio
from agno.agent import Agent
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.vectordb.redisvl import RedisVL

async def main():
    vector_db = RedisVL(
        collection="async-recipes",
        host="localhost",
        port=6379,
        embedder=OpenAIEmbedder()
    )
    
    knowledge_base = PDFUrlKnowledgeBase(
        urls=["https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"],
        vector_db=vector_db,
    )
    
    await knowledge_base.aload(recreate=False)
    
    agent = Agent(knowledge=knowledge_base, show_tool_calls=True)
    await agent.aprint_response("What are the ingredients for Tom Kha Gai?", markdown=True)

if __name__ == "__main__":
    asyncio.run(main())
```

### 4. Quora Dataset Integration

This example demonstrates the assignment requirements using the Quora question pairs dataset:

```python
import pandas as pd
from agno.knowledge.text import TextKnowledgeBase
from agno.vectordb.redisvl import RedisVL

# Load Quora dataset
df = pd.read_csv("data/questions.csv")

# Create RedisVL vector store
vector_db = RedisVL(
    collection="quora-questions",
    host="localhost",
    port=6379,
    embedder=OpenAIEmbedder()
)

# Populate with question1 column data
# (See full example in quora_redisvl_integration.py)
```

## 🔧 Configuration Options

```python
vector_db = RedisVL(
    collection="my-collection",        # Redis collection name
    host="localhost",                  # Redis host
    port=6379,                        # Redis port
    db=0,                             # Redis database number
    password=None,                    # Redis password (if required)
    username=None,                    # Redis username (if required)
    embedder=OpenAIEmbedder(),        # Embedding model
    distance="cosine",                # Distance metric: cosine, l2, max_inner_product
    search_type=SearchType.vector,    # Search type: vector, keyword, hybrid
    vector_index="hnsw",              # Vector index: hnsw, flat
)
```

## 📁 Example Files

1. **`redisvl_db.py`** - Basic vector search with PDF knowledge base
2. **`async_redisvl_db.py`** - Asynchronous operations example
3. **`redisvl_db_hybrid_search.py`** - Hybrid search (vector + keyword) example
4. **`quora_redisvl_integration.py`** - Complete Quora dataset integration demo

## 🧪 Testing

Run the examples:

```bash
# Basic example
python cookbook/agent_concepts/knowledge/vector_dbs/redisvl_db/redisvl_db.py

# Async example  
python cookbook/agent_concepts/knowledge/vector_dbs/redisvl_db/async_redisvl_db.py

# Hybrid search
python cookbook/agent_concepts/knowledge/vector_dbs/redisvl_db/redisvl_db_hybrid_search.py

# Quora dataset integration
python cookbook/agent_concepts/knowledge/vector_dbs/redisvl_db/quora_redisvl_integration.py
```

## 🎯 Assignment Requirements - Status

✅ **Completed:**
- Minimal RedisVL integration for Agno agent framework
- Populate vector store with new data and embeddings
- Search for records given new queries
- Quora dataset integration (question1 → populate, question2 → query)
- Full async support
- Hybrid search capabilities
- Comprehensive cookbook examples
- Vector database integration following Agno patterns

✅ **Integration Features:**
- Follows Agno VectorDb base class pattern
- Supports all search types (vector, keyword, hybrid)
- Async/await support throughout
- Proper error handling and logging
- Distance metric support (cosine, L2, inner product)
- Configurable Redis connection parameters
- Integration with Agno embedders and rerankers

## 📚 Redis Vector Library (RedisVL) Features

This integration leverages the full power of RedisVL:
- **Index Management**: Automatic schema creation and management
- **Advanced Vector Search**: HNSW and FLAT vector indices
- **Hybrid Queries**: Combining vector similarity and keyword matching
- **Filtering**: Advanced query filtering capabilities
- **Performance**: Optimized for high-throughput applications

## 🔍 Troubleshooting

1. **Redis Connection Issues**: Ensure Redis Stack is running on port 6379
2. **Memory Issues**: Monitor Redis memory usage for large datasets
3. **Embedding Errors**: Verify OpenAI API key is properly set
4. **Index Creation**: Check Redis logs if index creation fails

## 🤝 Contributing

This integration follows Agno's patterns and can be extended with:
- Additional distance metrics
- Custom embedding models
- Advanced filtering capabilities
- Performance optimizations

For questions or improvements, refer to the main Agno documentation and RedisVL documentation. 