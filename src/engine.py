import math
import time
from typing import Dict, Tuple
from skyfield.api import Topos, load, EarthSatellite
from .models import AstroRequest, PlanetaryPosition

class Constants:
    ZODIAC_SIGNS = [
        "Aries", "Taurus", "Gemini", "Cancer",
        "Leo", "Virgo", "Libra", "Scorpio",
        "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    NAKSHATRAS = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
        "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
        "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
        "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
        "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
        "Uttara Bhadrapada", "Revati"
    ]

class AstroEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AstroEngine, cls).__new__(cls)
            # Memory singleton for astronomical data
            cls._instance.ts = load.timescale()
            cls._instance.eph = load('de421.bsp')
            cls._instance.earth = cls._instance.eph['earth']
            cls._instance.sun = cls._instance.eph['sun']
            cls._instance.moon = cls._instance.eph['moon']
            cls._instance.mars = cls._instance.eph['mars']
            cls._instance.mercury = cls._instance.eph['mercury']
            cls._instance.jupiter = cls._instance.eph['jupiter barycenter']
            cls._instance.venus = cls._instance.eph['venus']
            cls._instance.saturn = cls._instance.eph['saturn barycenter']
            
            # Mapping definitions
            cls._instance.bodies = {
                "Sun": cls._instance.sun,
                "Moon": cls._instance.moon,
                "Mars": cls._instance.mars,
                "Mercury": cls._instance.mercury,
                "Jupiter": cls._instance.jupiter,
                "Venus": cls._instance.venus,
                "Saturn": cls._instance.saturn
            }
        return cls._instance

    @staticmethod
    def _calculate_ayanamsa(year: int, mode: str) -> float:
        """
        Calculates Sidereal correction (Ayanamsa) if required.
        Using standard Lahiri approximation ~ 24 degrees in 2000 drift.
        Since skyfield isn't native swisseph sidereal generator.
        """
        if mode == "TROPICAL":
            return 0.0
        
        # Approximate Lahiri calculation (Chitra Paksha Ayanamsa)
        # Exactly 23.85 degrees in year 2000, shifting by 50.290966 seconds per year
        if mode == "LAHIRI":
            years_diff = year - 2000
            drift = years_diff * (50.290966 / 3600.0)
            return 23.85 + drift
        
        # Raman Ayanamsa (~22.46 in 2000)
        if mode == "RAMAN":
            years_diff = year - 2000
            drift = years_diff * (50.259899 / 3600.0)
            return 22.46 + drift

        return 0.0

    @staticmethod
    def compute_zodiac_and_nakshatra(longitude: float) -> Tuple[str, float, str, int]:
        """
        Strict mathematical boundaries for precise mapping.
        """
        # Zodiac Sign (Each 30 degrees)
        sign_idx = int(longitude // 30)
        sign = Constants.ZODIAC_SIGNS[min(11, max(0, sign_idx))]
        
        # Exact Degree inside sign
        sign_degree = longitude % 30.0

        # Nakshatra Calculation (360/27 = 13.33333333...)
        # Multiplying by 27 prevents truncation artifacts
        nakshatra_fraction = (longitude * 27) / 360
        nakshatra_idx = int(nakshatra_fraction)
        nakshatra = Constants.NAKSHATRAS[min(26, max(0, nakshatra_idx))]

        # Pada is the exact quarter within the Nakshatra (each Nakshatra is 4 padas)
        fractional_part = nakshatra_fraction - nakshatra_idx
        pada = int(fractional_part * 4) + 1  # 1 to 4

        return sign, sign_degree, nakshatra, pada

    def process(self, request: AstroRequest) -> Dict[str, PlanetaryPosition]:
        # 1. Setup Temporal Constraints
        dt_input = request.datetime
        t = self.ts.utc(
            dt_input.year, 
            dt_input.month, 
            dt_input.day, 
            dt_input.hour, 
            dt_input.minute - int(dt_input.utc_offset * 60), 
            dt_input.second
        )

        # 2. Setup Topocentric Views (Considering Altitude & Atmospheric Refraction Defaults)
        loc = request.location
        observer = self.earth + Topos(
            latitude_degrees=loc.latitude, 
            longitude_degrees=loc.longitude, 
            elevation_m=loc.altitude
        )

        ayanamsa_correction = self._calculate_ayanamsa(dt_input.year, request.ayanamsa)

        results = {}
        for name, body in self.bodies.items():
            # Apparent position from topocentric observer, accounting for refraction mapping bounds
            # For strict sidereal boundaries, converting RA/Dec to Ecliptic
            astrometric = observer.at(t).observe(body).apparent()
            lat, lon, distance = astrometric.ecliptic_latlon()
            
            ecliptic_lon_deg = lon.degrees
            
            # Apply Sidereal shift if required
            adjusted_lon = (ecliptic_lon_deg - ayanamsa_correction) % 360.0
            if adjusted_lon < 0:
                adjusted_lon += 360.0

            sign, sign_deg, nakshatra, pada = self.compute_zodiac_and_nakshatra(adjusted_lon)

            results[name] = PlanetaryPosition(
                planet=name,
                longitude=adjusted_lon,
                sign=sign,
                sign_degree=sign_deg,
                nakshatra=nakshatra,
                nakshatra_pada=pada
            )

        # Mean Lunar Nodes (Rahu and Ketu) Calculation based on Julian Centuries since J2000
        # t.tt provides the Julian Date (Terrestrial Time)
        T = (t.tt - 2451545.0) / 36525.0
        # Mean longitude of the ascending node (Rahu)
        rahu_lon_deg = (125.04452 - 1934.136261 * T) % 360.0
        ketu_lon_deg = (rahu_lon_deg + 180.0) % 360.0

        for name, original_lon in [("Rahu", rahu_lon_deg), ("Ketu", ketu_lon_deg)]:
            adjusted_lon = (original_lon - ayanamsa_correction) % 360.0
            if adjusted_lon < 0:
                adjusted_lon += 360.0

            sign, sign_deg, nakshatra, pada = self.compute_zodiac_and_nakshatra(adjusted_lon)

            results[name] = PlanetaryPosition(
                planet=name,
                longitude=adjusted_lon,
                sign=sign,
                sign_degree=sign_deg,
                nakshatra=nakshatra,
                nakshatra_pada=pada
            )
        
        return results
