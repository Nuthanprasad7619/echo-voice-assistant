import os
import joblib
from app import create_app
from app.routes import register_routes
from app.services.chat_service import ConversationManager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), 'frontend')
TEMP_DIR = os.path.join(BASE_DIR, 'temp')

if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Load Model/Data
print("Loading ML Model...")
try:
    model = joblib.load(os.path.join(BASE_DIR, 'chat_model.pkl'))
    responses_data = joblib.load(os.path.join(BASE_DIR, 'responses.pkl'))
    print("Model loaded successfully.")
except Exception as e:
    print(f"Error loading model: {e}")
    model = None
    responses_data = {}

# Initialize shared components
conversation_manager = ConversationManager()

# Create and configure app
app = create_app(FRONTEND_DIR)
register_routes(app, model, responses_data, conversation_manager, TEMP_DIR, FRONTEND_DIR)

if __name__ == '__main__':
    print("Echo AI v2.1 (Modular) Starting...")
    app.run(debug=True, port=5000, threaded=True, host='0.0.0.0')
