from agno.agent import Agent
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.vectordb.redisvl import RedisVL
<<<<<<< HEAD
from agno.embedder.openai import OpenAIEmbedder

COLLECTION_NAME = "thai-recipes"

vector_db = RedisVL(
    collection=COLLECTION_NAME, 
    host="localhost", 
    port=6379,
    embedder=OpenAIEmbedder()  # Add embedder for vector search
)
=======

COLLECTION_NAME = "thai-recipes"

vector_db = RedisVL(collection=COLLECTION_NAME, host="localhost", port=6379)
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53

knowledge_base = PDFUrlKnowledgeBase(
    urls=["https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"],
    vector_db=vector_db,
)

knowledge_base.load(recreate=False)  # Comment out after first run

# Create and use the agent
agent = Agent(knowledge=knowledge_base, show_tool_calls=True)
<<<<<<< HEAD
agent.print_response("How to make Thai curry?", markdown=True)
=======
agent.print_response("How to make Thai curry?", markdown=True) 
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
