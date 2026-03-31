import json
import datetime
import sys
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

    res = process_astro_request(payload, query_house=7)

    # Convert Pydantic to dict if necessary for positions
    def p2d(p):
        return p if isinstance(p, dict) else p.__dict__

    pos_asc = p2d(res["positions"]["Ascendant"])
    pos_moon = p2d(res["positions"]["Moon"])
    pos_sun = p2d(res["positions"]["Sun"])

    out = {
        "positions": {
            "Ascendant": {
                "sign": pos_asc.get("sign"),
                "longitude": pos_asc.get("longitude")
            },
            "Moon": {
                "sign": pos_moon.get("sign"),
                "longitude": pos_moon.get("longitude")
            },
            "Sun": {
                "longitude": pos_sun.get("longitude")
            }
        },
        "house_judgment": {k: res["house_judgment"].get(k) for k in [
            "lagna_lord", "karyesh", "karyasiddhi_percent", "moon_supports_query", 
            "moon_phase", "query_time_reference", "query_time_meaning"
        ]},
        "timing_estimate": {k: res.get("timing_estimate", {}).get(k) for k in [
            "timing_note", "most_likely"
        ]}
    }
    
    with open("output_utf8.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
except Exception as e:
    print(f"Error: {e}")
