"""Service for fetching real earthquake data from USGS."""

import httpx
from datetime import datetime, timedelta
from typing import List, Optional
from ..routes.events import EarthquakeEvent


class USGSEarthquakeService:
    """Service to fetch earthquake data from USGS."""

    BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

    @staticmethod
    async def fetch_recent_earthquakes(
        hours: int = 24,
        min_magnitude: float = 3.0,
        min_lat: Optional[float] = None,
        max_lat: Optional[float] = None,
        min_lon: Optional[float] = None,
        max_lon: Optional[float] = None,
    ) -> List[EarthquakeEvent]:
        """
        Fetch recent earthquakes from USGS.

        Args:
            hours: Hours to look back
            min_magnitude: Minimum magnitude
            min_lat: Minimum latitude (for bounding box)
            max_lat: Maximum latitude (for bounding box)
            min_lon: Minimum longitude (for bounding box)
            max_lon: Maximum longitude (for bounding box)

        Returns:
            List of EarthquakeEvent objects
        """
        # Calculate start time
        start_time = datetime.utcnow() - timedelta(hours=hours)

        # Build query parameters
        params = {
            "format": "geojson",
            "starttime": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "endtime": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
            "minmagnitude": min_magnitude,
            "orderby": "time",
        }

        # Add bounding box if specified (useful for India region)
        if all([min_lat, max_lat, min_lon, max_lon]):
            params.update({
                "minlatitude": min_lat,
                "maxlatitude": max_lat,
                "minlongitude": min_lon,
                "maxlongitude": max_lon,
            })

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(USGSEarthquakeService.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

                earthquakes = []
                for feature in data.get("features", []):
                    props = feature.get("properties", {})
                    coords = feature.get("geometry", {}).get("coordinates", [])

                    if len(coords) >= 3:
                        earthquake = EarthquakeEvent(
                            event_id=feature.get("id", "unknown"),
                            time=datetime.fromtimestamp(props.get("time", 0) / 1000),
                            latitude=coords[1],
                            longitude=coords[0],
                            depth_km=coords[2],
                            magnitude=props.get("mag", 0.0),
                            magnitude_type=props.get("magType", "unknown"),
                            source="USGS",
                            location=props.get("place", "Unknown location"),
                        )
                        earthquakes.append(earthquake)

                return earthquakes

        except Exception as e:
            print(f"Error fetching USGS data: {e}")
            # Return empty list on error
            return []

    @staticmethod
    async def fetch_earthquake_details(event_id: str) -> Optional[dict]:
        """
        Fetch detailed information for a specific earthquake.

        Args:
            event_id: USGS event ID

        Returns:
            Dictionary with detailed event information
        """
        try:
            url = f"https://earthquake.usgs.gov/fdsnws/event/1/query"
            params = {
                "format": "geojson",
                "eventid": event_id,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                if data.get("features"):
                    feature = data["features"][0]
                    props = feature.get("properties", {})
                    coords = feature.get("geometry", {}).get("coordinates", [])

                    return {
                        "event_id": feature.get("id"),
                        "time": datetime.fromtimestamp(props.get("time", 0) / 1000),
                        "latitude": coords[1] if len(coords) >= 2 else None,
                        "longitude": coords[0] if len(coords) >= 1 else None,
                        "depth_km": coords[2] if len(coords) >= 3 else None,
                        "magnitude": props.get("mag"),
                        "magnitude_type": props.get("magType"),
                        "location": props.get("place"),
                        "status": props.get("status"),
                        "tsunami": props.get("tsunami"),
                        "felt_reports": props.get("felt"),
                        "cdi": props.get("cdi"),  # Community Decimal Intensity
                        "mmi": props.get("mmi"),  # Modified Mercalli Intensity
                        "alert": props.get("alert"),
                        "url": props.get("url"),
                        "detail": props.get("detail"),
                    }

                return None

        except Exception as e:
            print(f"Error fetching earthquake details: {e}")
            return None
