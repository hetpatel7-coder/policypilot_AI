from flask import Blueprint, request, jsonify

auth_bp = Blueprint("auth", __name__)

# Demo users — replace with a real DB in production
DEMO_USERS = {
    "9999999999": {"password": "1234", "name": "Demo Citizen", "state": "Gujarat"},
}


@auth_bp.route("/login", methods=["POST"])
def login():
    """POST /api/auth/login — { mobile, password }"""
    data = request.get_json()
    mobile = data.get("mobile", "").strip()
    password = data.get("password", "").strip()

    user = DEMO_USERS.get(mobile)
    if user and user["password"] == password:
        return jsonify({
            "success": True,
            "name": user["name"],
            "state": user["state"],
            "token": f"demo-token-{mobile}",  # Replace with JWT in production
        })

    return jsonify({"success": False, "error": "Invalid mobile or password"}), 401
