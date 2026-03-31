"""
src/query_engine.py
-------------------
Prasna Tantra horary astrology — single orchestration entry point.

Exposes public functions:
    run_prasna_query(city, date_str, time_str, query_topic) -> dict
    run_prasna_query_from_coords(lat, lon, date_str, time_str, query_topic) -> dict

Supported query topics:
    wealth, marriage, children, illness, career, property,
    siblings, longevity, father, travel, legal, loss

All modules are called directly (no subprocess). The AstroTrack engine
singleton is shared via src/main.py — already loaded at import time.
"""

from __future__ import annotations
import time as _time

# ---------------------------------------------------------------------------
# Topic → House mapping (Prasna Tantra standard)
# ---------------------------------------------------------------------------

_TOPIC_TO_HOUSE: dict[str, int] = {
    "wealth":   2,
    "marriage": 7,
    "children": 5,
    "illness":  6,
    "career":   10,
    "property": 4,
    "siblings": 3,
    "longevity": 8,
    "father":   9,
    "travel":   9,
    "legal":    7,
    "loss":     12,
}

VALID_TOPICS = frozenset(_TOPIC_TO_HOUSE.keys())

# ---------------------------------------------------------------------------
# Core Orchestrator
# ---------------------------------------------------------------------------

def _run_prasna_core(
    engine_result: dict,
    query_topic: str,
    query_house: int,
    engine_ms: float,
    t_total_start: float,
    errors: list,
) -> dict:
    """Shared post-engine orchestration used by both public entry points."""
    avasthas        = engine_result.get("avasthas", {})
    yogas           = engine_result.get("tajaka_yogas", {})
    house_judgment  = engine_result.get("house_judgment", {})
    sincerity       = engine_result.get("sincerity_check", {})
    timing_estimate = engine_result.get("timing_estimate", {})

    # Sincerity is now handled exclusively at the UI layer.

    # Build summary
    summary_parts: list[str] = []
    if sincerity:
        summary_parts.append(sincerity.get("recommendation", ""))
    if house_judgment:
        summary_parts.append(house_judgment.get("interpretation", ""))
    
    # Timing: only meaningful when Ithasala is present between lagna lord and karyesh
    ithasala_ok = bool(house_judgment and house_judgment.get("ithasala_present"))
    if not ithasala_ok:
        summary_parts.append("Timing unavailable: no applying aspect between significators.")
    elif timing_estimate and "most_likely" in timing_estimate:
        ml = timing_estimate["most_likely"]
        summary_parts.append(f"Estimated timing: {ml['value']} {ml['unit']}.")

    return {
        "query_topic":    query_topic,
        "query_house":    query_house,
        "summary":        " ".join(p for p in summary_parts if p),
        "sincerity":      sincerity,
        "avasthas":       avasthas,
        "yogas":          yogas,
        "positions":      engine_result.get("positions", {}),
        "house_judgment": house_judgment,
        "timing_estimate": timing_estimate,
        "performance": {
            "engine_ms": round(engine_ms, 2),
            "total_ms":  round((_time.perf_counter() - t_total_start) * 1000.0, 2),
        },
        "errors": errors,
    }

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_prasna_query(
    city:        str,
    date_str:    str,
    time_str:    str,
    query_topic: str,
) -> dict:
    """Run Prasna reading by city name (geocoded)."""
    query_topic = query_topic.lower().strip()
    if query_topic not in VALID_TOPICS:
        return {"error": f"Unknown query_topic '{query_topic}'. Valid: {sorted(VALID_TOPICS)}"}

    query_house = _TOPIC_TO_HOUSE[query_topic]
    errors: list[str] = []
    t_total_start = _time.perf_counter()

    t_engine_start = _time.perf_counter()
    try:
        from .main import calculate
        engine_result = calculate(city, date_str, time_str, query_house=query_house)
    except Exception as exc:
        errors.append(f"engine: {exc}")
        engine_result = {}
    engine_ms = (_time.perf_counter() - t_engine_start) * 1000.0

    return _run_prasna_core(engine_result, query_topic, query_house, engine_ms, t_total_start, errors)


def run_prasna_query_from_coords(
    lat:         float,
    lon:         float,
    date_str:    str,
    time_str:    str,
    query_topic: str,
    utc_offset:  float | None = None,
) -> dict:
    """
    Run Prasna reading using raw coordinates — no geocoding latency.

    Parameters
    ----------
    lat, lon     : Decimal degrees (WGS84)
    date_str     : 'YYYY-MM-DD'
    time_str     : 'HH:MM:SS' (local time)
    query_topic  : One of VALID_TOPICS
    utc_offset   : Hours east of UTC. If None, auto-resolved via timezonefinder.
    """
    import datetime
    query_topic = query_topic.lower().strip()
    if query_topic not in VALID_TOPICS:
        return {"error": f"Unknown query_topic '{query_topic}'. Valid: {sorted(VALID_TOPICS)}"}

    query_house = _TOPIC_TO_HOUSE[query_topic]
    errors: list[str] = []
    t_total_start = _time.perf_counter()

    # Resolve UTC offset if not provided
    if utc_offset is None:
        try:
            from timezonefinder import TimezoneFinder
            import pytz
            year, month, day = map(int, date_str.split("-"))
            hour, minute, second = map(int, time_str.split(":"))
            tz_name = TimezoneFinder().timezone_at(lng=lon, lat=lat)
            if tz_name:
                local_tz = pytz.timezone(tz_name)
                naive_dt = datetime.datetime(year, month, day, hour, minute, second)
                utc_offset = local_tz.localize(naive_dt).utcoffset().total_seconds() / 3600.0
            else:
                utc_offset = 0.0
        except Exception as exc:
            errors.append(f"timezone error: {exc}")
            utc_offset = 0.0
    
    payload = {
        "datetime": {
            "year": int(date_str[:4]),
            "month": int(date_str[5:7]),
            "day": int(date_str[8:10]),
            "hour": int(time_str[:2]),
            "minute": int(time_str[3:5]),
            "second": int(time_str[6:8]),
            "utc_offset": utc_offset,
        },
        "location": {"latitude": lat, "longitude": lon, "altitude": 0.0},
        "ayanamsa": "LAHIRI",
    }

    t_engine_start = _time.perf_counter()
    try:
        from .main import process_astro_request
        engine_result = process_astro_request(payload, query_house=query_house)
    except Exception as exc:
        errors.append(f"engine: {exc}")
        engine_result = {}
    engine_ms = (_time.perf_counter() - t_engine_start) * 1000.0

    return _run_prasna_core(engine_result, query_topic, query_house, engine_ms, t_total_start, errors)
