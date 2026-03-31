from pydantic import BaseModel, Field, condecimal, validator
from typing import Optional, Dict, List, Any

class LocationInput(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Decimal Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Decimal Longitude")
    altitude: float = Field(default=0.0, description="Altitude in meters above sea level")

class DateTimeInput(BaseModel):
    year: int = Field(..., ge=-3000, le=3000)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    hour: int = Field(..., ge=0, le=23)
    minute: int = Field(..., ge=0, le=59)
    second: int = Field(..., ge=0, le=59)
    utc_offset: float = Field(default=0.0, description="UTC Offset in hours")

class AstroRequest(BaseModel):
    datetime: DateTimeInput
    location: LocationInput
    ayanamsa: str = Field(default="TROPICAL", description="Calculated Mode: LAHIRI, RAMAN, or TROPICAL")

    @validator('ayanamsa')
    def validate_ayanamsa(cls, v):
        valid = ["LAHIRI", "RAMAN", "TROPICAL"]
        if v.upper() not in valid:
            raise ValueError(f"Ayanamsa must be one of {valid}")
        return v.upper()

class VedicAspect(BaseModel):
    aspect_number: int
    target_house: int
    aspected_planets: List[str]

class PlanetaryPosition(BaseModel):
    planet: str
    longitude: float
    sign: str
    sign_degree: float
    nakshatra: str
    nakshatra_pada: int
    motion_direction: str
    house: int
    is_combust: bool
    speed_deg_per_day: Optional[float] = None  # None for Ascendant; -0.053 for Rahu/Ketu
    aspects: List[VedicAspect] = []

class AstroResponse(BaseModel):
    request_params: AstroRequest
    positions: Dict[str, PlanetaryPosition]
    house_lords: Dict[str, str]       # House number (1-12) → ruling planet name
    avasthas: Dict[str, Any]          # Planet name → {avastha, result_meaning, strength}
    tajaka_yogas: Dict[str, Any]      # Tajaka yoga detection results
    house_judgment: Dict[str, Any]    # Six-step Prasna Tantra horary judgment
    sincerity_check: Dict[str, Any]   # Chapter 1 sincerity check results
    timing_estimate: Optional[Dict[str, Any]]  # Three-method timing estimate
    latency_ms: float
