"""
OCR & Document Extraction
Reads uploaded Aadhaar, Income Certificate, Land Record etc.
and extracts structured data for auto-filling forms.
"""

import re
import os

# Try to import OCR libraries (optional — graceful fallback if not installed)
try:
    import pytesseract
    from PIL import Image
    import pdf2image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


def extract_text_from_file(filepath: str) -> str:
    """
    Extract raw text from image or PDF file using OCR.
    Falls back to empty string if OCR not available.
    """
    if not OCR_AVAILABLE:
        return ""

    ext = os.path.splitext(filepath)[1].lower()

    try:
        if ext == ".pdf":
            pages = pdf2image.convert_from_path(filepath, dpi=200)
            text = " ".join(pytesseract.image_to_string(p) for p in pages)
        elif ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
            img = Image.open(filepath)
            text = pytesseract.image_to_string(img)
        else:
            text = ""
    except Exception as e:
        print(f"OCR error: {e}")
        text = ""

    return text


def parse_aadhaar(text: str) -> dict:
    """Extract info from Aadhaar card OCR text."""
    data = {}

    # Aadhaar number: 12 digits, often spaced as XXXX XXXX XXXX
    aadhaar_match = re.search(r"\b(\d{4}\s?\d{4}\s?\d{4})\b", text)
    if aadhaar_match:
        data["aadhaar_number"] = aadhaar_match.group(1).replace(" ", "")

    # Name: usually appears after "Name:" or in CAPS
    name_match = re.search(r"(?:Name[:\s]+)([A-Z][a-zA-Z\s]{2,40})", text)
    if name_match:
        data["name"] = name_match.group(1).strip()

    # DOB
    dob_match = re.search(r"(?:DOB|Date of Birth)[:\s]+(\d{2}/\d{2}/\d{4})", text)
    if dob_match:
        data["dob"] = dob_match.group(1)

    # Gender
    if "MALE" in text.upper():
        data["gender"] = "male"
    elif "FEMALE" in text.upper():
        data["gender"] = "female"

    # Address
    addr_match = re.search(r"(?:Address|S/O|C/O)[:\s]+(.{10,100})", text, re.IGNORECASE)
    if addr_match:
        data["address"] = addr_match.group(1).strip()

    return data


def parse_income_certificate(text: str) -> dict:
    """Extract info from Income Certificate OCR text."""
    data = {}

    # Income amount
    income_match = re.search(r"(?:income|annual)[^\d]*(\d[\d,\.]*)", text, re.IGNORECASE)
    if income_match:
        raw = income_match.group(1).replace(",", "")
        try:
            data["income"] = int(float(raw))
        except:
            pass

    # Name
    name_match = re.search(r"(?:Name|Shri|Smt)[:\s\.]+([A-Za-z\s]{3,40})", text)
    if name_match:
        data["name"] = name_match.group(1).strip()

    # Certificate number
    cert_match = re.search(r"(?:Certificate No|Cert\.?\s*No)[:\s]+([A-Z0-9\-\/]+)", text, re.IGNORECASE)
    if cert_match:
        data["certificate_number"] = cert_match.group(1)

    return data


def parse_land_record(text: str) -> dict:
    """Extract info from 7/12 or land record OCR text."""
    data = {}

    # Survey number
    survey_match = re.search(r"(?:Survey No|Khasra)[:\s]+([0-9\/A-Z\-]+)", text, re.IGNORECASE)
    if survey_match:
        data["survey_number"] = survey_match.group(1)

    # Land area
    land_match = re.search(r"(\d+\.?\d*)\s*(acre|hectare|bigha|guntha)", text, re.IGNORECASE)
    if land_match:
        data["land_area"] = land_match.group(1)
        data["land_unit"] = land_match.group(2)

    # Owner name
    owner_match = re.search(r"(?:Owner|Khataedar|Khatedar)[:\s]+([A-Za-z\s]{3,40})", text, re.IGNORECASE)
    if owner_match:
        data["owner_name"] = owner_match.group(1).strip()

    return data


def parse_caste_certificate(text: str) -> dict:
    """Extract info from Caste Certificate OCR text."""
    data = {}

    text_upper = text.upper()
    if "SCHEDULED CASTE" in text_upper or " SC " in text_upper:
        data["caste"] = "sc"
    elif "SCHEDULED TRIBE" in text_upper or " ST " in text_upper:
        data["caste"] = "st"
    elif "OTHER BACKWARD" in text_upper or " OBC " in text_upper:
        data["caste"] = "obc"

    name_match = re.search(r"(?:Name|Shri|Smt)[:\s\.]+([A-Za-z\s]{3,40})", text)
    if name_match:
        data["name"] = name_match.group(1).strip()

    return data


# ─── Main processor ───────────────────────────────────────────────────────────

DOCUMENT_PARSERS = {
    "aadhaar": parse_aadhaar,
    "income": parse_income_certificate,
    "land": parse_land_record,
    "caste": parse_caste_certificate,
}


def process_document(filepath: str, doc_type: str) -> dict:
    """
    Full pipeline: file → OCR text → parsed fields
    """
    text = extract_text_from_file(filepath)

    parser = DOCUMENT_PARSERS.get(doc_type)
    if parser:
        extracted = parser(text)
    else:
        extracted = {}

    return {
        "doc_type": doc_type,
        "ocr_available": OCR_AVAILABLE,
        "raw_text_preview": text[:300] if text else "(OCR not available — install pytesseract)",
        "extracted_fields": extracted,
    }


def merge_extracted_data(results: list) -> dict:
    """
    Merge extracted fields from multiple documents into one profile dict.
    Used to auto-fill the application form.
    """
    merged = {}
    for r in results:
        merged.update(r.get("extracted_fields", {}))
    return merged
