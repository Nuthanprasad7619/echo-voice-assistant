import wikipedia
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

def search_wikipedia(text):
    """
    Search Wikipedia for a summary of the query.
    Used for specific "who/what is" questions to get a direct answer.
    """
    # Clean the query to get the key term
    clean_query = text
    for prefix in ["who is", "what is", "tell me about", "search for", "define"]:
        if clean_query.lower().startswith(prefix):
            clean_query = clean_query[len(prefix):].strip()
            
    print(f"Searching Wikipedia for: {clean_query}")
    try:
        # Get a brief summary (2 sentences is usually enough for TTS)
        summary = wikipedia.summary(clean_query, sentences=2)
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        # If ambiguous, try the first option
        try:
            return wikipedia.summary(e.options[0], sentences=2)
        except:
            return None
    except wikipedia.exceptions.PageError:
        return None # Fallback to DuckDuckGo
    except Exception as e:
        print(f"Wikipedia Error: {e}")
        return None

def search_duckduckgo(query):
    try:
        print(f"Searching for: {query}") 

        # Check for "latest" intent
        timelimit = None
        if any(w in query.lower() for w in ['latest', 'current', 'news', 'today', 'now', 'price', 'stock']):
             timelimit = 'd' # Last day

        with DDGS() as ddgs:
            # Enforce 'us-en' region for better English results
            results = list(ddgs.text(query, region='us-en', safesearch='moderate', timelimit=timelimit, max_results=3)) 
            
            if results:
                print(f"Text results found: {len(results)}")
                
                # Intelligent Fallback: 
                # If the top result is a Wikipedia entry, prefer the clean Wikipedia summary over the DDG snippet.
                top_result = results[0]
                if 'wikipedia.org' in top_result.get('href', ''):
                    print("Top result is Wikipedia, attempting to get clean summary...")
                    wiki_summary = search_wikipedia(top_result.get('title', '').replace(' - Wikipedia', ''))
                    if wiki_summary:
                        return f"According to Wikipedia: {wiki_summary}"

                # Standard behavior
                source_name = top_result.get('title', 'Source')
                body_text = top_result.get('body', '')
                
                # Construct response with attribution
                response = f"According to {source_name}: {body_text}"
                
                # Check length for TTS (approx 3 sentences or 350 chars)
                if len(response) > 350:
                    response = response[:347] + "..."
                return response
            else:
                print("No text results found.")
                return "I couldn't find anything on the web about that right now."
                
    except Exception as e:
        print(f"Error searching DuckDuckGo: {e}")
        return "I'm having trouble connecting to the internet."
