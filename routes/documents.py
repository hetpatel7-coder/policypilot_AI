import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from ai.ocr_extractor import process_document, merge_extracted_data

documents_bp = Blueprint("documents", __name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "bmp", "tiff"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@documents_bp.route("/upload", methods=["POST"])
def upload():
    """
    POST /api/documents/upload
    Form fields: aadhaar, income, caste, land (file inputs)
    Returns extracted data from all uploaded documents.
    """
    results = []
    doc_types = ["aadhaar", "income", "caste", "land"]

    for doc_type in doc_types:
        if doc_type not in request.files:
            continue
        file = request.files[doc_type]
        if file.filename == "" or not allowed_file(file.filename):
            continue

        filename = secure_filename(f"{doc_type}_{file.filename}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        extracted = process_document(filepath, doc_type)
        results.append(extracted)

    if not results:
        return jsonify({"error": "No valid files uploaded"}), 400

    merged = merge_extracted_data(results)

    return jsonify({
        "documents_processed": len(results),
        "details": results,
        "auto_fill_data": merged,
        "message": "Documents processed. Use auto_fill_data to pre-fill the application form.",
    })
