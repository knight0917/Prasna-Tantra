import json
import datetime
from src.main import process_astro_request
from timezonefinder import TimezoneFinder
import pytz

try:
    lat, lon = 28.6139, 77.2090
    now = datetime.datetime.now()
    
    tf = TimezoneFinder()
    tz_name = tf.timezone_at(lng=lon, lat=lat)
    if tz_name:
        local_tz = pytz.timezone(tz_name)
        naive_dt = datetime.datetime(now.year, now.month, now.day, 12, 0, 0)
        utc_offset = local_tz.localize(naive_dt).utcoffset().total_seconds() / 3600.0
    else:
        utc_offset = 0.0

    payload = {
        "datetime": {
            "year": now.year, "month": now.month, "day": now.day,
            "hour": 12, "minute": 0, "second": 0,
            "utc_offset": utc_offset
        },
        "location": {"latitude": lat, "longitude": lon, "altitude": 0.0},
        "ayanamsa": "LAHIRI"
    }

    results_out = {}
    house_names = {
        2: "Wealth (2)",
        7: "Marriage (7)",
        6: "Illness (6)",
        10: "Career (10)",
        3: "Siblings (3)",
        4: "Property (4)",
        5: "Children (5)",
        9: "Travel (9)"
    }
    
    for qh in [2, 7, 6, 10, 3, 4, 5, 9]:
        res = process_astro_request(payload, query_house=qh)
        hj = res.get("house_judgment", {})
        results_out[house_names[qh]] = {
            "specific_verdict": hj.get("specific_verdict"),
            "specific_factors": hj.get("specific_factors", [])
        }

    with open("houses_result.json", "w", encoding="utf-8") as f:
        json.dump(results_out, f, indent=2)

    print("SUCCESS")
except Exception as e:
    import traceback
    traceback.print_exc()
