from agno.agent import Agent
from agno.embedder.openai import OpenAIEmbedder
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.vectordb.redisvl import RedisVL
from agno.vectordb.search import SearchType

COLLECTION_NAME = "thai-recipes"

# Configure RedisVL with hybrid search (combines vector and keyword search)
vector_db = RedisVL(
    collection=COLLECTION_NAME,
    host="localhost",
    port=6379,
    search_type=SearchType.hybrid,  # Enables both vector and keyword search
    embedder=OpenAIEmbedder(),  # Add embedder for vector search functionality
)

knowledge_base = PDFUrlKnowledgeBase(
    urls=["https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"],
    vector_db=vector_db,
)

knowledge_base.load(recreate=False)  # Comment out after first run

# Create and use the agent with hybrid search capabilities
agent = Agent(
    knowledge=knowledge_base,
    show_tool_calls=True,
    search_knowledge=True,
)

# This will use both vector similarity and keyword matching
agent.print_response("Find recipes with coconut milk and curry paste", markdown=True)

# Test with another hybrid search
agent.print_response("Show me spicy Thai soup recipes", markdown=True)
