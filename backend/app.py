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

def generate_response(intent, text):
    # Dynamic handlers
    if intent == 'time':
        return f"It is {datetime.now().strftime('%I:%M %p')}."
    elif intent == 'date':
        return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}."
    
    # Priority Regex Handlers (Before ML fallback)
    if 'search for' in text.lower() or 'who is' in text.lower() or 'what is' in text.lower() or 'tell me about' in text.lower():
        return search_wikipedia(text)
        
    if intent == 'wikipedia_search':
        return search_wikipedia(text)
    elif intent in responses_data:
        return random.choice(responses_data[intent])
    
    # Fallback/Regex Handlers
    if 'calculate' in text or re.search(r'\d+\s*[\+\-\*\/]', text):
        return calculate_math(text)

    return "I'm not exactly sure what you mean, but I'm learning every day!"

def calculate_math(text):
    try:
        match = re.search(r'([\d\.\s\+\-\*\/\(\)]+)', text)
        if match:
            return f"The result is {eval(match.group(1))}"
    except:
        pass
    return "I couldn't calculate that."

def search_wikipedia(text):
    clean_query = text.replace("who is", "").replace("what is", "").replace("tell me about", "").replace("search for", "").strip()
    try:
        summary = wikipedia.summary(clean_query, sentences=2)
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        return f"There are multiple results for {clean_query}. Can you be more specific?"
    except wikipedia.exceptions.PageError:
        return f"I couldn't find anything about {clean_query} on Wikipedia."
    except Exception as e:
        return "I'm having trouble connecting to the knowledge base."

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
