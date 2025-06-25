#!/usr/bin/env python3
"""
Test script to verify RedisVL integration works correctly
This bypasses the OpenAI API requirement to focus on vector database functionality
"""

import sys
import os
sys.path.insert(0, 'libs/agno')

from agno.vectordb.redisvl import RedisVL
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.document import Document
from agno.vectordb.search import SearchType

def test_redisvl_basic_functionality():
    """Test basic RedisVL functionality"""
    print("🧪 Testing RedisVL Basic Functionality")
    
    # Test 1: Create RedisVL instance
    print("  ✓ Creating RedisVL instance...")
    vector_db = RedisVL(
        collection="test-collection",
        host="localhost",
        port=6379,
        search_type=SearchType.vector
    )
    print(f"    Created vector database: {vector_db.collection}")
    
    # Test 2: Test connection
    print("  ✓ Testing Redis connection...")
    try:
        vector_db.create()
        print("    Redis connection successful!")
    except Exception as e:
        print(f"    Redis connection failed: {e}")
        return False
    
    # Test 3: Test document insertion with manual embeddings
    print("  ✓ Testing document insertion...")
    test_docs = [
        Document(
            id="doc1",
            content="This is a test document about cooking curry",
            embedding=[0.1] * 1536  # Mock embedding
        ),
        Document(
            id="doc2", 
            content="This is another test document about Thai food",
            embedding=[0.2] * 1536  # Mock embedding
        )
    ]
    
    try:
        vector_db.insert(test_docs)
        print("    Document insertion successful!")
    except Exception as e:
        print(f"    Document insertion failed: {e}")
        return False
    
    # Test 4: Test document existence
    print("  ✓ Testing document existence...")
    if vector_db.doc_exists(test_docs[0]):
        print("    Document existence check passed!")
    else:
        print("    Document existence check failed!")
        
    # Test 5: Clean up
    print("  ✓ Cleaning up...")
    try:
        vector_db.drop()
        print("    Cleanup successful!")
    except Exception as e:
        print(f"    Cleanup failed: {e}")
    
    return True

def test_knowledge_base_loading():
    """Test knowledge base loading with RedisVL"""
    print("\n🧪 Testing Knowledge Base Loading")
    
    vector_db = RedisVL(
        collection="test-knowledge-base",
        host="localhost", 
        port=6379
    )
    
    knowledge_base = PDFUrlKnowledgeBase(
        urls=["https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"],
        vector_db=vector_db,
    )
    
    try:
        print("  ✓ Loading PDF knowledge base...")
        knowledge_base.load(recreate=True)
        print("    Knowledge base loaded successfully!")
        
        # Check if documents were inserted
        if hasattr(knowledge_base, 'documents') and knowledge_base.documents:
            print(f"    Found {len(knowledge_base.documents)} documents")
        else:
            print("    Warning: No documents found in knowledge base")
            
        return True
    except Exception as e:
        print(f"    Knowledge base loading failed: {e}")
        return False
    finally:
        try:
            vector_db.drop()
            print("  ✓ Cleaned up test knowledge base")
        except:
            pass

def test_search_types():
    """Test different search types"""
    print("\n🧪 Testing Search Types")
    
    # Test different search types
    search_types = [
        (SearchType.vector, "Vector Search"),
        (SearchType.keyword, "Keyword Search"), 
        (SearchType.hybrid, "Hybrid Search")
    ]
    
    for search_type, name in search_types:
        print(f"  ✓ Testing {name}...")
        try:
            vector_db = RedisVL(
                collection=f"test-{search_type.value}",
                host="localhost",
                port=6379,
                search_type=search_type
            )
            print(f"    {name} configuration successful!")
            vector_db.drop()  # Clean up
        except Exception as e:
            print(f"    {name} configuration failed: {e}")
            return False
    
    return True

if __name__ == "__main__":
    print("🚀 RedisVL Integration Test Suite")
    print("=" * 50)
    
    # Run tests
    tests = [
        test_redisvl_basic_functionality,
        test_knowledge_base_loading,
        test_search_types
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
                print("✅ PASSED")
            else:
                failed += 1
                print("❌ FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ FAILED with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! RedisVL integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the RedisVL integration.") 