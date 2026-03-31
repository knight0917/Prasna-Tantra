"""
src/sincerity_check.py
----------------------
Prasna Tantra horary astrology — sincerity check engine.

Implements the rules from Chapter 1 to determine if a querent's intent is sincere.
Based on the placement and aspects of natural benefics, malefics, and key lords.

Public API
----------
    check_sincerity(positions, house_lords) -> dict
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Classification Tables
# ---------------------------------------------------------------------------

_MALEFICS = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})
_BENEFICS = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})

# ---------------------------------------------------------------------------
# Dual-access helpers (supports Pydantic objects or dicts)
# ---------------------------------------------------------------------------

def _get(obj, field: str, default=None):
    if isinstance(obj, dict):
        return obj.get(field, default)
    return getattr(obj, field, default)


def _get_aspects(planet_data) -> list:
    return _get(planet_data, "aspects", []) or []


def _aspect_target_house(aspect_entry) -> int:
    return int(_get(aspect_entry, "target_house", -1))


def _aspect_number(aspect_entry) -> int:
    # Assuming 'aspect_number' or 'aspect_type' can be mapped
    # Common Vedic aspects: 1 (conjunction), 4 (square), 7 (opposition), 5/9 (trine)
    # The engine output 'aspect_number' typically holds the 1-indexed count
    val = _get(aspect_entry, "aspect_num", -1)
    if val == -1:
        # Fallback to older field name if present
        val = _get(aspect_entry, "aspect_number", -1)
    return int(val)


def _aspected_planets(aspect_entry) -> list[str]:
    return _get(aspect_entry, "aspected_planets", []) or []

# ---------------------------------------------------------------------------
# Helper functions requested
# ---------------------------------------------------------------------------

def _planet_in_house(name: str, house_num: int, positions: dict) -> bool:
    planet = positions.get(name)
    if planet is None:
        return False
    return _get(planet, "house") == house_num


def _planet_aspects_house(name: str, house_num: int, positions: dict) -> bool:
    planet = positions.get(name)
    if planet is None:
        return False
    for asp in _get_aspects(planet):
        if _aspect_target_house(asp) == house_num:
            return True
    return False


def _planets_in_house(house_num: int, positions: dict) -> list[str]:
    return [
        name for name, p in positions.items()
        if name != "Ascendant" and _get(p, "house") == house_num
    ]


def _planet_aspects_planet_with_number(name: str, target_name: str, aspect_num: int, positions: dict) -> bool:
    planet = positions.get(name)
    if planet is None:
        return False
    for asp in _get_aspects(planet):
        if target_name in _aspected_planets(asp) and _aspect_number(asp) == aspect_num:
            return True
    return False


def _planet_aspects_house_with_number(name: str, target_house: int, aspect_num: int, positions: dict) -> bool:
    planet = positions.get(name)
    if planet is None:
        return False
    for asp in _get_aspects(planet):
        if _aspect_target_house(asp) == target_house and _aspect_number(asp) == aspect_num:
            return True
    return False

# ---------------------------------------------------------------------------
# Main Sincerity Logic
# ---------------------------------------------------------------------------

def check_sincerity(positions: dict, house_lords: dict) -> dict:
    matched_insincere = []
    matched_sincere = []
    
    seventh_lord = house_lords.get("7")
    
    # --- INSINCERE indicators ---
    
    # Rule I1: Moon in H1 AND Saturn in a quadrant (1,4,7,10) AND Mercury combust
    quadrants = {1, 4, 7, 10}
    saturn_h = _get(positions.get("Saturn"), "house")
    mercury_combust = _get(positions.get("Mercury"), "is_combust", False)
    if (_planet_in_house("Moon", 1, positions) and 
        saturn_h in quadrants and 
        mercury_combust):
        matched_insincere.append("Rule I1")

    # Rule I2: Mars aspects H1 AND Mercury aspects H1 AND Moon in H1
    if (_planet_aspects_house("Mars", 1, positions) and 
        _planet_aspects_house("Mercury", 1, positions) and 
        _planet_in_house("Moon", 1, positions)):
        matched_insincere.append("Rule I2")

    # Rule I3: Any natural malefic is in house 1
    h1_occupants = _planets_in_house(1, positions)
    if any(m in h1_occupants for m in _MALEFICS):
        matched_insincere.append("Rule I3")

    # Rule I4: Jupiter aspects 7th lord with square (4) OR Mercury aspects 7th lord's house (H7) with square
    if seventh_lord:
        if _planet_aspects_planet_with_number("Jupiter", seventh_lord, 4, positions) or \
           _planet_aspects_house_with_number("Mercury", 7, 4, positions):
            matched_insincere.append("Rule I4")

    # --- SINCERE indicators ---

    # Rule S1: Any natural benefic is in house 1
    if any(b in h1_occupants for b in _BENEFICS):
        matched_sincere.append("Rule S1")

    # Rule S2: Mars aspects H1 AND (full Moon aspects H1 OR Jupiter aspects H1)
    # Using 'full Moon' as any Moon for now (as per stub request)
    if _planet_aspects_house("Mars", 1, positions) and \
       (_planet_aspects_house("Moon", 1, positions) or _planet_aspects_house("Jupiter", 1, positions)):
        matched_sincere.append("Rule S2")

    # Rule S3: Jupiter aspects 7th lord's house (H7) with trine (5 or 9) OR Mercury aspects H7 with trine
    if (_planet_aspects_house_with_number("Jupiter", 7, 5, positions) or \
        _planet_aspects_house_with_number("Jupiter", 7, 9, positions) or \
        _planet_aspects_house_with_number("Mercury", 7, 5, positions) or \
        _planet_aspects_house_with_number("Mercury", 7, 9, positions)):
        matched_sincere.append("Rule S3")

    # VERDICT LOGIC — book-accurate:
    if len(matched_insincere) > 0 and len(matched_sincere) == 0:
        # Only insincere rules fired — clear dishonest intent
        sincere = False
        verdict = 'declined'
        message = 'The chart indicates this question was not asked with genuine intent.'
    elif len(matched_insincere) > 0 and len(matched_sincere) > 0:
        # Both fired — sincere rules partially override insincere
        # Book says sincere indicators save the reading
        sincere = True
        verdict = 'caution'
        message = 'Mixed signals in the chart. The question may be sincere but asked under stress or confusion. Proceed carefully.'
    elif len(matched_sincere) > 0 and len(matched_insincere) == 0:
        # Only sincere rules fired — confirmed genuine
        sincere = True
        verdict = 'confirmed'
        message = 'The chart confirms this question is asked with genuine and sincere intent.'
    else:
        # No rules fired either way — neutral chart
        sincere = True
        verdict = 'neutral'
        message = 'No special combinations present. Proceeding with the reading.'

    return {
        'sincere': sincere,
        'verdict': verdict,
        'message': message,
        'matched_insincere_rules': matched_insincere,
        'matched_sincere_rules': matched_sincere
    }
