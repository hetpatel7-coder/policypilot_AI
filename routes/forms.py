from flask import Blueprint, request, jsonify

forms_bp = Blueprint("forms", __name__)


@forms_bp.route("/autofill", methods=["POST"])
def autofill():
    """
    POST /api/forms/autofill
    Body: { "auto_fill_data": {...}, "scheme_id": "pm_kisan" }
    Returns a pre-filled application form dict.
    """
    data = request.get_json()
    fill = data.get("auto_fill_data", {})
    scheme_id = data.get("scheme_id", "")

    form = {
        "applicant_name": fill.get("name", ""),
        "aadhaar_number": fill.get("aadhaar_number", ""),
        "dob": fill.get("dob", ""),
        "gender": fill.get("gender", ""),
        "address": fill.get("address", ""),
        "annual_income": fill.get("income", ""),
        "land_survey_number": fill.get("survey_number", ""),
        "land_area": fill.get("land_area", ""),
        "caste_category": fill.get("caste", ""),
        "scheme_applied_for": scheme_id,
        "certificate_number": fill.get("certificate_number", ""),
    }

    # Checklist for this application
    checklist = [
        {"item": "Aadhaar Card", "done": bool(fill.get("aadhaar_number"))},
        {"item": "Income Certificate", "done": bool(fill.get("income"))},
        {"item": "Land Record (7/12)", "done": bool(fill.get("survey_number"))},
        {"item": "Caste Certificate", "done": bool(fill.get("caste"))},
        {"item": "Bank Account Details", "done": False},
        {"item": "Passport Size Photo", "done": False},
        {"item": "Mobile Number Linked to Aadhaar", "done": False},
    ]

    return jsonify({
        "form_data": form,
        "checklist": checklist,
        "message": "Form pre-filled from uploaded documents. Please verify all fields.",
    })
