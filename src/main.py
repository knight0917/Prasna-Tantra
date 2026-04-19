import time
import json
from .models import AstroRequest, AstroResponse
from .engine import AstroEngine
from .avasthas import classify_avasthas
from .tajaka_yogas import detect_tajaka_yogas
from .house_judgment import judge_house
from .sincerity_check import check_sincerity
from .timing import estimate_timing

# ---------------------------------------------------------------------------
# Vedic House Lord Lookup Tables (module-level constants, no runtime cost)
# ---------------------------------------------------------------------------
_ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

_SIGN_LORDS = {
    "Aries": "Mars",       "Taurus": "Venus",    "Gemini": "Mercury",
    "Cancer": "Moon",      "Leo": "Sun",          "Virgo": "Mercury",
    "Libra": "Venus",      "Scorpio": "Mars",     "Sagittarius": "Jupiter",
    "Capricorn": "Saturn", "Aquarius": "Saturn",  "Pisces": "Jupiter"
}

# Initialize the engine at startup to load the BSP file ONCE
# This secures the <100ms calculation constraint requirement
print("Initializing AstroTrack Engine cache...")
engine = AstroEngine()
print("Engine caching complete.")

def _compute_house_lords(asc_sign: str) -> dict:
    """
    Derives the ruling planet for each of the 12 whole-sign houses.
    House 1 = Ascendant sign; each subsequent house is the next sign clockwise.
    """
    asc_idx = _ZODIAC_SIGNS.index(asc_sign)
    return {
        str(i + 1): _SIGN_LORDS[_ZODIAC_SIGNS[(asc_idx + i) % 12]]
        for i in range(12)
    }


def calculate(city: str, date_str: str, time_str: str, query_house: int = 7) -> dict:
    """
    High-level entry point for query_engine.py.
    Geocodes `city`, resolves UTC offset, builds the request payload,
    and returns the full Prasna result for `query_house`.

    Parameters
    ----------
    city        : e.g. 'New Delhi', 'Mumbai'
    date_str    : 'YYYY-MM-DD'
    time_str    : 'HH:MM:SS'
    query_house : int 1–12 (default 7)

    Returns
    -------
    Full result dict from process_astro_request() for the given query_house.
    """
    import datetime
    try:
        from geopy.geocoders import Nominatim
        from timezonefinder import TimezoneFinder
        import pytz
    except ImportError as e:
        raise RuntimeError(f"Missing geocoding package: {e}. Run: pip install geopy timezonefinder pytz") from e

    # Geocode
    geolocator = Nominatim(user_agent="prasna-tantra-astrology/1.0")
    location_data = geolocator.geocode(city)
    if location_data is None:
        raise ValueError(f"Could not geocode city: '{city}'")
    lat, lon = location_data.latitude, location_data.longitude

    # Parse date/time
    year, month, day = map(int, date_str.split("-"))
    hour, minute, second = map(int, time_str.split(":"))

    # Resolve UTC offset (DST-aware)
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lng=lon, lat=lat)
    if tz_name:
        local_tz = pytz.timezone(tz_name)
        naive_dt = datetime.datetime(year, month, day, hour, minute, second)
        utc_offset = local_tz.localize(naive_dt).utcoffset().total_seconds() / 3600.0
    else:
        utc_offset = 0.0

    payload = {
        "datetime": {
            "year": year, "month": month, "day": day,
            "hour": hour, "minute": minute, "second": second,
            "utc_offset": utc_offset,
        },
        "location": {"latitude": lat, "longitude": lon, "altitude": 0.0},
        "ayanamsa": "LAHIRI",
    }

    return process_astro_request(payload, query_house=query_house)


def process_astro_request(req_dict: dict, query_house: int = 7) -> dict:
    start_time = time.perf_counter()

    # Validation boundary mapping
    request = AstroRequest(**req_dict)

    # Computation Layer isolating Geocoder latency from Physics
    positions = engine.process(request)

    # Derive whole-sign house lordships from the Ascendant sign
    house_lords = _compute_house_lords(positions["Ascendant"].sign)

    # Build flat planet list for the avastha classifier
    planets_for_avastha = [
        {
            "name":              name,
            "longitude":         p.longitude,
            "sign":              p.sign,
            "house":             p.house,
            "is_combust":        p.is_combust,
            "speed_deg_per_day": p.speed_deg_per_day or 0.0,
        }
        for name, p in positions.items()
        if name != "Ascendant"
    ]
    avasthas = classify_avasthas(planets_for_avastha)

    # Build planet list for Tajaka yoga detection (Ascendant excluded)
    planets_for_tajaka = [
        {
            "name":              name,
            "longitude":         p.longitude,
            "speed_deg_per_day": p.speed_deg_per_day or 0.0,
        }
        for name, p in positions.items()
        if name != "Ascendant"
    ]
    tajaka_yogas = detect_tajaka_yogas(planets_for_tajaka, avasthas)

    # House judgment for the requested query house
    house_judgment = judge_house(
        positions=positions,
        house_lords=house_lords,
        query_house=query_house,
        precomputed_yogas=tajaka_yogas,   # reuse — no second yoga pass
    )

    sincerity = check_sincerity(positions, house_lords)

    # Timing estimate — uses lagna lord and karyesh from the default H7 judgment
    _ll_name  = house_judgment["lagna_lord"]
    _kar_name = house_judgment["karyesh"]
    _ll_p     = positions.get(_ll_name)
    _kar_p    = positions.get(_kar_name)
    timing = None
    if _ll_p is not None and _kar_p is not None:
        _ll_lon  = _ll_p.longitude  if hasattr(_ll_p,  'longitude')  else _ll_p['longitude']
        _kar_lon = _kar_p.longitude if hasattr(_kar_p, 'longitude')  else _kar_p['longitude']
        _ll_nak  = _ll_p.nakshatra  if hasattr(_ll_p,  'nakshatra')  else _ll_p['nakshatra']
        _kar_nak = _kar_p.nakshatra if hasattr(_kar_p, 'nakshatra')  else _kar_p['nakshatra']
        _kar_sign = _kar_p.sign     if hasattr(_kar_p, 'sign')       else _kar_p['sign']
        _asc_sign = positions["Ascendant"].sign if hasattr(positions["Ascendant"], 'sign') else positions["Ascendant"]['sign']

        # Orb comes from house_judgment — authoritative single source of truth
        _orb = house_judgment.get("ithasala_orb_remaining", 0.0)

        try:
            timing = estimate_timing(
                lagna_sign=_asc_sign,
                lagna_lord_longitude=_ll_lon,
                karyesh_longitude=_kar_lon,
                lagna_lord_nakshatra=_ll_nak,
                karyesh_nakshatra=_kar_nak,
                ithasala_orb_remaining=_orb,
                karyesh_sign=_kar_sign,
                moon_phase=house_judgment.get("moon_phase"),
            )
        except (ValueError, KeyError) as e:
            timing = {"error": f"Could not compute timing: {e}"}


    latency = (time.perf_counter() - start_time) * 1000.0  # ms precision

    response = AstroResponse(
        request_params=request,
        positions=positions,
        house_lords=house_lords,
        avasthas=avasthas,
        tajaka_yogas=tajaka_yogas,
        house_judgment=house_judgment,
        sincerity_check=sincerity,
        timing_estimate=timing,
        latency_ms=latency
    )

    return json.loads(response.model_dump_json())

if __name__ == "__main__":
    import sys
    import datetime
    from .query_engine import run_prasna_query_from_coords, VALID_TOPICS

    # Check for --prasna flag
    IS_PRASNA = "--prasna" in sys.argv

    if not IS_PRASNA:
        # Existing astronomical engine CLI (standard output)
        try:
            from geopy.geocoders import Nominatim
            from timezonefinder import TimezoneFinder
            import pytz
        except ImportError:
            print("[ERROR] Missing packages! Run: pip install geopy timezonefinder pytz")
            sys.exit(1)

        print("\n--- AstroTrack Python Engine ---")
        city = input("Enter City name (e.g., 'New York', 'Delhi') [Default: New Delhi]: ").strip()
        if not city: city = "New Delhi"
        
        geolocator = Nominatim(user_agent="prasna-tantra-astrology/1.0")
        try:
            location_data = geolocator.geocode(city)
            lat, lon = (location_data.latitude, location_data.longitude) if location_data else (28.6139, 77.2090)
        except Exception:
            lat, lon = (28.6139, 77.2090)

        date_str = input("Enter Date (YYYY-MM-DD) [Default: Today]: ").strip()
        if not date_str:
            now = datetime.datetime.now()
            date_str = f"{now.year:04d}-{now.month:02d}-{now.day:02d}"
        
        time_str = input("Enter Local Time (HH:MM:SS) [Default: 12:00:00]: ").strip()
        if not time_str: time_str = "12:00:00"

        # Resolve Offset
        try:
            tf = TimezoneFinder()
            tz_name = tf.timezone_at(lng=lon, lat=lat)
            if tz_name:
                local_tz = pytz.timezone(tz_name)
                year, month, day = map(int, date_str.split("-"))
                hour, minute, second = map(int, time_str.split(":"))
                naive_dt = datetime.datetime(year, month, day, hour, minute, second)
                utc_offset = local_tz.localize(naive_dt).utcoffset().total_seconds() / 3600.0
            else:
                utc_offset = 0.0
        except Exception:
            utc_offset = 0.0

        user_payload = {
            "datetime": {
                "year": int(date_str[:4]), "month": int(date_str[5:7]), "day": int(date_str[8:10]),
                "hour": int(time_str[:2]), "minute": int(time_str[3:5]), "second": int(time_str[6:8]),
                "utc_offset": utc_offset
            },
            "location": {"latitude": lat, "longitude": lon, "altitude": 0.0},
            "ayanamsa": "LAHIRI"
        }
        print("\nCalculating Astro Results...")
        result = process_astro_request(user_payload)
        print(json.dumps(result, indent=2))
        sys.exit(0)

    # ── PRASNA MODE ──────────────────────────────────────────────────────────
    print("\n╔═════════════════════════════════════════╗")
    print("║      ASTROTRACK PRASNA TANTRA CLI       ║")
    print("╚═════════════════════════════════════════╝")

    # Step 1: Location
    loc_input = input("Enter City name or press 'C' to enter coordinates directly: ").strip()
    if loc_input.upper() == 'C':
        lat = float(input("Latitude  ([-90, 90]):  "))
        lon = float(input("Longitude ([-180, 180]): "))
    else:
        from geopy.geocoders import Nominatim
        if not loc_input: loc_input = "New Delhi"
        print(f"Resolving coordinates for {loc_input}...")
        try:
            loc = Nominatim(user_agent="prasna-tantra-astrology/1.0").geocode(loc_input)
            lat, lon = (loc.latitude, loc.longitude) if loc else (28.6139, 77.2090)
            print(f"Resolved: {lat:.4f}, {lon:.4f}")
        except Exception:
            print("Resolution failed. Defaulting to New Delhi.")
            lat, lon = 28.6139, 77.2090

    # Step 2: Date/Time
    d_input = input("Enter Date (YYYY-MM-DD) [Default: Today]: ").strip()
    if not d_input:
        now = datetime.datetime.now()
        d_input = f"{now.year:04d}-{now.month:02d}-{now.day:02d}"
    
    t_input = input("Enter Local Time (HH:MM:SS) [Default: 12:00:00]: ").strip()
    if not t_input: t_input = "12:00:00"

    # Step 3: Topic
    TOPICS_LIST = ['wealth','marriage','children','illness','career','property','siblings','longevity','father','travel','legal','loss']
    print("\nSelect your query topic:")
    print(" 1. Wealth & Finance       7. Siblings")
    print(" 2. Marriage & Relations   8. Longevity")
    print(" 3. Children               9. Father & Fortune")
    print(" 4. Illness & Health      10. Travel")
    print(" 5. Career & Profession   11. Legal Matters")
    print(" 6. Property & Home       12. Loss & Foreign")
    
    choice = int(input("\nChoice (1-12): "))
    query_topic = TOPICS_LIST[choice - 1]

    # Step 4: Run
    print("\nAnalyzing query...")
    res = run_prasna_query_from_coords(lat, lon, d_input, t_input, query_topic)

    if "error" in res:
        print(f"\n[ERROR] {res['error']}")
        sys.exit(1)

    # Pretty Print
    sinc = res["sincerity"]
    avas = res["avasthas"]
    yog  = res["yogas"]
    judg = res["house_judgment"]
    tim  = res["timing_estimate"]
    perf = res["performance"]

    print("\n╔══ PRASNA TANTRA READING ══╗")
    print(f"\nQUERY: {query_topic.upper()} (House {res['query_house']})")
    print(f"DATE:  {d_input} {t_input} | LOCATION: {lat:.4f}, {lon:.4f}")

    print("\n── SINCERITY CHECK ──────────────────")
    mark = '✓' if sinc.get('sincere') else '✗'
    print(f"{mark} {sinc.get('message')}")
    print(f"Matched rules: {sinc.get('matched_sincere_rules')} / Insincere: {sinc.get('matched_insincere_rules')}")

    print("\n── PLANET STATES (AVASTHAS) ─────────")
    print(f"{'Planet':<10} {'Avastha':<12} {'Strength':<10} {'Meaning'}")
    for p_name, data in avas.items():
        # Correct keys from avasthas.py: avastha, strength, result_meaning
        print(f"{p_name:<10} {data['avastha']:<12} {data['strength']:<10} {data['result_meaning']}")

    print("\n── TAJAKA YOGAS DETECTED ────────────")
    y_list = []
    
    # 1. Ithasala & Easarapha
    for category in ['ithasala', 'easarapha']:
        for inst in yog.get(category, []):
            deg = inst.get('exact_aspect_deg', '?')
            y_list.append(f"{category.capitalize()}: {inst['faster_planet']} + {inst['slower_planet']} ({deg}°)")
            
    # 2. Naktha & Yamaya (Mediators)
    for category in ['naktha', 'yamaya']:
        for inst in yog.get(category, []):
            pair = inst.get('planet_pair', ('?', '?'))
            med  = inst.get('mediator', '?')
            y_list.append(f"{category.capitalize()}: {pair[0]}/{pair[1]} via {med}")
            
    # 3. Kamboola
    for inst in yog.get('kamboola', []):
        pair = inst.get('ithasala_pair', ('?', '?'))
        y_list.append(f"Kamboola: {pair[0]}/{pair[1]} reinforced by Moon")

    if not y_list: print("None detected.")
    else: 
        for y in y_list: print(y)

    if judg:
        print("\n── HOUSE JUDGMENT ───────────────────")
        print(f"Query House : {judg['query_house']} ({judg.get('query_house_sign')})")
        print(f"Lagna Lord  : {judg.get('lagna_lord')} | Significator: {judg.get('karyesh')}")
        print(f"Success %   : {judg.get('karyasiddhi_percent')}%")
        print(f"House State : {judg.get('house_vitality')}")
        print(f"Ithasala    : {judg.get('ithasala_present')} | Easarapha: {judg.get('easarapha_present')}")
        print(f"Verdict     : {judg.get('interpretation')}")

    if tim:
        print("\n── TIMING ESTIMATE ──────────────────")
        print(f"Method 1 (Degrees)   : {tim['method_1']['value']} {tim['method_1']['unit']}")
        print(f"Method 2 (Nakshatra) : {tim['method_2']['value']} {tim['method_2']['unit']}")
        print(f"Method 3 (Signs)     : {tim['method_3']['value']} {tim['method_3']['unit']}")
        print(f"Most Likely          : {tim['most_likely']['value']} {tim['most_likely']['unit']}")
        print(f"Note: {tim.get('timing_note', '')}")

    print("\n── SUMMARY ──────────────────────────")
    print(res["summary"])

    print(f"\nComputation: {perf['total_ms']}ms")
    print("╚════════════════════════════════════╝\n")
