from pydantic import BaseModel, Field, condecimal, validator
from typing import Optional, Dict

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

class PlanetaryPosition(BaseModel):
    planet: str
    longitude: float
    sign: str
    sign_degree: float
    nakshatra: str
    nakshatra_pada: int

class AstroResponse(BaseModel):
    request_params: AstroRequest
    positions: Dict[str, PlanetaryPosition]
    latency_ms: float
