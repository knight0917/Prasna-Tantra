# AstroTrack Python

A high-performance computational engine to generate planetary degrees, Zodiac signs, and Nakshatras using precise ephemeris data (NASA JPL DE421 via `skyfield`).

## Requirements

- Python 3.10+
- 20MB free RAM (for Ephemeris caching)

## 1. Setup Environment

First, create a virtual environment and install the required calculation bounds:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Running The Engine Benchmark

We have provisioned a direct internal benchmark that asserts the mathematical constraints and the $< 100ms$ validation limits requested in the PRD.

Run the module explicitly from the root folder:

```powershell
python -m src.main
```

### Expected Output

The system will initialize the `de421.bsp` (a 17MB astronomical database downloaded dynamically on your very first run) explicitly into RAM, and then spit out the precise planetary dictionary including the 9 celestial bodies + the exact execution time.

## 3. Integrating with Other Frontends

The core class `AstroEngine` expects a pure dictionary injected into the `process_astro_request` wrapper. You can wrap `process_astro_request()` directly into a `FastAPI` route like so:

```python
from src.main import process_astro_request

payload = {
    "datetime": {
        "year": 2026,
        "month": 2,
        "day": 22,
        "hour": 10,
        "minute": 0,
        "second": 0,
        "utc_offset": 5.5
    },
    "location": {
        "latitude": 28.6139,
        "longitude": 77.2090,
        "altitude": 200.0
    },
    "ayanamsa": "LAHIRI" # Or "TROPICAL", "RAMAN"
}

# The dictionary response is instantly JSON serializable!
dict_json = process_astro_request(payload)
```
