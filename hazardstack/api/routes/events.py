"""Event query endpoints (earthquakes, floods, etc.)."""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from ..services.earthquake_service import USGSEarthquakeService

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

    if include_earthquakes:
        # Fetch real earthquake data from USGS
        # Focus on South Asia region (India and surrounding areas)
        earthquakes = await USGSEarthquakeService.fetch_recent_earthquakes(
            hours=hours,
            min_magnitude=min_magnitude,
            min_lat=5.0,  # Southern tip of India
            max_lat=37.0,  # Northern India/Himalayas
            min_lon=65.0,  # Western border
            max_lon=98.0,  # Eastern border (includes Andaman)
        )

        # If no regional earthquakes found, get global significant events
        if not earthquakes:
            earthquakes = await USGSEarthquakeService.fetch_recent_earthquakes(
                hours=hours,
                min_magnitude=max(min_magnitude, 4.5),  # Higher threshold for global
            )

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
    details = await USGSEarthquakeService.fetch_earthquake_details(event_id)

    if not details:
        return {
            "event_id": event_id,
            "error": "Event not found",
            "message": f"Could not find earthquake event with ID: {event_id}",
        }

    # Calculate simple aftershock probability based on magnitude
    # Using simplified Omori's law: higher magnitude = more aftershocks
    magnitude = details.get("magnitude", 0)
    aftershock_probability = min(0.95, max(0.05, (magnitude - 4.0) / 5.0))

    return {
        "event_id": event_id,
        "details": details,
        "aftershock_forecast": {
            "probability_24h": aftershock_probability,
            "expected_count_24h": int(aftershock_probability * 100),
            "magnitude_range": [magnitude - 2, magnitude - 0.5],
            "model": "simplified_omori",
            "note": "Simplified forecast - actual aftershock behavior may vary",
        },
        "impact_assessment": {
            "intensity": details.get("mmi"),
            "felt_reports": details.get("felt_reports"),
            "alert_level": details.get("alert"),
            "tsunami_warning": details.get("tsunami", False),
        },
    }
