from flask import Blueprint, request, jsonify
from ai.scheme_matcher import match_schemes

schemes_bp = Blueprint("schemes", __name__)


@schemes_bp.route("/match", methods=["POST"])
def match():
    """
    POST /api/schemes/match
    Body: { "description": "...", "form_data": {...} }
    Returns matched schemes, conflicts, best scheme.
    """
    data = request.get_json()
    description = data.get("description", "")
    form_data = data.get("form_data", {})

    if not description and not form_data:
        return jsonify({"error": "Provide a description or form data"}), 400

    result = match_schemes(description, form_data)
    return jsonify(result)


@schemes_bp.route("/all", methods=["GET"])
def all_schemes():
    """GET /api/schemes/all — Return full scheme list."""
    from data.schemes_db import SCHEMES
    return jsonify({"schemes": SCHEMES, "total": len(SCHEMES)})


@schemes_bp.route("/<scheme_id>", methods=["GET"])
def scheme_detail(scheme_id):
    """GET /api/schemes/<id> — Return one scheme."""
    from data.schemes_db import SCHEMES
    scheme = next((s for s in SCHEMES if s["id"] == scheme_id), None)
    if not scheme:
        return jsonify({"error": "Scheme not found"}), 404
    return jsonify(scheme)
