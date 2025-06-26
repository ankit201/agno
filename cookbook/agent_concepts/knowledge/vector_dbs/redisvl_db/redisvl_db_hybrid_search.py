"""
RedisVL Database with Native Hybrid Search

This example demonstrates RedisVL's improved hybrid search using native HybridQuery
for better performance and scoring compared to basic vector + keyword combination.
"""

from agno.agent import Agent
from agno.embedder.openai import OpenAIEmbedder
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.vectordb.redisvl import RedisVL
from agno.vectordb.search import SearchType

COLLECTION_NAME = "thai-recipes-hybrid"

# Configure RedisVL with improved native hybrid search
vector_db = RedisVL(
    collection=COLLECTION_NAME,
    host="localhost",
    port=6379,
    search_type=SearchType.hybrid,  # Uses native HybridQuery for optimized search
    embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    hybrid_alpha=0.7,  # 70% vector, 30% text - configurable balance (0.0=text only, 1.0=vector only)
)

knowledge_base = PDFUrlKnowledgeBase(
    urls=["https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"],
    vector_db=vector_db,
)

knowledge_base.load(recreate=False)  # Comment out after first run

# Create and use the agent with improved hybrid search
agent = Agent(
    knowledge=knowledge_base,
    show_tool_calls=True,
    search_knowledge=True,
)

print("🔍 Testing RedisVL Native Hybrid Search (70% vector, 30% text)")
print("=" * 60)

# This will use RedisVL's native HybridQuery for optimized hybrid search
agent.print_response("Find recipes with coconut milk and curry paste", markdown=True)

print("\n" + "=" * 60)

# Test with another hybrid search query
agent.print_response("Show me spicy Thai soup recipes", markdown=True)
