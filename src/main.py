import time
import json
from .models import AstroRequest, AstroResponse
from .engine import AstroEngine
from decimal import Decimal

# Initialize the engine at startup to load the BSP file ONCE
# This secures the <100ms calculation constraint requirement
print("Initializing AstroTrack Engine cache...")
engine = AstroEngine()
print("Engine caching complete.")

def process_astro_request(req_dict: dict) -> dict:
    start_time = time.perf_counter()
    
    # Validation boundary mapping
    request = AstroRequest(**req_dict)
    
    # Computation Layer isolating Geocoder latency from Physics
    positions = engine.process(request)
    
    latency = (time.perf_counter() - start_time) * 1000.0  # ms precision
    
    response = AstroResponse(
        request_params=request,
        positions=positions,
        latency_ms=latency
    )
    
    return json.loads(response.model_dump_json())

if __name__ == "__main__":
    import datetime
    try:
        from geopy.geocoders import Nominatim
        from timezonefinder import TimezoneFinder
        import pytz
    except ImportError:
        print("[ERROR] Missing packages! Please run: pip install geopy timezonefinder pytz")
        exit(1)

    print("\n--- AstroTrack Python Engine ---")
    
    # 1. Location Input
    city = input("Enter City name (e.g., 'New York', 'Delhi') [Default: New Delhi]: ").strip()
    if not city:
        city = "New Delhi"
        
    print(f"Resolving coordinates for {city}...")
    geolocator = Nominatim(user_agent="astrotrack_local_app")
    try:
        location_data = geolocator.geocode(city)
        if location_data is None:
            print("Could not resolve city! Defaulting to New Delhi coordinates.")
            lat, lon = 28.6139, 77.2090
        else:
            lat, lon = location_data.latitude, location_data.longitude
            print(f"Resolved {city} -> Lat: {lat:.4f}, Lon: {lon:.4f}")
    except Exception as e:
        print(f"Network error resolving city: {e}. Defaulting to New Delhi.")
        lat, lon = 28.6139, 77.2090

    # 2. Date Input
    date_str = input("Enter Date (YYYY-MM-DD) [Default: Today]: ").strip()
    if not date_str:
        now = datetime.datetime.now()
        year, month, day = now.year, now.month, now.day
    else:
        year, month, day = map(int, date_str.split("-"))

    # 3. Time Input
    time_str = input("Enter Local Time (HH:MM:SS) [Default: 12:00:00]: ").strip()
    if not time_str:
        hour, minute, second = 12, 0, 0
    else:
        hour, minute, second = map(int, time_str.split(":"))

    # 4. Auto-Calculate UTC Offset based on Lat/Long
    tf = TimezoneFinder()
    timezone_name = tf.timezone_at(lng=lon, lat=lat)
    
    if timezone_name:
        local_tz = pytz.timezone(timezone_name)
        naive_dt = datetime.datetime(year, month, day, hour, minute, second)
        # Find offset adjusting for Daylight Saving Time correctly
        localized_dt = local_tz.localize(naive_dt)
        utc_offset = localized_dt.utcoffset().total_seconds() / 3600.0
        print(f"Auto-Calculated Timezone: {timezone_name} (UTC Offset: {utc_offset} hours)")
    else:
        print("Could not auto-determine timezone. Defaulting to UTC +0.0")
        utc_offset = 0.0

    user_payload = {
        "datetime": {
            "year": year,
            "month": month,
            "day": day,
            "hour": hour,
            "minute": minute,
            "second": second,
            "utc_offset": utc_offset
        },
        "location": {
            "latitude": lat,
            "longitude": lon,
            "altitude": 0.0
        },
        "ayanamsa": "LAHIRI"
    }
    
    print("\nCalculating Astronomical Engine Constraints...")
    result = process_astro_request(user_payload)
    print(json.dumps(result, indent=2))
    print(f"\nAll validations passed! Computation Time: {result['latency_ms']:.2f}ms")
