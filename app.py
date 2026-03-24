from flask import Flask, request, jsonify
from flask_cors import CORS
from routes.auth import auth_bp
from routes.schemes import schemes_bp
from routes.documents import documents_bp
from routes.forms import forms_bp

app = Flask(__name__)
CORS(app)  # Allow frontend to call backend

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(schemes_bp, url_prefix="/api/schemes")
app.register_blueprint(documents_bp, url_prefix="/api/documents")
app.register_blueprint(forms_bp, url_prefix="/api/forms")

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "message": "PolicyPilot backend running"})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
