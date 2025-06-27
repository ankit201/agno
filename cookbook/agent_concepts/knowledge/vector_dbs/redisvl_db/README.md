# Redis VL Vector Database Integration

This directory contains examples for using Redis VL (Vector Library) as a vector database backend in Agno.

## Quick Start

### Prerequisites

1. **Start Redis Stack:**
   ```bash
   docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
   ```

2. **Set OpenAI API Key:**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

### Basic Usage

```python
from agno.vectordb.redisvl import RedisVL
from agno.embedder.openai import OpenAIEmbedder

vector_db = RedisVL(
    collection="my_collection",
    host="localhost",
    port=6379,
    embedder=OpenAIEmbedder(),
)
```

## Configuration Options

The Redis VL integration supports various configuration options:

- **Vector algorithms**: `hnsw` (default) or `flat`
- **Data types**: `FLOAT32` (default), `FLOAT64`, `FLOAT16`, `BFLOAT16`
- **Storage types**: `hash` (default) or `json`
- **HNSW tuning**: `hnsw_m`, `hnsw_ef_construction`, `hnsw_ef_runtime`
- **Custom schemas**: Via `schema_dict` or `schema_yaml_path`

### Example with Custom Configuration

```python
vector_db = RedisVL(
    collection="advanced_collection",
    vector_index="hnsw",
    vector_datatype="FLOAT32",
    hnsw_m=32,
    hnsw_ef_construction=400,
    embedder=OpenAIEmbedder(),
)
```

## Examples

- `redisvl_db.py` - Basic usage example
- `test_redisvl_configurations.py` - Test different configurations
- `redisvl_db_hybrid_search.py` - Hybrid search example
- `async_redisvl_db.py` - Async operations

## Backward Compatibility

The implementation is fully backward compatible. Existing code will continue to work unchanged:

```python
# This still works exactly as before
vector_db = RedisVL(collection="test", embedder=embedder)
```

## Performance Tips

1. **HNSW vs FLAT**: Use HNSW for large datasets (>1M vectors), FLAT for small datasets with perfect accuracy needs
2. **Memory optimization**: Use `FLOAT16` for memory-constrained environments
3. **Performance tuning**: Adjust HNSW parameters based on your accuracy/speed requirements

For detailed configuration options and advanced usage, see `test_redisvl_configurations.py`. 