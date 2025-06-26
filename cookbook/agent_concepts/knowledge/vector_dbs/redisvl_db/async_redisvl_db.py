import asyncio

from agno.agent import Agent
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.vectordb.redisvl import RedisVL
from agno.embedder.openai import OpenAIEmbedder

COLLECTION_NAME = "thai-recipes"


async def main():
    vector_db = RedisVL(
        collection=COLLECTION_NAME, 
        host="localhost", 
        port=6379,
        embedder=OpenAIEmbedder()  # Add embedder for vector search functionality
    )

    knowledge_base = PDFUrlKnowledgeBase(
        urls=["https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"],
        vector_db=vector_db,
    )

    await knowledge_base.aload(recreate=False)  # Comment out after first run

    # Create and use the agent
    agent = Agent(knowledge=knowledge_base, show_tool_calls=True)
<<<<<<< HEAD
    await agent.aprint_response(
        "What are the ingredients for Tom Kha Gai?", markdown=True
    )


if __name__ == "__main__":
    asyncio.run(main())
=======
    await agent.aprint_response("What are the ingredients for Tom Kha Gai?", markdown=True)


if __name__ == "__main__":
    asyncio.run(main()) 
>>>>>>> 9ad779499e224522529d206d7dcfb2b978213f53
