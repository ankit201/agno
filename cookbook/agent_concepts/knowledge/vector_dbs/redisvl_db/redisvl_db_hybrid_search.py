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

# Redis VL with hybrid search configuration
vector_db = RedisVL(
    collection=COLLECTION_NAME,
    host="localhost",
    port=6379,
    embedder=OpenAIEmbedder(),
    search_type=SearchType.hybrid,  # Enable hybrid search
    hybrid_alpha=0.7,  # Balance between vector (0.7) and text (0.3) search
)

knowledge_base = PDFUrlKnowledgeBase(
    urls=["https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"],
    vector_db=vector_db,
)

knowledge_base.load(recreate=False)  # Comment out after first run

# Create and use the agent with hybrid search
agent = Agent(knowledge=knowledge_base, show_tool_calls=True)

print("🔍 Using Hybrid Search (combines vector similarity + text matching)")
print("=" * 60)

# Test hybrid search queries
queries = [
    "How to make Thai curry?",
    "coconut soup recipe",
    "spicy pad thai ingredients",
    "traditional Thai desserts"
]

for query in queries:
    print(f"\n📝 Query: {query}")
    print("-" * 40)
    agent.print_response(query, markdown=True)
    print("\n")
