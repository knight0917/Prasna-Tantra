"""
src/avasthas.py
---------------
Vedic / Prasna Tantra Avastha (planetary state) classifier.

Each planet is classified into exactly ONE of 10 avasthas using a strict
priority chain (highest-priority match wins). The function is purely
functional — no global state, no side-effects.

Public API
----------
    classify_avasthas(planets: list[dict]) -> dict[str, dict]

Each element of `planets` must be a dict with:
    name              str   — planet name (e.g. "Sun")
    longitude         float — tropical ecliptic longitude 0–360°
    sign              str   — zodiac sign name
    house             int   — whole-sign house number 1–12
    is_combust        bool
    speed_deg_per_day float — negative = retrograde

Priority chain (highest wins):
    1. mushita    — combust (is_combust=True)
    2. nipeeditha — losing planetary war (within 1° same sign, lower longitude)
    3. deeptha    — within 15° of exaltation peak
    4. swastha    — in own sign
    5. muditha    — sign lord is a MUTUAL friend
    6. suptha     — sign lord is inimical (not mutual friend) — overrides motion
    7. suveerya   — direct, moving toward exaltation
    8. pariheena  — retrograde OR direct but past exaltation, heading to debilitation
    9. athiveerya — stub: kendra house (1,4,7,10) when none above matched
   10. deena      — within 15° of debilitation peak
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Hardcoded Vedic Tables
# ---------------------------------------------------------------------------

# Exaltation: (sign, exact_degree_within_sign)
_EXALTATION: dict[str, tuple[str, float]] = {
    "Sun":     ("Aries",       10.0),
    "Moon":    ("Taurus",       3.0),
    "Mars":    ("Capricorn",   28.0),
    "Mercury": ("Virgo",       15.0),
    "Jupiter": ("Cancer",       5.0),
    "Venus":   ("Pisces",      27.0),
    "Saturn":  ("Libra",       20.0),
}

# Debilitation: (sign, exact_degree_within_sign)
_DEBILITATION: dict[str, tuple[str, float]] = {
    "Sun":     ("Libra",       10.0),
    "Moon":    ("Scorpio",      3.0),
    "Mars":    ("Cancer",      28.0),
    "Mercury": ("Pisces",      15.0),
    "Jupiter": ("Capricorn",    5.0),
    "Venus":   ("Virgo",       27.0),
    "Saturn":  ("Aries",       20.0),
}

# Own signs
_OWN_SIGNS: dict[str, list[str]] = {
    "Sun":     ["Leo"],
    "Moon":    ["Cancer"],
    "Mars":    ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"],
    "Jupiter": ["Sagittarius", "Pisces"],
    "Venus":   ["Taurus", "Libra"],
    "Saturn":  ["Capricorn", "Aquarius"],
}

# Sign lords
_SIGN_LORDS: dict[str, str] = {
    "Aries":       "Mars",    "Taurus":      "Venus",   "Gemini":      "Mercury",
    "Cancer":      "Moon",    "Leo":         "Sun",     "Virgo":       "Mercury",
    "Libra":       "Venus",   "Scorpio":     "Mars",    "Sagittarius": "Jupiter",
    "Capricorn":   "Saturn",  "Aquarius":    "Saturn",  "Pisces":      "Jupiter",
}

# Mutual friendship pairs — muditha requires BOTH planets to be friends of each other.
# Encoded as a frozenset of frozensets for O(1) pair membership testing.
_MUTUAL_FRIEND_PAIRS: frozenset[frozenset[str]] = frozenset({
    frozenset({"Sun",     "Moon"}),
    frozenset({"Sun",     "Mars"}),
    frozenset({"Moon",    "Mars"}),
    frozenset({"Moon",    "Jupiter"}),
    frozenset({"Mars",    "Jupiter"}),
    frozenset({"Mercury", "Venus"}),
    frozenset({"Mercury", "Saturn"}),
    frozenset({"Venus",   "Saturn"}),
})

# Pre-compute per-planet mutual friends for O(1) lookup: planet → set of mutual friends
_MUTUAL_FRIENDS: dict[str, set[str]] = {p: set() for p in _EXALTATION}
for _pair in _MUTUAL_FRIEND_PAIRS:
    _a, _b = tuple(_pair)
    if _a in _MUTUAL_FRIENDS:
        _MUTUAL_FRIENDS[_a].add(_b)
    if _b in _MUTUAL_FRIENDS:
        _MUTUAL_FRIENDS[_b].add(_a)

# Sign order for absolute longitude conversion
_SIGNS_ORDER = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Avastha result metadata
_RESULT_MEANINGS: dict[str, str] = {
    "deeptha":    "Success in undertaking",
    "swastha":    "Fame and recognition",
    "muditha":    "Gain of wealth and happiness",
    "suveerya":   "Access to conveyance and prosperity",
    "pariheena":  "Loss of money and failure",
    "athiveerya": "Political success and valuable contacts",
    "deena":      "Sorrow",
    "suptha":     "Sorrow and fear from enemies",
    "nipeeditha": "Loss of money",
    "mushita":    "Failure and loss",
}

_STRENGTH: dict[str, str] = {
    "deeptha":    "strong",
    "swastha":    "strong",
    "muditha":    "strong",
    "suveerya":   "strong",
    "athiveerya": "strong",
    "pariheena":  "moderate",
    "deena":      "moderate",
    "suptha":     "weak",
    "nipeeditha": "weak",
    "mushita":    "weak",
}

# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

def _absolute_lon(sign: str, degree_in_sign: float) -> float:
    """Convert sign + degree-within-sign to absolute 0–360° longitude."""
    return float(_SIGNS_ORDER.index(sign) * 30) + degree_in_sign


def _angular_distance(a: float, b: float) -> float:
    """
    Shortest arc between two longitudes on the 360° circle (always ≥ 0).
    Uses min(|diff|, 360 - |diff|) to handle the 0°/360° wrap correctly.
    """
    diff = abs(a - b) % 360.0
    return min(diff, 360.0 - diff)


def _forward_arc(from_lon: float, to_lon: float) -> float:
    """
    Arc going in the prograde (direct) direction from `from_lon` to `to_lon`.
    Returns a value in [0, 360).
    """
    return (to_lon - from_lon) % 360.0


# ---------------------------------------------------------------------------
# Per-condition predicates
# ---------------------------------------------------------------------------

def _is_deeptha(name: str, longitude: float) -> bool:
    """Within 15° (shortest arc) of exact exaltation longitude."""
    if name not in _EXALTATION:
        return False
    exalt_lon = _absolute_lon(*_EXALTATION[name])
    return _angular_distance(longitude, exalt_lon) <= 15.0


def _is_deena(name: str, longitude: float) -> bool:
    """Within 15° (shortest arc) of exact debilitation longitude."""
    if name not in _DEBILITATION:
        return False
    debil_lon = _absolute_lon(*_DEBILITATION[name])
    return _angular_distance(longitude, debil_lon) <= 15.0


def _is_swastha(name: str, sign: str) -> bool:
    return sign in _OWN_SIGNS.get(name, [])


def _is_muditha(name: str, sign: str) -> bool:
    """
    Muditha only if the sign's lord is a MUTUAL friend of this planet.
    Uses the pre-computed _MUTUAL_FRIENDS table for O(1) lookup.
    """
    lord = _SIGN_LORDS.get(sign)
    if lord is None or lord == name:
        return False
    return lord in _MUTUAL_FRIENDS.get(name, set())


def _is_suptha(name: str, sign: str) -> bool:
    """
    Suptha if the sign's lord is NOT a mutual friend and NOT the planet itself.
    (Inimical: not in mutual friends list, not own sign.)
    """
    lord = _SIGN_LORDS.get(sign)
    if lord is None or lord == name:
        return False
    return lord not in _MUTUAL_FRIENDS.get(name, set())


def _is_suveerya(name: str, longitude: float, speed: float) -> bool:
    """
    Direct (speed > 0) AND the exaltation point is within the forward
    half-circle (prograde arc to exaltation < 180°).
    """
    if speed <= 0 or name not in _EXALTATION:
        return False
    exalt_lon = _absolute_lon(*_EXALTATION[name])
    return _forward_arc(longitude, exalt_lon) < 180.0


def _is_pariheena(name: str, longitude: float, speed: float) -> bool:
    """
    Retrograde (speed < 0) OR direct but past the exaltation peak and heading
    toward debilitation (prograde arc to exaltation >= 180°, meaning exaltation
    is now in the backward half-circle — planet overshot it).

    Does NOT trigger based on sign placement alone.
    """
    if speed < 0:
        return True  # Retrograde — always pariheena
    if name not in _EXALTATION:
        return False
    exalt_lon = _absolute_lon(*_EXALTATION[name])
    return _forward_arc(longitude, exalt_lon) >= 180.0


# ---------------------------------------------------------------------------
# O(1) planetary war pre-computation
# ---------------------------------------------------------------------------

def _build_war_losers(planets: list[dict]) -> frozenset[str]:
    """
    Compute all planetary war losers in one O(n²/2) pass before classification.
    A planet loses the war if it is within 1° of another planet in the SAME sign
    and has the LOWER longitude.

    Returns a frozenset of planet names that lost a war (are nipeeditha-eligible).
    Only classical planets (those in _EXALTATION) are considered.
    """
    classical = [p for p in planets if p["name"] in _EXALTATION]
    losers: set[str] = set()

    for i in range(len(classical)):
        for j in range(i + 1, len(classical)):
            a, b = classical[i], classical[j]
            if a.get("sign") != b.get("sign"):
                continue
            lon_a, lon_b = a["longitude"], b["longitude"]
            if _angular_distance(lon_a, lon_b) <= 1.0:
                # Lower longitude planet loses the war
                if lon_a < lon_b:
                    losers.add(a["name"])
                elif lon_b < lon_a:
                    losers.add(b["name"])
                # Exact tie: neither loses

    return frozenset(losers)


# ---------------------------------------------------------------------------
# Priority-ordered classifier for a single planet
# ---------------------------------------------------------------------------

def _classify_one(
    name: str,
    longitude: float,
    sign: str,
    house: int,
    is_combust: bool,
    speed: float,
    war_losers: frozenset[str],
) -> str:
    """
    Classify one planet into its avastha following the 10-level priority chain.
    `war_losers` is pre-computed once by classify_avasthas() for O(1) lookup.

    Order: mushita → nipeeditha → deeptha → swastha → muditha → suptha
           → suveerya → pariheena → athiveerya → deena
    """

    # 1. Mushita — combust overrides everything
    if is_combust:
        return "mushita"

    # 2. Nipeeditha — losing planetary war (lower longitude, within 1° in same sign)
    if name in war_losers:
        return "nipeeditha"

    # 3. Deeptha — within 15° of exaltation peak
    if _is_deeptha(name, longitude):
        return "deeptha"

    # 4. Swastha — in own sign
    if _is_swastha(name, sign):
        return "swastha"

    # 5. Muditha — sign lord is a MUTUAL friend
    if _is_muditha(name, sign):
        return "muditha"

    # 6. Suptha — sign lord is inimical (not mutual friend, not self)
    #    Enemy sign overrides directional motion states below.
    if _is_suptha(name, sign):
        return "suptha"

    # 7. Suveerya — direct, progressing toward exaltation
    if _is_suveerya(name, longitude, speed):
        return "suveerya"

    # 8. Pariheena — retrograde OR direct but past exaltation peak
    if _is_pariheena(name, longitude, speed):
        return "pariheena"

    # 9. Athiveerya (stub) — none of above matched; planet in kendra house
    if house in (1, 4, 7, 10):
        return "athiveerya"

    # 10. Deena — within 15° of debilitation peak
    if _is_deena(name, longitude):
        return "deena"

    # Fallback — should not be reached for well-formed classical planet input
    return "suptha"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_avasthas(planets: list[dict]) -> dict[str, dict]:
    """
    Classify all planets into their Vedic avastha.

    Parameters
    ----------
    planets : list of dicts, each with keys:
        name              str
        longitude         float   (tropical, 0–360°)
        sign              str
        house             int     (1–12)
        is_combust        bool
        speed_deg_per_day float   (negative = retrograde)

    Returns
    -------
    dict keyed by planet name:
        avastha        str
        result_meaning str
        strength       str  ('strong' | 'moderate' | 'weak')
    """
    # Pre-compute planetary war losers once — O(n²/2) pass, O(1) lookups later
    war_losers = _build_war_losers(planets)

    result: dict[str, dict] = {}

    for p in planets:
        name: str = p["name"]

        # Rahu, Ketu, Ascendant — no avastha classification
        if name not in _EXALTATION:
            continue

        avastha = _classify_one(
            name=name,
            longitude=p["longitude"],
            sign=p["sign"],
            house=p.get("house", 0),
            is_combust=p.get("is_combust", False),
            speed=p.get("speed_deg_per_day", 0.0),
            war_losers=war_losers,
        )

        result[name] = {
            "avastha":        avastha,
            "result_meaning": _RESULT_MEANINGS[avastha],
            "strength":       _STRENGTH[avastha],
        }

    return result
