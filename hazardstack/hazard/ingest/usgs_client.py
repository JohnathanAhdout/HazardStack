"""USGS earthquake event feed client for global context."""

import requests
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging
import pandas as pd

logger = logging.getLogger(__name__)


class USGSClient:
    """
    Client for USGS earthquake event feeds.

    Provides global context and cross-validation for NCS events.
    """

    def __init__(self):
        """Initialize USGS client."""
        self.base_url = "https://earthquake.usgs.gov/fdsnws/event/1"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "HazardStack/0.1.0 (Research; hazardstack@example.com)"
        })

    def query(
        self,
        starttime: Optional[datetime] = None,
        endtime: Optional[datetime] = None,
        minmagnitude: float = 3.0,
        bbox: Optional[Dict] = None,
        limit: int = 20000,
    ) -> pd.DataFrame:
        """
        Query USGS event service.

        Args:
            starttime: Start time (UTC)
            endtime: End time (UTC)
            minmagnitude: Minimum magnitude
            bbox: Bounding box dict with lat_min, lat_max, lon_min, lon_max
            limit: Maximum number of events

        Returns:
            DataFrame with events
        """
        if starttime is None:
            starttime = datetime.utcnow() - timedelta(days=30)

        if endtime is None:
            endtime = datetime.utcnow()

        params = {
            "format": "geojson",
            "starttime": starttime.strftime("%Y-%m-%dT%H:%M:%S"),
            "endtime": endtime.strftime("%Y-%m-%dT%H:%M:%S"),
            "minmagnitude": minmagnitude,
            "limit": limit,
            "orderby": "time-asc",
        }

        if bbox:
            params["minlatitude"] = bbox["lat_min"]
            params["maxlatitude"] = bbox["lat_max"]
            params["minlongitude"] = bbox["lon_min"]
            params["maxlongitude"] = bbox["lon_max"]

        try:
            logger.info("Querying USGS event service...")
            response = self.session.get(f"{self.base_url}/query", params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            if "features" not in data:
                logger.warning("No features in USGS response")
                return pd.DataFrame()

            events = []
            for feature in data["features"]:
                props = feature["properties"]
                coords = feature["geometry"]["coordinates"]

                events.append({
                    "event_id": feature["id"],
                    "time": datetime.utcfromtimestamp(props["time"] / 1000),
                    "latitude": coords[1],
                    "longitude": coords[0],
                    "depth_km": coords[2] if len(coords) > 2 else None,
                    "magnitude": props.get("mag"),
                    "magnitude_type": props.get("magType"),
                    "place": props.get("place"),
                    "source": "USGS",
                    "url": props.get("url"),
                })

            df = pd.DataFrame(events)
            logger.info(f"Retrieved {len(df)} events from USGS")

            return df

        except Exception as e:
            logger.error(f"Error querying USGS: {e}")
            return pd.DataFrame()

    def get_india_events(
        self,
        days: int = 30,
        minmagnitude: float = 3.0,
    ) -> pd.DataFrame:
        """
        Get events in India region from USGS.

        Args:
            days: Days to look back
            minmagnitude: Minimum magnitude

        Returns:
            DataFrame with events
        """
        bbox = {
            "lat_min": 5.0,
            "lat_max": 40.0,
            "lon_min": 65.0,
            "lon_max": 100.0,
        }

        starttime = datetime.utcnow() - timedelta(days=days)

        return self.query(
            starttime=starttime,
            minmagnitude=minmagnitude,
            bbox=bbox,
        )
