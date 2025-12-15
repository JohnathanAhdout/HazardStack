"""Type definitions for the HazardStack system."""

from typing import TypedDict, Literal, Optional
from datetime import datetime
import numpy as np
import numpy.typing as npt


HazardType = Literal["rain", "flood", "earthquake", "aftershock", "tsunami"]
RiskLevel = Literal["LOW", "MODERATE", "HIGH", "EXTREME"]
HorizonType = Literal["1h", "6h", "12h", "24h", "72h"]


class TokenDict(TypedDict):
    """Single spatiotemporal token."""
    h3_id: str
    t: int  # Unix timestamp UTC
    x: npt.NDArray[np.float32]  # Features [D]
    mask: npt.NDArray[np.bool_]  # Missing flags [D]
    meta: "TokenMeta"


class TokenMeta(TypedDict, total=False):
    """Metadata for a token."""
    lat: float
    lon: float
    basin_id: Optional[str]
    elev_m: Optional[float]
    state: Optional[str]
    district: Optional[str]


class RiskOutput(TypedDict):
    """Risk output for a single cell and horizon."""
    h3_id: str
    centroid: tuple[float, float]  # (lat, lon)
    risk_score: float
    risk_level: RiskLevel
    horizon: HorizonType
    components: "RiskComponents"
    timestamp: datetime
    explain: Optional[list["FeatureContribution"]]


class RiskComponents(TypedDict, total=False):
    """Individual hazard contributions to risk."""
    rain_extreme_1h: Optional[float]
    rain_extreme_6h: Optional[float]
    rain_extreme_24h: Optional[float]
    flood_12h: Optional[float]
    flood_24h: Optional[float]
    mmi_mean: Optional[float]
    mmi_std: Optional[float]
    aftershock_24h: Optional[float]


class FeatureContribution(TypedDict):
    """Feature contribution to a prediction."""
    feature: str
    impact: float


class EarthquakeEvent(TypedDict):
    """Earthquake event representation."""
    event_id: str
    time: datetime
    latitude: float
    longitude: float
    depth_km: float
    magnitude: float
    magnitude_type: str
    source: Literal["NCS", "USGS"]


class BasinInfo(TypedDict):
    """River basin information."""
    basin_id: str
    name: str
    area_km2: float
    mean_elevation_m: float
    upstream_basins: list[str]
    danger_threshold_m3s: Optional[float]
