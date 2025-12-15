"""Risk query endpoints."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hazard.common.geo import H3Grid
from hazard.common.typing import RiskLevel

router = APIRouter()

# Initialize H3 grid (in production, this would be cached/singleton)
# For now, create a dummy instance
grid = H3Grid(resolution=4)


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

    # TODO: In production, fetch from Redis cache or run inference
    # For now, return mock data
    import h3

    cell_risks = []
    for cell in cells_in_radius[:20]:  # Limit to 20 cells for response size
        cell_lat, cell_lon = h3.h3_to_geo(cell)

        # Mock risk data (in production, fetch from model/cache)
        import random

        random.seed(hash(cell))  # Deterministic per cell

        risk_by_horizon = {}
        for horizon in horizon_list:
            score = random.uniform(0.1, 0.8)
            level = (
                "EXTREME"
                if score > 0.75
                else "HIGH" if score > 0.5 else "MODERATE" if score > 0.2 else "LOW"
            )
            risk_by_horizon[horizon] = HorizonRisk(level=level, score=score)

        cell_risk = CellRisk(
            h3_id=cell,
            centroid=(cell_lat, cell_lon),
            risk=risk_by_horizon,
            components=RiskComponent(
                rain_extreme_6h=random.uniform(0.1, 0.7),
                flood_12h=random.uniform(0.0, 0.4),
                mmi_mean=random.uniform(0.0, 3.0),
                aftershock_24h=random.uniform(0.0, 0.2),
            ),
            explain=[
                {"feature": "R_acc_3h", "impact": 0.25},
                {"feature": "API_3d", "impact": 0.18},
                {"feature": "climo_p95", "impact": 0.12},
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
    z: int = Query(..., ge=0, le=15, description="Zoom level"),
    x: int = Query(..., description="Tile X coordinate"),
    y: int = Query(..., description="Tile Y coordinate"),
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
    # TODO: Implement tile generation
    # For now, return empty GeoJSON
    return {
        "type": "FeatureCollection",
        "features": [],
        "metadata": {
            "tile": {"z": z, "x": x, "y": y},
            "horizon": horizon,
            "generated_at": datetime.utcnow().isoformat(),
        },
    }
