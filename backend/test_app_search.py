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
    
    from app import generate_response, predict_intent, conversation_manager # Import here to avoid circular issues if any
    
    # Case 4: Logical Thinking (Wikipedia Integration)
    query4 = "Who is the Prime Minister of India"
    print(f"\nQuery 4: {query4}")
    intent4 = predict_intent(query4)
    res4 = generate_response(intent4, query4)
    print(f"Result 4: {res4}")

    query5 = "What is a mitochondrion"
    print(f"\nQuery 5: {query5}")
    res5 = generate_response(None, query5)
    print(f"Result 5: {res5}")

    # Case 6: Context Awareness
    print("\n--- Testing Context Awareness ---")
    session_id = "test_session_final"
    q6a = "what do we celebrate on August 15"
    print(f"User: {q6a}")
    intent6a = predict_intent(q6a)
    res6a = generate_response(intent6a, q6a, session_id)
    conversation_manager.add_message(session_id, 'user', q6a, intent6a)
    conversation_manager.add_message(session_id, 'assistant', res6a, intent6a)
    print(f"Assistant: {res6a}")

    q6b = "in India"
    print(f"User: {q6b}")
    intent6b = predict_intent(q6b)
    res6b = generate_response(intent6b, q6b, session_id)
    conversation_manager.add_message(session_id, 'user', q6b, intent6b)
    conversation_manager.add_message(session_id, 'assistant', res6b, intent6b)
    print(f"Assistant: {res6b}")

if __name__ == "__main__":
    # Fix encoding for Windows console if needed
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    test_search_cases()
