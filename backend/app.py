from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from datetime import datetime
from threading import Lock
import webbrowser
import os
import time
import random
import re
import json
import urllib.request
import urllib.parse
import uuid
from gtts import gTTS
import joblib
import wikipedia

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), 'frontend')
TEMP_DIR = os.path.join(BASE_DIR, 'temp')

if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

app = Flask(__name__, template_folder=FRONTEND_DIR, static_folder=FRONTEND_DIR)
CORS(app, resources={r"/*": {"origins": "*"}}) # In production, you might want to restrict this to your Vercel URL
app.config['JSON_SORT_KEYS'] = False

# Load Model
try:
    print("Loading ML Model...")
    model = joblib.load(os.path.join(BASE_DIR, 'chat_model.pkl'))
    responses_data = joblib.load(os.path.join(BASE_DIR, 'responses.pkl'))
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None
    responses_data = {}

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

conversation_manager = ConversationManager()

def predict_intent(text):
    if model:
        try:
            intent = model.predict([text])[0]
            # Simple confidence check logic isn't available directly with pipeline predict, 
            # effectively we trust the model but add regex fallback for math/search.
            return intent
        except:
            return None
    return None

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

def generate_response(intent, text):
    # 0. High Priority Logic (Identity/Definitions) using Wikipedia
    # We check this BEFORE intent classifiers because "Who is X" is often misclassified or needs better answers than search snippets.
    text_lower = text.lower()
    if any(text_lower.startswith(p) for p in ["who is", "what is", "tell me about", "define"]):
        print(f"Identity question detected: '{text}' -> Trying Wikipedia")
        wiki_res = search_wikipedia(text)
        if wiki_res:
            return f"According to Wikipedia: {wiki_res}"
        # If Wikipedia fails, it falls through to standard search below

    # 1. Dynamic Handlers (Strictly matched first)
    if intent == 'time':
        return f"It is {datetime.now().strftime('%I:%M %p')}."
    elif intent == 'date':
        return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}."
    elif intent == 'jokes' and ('joke' in text.lower() or 'laugh' in text.lower()):
        return random.choice(responses_data[intent])

    # 2. Universal Search Trigger
    question_words = ['who', 'what', 'where', 'when', 'why', 'how', 'is', 'can', 'does', 'do', 'search', 'tell me']
    if any(word in text_lower.split() for word in question_words):
        print(f"Question detected: '{text}' -> Triggering Search")
        return search_duckduckgo(text)

    # 3. Fallback to ML Intent (Small Talk)
    if intent in responses_data:
        return random.choice(responses_data[intent])
    
    # 4. Regex Logic (Math)
    if 'calculate' in text or re.search(r'\d+\s*[\+\-\*\/]', text):
        return calculate_math(text)
    
    # 5. Final Fallback (Everything else)
    return search_duckduckgo(text)

def calculate_math(text):
    try:
        match = re.search(r'([\d\.\s\+\-\*\/\(\)]+)', text)
        if match:
            return f"The result is {eval(match.group(1))}"
    except:
        pass
    return "I couldn't calculate that."

# search_wikipedia is now defined above to be used by other functions.
# Removing the old unused search_wikipedia definition at line 171 would be cleaner,
# but our replacement covers the calls.
# To be safe and clean, let's remove the old function if it exists or just ignore it 
# since we overwrote the calls in generate_response.
# Actually, the replacement above is large enough it replaces the old `search_duckduckgo` and `generate_response`.
# We need to make sure we didn't leave a duplicate `search_wikipedia` at the bottom.
# The original file had `search_wikipedia` at line 171. My replacement chunk ends at `calculate_math`. 
# I should probably delete the old `search_wikipedia` to avoid confusion/errors.

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/styles.css')
def css():
    return send_from_directory(FRONTEND_DIR, 'styles.css')

@app.route('/script.js')
def js():
    return send_from_directory(FRONTEND_DIR, 'script.js')

@app.route('/assets/<path:filename>')
def assets(filename):
    assets_dir = os.path.join(FRONTEND_DIR, 'assets')
    return send_from_directory(assets_dir, filename)

@app.route('/process', methods=['POST'])
def process():
    try:
        data = request.get_json()
        command = data.get('command', '')
        session_id = data.get('session_id', 'default')
        
        intent = predict_intent(command)
        response = generate_response(intent, command)
        
        conversation_manager.add_message(session_id, 'user', command, intent)
        conversation_manager.add_message(session_id, 'assistant', response, intent)
        
        return jsonify({
            'response': response,
            'intent': intent,
            'success': True
        })
    except Exception as e:
        print(e)
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'ml_enabled': model is not None})

@app.route('/tts', methods=['POST'])
def tts_generate():
    try:
        data = request.get_json()
        text = data.get('text', '')
        if not text: return jsonify({'error': 'No text'}), 400
        
        filename = f"speech_{uuid.uuid4()}.mp3"
        filepath = os.path.join(TEMP_DIR, filename)
        
        # Cleanup
        for f in os.listdir(TEMP_DIR):
            if os.path.getmtime(os.path.join(TEMP_DIR, f)) < time.time() - 300:
                try: os.remove(os.path.join(TEMP_DIR, f))
                except: pass
        
        tts = gTTS(text=text, lang='en')
        tts.save(filepath)
        return jsonify({'success': True, 'audio_url': f'/audio/{filename}'})
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    return send_file(os.path.join(TEMP_DIR, filename))

@app.route('/clear/<session_id>', methods=['POST'])
def clear_session(session_id):
    conversation_manager.sessions.pop(session_id, None)
    return jsonify({'success': True})

if __name__ == '__main__':
    print("Echo AI v2.0 Starting...")
    app.run(debug=True, port=5000, threaded=True, host='0.0.0.0')
