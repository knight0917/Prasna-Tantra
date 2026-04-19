from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


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

    @field_validator("ayanamsa")
    @classmethod
    def validate_ayanamsa(cls, value: str) -> str:
        valid = ["LAHIRI", "RAMAN", "TROPICAL"]
        normalized = value.upper()
        if normalized not in valid:
            raise ValueError(f"Ayanamsa must be one of {valid}")
        return normalized


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
    speed_deg_per_day: Optional[float] = None
    aspects: List[VedicAspect] = Field(default_factory=list)


class AstroResponse(BaseModel):
    request_params: AstroRequest
    positions: Dict[str, PlanetaryPosition]
    house_lords: Dict[str, str]
    avasthas: Dict[str, Any]
    tajaka_yogas: Dict[str, Any]
    house_judgment: Dict[str, Any]
    sincerity_check: Dict[str, Any]
    timing_estimate: Optional[Dict[str, Any]]
    latency_ms: float
