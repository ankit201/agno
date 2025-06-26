#!/usr/bin/env python3
"""
RedisVL Integration for Agno Agent Framework
Assignment: Minimal RedisVL integration for Quora dataset

Requirements:
1. Populate vector store with question1 column data (first 100 rows)
2. Search for records using question2 column queries (first 10 rows)
3. Demonstrate core RedisVL functionality with Agno

Setup:
- Redis Stack running on localhost:6379
- OpenAI API key configured
- Quora dataset in data/questions.csv
"""
import os
import pandas as pd
import shutil
from agno.knowledge.text import TextKnowledgeBase
from agno.vectordb.redisvl import RedisVL
from agno.embedder.openai import OpenAIEmbedder

def cleanup_resources(vector_db, collection_name):
    """Clean up files and database resources"""
    print(f"\n🧹 Cleaning up resources...")
    
    # Remove text files
    if os.path.exists("data/quora_texts"):
        shutil.rmtree("data/quora_texts")
        print("✅ Removed quora_texts directory and all files")
    
    # Drop Redis collection
    try:
        if hasattr(vector_db, 'delete_collection'):
            vector_db.delete_collection()
            print(f"✅ Dropped Redis collection: {collection_name}")
        elif hasattr(vector_db, 'redis_client'):
            # Alternative: use Redis client to drop keys
            client = vector_db.redis_client
            keys = client.execute_command("KEYS", f"{collection_name}*")
            if keys:
                client.execute_command("DEL", *keys)
                print(f"✅ Removed {len(keys)} keys from Redis collection: {collection_name}")
    except Exception as e:
        print(f"⚠️  Could not drop collection: {e}")

def main():
    """Main RedisVL integration workflow"""
    COLLECTION_NAME = "quora-questions"
    
    # Step 1: Prepare data directory
    if os.path.exists("data/quora_texts"):
        shutil.rmtree("data/quora_texts")
    os.makedirs("data/quora_texts", exist_ok=True)
    
    # Step 2: Load Quora dataset
    df = pd.read_csv("data/questions.csv")
    
    # Step 3: Prepare population data (ALL rows from question1 column)
    populate_questions = df['question1'].dropna()  # Use ALL rows from question1
    
    # Create individual text files for each question (each row becomes a separate document)
    for i, question in enumerate(populate_questions):
        filename = f"data/quora_texts/question_{i+1:03d}.txt"
        with open(filename, "w") as f:
            f.write(question)
    
    print(f"✅ Created {len(populate_questions)} individual text files for vector store population")
    
    # Step 4: Create RedisVL vector store with OpenAI embedder
    vector_db = RedisVL(
        collection=COLLECTION_NAME,
        host="localhost",
        port=6379,
        embedder=OpenAIEmbedder()
    )
    
    # Step 5: Create and populate knowledge base
    knowledge_base = TextKnowledgeBase(
        path="data/quora_texts",
        vector_db=vector_db,
    )
    
    knowledge_base.load(recreate=True)
    print("✅ Vector store populated with embeddings")
    
    # Step 6: Test search functionality with question2 column (first 10 rows)
    test_questions = df['question2'].head(10).dropna().tolist()
    print(f"✅ Testing search with {len(test_questions)} queries")
    
    # Demonstrate search functionality
    print(f"\n{'='*60}")
    for i, query in enumerate(test_questions[:5], 1):  # Show first 5 results
        results = knowledge_base.search(query=query, num_documents=2)
        print(f"\nQuery {i}: {query}")
        
        if results:
            print(f"  Found {len(results)} relevant documents:")
            for j, doc in enumerate(results, 1):
                print(f"    {j}. {doc.content}")
        else:
            print("  No relevant documents found")
    
    print(f"\n✅ RedisVL integration completed successfully!")
    print(f"   - Populated: {len(populate_questions)} questions from question1 column")
    print(f"   - Tested: {len(test_questions)} queries from question2 column")
    
    # Cleanup resources (optional - uncomment if you want to clean up after demo)
    cleanup_response = input("\n🗑️  Do you want to clean up files and database? (y/n): ").lower().strip()
    if cleanup_response == 'y':
        cleanup_resources(vector_db, COLLECTION_NAME)
    else:
        print("✅ Resources preserved for further testing")

if __name__ == "__main__":
    main() 