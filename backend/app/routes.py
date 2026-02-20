import os
import uuid
import time
from flask import render_template, request, jsonify, send_from_directory, send_file
from gtts import gTTS
from .services.chat_service import generate_response

def register_routes(app, model, responses_data, conversation_manager, TEMP_DIR, FRONTEND_DIR):
    
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
            
            # Predict intent
            intent = None
            if model:
                try:
                    intent = model.predict([command])[0]
                except:
                    pass
            
            response = generate_response(intent, command, session_id, conversation_manager, responses_data)
            
            conversation_manager.add_message(session_id, 'user', command, intent)
            conversation_manager.add_message(session_id, 'assistant', response, intent)
            
            return jsonify({
                'response': response,
                'intent': intent,
                'success': True
            })
        except Exception as e:
            print(f"Error in /process: {e}")
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
            
            # Cleanup old audio files
            for f in os.listdir(TEMP_DIR):
                if os.path.getmtime(os.path.join(TEMP_DIR, f)) < time.time() - 300:
                    try: os.remove(os.path.join(TEMP_DIR, f))
                    except: pass
            
            tts = gTTS(text=text, lang='en')
            tts.save(filepath)
            return jsonify({'success': True, 'audio_url': f'/audio/{filename}'})
        except Exception as e:
            print(f"Error in /tts: {e}")
            return jsonify({'error': str(e), 'success': False}), 500

    @app.route('/audio/<filename>')
    def serve_audio(filename):
        return send_file(os.path.join(TEMP_DIR, filename))

    @app.route('/clear/<session_id>', methods=['POST'])
    def clear_session(session_id):
        conversation_manager.sessions.pop(session_id, None)
        return jsonify({'success': True})
