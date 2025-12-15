"""Event query endpoints (earthquakes, floods, etc.)."""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

router = APIRouter()


class EarthquakeEvent(BaseModel):
    """Earthquake event."""

    event_id: str
    time: datetime
    latitude: float
    longitude: float
    depth_km: float
    magnitude: float
    magnitude_type: str
    source: str
    location: Optional[str] = None


class FloodBulletin(BaseModel):
    """Flood bulletin from CWC."""

    basin_id: str
    basin_name: str
    issued_at: datetime
    risk_level: str
    message: str
    danger_threshold_m3s: Optional[float] = None
    current_discharge_m3s: Optional[float] = None


class EventsResponse(BaseModel):
    """Response for events query."""

    earthquakes: List[EarthquakeEvent]
    flood_bulletins: List[FloodBulletin]
    generated_at: datetime


@router.get("/events/recent", response_model=EventsResponse)
async def get_recent_events(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    include_earthquakes: bool = Query(True, description="Include earthquakes"),
    include_floods: bool = Query(True, description="Include flood bulletins"),
    min_magnitude: float = Query(3.0, ge=0, le=10, description="Minimum earthquake magnitude"),
):
    """
    Get recent hazard events.

    Returns:
    - Recent earthquakes from NCS/USGS
    - Flood bulletins from CWC

    Args:
        hours: Hours to look back
        include_earthquakes: Whether to include earthquakes
        include_floods: Whether to include flood bulletins
        min_magnitude: Minimum magnitude for earthquakes

    Returns:
        EventsResponse with recent events
    """
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)

    earthquakes = []
    flood_bulletins = []

    # TODO: Fetch from database/cache
    # For now, return mock data

    if include_earthquakes:
        # Mock earthquake data
        earthquakes = [
            EarthquakeEvent(
                event_id="ncs_2024_001234",
                time=datetime.utcnow() - timedelta(hours=2),
                latitude=28.5,
                longitude=77.2,
                depth_km=10.0,
                magnitude=4.2,
                magnitude_type="Mw",
                source="NCS",
                location="Delhi NCR",
            ),
            EarthquakeEvent(
                event_id="ncs_2024_001235",
                time=datetime.utcnow() - timedelta(hours=12),
                latitude=26.9,
                longitude=88.4,
                depth_km=15.0,
                magnitude=3.8,
                magnitude_type="ML",
                source="NCS",
                location="Sikkim",
            ),
        ]

    if include_floods:
        # Mock flood bulletin
        flood_bulletins = [
            FloodBulletin(
                basin_id="brahmaputra_001",
                basin_name="Brahmaputra - Guwahati",
                issued_at=datetime.utcnow() - timedelta(hours=1),
                risk_level="HIGH",
                message="Water level rising. Expected to cross danger mark in 12 hours.",
                danger_threshold_m3s=50000.0,
                current_discharge_m3s=48500.0,
            ),
        ]

    return EventsResponse(
        earthquakes=earthquakes,
        flood_bulletins=flood_bulletins,
        generated_at=datetime.utcnow(),
    )


@router.get("/events/earthquake/{event_id}")
async def get_earthquake_details(event_id: str):
    """
    Get detailed information for a specific earthquake event.

    Args:
        event_id: Event ID from NCS or USGS

    Returns:
        Detailed event information including aftershock forecast
    """
    # TODO: Implement
    return {
        "event_id": event_id,
        "detail": "Not implemented yet",
        "message": "This endpoint will return detailed event info + impact map + aftershock forecast",
    }
