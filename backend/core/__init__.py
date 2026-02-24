from flask import Flask
from flask_cors import CORS

def create_app(frontend_dir):
    app = Flask(__name__, template_folder=frontend_dir, static_folder=frontend_dir)
    CORS(app, resources={r"/*": {"origins": "*"}})
    app.config['JSON_SORT_KEYS'] = False
    return app
