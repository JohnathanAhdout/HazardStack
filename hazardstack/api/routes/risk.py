"""Risk query endpoints."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
import sys
from pathlib import Path
import math

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hazard.common.geo import H3Grid
from hazard.common.typing import RiskLevel
from ..services.earthquake_service import USGSEarthquakeService

router = APIRouter()

# Initialize H3 grid (in production, this would be cached/singleton)
# For now, create a dummy instance
grid = H3Grid(resolution=4)


# Helper functions for h3 API compatibility
def h3_cell_to_latlng(cell: str) -> tuple:
    """Convert H3 cell to lat/lng (compatible with h3 v3 and v4)"""
    import h3
    try:
        return h3.cell_to_latlng(cell)
    except AttributeError:
        return h3.h3_to_geo(cell)


def h3_cell_to_boundary(cell: str) -> list:
    """Get H3 cell boundary (compatible with h3 v3 and v4)"""
    import h3
    try:
        return h3.cell_to_boundary(cell, geo_json=True)
    except (AttributeError, TypeError):
        return h3.h3_to_geo_boundary(cell, geo_json=True)


def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula."""
    R = 6371  # Earth's radius in km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))

    return R * c


def calculate_mmi(magnitude: float, distance_km: float, depth_km: float) -> float:
    """
    Calculate Modified Mercalli Intensity using simplified attenuation model.

    Based on USGS attenuation relationships for stable continental regions.
    Returns MMI value (1-10 scale).
    """
    if distance_km < 1:
        distance_km = 1  # Avoid division by zero

    # Simplified attenuation model: MMI = a + b*M - c*log10(R) - d*R
    # Where R is hypocentral distance
    hypocentral_dist = math.sqrt(distance_km**2 + depth_km**2)

    # Coefficients for stable continental regions
    a = 2.0
    b = 1.7
    c = 3.5
    d = 0.01

    mmi = a + b * magnitude - c * math.log10(hypocentral_dist) - d * hypocentral_dist

    # Clamp to reasonable range
    return max(1.0, min(10.0, mmi))


def calculate_aftershock_probability(magnitude: float, hours_since: float) -> float:
    """
    Calculate aftershock probability using simplified Omori's law.

    Returns probability of experiencing aftershock in next 24h.
    """
    if hours_since < 0.1:
        hours_since = 0.1  # Avoid division by zero

    # Omori's law: rate = K / (t + c)^p
    # K depends on mainshock magnitude, p ≈ 1 for most sequences, c ≈ 0.1 days
    K = 10 ** (magnitude - 4.5)  # Scaling with magnitude
    c = 0.1 * 24  # c in hours
    p = 1.0

    # Calculate expected number of aftershocks in next 24h
    t1 = hours_since
    t2 = hours_since + 24

    # Integral of Omori's law
    if p == 1.0:
        expected_count = K * math.log((t2 + c) / (t1 + c))
    else:
        expected_count = K / (1 - p) * ((t1 + c)**(1-p) - (t2 + c)**(1-p))

    # Convert to probability (Poisson distribution)
    probability = 1 - math.exp(-expected_count / 10)  # Normalize

    return max(0.0, min(1.0, probability))


class RiskComponent(BaseModel):
    """Individual hazard risk components."""

    rain_extreme_1h: Optional[float] = None
    rain_extreme_6h: Optional[float] = None
    rain_extreme_24h: Optional[float] = None
    flood_12h: Optional[float] = None
    flood_24h: Optional[float] = None
    mmi_mean: Optional[float] = None
    mmi_std: Optional[float] = None
    aftershock_24h: Optional[float] = None


class HorizonRisk(BaseModel):
    """Risk for a single horizon."""

    level: RiskLevel
    score: float = Field(..., ge=0.0, le=1.0)


class CellRisk(BaseModel):
    """Risk output for a single H3 cell."""

    h3_id: str
    centroid: tuple[float, float]  # (lat, lon)
    risk: dict[str, HorizonRisk]
    components: RiskComponent
    explain: Optional[List[dict]] = None


class RiskQueryResponse(BaseModel):
    """Response for risk query."""

    query: dict
    generated_at: datetime
    cells: List[CellRisk]


@router.get("/risk", response_model=RiskQueryResponse)
async def get_risk(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
    radius_km: float = Query(10, ge=1, le=50, description="Radius in kilometers"),
    horizons: str = Query("1h,6h,24h", description="Comma-separated horizons"),
):
    """
    Get multi-hazard risk for a location.

    Returns calibrated probabilities and risk levels for:
    - Extreme rainfall
    - Flood exceedance
    - Earthquake shaking
    - Aftershock probability

    Args:
        lat: Latitude of query point
        lon: Longitude of query point
        radius_km: Radius to query around point
        horizons: Forecast horizons (e.g., "1h,6h,24h")

    Returns:
        RiskQueryResponse with risk data for all cells within radius
    """
    # Parse horizons
    horizon_list = [h.strip() for h in horizons.split(",")]

    # Get cells within radius
    try:
        cells_in_radius = grid.cells_within_radius(lat, lon, radius_km)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying grid: {str(e)}")

    if not cells_in_radius:
        return RiskQueryResponse(
            query={"lat": lat, "lon": lon, "radius_km": radius_km, "horizons": horizon_list},
            generated_at=datetime.utcnow(),
            cells=[],
        )

    # Fetch recent earthquakes to calculate accurate risk
    import h3

    # Get earthquakes from last 7 days
    earthquakes = await USGSEarthquakeService.fetch_recent_earthquakes(
        hours=168,  # 7 days
        min_magnitude=2.5,
        min_lat=-90,
        max_lat=90,
        min_lon=-180,
        max_lon=180,
    )

    cell_risks = []
    for cell in cells_in_radius[:20]:  # Limit to 20 cells for response size
        cell_lat, cell_lon = h3_cell_to_latlng(cell)

        # Calculate earthquake-based risk components
        max_mmi = 1.0  # Baseline MMI (not felt)
        max_aftershock_prob = 0.0

        for eq in earthquakes:
            distance = calculate_distance_km(cell_lat, cell_lon, eq.latitude, eq.longitude)

            # Only consider earthquakes within reasonable distance (500km)
            if distance > 500:
                continue

            # Calculate MMI at this location
            mmi = calculate_mmi(eq.magnitude, distance, eq.depth_km)
            max_mmi = max(max_mmi, mmi)

            # Calculate aftershock probability
            hours_since = (datetime.utcnow() - eq.time).total_seconds() / 3600
            aftershock_prob = calculate_aftershock_probability(eq.magnitude, hours_since)

            # Weight by distance (closer = higher probability)
            distance_weight = max(0, 1 - distance / 500)
            weighted_aftershock = aftershock_prob * distance_weight

            max_aftershock_prob = max(max_aftershock_prob, weighted_aftershock)

        # Normalize MMI to 0-1 scale (MMI ranges 1-10)
        mmi_normalized = (max_mmi - 1.0) / 9.0

        # Rain and flood risks - set to low baseline (no real forecast data yet)
        rain_risk = 0.05
        flood_risk = 0.02

        # Calculate overall risk scores by horizon
        risk_by_horizon = {}
        for horizon in horizon_list:
            # Different time horizons weight components differently
            if horizon == "1h":
                # Short term: mainly current shaking
                score = mmi_normalized * 0.9 + rain_risk * 0.1
            elif horizon == "6h":
                # Medium term: shaking + rain
                score = mmi_normalized * 0.5 + rain_risk * 0.4 + flood_risk * 0.1
            elif horizon == "12h":
                # Medium-long term: aftershocks + rain + flood
                score = mmi_normalized * 0.3 + max_aftershock_prob * 0.3 + rain_risk * 0.2 + flood_risk * 0.2
            elif horizon == "24h":
                # Long term: mainly aftershocks + flood
                score = max_aftershock_prob * 0.5 + flood_risk * 0.3 + rain_risk * 0.2
            elif horizon == "72h":
                # Very long term: mainly flood risk
                score = max_aftershock_prob * 0.3 + flood_risk * 0.5 + rain_risk * 0.2
            else:
                # Default weighting
                score = (mmi_normalized + max_aftershock_prob + rain_risk + flood_risk) / 4

            # Determine risk level based on score
            if score >= 0.70:
                level = "EXTREME"
            elif score >= 0.45:
                level = "HIGH"
            elif score >= 0.20:
                level = "MODERATE"
            else:
                level = "LOW"

            risk_by_horizon[horizon] = HorizonRisk(level=level, score=round(score, 3))

        cell_risk = CellRisk(
            h3_id=cell,
            centroid=(cell_lat, cell_lon),
            risk=risk_by_horizon,
            components=RiskComponent(
                rain_extreme_6h=rain_risk,
                flood_12h=flood_risk,
                mmi_mean=round(max_mmi, 2),
                aftershock_24h=round(max_aftershock_prob, 3),
            ),
            explain=[
                {"feature": "earthquake_mmi", "impact": round(mmi_normalized, 3)},
                {"feature": "aftershock_prob", "impact": round(max_aftershock_prob, 3)},
                {"feature": "recent_events", "impact": min(len(earthquakes) / 100, 1.0)},
            ],
        )

        cell_risks.append(cell_risk)

    return RiskQueryResponse(
        query={
            "lat": lat,
            "lon": lon,
            "radius_km": radius_km,
            "horizons": horizon_list,
        },
        generated_at=datetime.utcnow(),
        cells=cell_risks,
    )


@router.get("/tiles/{z}/{x}/{y}")
async def get_tile(
    z: int,
    x: int,
    y: int,
    horizon: str = Query("6h", description="Forecast horizon"),
):
    """
    Get risk tile for map visualization.

    Returns a vector tile (GeoJSON) of risk hexagons.

    Args:
        z: Zoom level
        x: Tile X coordinate
        y: Tile Y coordinate
        horizon: Forecast horizon

    Returns:
        GeoJSON FeatureCollection
    """
    import math
    import random

    # Convert tile coordinates to lat/lon bounds
    def tile_to_latlon(x: int, y: int, z: int):
        n = 2.0 ** z
        lon_min = x / n * 360.0 - 180.0
        lat_max_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
        lat_max = math.degrees(lat_max_rad)

        lon_max = (x + 1) / n * 360.0 - 180.0
        lat_min_rad = math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n)))
        lat_min = math.degrees(lat_min_rad)

        return lat_min, lon_min, lat_max, lon_max

    lat_min, lon_min, lat_max, lon_max = tile_to_latlon(x, y, z)

    # Get center of tile and determine appropriate radius
    center_lat = (lat_min + lat_max) / 2
    center_lon = (lon_min + lon_max) / 2

    # Calculate approximate radius in km (tile width)
    lat_diff = lat_max - lat_min
    lon_diff = lon_max - lon_min
    radius_km = max(lat_diff, lon_diff) * 111  # Rough km per degree

    # Get cells within the tile bounds
    try:
        cells = grid.cells_within_radius(center_lat, center_lon, min(radius_km, 100))

        # Filter cells that are actually within tile bounds
        features = []
        for cell_id in cells[:50]:  # Limit to 50 cells per tile
            import h3

            cell_lat, cell_lon = h3_cell_to_latlng(cell_id)

            # Check if cell is within tile bounds
            if not (lat_min <= cell_lat <= lat_max and lon_min <= cell_lon <= lon_max):
                continue

            # Calculate accurate risk data for this cell using recent earthquakes
            # Fetch earthquakes (in production, this would be cached)
            earthquakes_tile = await USGSEarthquakeService.fetch_recent_earthquakes(
                hours=168,
                min_magnitude=2.5,
            )

            max_mmi = 1.0
            max_aftershock_prob = 0.0

            for eq in earthquakes_tile:
                distance = calculate_distance_km(cell_lat, cell_lon, eq.latitude, eq.longitude)
                if distance > 500:
                    continue

                mmi = calculate_mmi(eq.magnitude, distance, eq.depth_km)
                max_mmi = max(max_mmi, mmi)

                hours_since = (datetime.utcnow() - eq.time).total_seconds() / 3600
                aftershock_prob = calculate_aftershock_probability(eq.magnitude, hours_since)
                distance_weight = max(0, 1 - distance / 500)
                max_aftershock_prob = max(max_aftershock_prob, aftershock_prob * distance_weight)

            mmi_normalized = (max_mmi - 1.0) / 9.0

            # Calculate score based on horizon
            if horizon == "1h":
                score = mmi_normalized * 0.9 + 0.05 * 0.1
            elif horizon == "6h":
                score = mmi_normalized * 0.5 + 0.05 * 0.4 + 0.02 * 0.1
            elif horizon == "24h":
                score = max_aftershock_prob * 0.5 + 0.02 * 0.3 + 0.05 * 0.2
            else:
                score = (mmi_normalized + max_aftershock_prob + 0.05 + 0.02) / 4

            # Determine risk level
            if score >= 0.70:
                level = "EXTREME"
            elif score >= 0.45:
                level = "HIGH"
            elif score >= 0.20:
                level = "MODERATE"
            else:
                level = "LOW"

            # Get hexagon boundary
            boundary = h3_cell_to_boundary(cell_id)

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [boundary],
                },
                "properties": {
                    "h3_id": cell_id,
                    "risk_level": level,
                    "risk_score": score,
                    "horizon": horizon,
                    "centroid": [cell_lat, cell_lon],
                },
            }
            features.append(feature)

        return {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "tile": {"z": z, "x": x, "y": y},
                "bounds": {
                    "lat_min": lat_min,
                    "lon_min": lon_min,
                    "lat_max": lat_max,
                    "lon_max": lon_max,
                },
                "horizon": horizon,
                "generated_at": datetime.utcnow().isoformat(),
                "cell_count": len(features),
            },
        }

    except Exception as e:
        # Return empty GeoJSON on error
        return {
            "type": "FeatureCollection",
            "features": [],
            "metadata": {
                "tile": {"z": z, "x": x, "y": y},
                "horizon": horizon,
                "generated_at": datetime.utcnow().isoformat(),
                "error": str(e),
            },
        }
