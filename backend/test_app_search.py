import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import joblib

def test_search_cases():
    print("--- Testing App Search Logic ---")
    
    from app.services.chat_service import generate_response, predict_intent, ConversationManager
    from app.services.search_service import search_duckduckgo
    
    # Load Model for testing
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chat_model.pkl')
    model = joblib.load(model_path) if os.path.exists(model_path) else None
    responses_data = joblib.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'responses.pkl'))

    # New Case: Normal Conversation Check
    print("\n--- Testing Normal Conversation ---")
    query_conv = "How are you"
    print(f"User: {query_conv}")
    intent_conv = predict_intent(query_conv, model)
    res_conv = generate_response(intent_conv, query_conv, 'test_session', ConversationManager(), responses_data)
    print(f"Assistant: {res_conv}")
    if "According to" in res_conv or "Searching" in res_conv:
         print("FAILED: Triggered search for normal conversation.")
    else:
         print("SUCCESS: Handled conversation naturally.")

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
    intent4 = predict_intent(query4, model)
    res4 = generate_response(intent4, query4, 'test', ConversationManager(), responses_data)
    print(f"Result 4: {res4}")

    # Case 6: Context Awareness
    print("\n--- Testing Context Awareness ---")
    session_id = "test_session_final"
    cm = ConversationManager()
    q6a = "what do we celebrate on August 15"
    print(f"User: {q6a}")
    intent6a = predict_intent(q6a, model)
    res6a = generate_response(intent6a, q6a, session_id, cm, responses_data)
    cm.add_message(session_id, 'user', q6a, intent6a)
    cm.add_message(session_id, 'assistant', res6a, intent6a)
    print(f"Assistant: {res6a}")

    q6b = "in India"
    print(f"User: {q6b}")
    intent6b = predict_intent(q6b, model)
    res6b = generate_response(intent6b, q6b, session_id, cm, responses_data)
    print(f"Assistant: {res6b}")

    # Case 7: Greeting after search (Regression check for aggressive merging)
    print("\n--- Testing Greeting after Search ---")
    session_id_7 = "test_session_aggro"
    cm7 = ConversationManager()
    
    q7a = "who is Elon Musk"
    print(f"User: {q7a}")
    intent7a = predict_intent(q7a, model)
    res7a = generate_response(intent7a, q7a, session_id_7, cm7, responses_data)
    cm7.add_message(session_id_7, 'user', q7a, intent7a)
    cm7.add_message(session_id_7, 'assistant', res7a, intent7a)
    print(f"Assistant: {res7a[:50]}...")

    q7b = "hi"
    print(f"User: {q7b}")
    intent7b = predict_intent(q7b, model)
    res7b = generate_response(intent7b, q7b, session_id_7, cm7, responses_data)
    print(f"Assistant: {res7b}")
    if "Wikipedia" in res7b or "Elon Musk" in res7b:
        print("FAILED: Aggressive merging persists.")
    else:
        print("SUCCESS: Greeting handled correctly.")

    # Case 8: Informational Keyword (no question word)
    print("\n--- Testing Informational Keyword ---")
    q8 = "pm of india"
    print(f"User: {q8}")
    intent8 = predict_intent(q8, model)
    res8 = generate_response(intent8, q8, "test_session_8", ConversationManager(), responses_data)
    print(f"Assistant: {res8[:50]}...")
    if "According to" in res8 or "Searching" in res8 or "minister" in res8.lower():
        print("SUCCESS: Informational query triggered search.")
    else:
        print("FAILED: Informational query misclassified as greeting.")

    # Case 9: Multi-word query (Fallback check)
    print("\n--- Testing Multi-word Fallback ---")
    q9 = "capital of France" # No 'who/what', not in specific info_keywords (until I added 'capital')
    print(f"User: {q9}")
    intent9 = predict_intent(q9, model)
    res9 = generate_response(intent9, q9, "test_session_9", ConversationManager(), responses_data)
    print(f"Assistant: {res9[:50]}...")
    if "According to" in res9 or "Searching" in res9 or "Paris" in res9:
        print("SUCCESS: Multi-word query triggered search.")
    else:
        print("FAILED: Multi-word query failed to search.")

if __name__ == "__main__":
    # Fix encoding for Windows console if needed
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    test_search_cases()
