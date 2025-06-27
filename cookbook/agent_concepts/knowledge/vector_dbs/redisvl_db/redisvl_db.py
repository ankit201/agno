"""Basic RedisVL vector database example with Agno.

Requirements:
- pip install redisvl redis
- Redis server with RedisSearch module (Redis Stack recommended)
"""

from agno.agent import Agent
from agno.embedder.openai import OpenAIEmbedder
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.vectordb.redisvl import RedisVL

COLLECTION_NAME = "thai-recipes"

# Create vector database
vector_db = RedisVL(
    collection=COLLECTION_NAME,
    host="localhost",
    port=6379,
    embedder=OpenAIEmbedder(),
)

# Create knowledge base
knowledge_base = PDFUrlKnowledgeBase(
    urls=["https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"],
    vector_db=vector_db,
)

# Load knowledge base (comment out after first run)
knowledge_base.load(recreate=False)

# Create and use the agent
agent = Agent(knowledge=knowledge_base, show_tool_calls=True)

if __name__ == "__main__":
    agent.print_response("What are the ingredients for Tom Kha Gai?", markdown=True)
