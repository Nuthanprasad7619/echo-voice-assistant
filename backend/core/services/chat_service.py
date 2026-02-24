import random
import re
from datetime import datetime
from threading import Lock
from .search_service import search_duckduckgo, search_wikipedia

def predict_intent(text, model):
    if model:
        try:
            intent = model.predict([text])[0]
            return intent
        except:
            return None
    return None

class ConversationManager:
    def __init__(self, max_history=50):
        self.sessions = {}
        self.lock = Lock()
        self.max_history = max_history
        self.analytics = {}
    
    def get_session(self, session_id: str) -> dict:
        with self.lock:
            if session_id not in self.sessions:
                current_time = datetime.now().isoformat()
                self.sessions[session_id] = {
                    'history': [],
                    'context': {},
                    'created_at': current_time
                }
                self.analytics[session_id] = {
                    'total_messages': 0,
                    'commands_used': {},
                    'session_start': current_time,
                    'last_active': current_time
                }
            else:
                self.analytics[session_id]['last_active'] = datetime.now().isoformat()
            return self.sessions[session_id]
    
    def add_message(self, session_id: str, role: str, message: str, intent = None):
        session = self.get_session(session_id)
        session['history'].append({
            'role': role,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'intent': intent
        })
        self.analytics[session_id]['total_messages'] += 1
        if intent:
            if intent not in self.analytics[session_id]['commands_used']:
                self.analytics[session_id]['commands_used'][intent] = 0
            self.analytics[session_id]['commands_used'][intent] += 1

def calculate_math(text):
    try:
        match = re.search(r'([\d\.\s\+\-\*\/\(\)]+)', text)
        if match:
            return f"The result is {eval(match.group(1))}"
    except:
        pass
    return "I couldn't calculate that."

def generate_response(intent, text, session_id, conversation_manager, responses_data):
    # 0. Context Refinement for Follow-up Questions
    refined_text = text
    text_lower = text.lower()
    
    is_short = len(text.split()) < 5
    is_connector = text_lower.startswith(("in ", "at ", "for ", "with ", "about ", "on ", "and "))
    
    # Bug Fix: Skip context merging if the query is a simple greeting or small talk
    small_talk_intents = ['greeting', 'goodbye', 'thanks', 'about', 'help']
    is_small_talk = intent in small_talk_intents or text_lower in ["hi", "hello", "hey", "hey there"]
    
    if (is_short or is_connector) and not is_small_talk:
        try:
            session = conversation_manager.get_session(session_id)
            history = session.get('history', [])
            
            last_user_msg = None
            for msg in reversed(history):
                if msg['role'] == 'user':
                    last_user_msg = msg['message']
                    break
            
            if last_user_msg:
                print(f"Context found. Merging '{last_user_msg}' with '{text}'")
                refined_text = f"{last_user_msg} {text}"
                print(f"Refined Query: {refined_text}")
                text_lower = refined_text.lower()
        except Exception as e:
            print(f"Error in context refinement: {e}")

    # 1. High Priority Logic (Identity/Definitions) using Wikipedia
    if any(text_lower.startswith(p) for p in ["who is", "what is", "tell me about", "define"]):
        print(f"Identity question detected: '{refined_text}' -> Trying Wikipedia")
        wiki_res = search_wikipedia(refined_text)
        if wiki_res:
            return f"According to Wikipedia: {wiki_res}"

    # 2. Dynamic Handlers (Time, Date, Jokes)
    if intent == 'time':
        return f"It is {datetime.now().strftime('%I:%M %p')}."
    elif intent == 'date':
        return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}."
    elif intent == 'jokes' and ('joke' in text.lower() or 'laugh' in text.lower()):
        return random.choice(responses_data[intent])

    # 3. Small Talk (Greetings, etc.) - REFINED PRIORITY
    # We only return early if it's a CLEAR small talk intent WITHOUT question indicators,
    # or if it's a known short greeting Phrase.
    small_talk_intents = ['greeting', 'goodbye', 'thanks', 'about', 'help']
    question_words = ['who', 'what', 'where', 'when', 'why', 'how', 'is', 'can', 'does', 'do', 'search', 'tell me']
    
    # Informational Keywords: Phrases that strongly imply a lookup is needed
    info_keywords = ['pm', 'prime minister', 'president', 'capital', 'population', 'weather', 'news', 'meaning', 'definition', 'price', 'stock', 'birth', 'death', 'distance', 'highest', 'largest', 'smallest']
    
    has_question_word = any(word in text_lower.split() for word in question_words)
    has_info_keyword = any(word in text_lower for word in info_keywords)
    
    # Exception: "How are you" and "How is it going" are greetings despite having "how"
    is_greeting_phrase = any(p in text_lower for p in ["how are you", "how's it going", "how is it going", "what's up"])
    
    if intent in small_talk_intents and intent in responses_data:
        # If it's a greeting phrased as a question (like "how are you"), handle as small talk.
        # Otherwise, if it has 1-2 words and NO info/question indicators, handle as small talk.
        # This prevents "pm of india" (3 words) from being a greeting.
        if is_greeting_phrase or (not has_question_word and not has_info_keyword and len(text.split()) < 3):
            print(f"Small talk detected: '{intent}' -> returning mapped response")
            return random.choice(responses_data[intent])

    # 4. Universal Search Trigger
    if has_question_word or has_info_keyword or is_connector:
        print(f"Informational query detected: '{refined_text}' -> Triggering Search")
        return search_duckduckgo(refined_text)

    # 5. Regex Logic (Math)
    if 'calculate' in text or re.search(r'\d+\s*[\+\-\*\/]', text):
        return calculate_math(text)
    
    # 6. Final Fallback
    # If it's > 2 words and hasn't been handled, it's likely a query of some kind.
    if len(text.split()) > 2:
        return search_duckduckgo(refined_text)
    
    # Otherwise fallback to a default response from ML if available
    if intent in responses_data:
        return random.choice(responses_data[intent])

    return "I'm not sure how to respond to that. Could you try rephrasing?"
