"""
src/timing.py
-------------
Prasna Tantra horary astrology — timing estimation engine.

Three independent timing methods derived from Prasna Tantra:
  1. Degrees method  — angular separation scaled by lagna sign type
  2. Nakshatra method — nakshatra gap scaled by lagna sign type
  3. Sign distance    — sign count from lagna to karyesh sign, scaled

Public API
----------
    estimate_timing(
        lagna_sign, lagna_lord_longitude, karyesh_longitude,
        lagna_lord_nakshatra, karyesh_nakshatra,
        karyesh_sign=None
    ) -> dict
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Hardcoded Tables
# ---------------------------------------------------------------------------

_SIGN_TYPES: dict[str, str] = {
    "Aries":       "Movable",   "Cancer":      "Movable",
    "Libra":       "Movable",   "Capricorn":   "Movable",
    "Taurus":      "Fixed",     "Leo":         "Fixed",
    "Scorpio":     "Fixed",     "Aquarius":    "Fixed",
    "Gemini":      "Common",    "Virgo":       "Common",
    "Sagittarius": "Common",    "Pisces":      "Common",
}

_ZODIAC_SIGNS: list[str] = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

_NAKSHATRAS: list[str] = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishtha", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada",
    "Revati",
]

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _separation(lon_a: float, lon_b: float) -> float:
    """Shortest arc between two ecliptic longitudes, result in [0, 180]."""
    diff = abs(lon_a - lon_b) % 360.0
    return min(diff, 360.0 - diff)


def _nakshatra_gap(nak_a: str, nak_b: str) -> int:
    """
    Shortest arc count between two nakshatras out of 27.
    Returns integer in [0, 13].
    """
    idx_a = _NAKSHATRAS.index(nak_a)
    idx_b = _NAKSHATRAS.index(nak_b)
    diff = abs(idx_b - idx_a)
    return diff if diff <= 13 else 27 - diff


def _sign_distance(from_sign: str, to_sign: str) -> int:
    """
    Forward count of signs from `from_sign` to `to_sign` (0–11).
    Same sign → 0 (event imminent). Ahead by one sign → 1, etc.
    """
    idx_from = _ZODIAC_SIGNS.index(from_sign)
    idx_to   = _ZODIAC_SIGNS.index(to_sign)
    return (idx_to - idx_from) % 12   # 0 when same, 1–11 otherwise

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def estimate_timing(
    lagna_sign:             str,
    lagna_lord_longitude:   float,
    karyesh_longitude:      float,
    lagna_lord_nakshatra:   str,
    karyesh_nakshatra:      str,
    ithasala_orb_remaining: float,          # degrees until exact aspect (from Ithasala orb_remaining)
    karyesh_sign:           str | None = None,
    moon_phase:             str | None = None,
) -> dict:
    """
    Estimate timing of query fulfilment using three Prasna Tantra methods.

    Parameters
    ----------
    lagna_sign             : Zodiac sign of the Ascendant (e.g. 'Gemini').
    lagna_lord_longitude   : Ecliptic longitude of the lagna lord (0–360°).
    karyesh_longitude      : Ecliptic longitude of the karyesh/significator (0–360°).
    lagna_lord_nakshatra   : Nakshatra name of the lagna lord.
    karyesh_nakshatra      : Nakshatra name of the karyesh.
    karyesh_sign           : Zodiac sign of the karyesh (needed for Method 3).
                             Defaults to lagna_sign if None.
    moon_phase             : 'waxing', 'waning', or None. Adds modifier note.

    Returns
    -------
    dict — see module docstring.
    """
    if lagna_sign not in _SIGN_TYPES:
        raise ValueError(f"Unknown lagna_sign: '{lagna_sign}'. Must be one of {list(_SIGN_TYPES)}")

    lagna_type = _SIGN_TYPES[lagna_sign]
    k_sign = karyesh_sign or lagna_sign

    # ── Method 1: Degrees method (uses Ithasala orb remaining, not total arc) ─
    orb = round(ithasala_orb_remaining, 2)
    if lagna_type == "Movable":
        m1_value, m1_unit = orb, "days"
        m1_desc = f"{orb}° to exact aspect → {orb} days (Movable lagna)."
    elif lagna_type == "Common":
        m1_value, m1_unit = orb, "weeks"
        m1_desc = f"{orb}° to exact aspect → {orb} weeks (Common lagna)."
    else:  # Fixed
        m1_value, m1_unit = orb, "months"
        m1_desc = f"{orb}° to exact aspect → {orb} months (Fixed lagna)."

    # ── Method 2: Nakshatra method ────────────────────────────────────────
    if lagna_lord_nakshatra not in _NAKSHATRAS:
        raise ValueError(f"Unknown nakshatra: '{lagna_lord_nakshatra}'")
    if karyesh_nakshatra not in _NAKSHATRAS:
        raise ValueError(f"Unknown nakshatra: '{karyesh_nakshatra}'")

    nak_count = _nakshatra_gap(lagna_lord_nakshatra, karyesh_nakshatra)
    if lagna_type == "Movable":
        m2_value, m2_unit = nak_count, "days"
        m2_desc = f"{nak_count} nakshatra gap → {nak_count} days (Movable lagna)."
    elif lagna_type == "Common":
        m2_value, m2_unit = nak_count * 2, "days"
        m2_desc = f"{nak_count} nakshatra gap × 2 → {nak_count * 2} days (Common lagna)."
    else:  # Fixed
        m2_value, m2_unit = nak_count * 3, "days"
        m2_desc = f"{nak_count} nakshatra gap × 3 → {nak_count * 3} days (Fixed lagna)."

    # ── Method 3: Sign distance method ───────────────────────────────────
    if k_sign not in _ZODIAC_SIGNS:
        raise ValueError(f"Unknown karyesh_sign: '{k_sign}'")

    sign_dist  = _sign_distance(lagna_sign, k_sign)
    product    = sign_dist * 12
    if lagna_type == "Movable":
        m3_value, m3_unit = product, "days"
        m3_desc = f"{sign_dist} sign(s) × 12 = {product} days (Movable lagna)."
    elif lagna_type == "Common":
        m3_value, m3_unit = product, "months"
        m3_desc = f"{sign_dist} sign(s) × 12 = {product} months (Common lagna)."
    else:  # Fixed
        m3_value, m3_unit = product, "years"
        m3_desc = f"{sign_dist} sign(s) × 12 = {product} years (Fixed lagna)."

    # ── most_likely and timing_note ───────────────────────────────────────
    if lagna_type == "Movable":
        timing_note = "Movable lagna: timing is most reliable."
    elif lagna_type == "Fixed":
        timing_note = "Fixed lagna: timing spans are longer, use as outer bound."
    else:
        timing_note = "Common lagna: double the degrees method for weeks."

    if moon_phase == "waxing":
        timing_note += " Waxing Moon — result expected sooner."
    elif moon_phase == "waning":
        timing_note += " Waning Moon — result may be delayed."

    most_likely = {
        "method": "Method 1 (Degrees)",
        "value":  m1_value,
        "unit":   m1_unit,
    }

    return {
        "lagna_sign_type": lagna_type,
        "method_1": {
            "value":       m1_value,
            "unit":        m1_unit,
            "description": m1_desc,
        },
        "method_2": {
            "value":       m2_value,
            "unit":        m2_unit,
            "description": m2_desc,
        },
        "method_3": {
            "value":       m3_value,
            "unit":        m3_unit,
            "description": m3_desc,
        },
        "most_likely":  most_likely,
        "timing_note":  timing_note,
    }
