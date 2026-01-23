import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set PYTHONPATH to include the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aeo_blog_engine.knowledge.knowledge_base import get_knowledge_base

def test_retrieval():
    print("Connecting to Qdrant Cloud...")
    try:
        kb = get_knowledge_base()
        
        # Test 1: General Brand Knowledge
        brand = "Minimalist"
        query = f"What is the brand philosophy of {brand}?"
        print(f"\n--- Testing Retrieval for: {brand} ---")
        print(f"Query: {query}")
        
        results = kb.search(query, limit=2)
        
        if results:
            for i, res in enumerate(results):
                content = getattr(res, 'content', 'No content')
                print(f"\nMatch {i+1}:")
                print(content[:300] + "...")
        else:
            print("No results found for brand query.")

    except Exception as e:
        import traceback
        print(f"\nVerification Failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_retrieval()
