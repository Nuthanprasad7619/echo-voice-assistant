from waitress import serve
from backend.app import app
import os

print("Starting Production Server on 0.0.0.0:8080")
print("Access at http://localhost:8080")

serve(app, host='0.0.0.0', port=8080)
