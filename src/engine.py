import math
import time
from typing import Dict, Tuple
from skyfield.api import Topos, load, EarthSatellite
from .models import AstroRequest, PlanetaryPosition, VedicAspect

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
    ASPECT_RULES = {
        "Mars": [4, 7, 8],
        "Jupiter": [5, 7, 9],
        "Saturn": [3, 7, 10],
        "Rahu": [5, 7, 9],
        "Ketu": [5, 7, 9]
    }

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

    @staticmethod
    def get_house(target_sign: str, asc_sign: str) -> int:
        """Calculates relative whole-sign house from Ascendant"""
        asc_idx = Constants.ZODIAC_SIGNS.index(asc_sign)
        target_idx = Constants.ZODIAC_SIGNS.index(target_sign)
        
        house_num = (target_idx - asc_idx) % 12 + 1
        return house_num

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
        
        # Build a 2-point time vector so Skyfield can batch-interpolate both
        # positions (T and T+1 day) in a single numpy pass — avoids 3 separate
        # round-trips per planet that caused the ~163ms regression.
        t_vec = self.ts.tt_jd([t.tt, t.tt + 1.0])

        # 2. Setup Topocentric Views (Considering Altitude & Atmospheric Refraction Defaults)
        loc = request.location
        observer = self.earth + Topos(
            latitude_degrees=loc.latitude, 
            longitude_degrees=loc.longitude, 
            elevation_m=loc.altitude
        )

        ayanamsa_correction = self._calculate_ayanamsa(dt_input.year, request.ayanamsa)

        results = {}

        # 3. Calculate Ascendant (Lagna) - Horizon intersection with Ecliptic
        gast = t.gast
        lst_rad = math.radians((gast + loc.longitude / 15.0) * 15.0)
        T_cent = (t.tt - 2451545.0) / 36525.0
        # Exact Obliquity of Ecliptic
        eps_deg = 23.43929111 - (46.8150 * T_cent - 0.00059 * T_cent**2 + 0.001813 * T_cent**3) / 3600.0
        eps_rad = math.radians(eps_deg)
        lat_rad = math.radians(loc.latitude)
        
        # Spherical offset formula for Ecliptic Longitude of the Eastern Horizon
        asc_y = math.cos(lst_rad)
        asc_x = -(math.sin(lst_rad) * math.cos(eps_rad) + math.tan(lat_rad) * math.sin(eps_rad))
        asc_deg_tropical = (math.degrees(math.atan2(asc_y, asc_x)) + 360.0) % 360.0
        
        # Apply sidereal offset mapping
        adjusted_asc = (asc_deg_tropical - ayanamsa_correction) % 360.0
        if adjusted_asc < 0:
            adjusted_asc += 360.0
        
        asc_sign, asc_sign_deg, asc_nak, asc_pada = self.compute_zodiac_and_nakshatra(adjusted_asc)
        
        asc_house = self.get_house(asc_sign, asc_sign)
        
        results["Ascendant"] = PlanetaryPosition(
            planet="Ascendant",
            longitude=adjusted_asc,
            sign=asc_sign,
            sign_degree=asc_sign_deg,
            nakshatra=asc_nak,
            nakshatra_pada=asc_pada,
            motion_direction="Direct",
            house=asc_house,
            is_combust=False
        )

        sun_lon_deg = None
        for name, body in self.bodies.items():
            # Single vectorized call: Skyfield computes T and T+1 day in one
            # numpy batch — no repeated BSP segment lookups per time point.
            astrometric_vec = observer.at(t_vec).observe(body).apparent()
            _, lon_vec, _ = astrometric_vec.ecliptic_latlon()

            ecliptic_lon_T      = lon_vec.degrees[0]  # Longitude at time T
            ecliptic_lon_T1     = lon_vec.degrees[1]  # Longitude at T + 1 day

            # Speed in degrees/day (handles 360° wraparound)
            speed = ecliptic_lon_T1 - ecliptic_lon_T
            if speed > 180.0:
                speed -= 360.0
            elif speed < -180.0:
                speed += 360.0

            # Retrograde detection: reuse the speed sign — no tiny-delta needed
            if name in ["Sun", "Moon"]:
                motion = "Direct"
            elif speed < 0:
                motion = "Retrograde"
            else:
                motion = "Direct"

            # Apply Sidereal shift if required
            adjusted_lon = (ecliptic_lon_T - ayanamsa_correction) % 360.0
            if adjusted_lon < 0:
                adjusted_lon += 360.0

            sign, sign_deg, nakshatra, pada = self.compute_zodiac_and_nakshatra(adjusted_lon)

            p_house = self.get_house(sign, asc_sign)

            if name == "Sun":
                sun_lon_deg = adjusted_lon

            is_combust = False
            if sun_lon_deg is not None and name in ["Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]:
                dist = abs(adjusted_lon - sun_lon_deg)
                if dist > 180.0:
                    dist = 360.0 - dist
                if dist <= 15.0:
                    is_combust = True

            results[name] = PlanetaryPosition(
                planet=name,
                longitude=adjusted_lon,
                sign=sign,
                sign_degree=sign_deg,
                nakshatra=nakshatra,
                nakshatra_pada=pada,
                motion_direction=motion,
                house=p_house,
                is_combust=is_combust,
                speed_deg_per_day=round(speed, 6)
            )

        # Mean Lunar Nodes (Rahu and Ketu) Calculation based on Julian Centuries since J2000
        # t.tt provides the Julian Date (Terrestrial Time)
        T_centuries = (t.tt - 2451545.0) / 36525.0
        # Mean longitude of the ascending node (Rahu)
        rahu_lon_deg = (125.04452 - 1934.136261 * T_centuries) % 360.0
        ketu_lon_deg = (rahu_lon_deg + 180.0) % 360.0

        for name, original_lon in [("Rahu", rahu_lon_deg), ("Ketu", ketu_lon_deg)]:
            adjusted_lon = (original_lon - ayanamsa_correction) % 360.0
            if adjusted_lon < 0:
                adjusted_lon += 360.0

            sign, sign_deg, nakshatra, pada = self.compute_zodiac_and_nakshatra(adjusted_lon)
            
            p_house = self.get_house(sign, asc_sign)

            results[name] = PlanetaryPosition(
                planet=name,
                longitude=adjusted_lon,
                sign=sign,
                sign_degree=sign_deg,
                nakshatra=nakshatra,
                nakshatra_pada=pada,
                motion_direction="Retrograde",  # Mean nodes always traverse retrograde
                house=p_house,
                is_combust=False,  # Nodes are shadows, cannot be combust
                speed_deg_per_day=-0.053  # Hardcoded: nodes are always slow & retrograde
            )

        # Phase 2: Compute Inter-Planetary Aspects (Drishti)
        for planet_name, planet_data in results.items():
            if planet_name == "Ascendant":
                continue
                
            current_house = planet_data.house
            aspect_targets = Constants.ASPECT_RULES.get(planet_name, [7])
            
            for aspect_num in aspect_targets:
                # 12-house wrap logic (+ aspect_num - 2) removes 1 for zero-index and 1 because relative house 1 is the 0 offset
                t_house = ((current_house + aspect_num - 2) % 12) + 1
                
                sitting_planets = [
                    name for name, data in results.items() 
                    if getattr(data, 'house', None) == t_house and name != planet_name and name != "Ascendant"
                ]
                
                planet_data.aspects.append(VedicAspect(
                    aspect_number=aspect_num,
                    target_house=t_house,
                    aspected_planets=sitting_planets
                ))

        return results
