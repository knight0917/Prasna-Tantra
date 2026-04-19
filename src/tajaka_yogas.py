"""
Prasna Tantra (Tajaka) yoga detector for horary astrology.

The book's practical use centers on the classical planets and on whether the
relevant significators are applying, separating, or joined through transfer of
light. This module therefore keeps the raw yoga detection classical and leaves
query-specific filtering to the judgment/output layers.
"""

from __future__ import annotations

from itertools import combinations, permutations

_SPEED_ORDER: list[str] = [
    "Saturn",
    "Jupiter",
    "Mars",
    "Sun",
    "Venus",
    "Mercury",
    "Moon",
]
_SPEED_IDX: dict[str, int] = {planet: idx for idx, planet in enumerate(_SPEED_ORDER)}
_CLASSICAL_PLANETS: frozenset[str] = frozenset(_SPEED_ORDER)

_ASPECTS: dict[str, float] = {
    "Conjunction": 0.0,
    "Sextile": 60.0,
    "Square": 90.0,
    "Trine": 120.0,
    "Opposition": 180.0,
}

_ASPECT_QUALITY: dict[str, str] = {
    "Conjunction": "supportive",
    "Sextile": "supportive",
    "Trine": "supportive",
    "Square": "obstructed",
    "Opposition": "adverse",
}

_DEEPTHAMSA: dict[str, float] = {
    "Sun": 15.0,
    "Moon": 12.0,
    "Mars": 8.0,
    "Mercury": 7.0,
    "Jupiter": 9.0,
    "Venus": 7.0,
    "Saturn": 9.0,
}


def _faster(a: str, b: str) -> bool:
    return _SPEED_IDX.get(a, -1) > _SPEED_IDX.get(b, -1)


def _slower(a: str, b: str) -> bool:
    return _SPEED_IDX.get(a, -1) < _SPEED_IDX.get(b, -1)


def _separation(lon_a: float, lon_b: float) -> float:
    diff = abs(lon_a - lon_b) % 360.0
    return min(diff, 360.0 - diff)


def _check_aspect(name_a: str, lon_a: float, name_b: str, lon_b: float) -> dict | None:
    orb_a = _DEEPTHAMSA.get(name_a)
    orb_b = _DEEPTHAMSA.get(name_b)
    if orb_a is None or orb_b is None:
        return None

    combined_orb = orb_a + orb_b
    sep = _separation(lon_a, lon_b)

    best_aspect: str | None = None
    best_exact = 0.0
    best_diff = float("inf")
    for aspect_name, exact_deg in _ASPECTS.items():
        diff = abs(sep - exact_deg)
        if diff < best_diff:
            best_diff = diff
            best_aspect = aspect_name
            best_exact = exact_deg

    if best_aspect is None or best_diff > combined_orb:
        return None

    return {
        "aspect_type": best_aspect,
        "aspect_quality": _ASPECT_QUALITY[best_aspect],
        "exact_aspect_deg": best_exact,
        "sep": round(sep, 4),
        "current_diff": round(best_diff, 4),
        "combined_orb": combined_orb,
        "within_one_degree": best_diff <= 1.0,
    }


def _detect_ithasala_easarapha(planets: list[dict]) -> tuple[list[dict], list[dict]]:
    ithasala: list[dict] = []
    easarapha: list[dict] = []
    pmap = {p["name"]: p for p in planets if p["name"] in _CLASSICAL_PLANETS}
    names = list(pmap.keys())

    for a_name, b_name in permutations(names, 2):
        if not _faster(a_name, b_name):
            continue

        a = pmap[a_name]
        b = pmap[b_name]
        aspect = _check_aspect(a_name, a["longitude"], b_name, b["longitude"])
        if aspect is None:
            continue

        offset = aspect["exact_aspect_deg"]
        target_plus = (b["longitude"] + offset) % 360.0
        target_minus = (b["longitude"] - offset) % 360.0
        dist_plus = _separation(a["longitude"], target_plus)
        dist_minus = _separation(a["longitude"], target_minus)
        exact_target_lon = target_plus if dist_plus <= dist_minus else target_minus
        gap = (exact_target_lon - a["longitude"]) % 360.0
        is_applying = gap <= 180.0

        if is_applying:
            perfects_matter = aspect["aspect_quality"] != "adverse"
            if aspect["aspect_quality"] == "supportive":
                interpretation = (
                    f"{a_name} applies by {aspect['aspect_type'].lower()} to {b_name} - "
                    f"{gap:.2f} degrees from exact. "
                    f"{'The matter is near completion.' if aspect['within_one_degree'] else 'The matter moves toward perfection.'}"
                )
            elif aspect["aspect_quality"] == "obstructed":
                interpretation = (
                    f"{a_name} applies by square to {b_name} - {gap:.2f} degrees from exact. "
                    "Perfection is possible, but strain and obstruction attend it."
                )
            else:
                interpretation = (
                    f"{a_name} applies by opposition to {b_name} - {gap:.2f} degrees from exact. "
                    "The application is hostile; denial, contention, or reversal is indicated."
                )

            ithasala.append(
                {
                    "faster_planet": a_name,
                    "slower_planet": b_name,
                    "aspect_type": aspect["aspect_type"],
                    "aspect_quality": aspect["aspect_quality"],
                    "exact_aspect_deg": aspect["exact_aspect_deg"],
                    "separation": aspect["sep"],
                    "current_diff": aspect["current_diff"],
                    "combined_orb": aspect["combined_orb"],
                    "orb_remaining": round(gap, 4),
                    "is_poorna": aspect["within_one_degree"],
                    "favorability": "FAVOURABLE" if perfects_matter else "UNFAVOURABLE",
                    "perfects_matter": perfects_matter,
                    "interpretation": interpretation,
                }
            )
            continue

        past_exact = (360.0 - gap) % 360.0
        easarapha.append(
            {
                "faster_planet": a_name,
                "slower_planet": b_name,
                "aspect_type": aspect["aspect_type"],
                "aspect_quality": aspect["aspect_quality"],
                "exact_aspect_deg": aspect["exact_aspect_deg"],
                "separation": aspect["sep"],
                "current_diff": round(past_exact, 4),
                "combined_orb": aspect["combined_orb"],
                "favorability": "UNFAVOURABLE",
                "interpretation": (
                    f"{a_name} separates from {aspect['aspect_type'].lower()} with {b_name} - "
                    f"{past_exact:.2f} degrees past exact. "
                    "The matter has receded; separation or failure is indicated."
                ),
            }
        )

    return ithasala, easarapha


def _detect_naktha(planets: list[dict]) -> list[dict]:
    instances: list[dict] = []
    pmap = {p["name"]: p for p in planets if p["name"] in _CLASSICAL_PLANETS}
    names = list(pmap.keys())

    for a_name, b_name in combinations(names, 2):
        a = pmap[a_name]
        b = pmap[b_name]

        if _check_aspect(a_name, a["longitude"], b_name, b["longitude"]) is not None:
            continue

        for c_name in names:
            if c_name in (a_name, b_name):
                continue
            if not (_faster(c_name, a_name) and _faster(c_name, b_name)):
                continue

            c = pmap[c_name]
            asp_ca = _check_aspect(c_name, c["longitude"], a_name, a["longitude"])
            asp_cb = _check_aspect(c_name, c["longitude"], b_name, b["longitude"])
            if asp_ca is None or asp_cb is None:
                continue

            instances.append(
                {
                    "planet_pair": (a_name, b_name),
                    "mediator": c_name,
                    "mediator_role": "faster",
                    "aspect_with_A": asp_ca["aspect_type"],
                    "aspect_with_B": asp_cb["aspect_type"],
                    "interpretation": (
                        f"{c_name} transfers light between {a_name} and {b_name}. "
                        "The matter may be completed through an intermediary."
                    ),
                }
            )

    return instances


def _detect_yamaya(planets: list[dict]) -> list[dict]:
    instances: list[dict] = []
    pmap = {p["name"]: p for p in planets if p["name"] in _CLASSICAL_PLANETS}
    names = list(pmap.keys())

    for a_name, b_name in combinations(names, 2):
        a = pmap[a_name]
        b = pmap[b_name]

        if _check_aspect(a_name, a["longitude"], b_name, b["longitude"]) is not None:
            continue

        for c_name in names:
            if c_name in (a_name, b_name):
                continue
            if not (_slower(c_name, a_name) and _slower(c_name, b_name)):
                continue

            c = pmap[c_name]
            asp_ca = _check_aspect(c_name, c["longitude"], a_name, a["longitude"])
            asp_cb = _check_aspect(c_name, c["longitude"], b_name, b["longitude"])
            if asp_ca is None or asp_cb is None:
                continue

            instances.append(
                {
                    "planet_pair": (a_name, b_name),
                    "mediator": c_name,
                    "mediator_role": "slower",
                    "aspect_with_A": asp_ca["aspect_type"],
                    "aspect_with_B": asp_cb["aspect_type"],
                    "interpretation": (
                        f"{c_name} transfers light between {a_name} and {b_name}. "
                        "The matter may be completed through an intermediary of slower agency."
                    ),
                }
            )

    return instances


def _detect_kamboola(ithasala_list: list[dict], planets: list[dict], avasthas: dict | None) -> list[dict]:
    if not ithasala_list:
        return []

    instances: list[dict] = []
    pmap = {p["name"]: p for p in planets if p["name"] in _CLASSICAL_PLANETS}
    if "Moon" not in pmap:
        return []

    ithasala_pairs: dict[frozenset[str], dict] = {}
    for inst in ithasala_list:
        if not inst.get("perfects_matter"):
            continue
        ithasala_pairs[frozenset({inst["faster_planet"], inst["slower_planet"]})] = inst

    for pair_key in ithasala_pairs:
        if "Moon" in pair_key:
            continue

        x_name, y_name = tuple(pair_key)
        moon_ithasala_with: str | None = None
        for target_name in (x_name, y_name):
            if frozenset({"Moon", target_name}) in ithasala_pairs:
                moon_ithasala_with = target_name
                break

        if moon_ithasala_with is None:
            continue

        grade = "adhama"
        grade_reason = "Moon's condition is not strong."
        if avasthas is not None:
            strong_set = {"deeptha", "swastha"}
            x_av = avasthas.get(x_name, {}).get("avastha", "")
            y_av = avasthas.get(y_name, {}).get("avastha", "")
            moon_av = avasthas.get("Moon", {}).get("avastha", "")

            if x_av in strong_set and y_av in strong_set and moon_av in strong_set:
                grade = "uttamottama"
                grade_reason = "Moon and both significators are strong."
            elif moon_av in {"muditha", "suveerya"}:
                grade = "madhyama"
                grade_reason = "Moon adds moderate strength to the perfection."
            else:
                grade_reason = "Moon reinforces the yoga, but not with full strength."

        instances.append(
            {
                "ithasala_pair": (x_name, y_name),
                "moon_ithasala_with": moon_ithasala_with,
                "grade": grade,
                "grade_reason": grade_reason,
                "interpretation": (
                    f"Moon reinforces the {x_name}-{y_name} perfection. "
                    f"Grade: {grade.upper()}."
                ),
            }
        )

    return instances


def detect_tajaka_yogas(planets: list[dict], avasthas: dict | None = None) -> dict:
    ithasala, easarapha = _detect_ithasala_easarapha(planets)
    naktha = _detect_naktha(planets)
    yamaya = _detect_yamaya(planets)
    kamboola = _detect_kamboola(ithasala, planets, avasthas)

    summary: list[str] = []
    for inst in ithasala:
        poorna = " (Poorna - near exact)" if inst["is_poorna"] else ""
        summary.append(
            f"ITHASALA{poorna}: {inst['faster_planet']} {inst['aspect_type']} "
            f"{inst['slower_planet']} - {inst['orb_remaining']:.2f} degrees to exact. "
            f"{inst['aspect_quality'].upper()}."
        )
    for inst in easarapha:
        summary.append(
            f"EASARAPHA: {inst['faster_planet']} {inst['aspect_type']} "
            f"{inst['slower_planet']} - {inst['current_diff']:.2f} degrees past exact."
        )
    for inst in naktha:
        a_name, b_name = inst["planet_pair"]
        summary.append(f"NAKTHA: {a_name}-{b_name} linked via {inst['mediator']}.")
    for inst in yamaya:
        a_name, b_name = inst["planet_pair"]
        summary.append(f"YAMAYA: {a_name}-{b_name} linked via {inst['mediator']}.")
    for inst in kamboola:
        a_name, b_name = inst["ithasala_pair"]
        summary.append(
            f"KAMBOOLA ({inst['grade'].upper()}): Moon reinforces {a_name}-{b_name}."
        )

    return {
        "ithasala": ithasala,
        "easarapha": easarapha,
        "naktha": naktha,
        "yamaya": yamaya,
        "kamboola": kamboola,
        "summary": summary,
    }
