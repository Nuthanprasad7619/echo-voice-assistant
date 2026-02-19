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
    
    # Case 3: Current price (should trigger timelimit='d')
    query3 = "current price of ethereum"
    print(f"\nQuery 3: {query3}")
    res3 = search_duckduckgo(query3)
    print(f"Result 3: {res3}")

if __name__ == "__main__":
    test_search_cases()
