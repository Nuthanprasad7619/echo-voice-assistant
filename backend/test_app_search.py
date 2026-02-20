import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import search_duckduckgo

def test_search_cases():
    print("--- Testing App Search Logic ---")
    
    # Case 1: General Knowledge
    query1 = "Who is the CEO of Tesla"
    print(f"\nQuery 1: {query1}")
    res1 = search_duckduckgo(query1)
    print(f"Result 1: {res1}")
    
    # Case 2: Latest/News (should trigger timelimit='d')
    query2 = "latest news about SpaceX"
    print(f"\nQuery 2: {query2}")
    res2 = search_duckduckgo(query2)
    print(f"Result 2: {res2}")
    
    # Case 4: Logical Thinking (Wikipedia Integration)
    query4 = "Who is the Prime Minister of India"
    print(f"\nQuery 4: {query4}")
    from app import generate_response, predict_intent # Import here to avoid circular issues if any
    intent4 = predict_intent(query4)
    res4 = generate_response(intent4, query4)
    print(f"Result 4: {res4}")

    query5 = "What is a mitochondrion"
    print(f"\nQuery 5: {query5}")
    res5 = generate_response(None, query5)
    print(f"Result 5: {res5}")

if __name__ == "__main__":
    # Fix encoding for Windows console if needed
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    test_search_cases()
