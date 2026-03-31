"""
src/tajaka_yogas.py
-------------------
Prasna Tantra (Tajaka) yoga detector for horary astrology.

Implements the five core Tajaka yogas:
  1. Ithasala   — faster planet applying to aspect with slower (FAVOURABLE)
  2. Easarapha  — faster planet separating after aspect with slower (UNFAVOURABLE)
  3. Naktha     — no direct aspect; faster mediator transfers light
  4. Yamaya     — no direct aspect; slower mediator transfers light
  5. Kamboola   — Ithasala triple: Moon reinforces an existing Ithasala pair

Public API
----------
    detect_tajaka_yogas(planets, avasthas=None) -> dict

`planets` is a list of dicts with at minimum:
    name              str
    longitude         float  (0–360°)
    speed_deg_per_day float  (sign used for applying/separating only; NOT for ordering)

`avasthas` is the optional dict from classify_avasthas() — required only for Kamboola grading.

References: Prasna Tantra / Tajaka Neelakanthi (Tajaka system by Neelakantha Daivajnya).
"""

from __future__ import annotations
from itertools import combinations, permutations

# ---------------------------------------------------------------------------
# Hardcoded Tajaka Tables
# ---------------------------------------------------------------------------

# Slowest (index 0) to fastest (index N): used for ALL faster/slower comparisons.
# Rahu and Ketu are always slowest — placed first.
_SPEED_ORDER: list[str] = [
    "Rahu", "Ketu",                            # always slowest
    "Saturn", "Jupiter", "Mars",               # outer planets
    "Sun", "Venus", "Mercury", "Moon",         # inner + luminaries
]
_SPEED_IDX: dict[str, int] = {p: i for i, p in enumerate(_SPEED_ORDER)}

# Tajaka aspects: name → exact angle in degrees
_ASPECTS: dict[str, float] = {
    "Conjunction":  0.0,
    "Sextile":     60.0,
    "Square":      90.0,
    "Trine":      120.0,
    "Opposition": 180.0,
}

# Deepthamsa (orb half-widths) per planet; Rahu/Ketu use Mars value
_DEEPTHAMSA: dict[str, float] = {
    "Sun":     15.0,
    "Moon":    12.0,
    "Mars":     8.0,
    "Mercury":  7.0,
    "Jupiter":  9.0,
    "Venus":    7.0,
    "Saturn":   9.0,
    "Rahu":     8.0,
    "Ketu":     8.0,
}

# Planets that cannot act as mediators (cannot transfer light)
_NO_MEDIATOR = frozenset({"Rahu", "Ketu"})

# ---------------------------------------------------------------------------
# Helper: faster/slower
# ---------------------------------------------------------------------------

def _faster(a: str, b: str) -> bool:
    """True if planet a is faster than planet b (higher index in _SPEED_ORDER)."""
    return _SPEED_IDX.get(a, -1) > _SPEED_IDX.get(b, -1)


def _slower(a: str, b: str) -> bool:
    return _SPEED_IDX.get(a, -1) < _SPEED_IDX.get(b, -1)

# ---------------------------------------------------------------------------
# Helper: angular separation (shortest arc, 0–180°)
# ---------------------------------------------------------------------------

def _separation(lon_a: float, lon_b: float) -> float:
    """Shortest arc between two ecliptic longitudes: result in [0, 180]."""
    diff = abs(lon_a - lon_b) % 360.0
    return min(diff, 360.0 - diff)

# ---------------------------------------------------------------------------
# Core aspect-check function
# ---------------------------------------------------------------------------

def _check_aspect(
    name_a: str, lon_a: float,
    name_b: str, lon_b: float,
) -> dict | None:
    """
    Check whether planets A and B share a valid Tajaka aspect.

    Returns a dict if an aspect is found within the combined Deepthamsa orb,
    else None.

    Returned dict keys:
        aspect_type       str    — e.g. 'Trine'
        exact_aspect_deg  float  — the canonical angle (0/60/90/120/180)
        sep               float  — actual shortest arc between A and B
        current_diff      float  — |sep - exact_aspect_deg| (closeness to exact)
        combined_orb      float  — deepthamsa[A] + deepthamsa[B]
        within_one_degree bool   — current_diff <= 1.0
    """
    orb_a = _DEEPTHAMSA.get(name_a, 8.0)
    orb_b = _DEEPTHAMSA.get(name_b, 8.0)
    combined_orb = orb_a + orb_b

    sep = _separation(lon_a, lon_b)

    best_aspect: str | None = None
    best_exact: float = 0.0
    best_diff: float = float("inf")

    for aspect_name, exact_deg in _ASPECTS.items():
        diff = abs(sep - exact_deg)
        if diff < best_diff:
            best_diff = diff
            best_aspect = aspect_name
            best_exact = exact_deg

    if best_diff > combined_orb:
        return None

    return {
        "aspect_type":       best_aspect,
        "exact_aspect_deg":  best_exact,
        "sep":               round(sep, 4),
        "current_diff":      round(best_diff, 4),
        "combined_orb":      combined_orb,
        "within_one_degree": best_diff <= 1.0,
    }

# ---------------------------------------------------------------------------
# Unified Detection: Ithasala (Applying) vs Easarapha (Separating)
# ---------------------------------------------------------------------------

def _detect_ithasala_easarapha(planets: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Detects Ithasala and Easarapha yogas for all planet pairs.
    Correctly handles circular arithmetic and exact aspect targets.
    """
    ithasala: list[dict] = []
    easarapha: list[dict] = []
    pmap = {p["name"]: p for p in planets}
    names = list(pmap.keys())

    for a_name, b_name in permutations(names, 2):
        if not _faster(a_name, b_name):
            continue

        a = pmap[a_name]
        b = pmap[b_name]
        
        # Check if any standard Tajaka aspect exists within combined orb
        aspect = _check_aspect(a_name, a["longitude"], b_name, b["longitude"])
        if aspect is None:
            continue

        # Rule: Find the exact longitude where A would form the aspect with B
        # For an offset 'exact_aspect_deg', possible targets are (B + offset) or (B - offset)
        offset = aspect["exact_aspect_deg"]
        target_plus  = (b["longitude"] + offset) % 360.0
        target_minus = (b["longitude"] - offset) % 360.0
        
        # Pick whichever is closer to A's current longitude (shortest arc)
        dist_plus = _separation(a["longitude"], target_plus)
        dist_minus = _separation(a["longitude"], target_minus)
        
        exact_target_lon = target_plus if dist_plus <= dist_minus else target_minus
        
        # Compute gap = (exact_target_lon - A_current_lon) % 360.0
        # If gap [0, 180] -> A moving toward target (Applying) -> Ithasala
        # If gap (180, 360) -> A moving away from target (Separating) -> Easarapha
        gap = (exact_target_lon - a["longitude"]) % 360.0
        
        is_applying = (gap <= 180.0)
        
        if is_applying:
            ithasala.append({
                "faster_planet":    a_name,
                "slower_planet":    b_name,
                "aspect_type":      aspect["aspect_type"],
                "exact_aspect_deg": aspect["exact_aspect_deg"],
                "separation":       aspect["sep"],
                "current_diff":     aspect["current_diff"],
                "combined_orb":     aspect["combined_orb"],
                "orb_remaining":    round(gap, 4),
                "is_poorna":        aspect["within_one_degree"],
                "favorability":     "FAVOURABLE",
                "interpretation": (
                    f"{a_name} ({aspect['aspect_type']}) applies to {b_name} — "
                    f"{gap:.2f}° from exact. "
                    f"{'Poorna Ithasala (near-exact).' if aspect['within_one_degree'] else 'Ithasala active.'} "
                    "Signifies success and accomplishment of the querent's desire."
                ),
            })
        else:
            # For Easarapha, the "past exact" degrees is the arc A has already travelled
            past_exact = (360.0 - gap) % 360.0
            easarapha.append({
                "faster_planet":    a_name,
                "slower_planet":    b_name,
                "aspect_type":      aspect["aspect_type"],
                "exact_aspect_deg": aspect["exact_aspect_deg"],
                "separation":       aspect["sep"],
                "current_diff":     round(past_exact, 4),
                "combined_orb":     aspect["combined_orb"],
                "favorability":     "UNFAVOURABLE",
                "interpretation": (
                    f"{a_name} separating from {aspect['aspect_type']} with {b_name} — "
                    f"{past_exact:.2f}° past exact. "
                    "The matter has already been decided in an unfavourable direction; "
                    "opportunity has passed."
                ),
            })

    return ithasala, easarapha


# ---------------------------------------------------------------------------
# Yoga 3 — Naktha (faster mediator transfers light)
# ---------------------------------------------------------------------------

def _detect_naktha(planets: list[dict]) -> list[dict]:
    """
    Pairs (A, B) with NO Tajaka aspect.
    A faster mediator C has valid aspects with BOTH A and B.
    Rahu/Ketu excluded from C.
    """
    instances: list[dict] = []
    pmap = {p["name"]: p for p in planets}
    names = list(pmap.keys())
    classical = [n for n in names if n not in _NO_MEDIATOR]

    for a_name, b_name in combinations(names, 2):
        a = pmap[a_name]
        b = pmap[b_name]

        # Pair must have NO direct Tajaka aspect
        if _check_aspect(a_name, a["longitude"], b_name, b["longitude"]) is not None:
            continue

        # Search for faster mediator C
        for c_name in classical:
            if c_name in (a_name, b_name):
                continue
            if not (_faster(c_name, a_name) and _faster(c_name, b_name)):
                continue

            c = pmap[c_name]
            asp_ca = _check_aspect(c_name, c["longitude"], a_name, a["longitude"])
            asp_cb = _check_aspect(c_name, c["longitude"], b_name, b["longitude"])

            if asp_ca is None or asp_cb is None:
                continue

            instances.append({
                "planet_pair":      (a_name, b_name),
                "mediator":         c_name,
                "mediator_role":    "faster",
                "aspect_with_A":    asp_ca["aspect_type"],
                "aspect_with_B":    asp_cb["aspect_type"],
                "interpretation":   (
                    f"No direct Tajaka aspect between {a_name} and {b_name}. "
                    f"{c_name} (faster mediator) transfers light via "
                    f"{asp_ca['aspect_type']} to {a_name} and "
                    f"{asp_cb['aspect_type']} to {b_name}. "
                    "Third party assistance will be needed for the matter to succeed."
                ),
            })

    return instances


# ---------------------------------------------------------------------------
# Yoga 4 — Yamaya (slower mediator transfers light)
# ---------------------------------------------------------------------------

def _detect_yamaya(planets: list[dict]) -> list[dict]:
    """
    Same as Naktha but the mediator C is SLOWER than both A and B.
    Rahu/Ketu excluded from C.
    """
    instances: list[dict] = []
    pmap = {p["name"]: p for p in planets}
    names = list(pmap.keys())
    classical = [n for n in names if n not in _NO_MEDIATOR]

    for a_name, b_name in combinations(names, 2):
        a = pmap[a_name]
        b = pmap[b_name]

        if _check_aspect(a_name, a["longitude"], b_name, b["longitude"]) is not None:
            continue

        for c_name in classical:
            if c_name in (a_name, b_name):
                continue
            if not (_slower(c_name, a_name) and _slower(c_name, b_name)):
                continue

            c = pmap[c_name]
            asp_ca = _check_aspect(c_name, c["longitude"], a_name, a["longitude"])
            asp_cb = _check_aspect(c_name, c["longitude"], b_name, b["longitude"])

            if asp_ca is None or asp_cb is None:
                continue

            instances.append({
                "planet_pair":      (a_name, b_name),
                "mediator":         c_name,
                "mediator_role":    "slower",
                "aspect_with_A":    asp_ca["aspect_type"],
                "aspect_with_B":    asp_cb["aspect_type"],
                "interpretation":   (
                    f"No direct Tajaka aspect between {a_name} and {b_name}. "
                    f"{c_name} (slower mediator) transfers light via "
                    f"{asp_ca['aspect_type']} to {a_name} and "
                    f"{asp_cb['aspect_type']} to {b_name}. "
                    "An elder, senior, or established authority will intervene "
                    "to facilitate the matter."
                ),
            })

    return instances


# ---------------------------------------------------------------------------
# Yoga 5 — Kamboola (Moon reinforces an Ithasala pair)
# ---------------------------------------------------------------------------

def _detect_kamboola(
    ithasala_list: list[dict],
    planets: list[dict],
    avasthas: dict | None,
) -> list[dict]:
    """
    Two planets X and Y already have Ithasala.
    The Moon also has Ithasala with either X or Y.

    Grade (requires avasthas dict):
      uttamottama — X, Y, and Moon all in {'deeptha', 'swastha'}
      madhyama    — Moon in {'muditha', 'suveerya'}
      adhama      — otherwise
    """
    if not ithasala_list:
        return []

    instances: list[dict] = []
    pmap = {p["name"]: p for p in planets}

    # Index Ithasala pairs for quick lookup: frozenset({A,B}) → instance
    ithasala_pairs: dict[frozenset, dict] = {}
    for inst in ithasala_list:
        key = frozenset({inst["faster_planet"], inst["slower_planet"]})
        ithasala_pairs[key] = inst

    # For each Ithasala pair (X, Y) where NEITHER is the Moon,
    # check if Moon separately has Ithasala with X or Y.
    # Moon is always the THIRD reinforcing planet — never part of the primary pair.
    for pair_key, pair_inst in ithasala_pairs.items():
        # Skip any pair that includes the Moon — Moon can only be the reinforcer
        if "Moon" in pair_key:
            continue

        x_name, y_name = tuple(pair_key)

        if "Moon" not in pmap:
            continue

        moon_ithasala_with: str | None = None

        for target_name in (x_name, y_name):
            target = pmap.get(target_name)
            if target is None:
                continue

            moon_key = frozenset({"Moon", target_name})
            if moon_key in ithasala_pairs:
                moon_ithasala_with = target_name
                break

        if moon_ithasala_with is None:
            continue

        # Grade
        grade = "adhama"
        grade_reason = "Moon's condition is not strong."
        if avasthas is not None:
            strong_set = {"deeptha", "swastha"}
            x_av = avasthas.get(x_name, {}).get("avastha", "")
            y_av = avasthas.get(y_name, {}).get("avastha", "")
            moon_av = avasthas.get("Moon", {}).get("avastha", "")

            if x_av in strong_set and y_av in strong_set and moon_av in strong_set:
                grade = "uttamottama"
                grade_reason = (
                    f"All three ({x_name}, {y_name}, Moon) are in excellent dignity "
                    "(deeptha or swastha). Highest grade — complete success assured."
                )
            elif moon_av in {"muditha", "suveerya"}:
                grade = "madhyama"
                grade_reason = (
                    f"Moon is in {moon_av} state — moderate positive dignity. "
                    "Moderate success; outcome achievable with effort."
                )
            else:
                grade_reason = (
                    f"Moon is in {moon_av} state — below moderate dignity. "
                    "Success is uncertain or delayed."
                )

        instances.append({
            "ithasala_pair":       (x_name, y_name),
            "moon_ithasala_with":  moon_ithasala_with,
            "grade":               grade,
            "grade_reason":        grade_reason,
            "interpretation": (
                f"Kamboola yoga: Moon reinforces the {x_name}–{y_name} Ithasala "
                f"via Ithasala with {moon_ithasala_with}. "
                f"Grade: {grade.upper()}. {grade_reason}"
            ),
        })

    return instances


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_tajaka_yogas(
    planets: list[dict],
    avasthas: dict | None = None,
) -> dict:
    """
    Detect all five Tajaka yogas for a given set of planet positions.

    Parameters
    ----------
    planets : list of dicts with keys: name, longitude, speed_deg_per_day
    avasthas : optional dict from classify_avasthas() — needed for Kamboola grading

    Returns
    -------
    dict with keys:
        ithasala   list[dict]
        easarapha  list[dict]
        naktha     list[dict]
        yamaya     list[dict]
        kamboola   list[dict]
        summary    list[str]   — one plain-English line per detected yoga instance
    """
    ithasala, easarapha = _detect_ithasala_easarapha(planets)
    naktha    = _detect_naktha(planets)
    yamaya    = _detect_yamaya(planets)
    kamboola  = _detect_kamboola(ithasala, planets, avasthas)

    # Build flat human-readable summary
    summary: list[str] = []

    for inst in ithasala:
        poorna = " (Poorna — near exact)" if inst["is_poorna"] else ""
        summary.append(
            f"ITHASALA{poorna}: {inst['faster_planet']} {inst['aspect_type']} "
            f"{inst['slower_planet']} — {inst['orb_remaining']:.2f}° to exact. FAVOURABLE."
        )

    for inst in easarapha:
        summary.append(
            f"EASARAPHA: {inst['faster_planet']} {inst['aspect_type']} "
            f"{inst['slower_planet']} — {inst['current_diff']:.2f}° past exact. UNFAVOURABLE."
        )

    for inst in naktha:
        a, b = inst["planet_pair"]
        summary.append(
            f"NAKTHA: {a}–{b} linked via faster mediator {inst['mediator']}. "
            "Third party assistance needed."
        )

    for inst in yamaya:
        a, b = inst["planet_pair"]
        summary.append(
            f"YAMAYA: {a}–{b} linked via slower mediator {inst['mediator']}. "
            "Senior intervention needed."
        )

    for inst in kamboola:
        a, b = inst["ithasala_pair"]
        summary.append(
            f"KAMBOOLA ({inst['grade'].upper()}): Moon reinforces {a}–{b} Ithasala "
            f"via {inst['moon_ithasala_with']}."
        )

    return {
        "ithasala":  ithasala,
        "easarapha": easarapha,
        "naktha":    naktha,
        "yamaya":    yamaya,
        "kamboola":  kamboola,
        "summary":   summary,
    }
