"""
src/house_judgment.py
---------------------
Prasna Tantra horary astrology — house-specific judgment engine.

Implements the six-step horary judgment procedure from Prasna Tantra stanzas 5–8:
  1. Identify key planets (Lagna lord + Karyesh/significator)
  2. Natural benefic/malefic classification
  3. Lagna strength analysis → karyasiddhi_percent
  4. Query house strength analysis
  5. Tajaka yoga check between Lagna lord and Karyesh
  6. Final horary judgment

Public API
----------
    judge_house(positions, house_lords, query_house) -> dict

`positions` — dict[str, PlanetaryPosition | dict] from AstroTrack engine.
`house_lords` — dict[str, str] mapping '1'–'12' → planet name.
`query_house` — int 1–12 representing the house of the querent's question.
"""

from __future__ import annotations
# Note: detect_tajaka_yogas is NOT imported here.
# Yoga results are computed once in main.py and passed in as precomputed_yogas.

# ---------------------------------------------------------------------------
# Static Classification Tables
# ---------------------------------------------------------------------------

_NATURAL_BENEFICS: frozenset[str] = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
_NATURAL_MALEFICS: frozenset[str] = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})

_ZODIAC_SIGNS: list[str] = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

_SIGN_LORDS: dict[str, str] = {
    "Aries": "Mars",       "Taurus": "Venus",    "Gemini": "Mercury",
    "Cancer": "Moon",      "Leo": "Sun",         "Virgo": "Mercury",
    "Libra": "Venus",      "Scorpio": "Mars",    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
}

# ---------------------------------------------------------------------------
# Dual-access helpers (supports both Pydantic objects and plain dicts)
# ---------------------------------------------------------------------------

def _get(obj, field: str, default=None):
    """Read a field from a Pydantic model or a plain dict."""
    if isinstance(obj, dict):
        return obj.get(field, default)
    return getattr(obj, field, default)


def _get_aspects(planet_data) -> list:
    """Return the aspects list from a planet (Pydantic or dict)."""
    raw = _get(planet_data, "aspects", [])
    return raw if raw is not None else []


def _aspect_target_house(aspect_entry) -> int:
    """Extract target_house from a VedicAspect Pydantic object or dict."""
    return int(_get(aspect_entry, "target_house", -1))


def _aspected_planets(aspect_entry) -> list[str]:
    """Extract aspected_planets list from a VedicAspect Pydantic object or dict."""
    raw = _get(aspect_entry, "aspected_planets", [])
    return raw if raw is not None else []

# ---------------------------------------------------------------------------
# Step 2 — Natural benefic/malefic resolution (with Mercury combust check)
# ---------------------------------------------------------------------------

def _resolve_benefics_and_malefics(positions: dict) -> tuple[set[str], set[str]]:
    """
    Return (effective_benefics, effective_malefics) from the planet set.

    Rules:
    - Jupiter, Venus: always natural benefics in this context.
    - Mercury: benefic only if NOT combust.
    - Moon: treated as benefic unconditionally (stub — waxing/waning phase TBD).
    - Sun, Mars, Saturn, Rahu, Ketu: always malefic.
    """
    present = set(positions.keys()) - {"Ascendant"}
    benefics: set[str] = set()
    malefics: set[str] = set()

    for name in present:
        p = positions[name]
        is_combust = _get(p, "is_combust", False)

        if name in ("Jupiter", "Venus", "Moon"):
            benefics.add(name)
        elif name == "Mercury":
            if not is_combust:
                benefics.add(name)
            else:
                malefics.add(name)  # Combust Mercury behaves as malefic
        elif name in _NATURAL_MALEFICS:
            malefics.add(name)

    return benefics, malefics

# ---------------------------------------------------------------------------
# Aspect-query helpers
# ---------------------------------------------------------------------------

def _planet_aspects_house(planet_data, target_house: int) -> bool:
    """True if this planet has any aspect entry targeting `target_house`."""
    for asp in _get_aspects(planet_data):
        if _aspect_target_house(asp) == target_house:
            return True
    return False


def _planet_aspects_planet(planet_data, target_planet: str) -> bool:
    """
    True if this planet's aspect list contains `target_planet` in
    `aspected_planets` for any aspect entry.
    """
    for asp in _get_aspects(planet_data):
        if target_planet in _aspected_planets(asp):
            return True
    return False

# ---------------------------------------------------------------------------
# Step 3 — Lagna strength analysis
# ---------------------------------------------------------------------------

def _analyze_lagna(
    positions: dict,
    lagna_lord: str,
    benefics: set[str],
    malefics: set[str],
) -> dict:
    """
    Returns lagna condition flags and karyasiddhi_percent.
    Based on Prasna Tantra stanzas 5–8.
    """
    ll_data = positions.get(lagna_lord)
    moon_data = positions.get("Moon")

    # Condition A: lagna_lord occupies lagna OR casts an aspect on house 1
    if ll_data is not None:
        ll_in_lagna = (_get(ll_data, "house", -1) == 1)
        ll_aspects_lagna = _planet_aspects_house(ll_data, 1)
        lagna_lord_aspects_lagna = ll_in_lagna or ll_aspects_lagna
    else:
        lagna_lord_aspects_lagna = False

    # Condition B: any benefic occupies house 1 OR casts an aspect on house 1
    benefic_in_lagna = any(
        _get(positions[b], "house", -1) == 1
        for b in benefics
        if b in positions
    )
    benefic_aspects_lagna = any(
        _planet_aspects_house(positions[b], 1)
        for b in benefics
        if b in positions
    ) or benefic_in_lagna

    # Condition C: count benefics occupying house 10
    benefics_in_10th = sum(
        1 for b in benefics
        if b in positions and _get(positions[b], "house", -1) == 10
    )

    # Condition D: Moon unafflicted — not combust AND no malefic aspects Moon
    if moon_data is not None:
        moon_combust = _get(moon_data, "is_combust", False)
        malefic_aspects_moon = any(
            _planet_aspects_planet(positions[m], "Moon")
            for m in malefics
            if m in positions
        )
        moon_unafflicted = (not moon_combust) and (not malefic_aspects_moon)
    else:
        moon_unafflicted = False

    # Sub-condition for 50% tier: any benefic aspects the lagna_lord directly
    benefic_aspects_lagna_lord = any(
        _planet_aspects_planet(positions[b], lagna_lord)
        for b in benefics
        if b in positions and lagna_lord in positions
    )

    # karyasiddhi_percent — exact logic from spec
    if lagna_lord_aspects_lagna and moon_unafflicted and benefic_aspects_lagna:
        karyasiddhi = 100
    elif (benefic_aspects_lagna
          or lagna_lord_aspects_lagna
          or benefics_in_10th >= 2):
        karyasiddhi = 75
    elif benefic_aspects_lagna_lord:
        karyasiddhi = 50
    else:
        karyasiddhi = 25

    return {
        "lagna_lord_aspects_lagna":   lagna_lord_aspects_lagna,
        "benefic_aspects_lagna":      benefic_aspects_lagna,
        "benefic_in_lagna":           benefic_in_lagna,
        "benefics_in_10th":           benefics_in_10th,
        "moon_unafflicted":           moon_unafflicted,
        "benefic_aspects_lagna_lord": benefic_aspects_lagna_lord,
        "karyasiddhi_percent":        karyasiddhi,
    }

# ---------------------------------------------------------------------------
# Step 4 — Query house strength
# ---------------------------------------------------------------------------

def _analyze_query_house(
    positions: dict,
    karyesh: str,
    query_house: int,
    benefics: set[str],
    malefics: set[str],
) -> dict:
    """
    Determines the vitality of the query house — 'strong', 'afflicted', 'mixed'.
    """
    karyesh_data = positions.get(karyesh)
    karyesh_in_own_house = (
        _get(karyesh_data, "house", -1) == query_house
        if karyesh_data is not None else False
    )

    benefic_aspects_query = any(
        _planet_aspects_house(positions[b], query_house)
        for b in benefics
        if b in positions
    )

    malefic_in_query = any(
        _get(positions[m], "house", -1) == query_house
        for m in malefics
        if m in positions
    )
    malefic_aspects_query = any(
        _planet_aspects_house(positions[m], query_house)
        for m in malefics
        if m in positions
    )
    malefic_afflicts_query_house = malefic_in_query or malefic_aspects_query

    has_positive = karyesh_in_own_house or benefic_aspects_query
    has_negative = malefic_afflicts_query_house

    if has_positive and not has_negative:
        house_vitality = "strong"
    elif has_negative and not has_positive:
        house_vitality = "afflicted"
    else:
        house_vitality = "mixed"

    return {
        "karyesh_in_own_house":       karyesh_in_own_house,
        "benefic_aspects_query_house": benefic_aspects_query,
        "malefic_afflicts_query_house": malefic_afflicts_query_house,
        "house_vitality":             house_vitality,
    }

# ---------------------------------------------------------------------------
# Step 5 — Tajaka yoga between Lagna lord and Karyesh
# ---------------------------------------------------------------------------

def _analyze_tajaka(
    lagna_lord: str,
    karyesh: str,
    same_lord: bool,
    precomputed_yogas: dict,
) -> dict:
    """
    Looks up Ithasala, Easarapha, and Kamboola from the already-computed
    tajaka_yogas dict (produced once in main.py). No recalculation.
    """
    if same_lord:
        return {
            "ithasala_present":      True,
            "ithasala_orb_remaining": 0.0,   # same planet — no gap
            "ithasala_aspect_type":  "Same lord",
            "ithasala_quality":      "supportive",
            "hostile_applying_present": False,
            "easarapha_present":     False,
            "kamboola_present":      False,
        }

    pair = frozenset({lagna_lord, karyesh})

    ithasala_inst = next(
        (
            i for i in precomputed_yogas.get("ithasala", [])
            if (
                frozenset({i["faster_planet"], i["slower_planet"]}) == pair
                and i.get("perfects_matter", True)
            )
        ),
        None,
    )
    hostile_applying_inst = next(
        (
            i for i in precomputed_yogas.get("ithasala", [])
            if (
                frozenset({i["faster_planet"], i["slower_planet"]}) == pair
                and not i.get("perfects_matter", True)
            )
        ),
        None,
    )
    easarapha_present = any(
        frozenset({i["faster_planet"], i["slower_planet"]}) == pair
        for i in precomputed_yogas.get("easarapha", [])
    )
    kamboola_present = any(
        set(inst["ithasala_pair"]) == {lagna_lord, karyesh}
        for inst in precomputed_yogas.get("kamboola", [])
    )

    return {
        "ithasala_present":      ithasala_inst is not None,
        "ithasala_orb_remaining": ithasala_inst["orb_remaining"] if ithasala_inst else 0.0,
        "ithasala_aspect_type":  ithasala_inst["aspect_type"] if ithasala_inst else None,
        "ithasala_quality":      ithasala_inst["aspect_quality"] if ithasala_inst else None,
        "hostile_applying_present": hostile_applying_inst is not None,
        "easarapha_present":     easarapha_present,
        "kamboola_present":      kamboola_present,
    }

# ---------------------------------------------------------------------------
# Step 6 — Final judgment string
# ---------------------------------------------------------------------------

def _build_judgment(
    ithasala_present: bool,
    ithasala_quality: str | None,
    hostile_applying_present: bool,
    easarapha_present: bool,
    kamboola_present: bool,
    karyasiddhi: int,
) -> str:
    """
    Compose the horary verdict from Prasna Tantra principles.
    """
    if hostile_applying_present and not ithasala_present:
        text = "NO - The significators apply by hostile aspect, so obstruction prevails."
    elif ithasala_present and ithasala_quality == "obstructed":
        text = "YES, WITH EFFORT - The matter tends to perfection, but not without obstruction."
    elif ithasala_present and karyasiddhi >= 75:
        text = "YES - The query is strongly supported and can be fulfilled."
    elif ithasala_present and karyasiddhi >= 50:
        text = "YES, WITH EFFORT - Fulfilment is possible, but not without obstacles."
    elif easarapha_present and not ithasala_present:
        text = "NO - A separating pattern is present, so the matter appears to be moving away."
    elif karyasiddhi <= 25:
        text = "NO - Conditions are not favourable for this query."
    else:
        text = "UNCLEAR - No applying aspect perfects the matter at present."

    if kamboola_present:
        text += " Kamboola further strengthens the promise."

    return text

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def judge_house(
    positions: dict,
    house_lords: dict,
    query_house: int,
    precomputed_yogas: dict,
) -> dict:
    """
    Perform a six-step Prasna Tantra horary judgment for the given query house.

    Parameters
    ----------
    positions          : dict[str, PlanetaryPosition | dict]
    house_lords        : dict[str, str]  mapping '1'–'12' → planet name
    query_house        : int  (1–12)
    precomputed_yogas  : dict  already-computed result from detect_tajaka_yogas()
                         — passed in from main.py to avoid duplicate computation.
    """
    # ── Step 1: Key planets ───────────────────────────────────────────────
    lagna_lord = house_lords["1"]
    karyesh    = house_lords[str(query_house)]
    same_lord  = (lagna_lord == karyesh)

    # Derive query house sign using whole-sign system from Ascendant
    asc_data   = positions.get("Ascendant")
    asc_sign   = _get(asc_data, "sign", "Aries") if asc_data else "Aries"
    asc_idx    = _ZODIAC_SIGNS.index(asc_sign) if asc_sign in _ZODIAC_SIGNS else 0
    query_house_sign = _ZODIAC_SIGNS[(asc_idx + query_house - 1) % 12]

    SIRSHODAYA = {'Gemini', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Aquarius'}
    PRUSHTODAYA = {'Aries', 'Taurus', 'Cancer', 'Sagittarius', 'Capricorn', 'Pisces'}
    
    lagna_sign = asc_sign
    if lagna_sign in SIRSHODAYA:
        lagna_rise_type = 'sirshodaya'
        lagna_rise_meaning = 'Rising sign is Sirshodaya — adds strength to Lagna'
        sirshodaya_bonus = True
    else:
        lagna_rise_type = 'prushtodaya'
        lagna_rise_meaning = 'Rising sign is Prushtodaya — Lagna strength is not enhanced by sign type'
        sirshodaya_bonus = False

    # ── Step 2: Benefic / malefic sets ───────────────────────────────────
    benefics, malefics = _resolve_benefics_and_malefics(positions)

    # ── Step 3: Lagna strength → karyasiddhi_percent ─────────────────────
    lagna_result = _analyze_lagna(positions, lagna_lord, benefics, malefics)
    karyasiddhi_percent = lagna_result["karyasiddhi_percent"]
    

    # ── Step 4: Query house vitality ──────────────────────────────────────
    query_result = _analyze_query_house(
        positions, karyesh, query_house, benefics, malefics
    )

    # ── Step 5: Tajaka yoga (from precomputed results — no re-calculation) ─
    tajaka_result = _analyze_tajaka(lagna_lord, karyesh, same_lord, precomputed_yogas)

    # ── NEW CHECK 1: Moon as co-Lagna ─────────────────────────────────────
    moon_data = positions.get("Moon")
    moon_supports_query = False
    if moon_data is not None:
        moon_sign = _get(moon_data, "sign", "Aries")
        moon_sign_lord = _SIGN_LORDS.get(moon_sign, "Mars")
        if moon_sign_lord == karyesh:
            moon_supports_query = True
        else:
            # check Ithasala between moon_sign_lord and karyesh
            pair = frozenset({moon_sign_lord, karyesh})
            moon_supports_query = any(
                frozenset({i["faster_planet"], i["slower_planet"]}) == pair
                for i in precomputed_yogas.get("ithasala", [])
            )
            
    moon_supports_meaning = "Moon sign lord strongly supports the query house — additional strength." if moon_supports_query else ""

    # ── NEW CHECK 2: Waxing/Waning Moon ───────────────────────────────────
    sun_data = positions.get("Sun")
    moon_phase = "unknown"
    if moon_data is not None and sun_data is not None:
        moon_lon = _get(moon_data, "longitude", 0.0)
        sun_lon = _get(sun_data, "longitude", 0.0)
        diff = (moon_lon - sun_lon) % 360
        moon_phase = "waxing" if diff < 180 else "waning"

    # ── NEW CHECK 3: Past/Present/Future ──────────────────────────────────
    query_time_reference = "unknown"
    query_time_meaning = "No clear time reference found from Lagna lord and Karyesh connections."
    
    ll_p = positions.get(lagna_lord)
    k_p = positions.get(karyesh)
    if ll_p is not None and k_p is not None and not same_lord:
        lon1 = _get(ll_p, "longitude", 0.0)
        lon2 = _get(k_p, "longitude", 0.0)
        diff = abs(lon1 - lon2) % 360
        dist = min(diff, 360.0 - diff)
        
        if dist <= 1.0:
            query_time_reference = "present"
            query_time_meaning = "Karyesh is in exact conjunction with Lagna lord — query relates to the PRESENT."
        elif tajaka_result["easarapha_present"]:
            query_time_reference = "past"
            query_time_meaning = "Karyesh is in Easarapha with Lagna lord — query relates to PAST events."
        elif tajaka_result["ithasala_present"]:
            query_time_reference = "future"
            query_time_meaning = "Karyesh is in Ithasala with Lagna lord — query relates to FUTURE events."
    elif same_lord:
        query_time_reference = "present"
        query_time_meaning = "Lagna lord and Karyesh are the same — focus is on PRESENT."

    # ── NEW CHECK 4: Judgment Notes (Fixes 1-5) ───────────────────────────
    judgment_notes = []
    
    # Fix 1: Benefic in Lagna note
    if lagna_result.get("benefic_in_lagna"):
        judgment_notes.append("Benefic planet occupies Ascendant — strong positive per book Stanza 2.")

    # Fix 2: Significator aspects Lagna
    k_data = positions.get(karyesh)
    karyesh_in_1 = _get(k_data, "house", -1) == 1 if k_data is not None else False
    karyesh_aspects_1 = _planet_aspects_house(k_data, 1) if k_data is not None else False
    karyesh_aspects_lagna = karyesh_in_1 or karyesh_aspects_1
    
    if karyesh_aspects_lagna:
        judgment_notes.append("Significator aspects Lagna — query will be fulfilled per Stanza 15.")
    elif not tajaka_result["ithasala_present"]:
        judgment_notes.append("Warning: Significator does not aspect Lagna or its lord — fulfilment is doubtful per Stanza 15.")
        
    # Fix 3: Lagna lord in dusthana warning
    ll_data = positions.get(lagna_lord)
    lagna_lord_house = _get(ll_data, "house", -1) if ll_data is not None else -1
    lagna_lord_dusthana_warning = ""
    if lagna_lord_house == 6:
        lagna_lord_dusthana_warning = "Lagna lord in 6th — querent faces self-created obstacles."
        judgment_notes.append(lagna_lord_dusthana_warning)
    elif lagna_lord_house == 8:
        lagna_lord_dusthana_warning = "Lagna lord in 8th — serious danger indicated."
        judgment_notes.append(lagna_lord_dusthana_warning)
    elif lagna_lord_house == 12:
        lagna_lord_dusthana_warning = "Lagna lord in 12th — losses and expenses likely."
        judgment_notes.append(lagna_lord_dusthana_warning)
        
    def _in_ithasala_or_conj(p1: str, p2: str) -> bool:
        if not p1 or not p2: return False
        if p1 == p2: return False
        p1_h = _get(positions.get(p1), "house", -1)
        p2_h = _get(positions.get(p2), "house", -2)
        if p1_h != -1 and p1_h == p2_h:
            return True
        pair = frozenset({p1, p2})
        return any(
            frozenset({i["faster_planet"], i["slower_planet"]}) == pair
            for i in precomputed_yogas.get("ithasala", [])
        )

    # Fix 4: 6th/8th lord affliction for query house
    lord6 = house_lords.get("6")
    lord8 = house_lords.get("8")
    query_house_afflicted_by_dusthana = False
    if _in_ithasala_or_conj(karyesh, lord6) or _in_ithasala_or_conj(karyesh, lord8):
        query_house_afflicted_by_dusthana = True
        judgment_notes.append("Warning: Query house lord connected to 6th/8th lord — house is afflicted per Stanza 16.")
        
    # Fix 5: Lagna lord + 11th lord benefic yoga
    lord11 = house_lords.get("11")
    if _in_ithasala_or_conj(lagna_lord, lord11):
        txt = "Lagna lord and 11th lord in applying aspect — benefic combination per Chapter 4 Stanza 4. Gain and prosperity indicated."
        moon_aspects = False
        if moon_data is not None:
            if _planet_aspects_planet(moon_data, lagna_lord) or _planet_aspects_planet(moon_data, lord11):
                moon_aspects = True
        if moon_aspects:
            txt += " Moon intensifies this combination — results come sooner."
        judgment_notes.append(txt)

    # ── Step 6: Final judgment ────────────────────────────────────────────
    interpretation = _build_judgment(
        ithasala_present=tajaka_result["ithasala_present"],
        ithasala_quality=tajaka_result["ithasala_quality"],
        hostile_applying_present=tajaka_result["hostile_applying_present"],
        easarapha_present=tajaka_result["easarapha_present"],
        kamboola_present=tajaka_result["kamboola_present"],
        karyasiddhi=karyasiddhi_percent,
    )
    
    if judgment_notes:
        interpretation += " " + " ".join(judgment_notes)

    out_dict = {
        # Context
        "query_house":                  query_house,
        "query_house_sign":             query_house_sign,
        "lagna_lord":                   lagna_lord,
        "karyesh":                      karyesh,
        "lagna_lord_is_karyesh":        same_lord,
        "lagna_sign":                   lagna_sign,
        "lagna_rise_type":              lagna_rise_type,
        "lagna_rise_meaning":           lagna_rise_meaning,
        "sirshodaya_bonus":             sirshodaya_bonus,
        
        # New Checks Outputs
        "moon_supports_query":          moon_supports_query,
        "moon_supports_meaning":        moon_supports_meaning,
        "moon_phase":             moon_phase,
        "query_time_reference":   query_time_reference,
        "query_time_meaning":     query_time_meaning,
        
        # Features from Fixes
        "karyesh_aspects_lagna":        karyesh_aspects_lagna,
        "lagna_lord_house":             lagna_lord_house,
        "lagna_lord_dusthana_warning":  lagna_lord_dusthana_warning,
        "query_house_afflicted_by_dusthana": query_house_afflicted_by_dusthana,

        # Step 3 — Lagna strength
        "karyasiddhi_percent":          karyasiddhi_percent,
        "lagna_lord_aspects_lagna":     lagna_result["lagna_lord_aspects_lagna"],
        "benefic_aspects_lagna":        lagna_result["benefic_aspects_lagna"],
        "moon_unafflicted":             lagna_result["moon_unafflicted"],
        "benefic_in_lagna":             lagna_result["benefic_in_lagna"],
        "benefic_aspects_lagna_lord":   lagna_result["benefic_aspects_lagna_lord"],
        "benefics_in_10th":             lagna_result["benefics_in_10th"],

        # Step 4 — Query house
        "house_vitality":               query_result["house_vitality"],
        "karyesh_in_own_house":         query_result["karyesh_in_own_house"],
        "benefic_aspects_query_house":  query_result["benefic_aspects_query_house"],
        "malefic_afflicts_query_house": query_result["malefic_afflicts_query_house"],

        # Step 5 — Tajaka
        "ithasala_present":             tajaka_result["ithasala_present"],
        "ithasala_orb_remaining":       tajaka_result["ithasala_orb_remaining"],
        "ithasala_aspect_type":         tajaka_result["ithasala_aspect_type"],
        "ithasala_quality":             tajaka_result["ithasala_quality"],
        "hostile_applying_present":     tajaka_result["hostile_applying_present"],
        "easarapha_present":            tajaka_result["easarapha_present"],
        "kamboola_present":             tajaka_result["kamboola_present"],

        # Step 6 — Verdict
        "interpretation":               interpretation,
    }

    # ── Step 7: Apply House-Specific Prasna Tantra Rules ─────────────────
    from .house_rules import apply_house_rules
    house_specifics = apply_house_rules(query_house, positions, house_lords, precomputed_yogas, out_dict)
    out_dict["specific_verdict"] = house_specifics["specific_verdict"]
    out_dict["specific_factors"] = house_specifics["specific_factors"]
    out_dict["source_rules"] = house_specifics.get("source_rules", [])

    return out_dict
