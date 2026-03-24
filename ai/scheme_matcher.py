"""
AI Scheme Matching Engine
- Parses natural language user input using keyword + NLP logic
- Scores each scheme against the user's profile
- Detects conflicts between central and state schemes
"""

import re
from data.schemes_db import SCHEMES


# ─── NLP: Extract Profile from User Description ───────────────────────────────

def extract_profile(description: str, form_data: dict = None) -> dict:
    """
    Parse user description (plain text) + optional form fields
    into a structured profile dict.
    """
    text = description.lower()

    profile = {
        "occupation": None,
        "income": None,
        "land_acres": None,
        "gender": None,
        "age": None,
        "caste": None,
        "bpl": False,
        "has_lpg": False,
        "education_level": None,
        "has_pucca_house": False,
    }

    # ── Occupation ──
    if any(w in text for w in ["farmer", "kisan", "kheti", "agriculture", "farm"]):
        profile["occupation"] = "farmer"
    elif any(w in text for w in ["student", "study", "college", "school", "education"]):
        profile["occupation"] = "student"
    elif any(w in text for w in ["business", "shop", "entrepreneur", "self employed"]):
        profile["occupation"] = "business"
    elif any(w in text for w in ["labour", "laborer", "worker", "daily wage", "mazdoor"]):
        profile["occupation"] = "labour"
    else:
        profile["occupation"] = "any"

    # ── Income ──
    income_match = re.search(r"income[^\d]*(\d[\d,\.]*)", text)
    if not income_match:
        income_match = re.search(r"(\d[\d,\.]*)\s*(lakh|lac|rs|rupee)", text)
    if income_match:
        raw = income_match.group(1).replace(",", "")
        val = float(raw)
        if val < 1000:  # user said "1.5 lakh" not "150000"
            val *= 100000
        profile["income"] = int(val)

    # ── Land ──
    land_match = re.search(r"(\d+\.?\d*)\s*(acre|bigha|hectare)", text)
    if land_match:
        profile["land_acres"] = float(land_match.group(1))

    # ── Gender ──
    if any(w in text for w in ["female", "woman", "women", "lady", "she", "her", "mahila"]):
        profile["gender"] = "female"
    elif any(w in text for w in ["male", "man", "men", "he", "his"]):
        profile["gender"] = "male"

    # ── Age ──
    age_match = re.search(r"(\d{1,2})\s*(year|yr|age|old)", text)
    if age_match:
        profile["age"] = int(age_match.group(1))

    # ── Caste ──
    if any(w in text for w in ["sc", "scheduled caste", "dalit", "harijan"]):
        profile["caste"] = "sc"
    elif any(w in text for w in ["st", "scheduled tribe", "tribal", "adivasi"]):
        profile["caste"] = "st"
    elif any(w in text for w in ["obc", "other backward", "backward class"]):
        profile["caste"] = "obc"
    else:
        profile["caste"] = "general"

    # ── BPL ──
    if any(w in text for w in ["bpl", "below poverty", "ration card", "antyodaya"]):
        profile["bpl"] = True

    # ── LPG ──
    if any(w in text for w in ["no lpg", "no gas", "without lpg", "kerosene"]):
        profile["has_lpg"] = False

    # ── Education level ──
    if any(w in text for w in ["graduation", "degree", "college", "university", "post matric", "12th", "hsc"]):
        profile["education_level"] = "post_matric"
    elif any(w in text for w in ["school", "10th", "ssc", "primary"]):
        profile["education_level"] = "pre_matric"

    # ── Override with form data if provided ──
    if form_data:
        if form_data.get("income"):
            try:
                profile["income"] = int(str(form_data["income"]).replace(",", ""))
            except:
                pass
        if form_data.get("land"):
            try:
                profile["land_acres"] = float(form_data["land"])
            except:
                pass
        if form_data.get("age"):
            try:
                profile["age"] = int(form_data["age"])
            except:
                pass
        if form_data.get("gender"):
            profile["gender"] = form_data["gender"].lower()
        if form_data.get("caste"):
            profile["caste"] = form_data["caste"].lower()

    return profile


# ─── Scoring Engine ────────────────────────────────────────────────────────────

def score_scheme(scheme: dict, profile: dict) -> tuple[int, list[str], list[str]]:
    """
    Returns (score 0-100, matched_criteria[], failed_criteria[])

    KEY RULES:
    - Only HARD FAIL (score=0) when user explicitly contradicts a strict rule
      e.g. user said male but scheme is female-only
    - If user did NOT provide a field, we give benefit of the doubt (partial credit)
    - Schemes open to "any" occupation always get full credit on that field
    """
    rules = scheme["eligibility"]
    matched = []
    failed = []
    hard_fail = False   # if True → score forced to 0, scheme excluded
    score_parts = []    # list of (earned, possible) tuples

    # ── Occupation ──
    rule_occ = rules.get("occupation", "any")
    if rule_occ == "any":
        # Open to everyone — full credit, no penalty
        score_parts.append((1, 1))
        matched.append("Open to all occupations")
    else:
        occ_list = rule_occ if isinstance(rule_occ, list) else [rule_occ]
        if profile["occupation"] is None or profile["occupation"] == "any":
            # User didn't specify — give half credit
            score_parts.append((0.5, 1))
        elif profile["occupation"] in occ_list:
            score_parts.append((1, 1))
            matched.append(f"Occupation matches ({profile['occupation']})")
        else:
            # Hard mismatch — exclude this scheme
            hard_fail = True
            failed.append(f"Requires occupation: {', '.join(occ_list)}")

    if hard_fail:
        return 0, matched, failed

    # ── Income ──
    if "max_income" in rules:
        if profile["income"] is not None:
            if profile["income"] <= rules["max_income"]:
                score_parts.append((1, 1))
                matched.append(f"Income ₹{profile['income']:,} within limit ₹{rules['max_income']:,}")
            else:
                # Hard fail only if income is WAY over limit (>50% above)
                if profile["income"] > rules["max_income"] * 1.5:
                    hard_fail = True
                    failed.append(f"Income ₹{profile['income']:,} far exceeds limit ₹{rules['max_income']:,}")
                else:
                    score_parts.append((0.3, 1))
                    failed.append(f"Income ₹{profile['income']:,} slightly over limit ₹{rules['max_income']:,}")
        else:
            # Income not stated — give benefit of the doubt
            score_parts.append((0.7, 1))
            matched.append("Income eligibility not specified — may qualify")

    if hard_fail:
        return 0, matched, failed

    # ── Land ──
    if rules.get("land_required"):
        max_land = rules.get("max_land_acres", 999)
        if profile["land_acres"] is not None:
            if 0 < profile["land_acres"] <= max_land:
                score_parts.append((1, 1))
                matched.append(f"Land {profile['land_acres']} acres within {max_land} acre limit")
            else:
                score_parts.append((0, 1))
                failed.append(f"Land must be between 0 and {max_land} acres")
        else:
            # Land not stated — partial credit
            score_parts.append((0.6, 1))

    # ── Gender ──
    if "gender" in rules:
        if profile["gender"] is None:
            # Not stated — give partial credit
            score_parts.append((0.6, 1))
        elif profile["gender"] == rules["gender"]:
            score_parts.append((1, 1))
            matched.append(f"Gender eligibility met ({rules['gender']})")
        else:
            # Hard fail — gender is a strict requirement
            hard_fail = True
            failed.append(f"Scheme is for {rules['gender']} only")

    if hard_fail:
        return 0, matched, failed

    # ── Caste ──
    if "caste" in rules and rules["caste"] != "any":
        caste_list = rules["caste"] if isinstance(rules["caste"], list) else [rules["caste"]]
        if profile["caste"] is None:
            score_parts.append((0.5, 1))
        elif profile["caste"] in caste_list:
            score_parts.append((1, 1))
            matched.append(f"Caste {profile['caste'].upper()} eligible")
        else:
            # Hard fail — caste is a strict requirement
            hard_fail = True
            failed.append(f"Scheme restricted to {', '.join(c.upper() for c in caste_list)}")

    if hard_fail:
        return 0, matched, failed

    # ── Age ──
    if "min_age" in rules:
        min_a = rules.get("min_age", 0)
        max_a = rules.get("max_age", 200)
        if profile["age"] is not None:
            if min_a <= profile["age"] <= max_a:
                score_parts.append((1, 1))
                matched.append(f"Age {profile['age']} within eligible range ({min_a}-{max_a})")
            else:
                hard_fail = True
                failed.append(f"Age must be between {min_a} and {max_a}")
        else:
            # Age not stated — assume eligible adult
            score_parts.append((0.7, 1))

    if hard_fail:
        return 0, matched, failed

    # ── BPL ──
    if rules.get("bpl"):
        if profile["bpl"]:
            score_parts.append((1, 1))
            matched.append("BPL status confirmed")
        else:
            # Not stated as BPL — soft penalty only
            score_parts.append((0.3, 1))
            failed.append("BPL card preferred — verify eligibility")

    # ── Education ──
    if "education_level" in rules:
        if profile["education_level"] is None:
            score_parts.append((0.5, 1))
        elif profile["education_level"] == rules["education_level"]:
            score_parts.append((1, 1))
            matched.append(f"Education level matches: {rules['education_level']}")
        else:
            score_parts.append((0.2, 1))
            failed.append(f"Preferred education level: {rules['education_level']}")

    # ── Compute final score ──
    if not score_parts:
        score = 60  # No specific criteria — open scheme
    else:
        total_earned = sum(e for e, _ in score_parts)
        total_possible = sum(p for _, p in score_parts)
        score = int((total_earned / total_possible) * 100)

    return score, matched, failed


# ─── Conflict Detection ────────────────────────────────────────────────────────

def detect_conflicts(matched_schemes: list) -> list:
    """
    Find pairs of schemes that conflict with each other.
    Returns list of conflict objects with explanation.
    """
    conflicts = []
    ids = {s["id"] for s in matched_schemes}

    for scheme in matched_schemes:
        for conflict_id in scheme.get("conflicts_with", []):
            if conflict_id in ids:
                # Only add each pair once
                pair = tuple(sorted([scheme["id"], conflict_id]))
                already = any(c["pair"] == list(pair) for c in conflicts)
                if not already:
                    other = next(s for s in matched_schemes if s["id"] == conflict_id)
                    conflicts.append({
                        "pair": list(pair),
                        "scheme_a": scheme["name"],
                        "scheme_b": other["name"],
                        "note": scheme.get("conflict_note", f"Cannot receive both {scheme['name']} and {other['name']}."),
                        "recommendation": f"Apply for '{other['name']}' (₹{other['benefit']:,}) if income is above ₹1.5L, or '{scheme['name']}' (₹{scheme['benefit']:,}) otherwise.",
                    })

    return conflicts


# ─── Main Match Function ───────────────────────────────────────────────────────

def match_schemes(description: str, form_data: dict = None, min_score: int = 20) -> dict:
    """
    Full pipeline:
    1. Extract profile from text + form
    2. Score all schemes
    3. Filter by min_score
    4. Detect conflicts
    5. Sort by score DESC
    """
    profile = extract_profile(description, form_data)
    results = []

    for scheme in SCHEMES:
        score, matched, failed = score_scheme(scheme, profile)
        if score >= min_score:
            results.append({
                **scheme,
                "match_score": score,
                "matched_criteria": matched,
                "failed_criteria": failed,
            })

    # Sort by score
    results.sort(key=lambda x: x["match_score"], reverse=True)

    # Detect conflicts only among top matches
    conflicts = detect_conflicts(results)

    # Best scheme suggestion
    best = results[0] if results else None

    return {
        "profile": profile,
        "matched_schemes": results,
        "conflicts": conflicts,
        "best_scheme": best,
        "total_found": len(results),
    }
