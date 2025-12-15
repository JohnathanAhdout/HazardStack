"""National Center for Seismology (NCS) earthquake data client."""

import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict
import logging
import pandas as pd

logger = logging.getLogger(__name__)


class NCSClient:
    """
    Client for NCS earthquake catalog and real-time events.

    Fetches earthquake events from India's official seismology agency.
    """

    def __init__(
        self,
        base_url: str = "https://seismo.gov.in",
        cache_dir: Optional[str] = None,
    ):
        """
        Initialize NCS client.

        Args:
            base_url: NCS base URL
            cache_dir: Cache directory
        """
        self.base_url = base_url
        self.data_portal_url = f"{base_url}/data-portal"
        self.cache_dir = Path(cache_dir) if cache_dir else Path("data/raw/ncs")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "HazardStack/0.1.0 (Research; hazardstack@example.com)"
        })

    def get_recent_events(
        self,
        hours: int = 24,
        min_magnitude: float = 3.0,
        region: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Get recent earthquake events.

        Args:
            hours: Hours to look back
            min_magnitude: Minimum magnitude
            region: Region filter (e.g., "himalayan", "ne_india")

        Returns:
            DataFrame with earthquake events
        """
        try:
            logger.info(f"Fetching NCS events from last {hours} hours...")

            # TODO: Implement actual NCS API/scraping
            # NCS provides data through their portal, may require scraping
            # or direct database access

            return self._create_mock_events(hours, min_magnitude)

        except Exception as e:
            logger.error(f"Error fetching NCS events: {e}")
            return pd.DataFrame()

    def get_catalog(
        self,
        start_date: datetime,
        end_date: datetime,
        min_magnitude: float = 3.0,
        bbox: Optional[Dict] = None,
    ) -> pd.DataFrame:
        """
        Get earthquake catalog for date range.

        Args:
            start_date: Start date
            end_date: End date
            min_magnitude: Minimum magnitude
            bbox: Bounding box dict

        Returns:
            DataFrame with catalog
        """
        if bbox is None:
            # Default to India + surrounding regions
            bbox = {
                "lat_min": 5.0,
                "lat_max": 40.0,
                "lon_min": 65.0,
                "lon_max": 100.0,
            }

        try:
            # Check cache
            cache_filename = f"catalog_{start_date.date()}_{end_date.date()}_M{min_magnitude}.csv"
            cache_path = self.cache_dir / cache_filename

            if cache_path.exists():
                logger.info(f"Loading catalog from cache: {cache_path}")
                return pd.read_csv(cache_path, parse_dates=["time"])

            # TODO: Download from NCS data portal
            logger.info("Fetching NCS catalog...")
            df = self._create_mock_catalog(start_date, end_date, min_magnitude, bbox)

            # Cache
            df.to_csv(cache_path, index=False)

            return df

        except Exception as e:
            logger.error(f"Error fetching catalog: {e}")
            return pd.DataFrame()

    def get_seismic_regions(self) -> Dict[str, Dict]:
        """
        Get seismic region definitions.

        Returns:
            Dict mapping region ID to region info
        """
        regions = {
            "himalayan_belt": {
                "name": "Himalayan Belt",
                "description": "Main Himalayan Thrust zone",
                "bbox": {
                    "lat_min": 26.0,
                    "lat_max": 36.0,
                    "lon_min": 70.0,
                    "lon_max": 97.0,
                },
                "avg_annual_rate": 50,  # M≥3.5
                "max_historical": 8.6,  # 1950 Assam earthquake
            },
            "ne_india": {
                "name": "Northeast India",
                "description": "Indo-Burman arc",
                "bbox": {
                    "lat_min": 23.0,
                    "lat_max": 29.0,
                    "lon_min": 88.0,
                    "lon_max": 97.0,
                },
                "avg_annual_rate": 80,
                "max_historical": 8.6,
            },
            "kutch": {
                "name": "Kutch Region",
                "description": "Intraplate zone, 2001 Bhuj earthquake",
                "bbox": {
                    "lat_min": 22.0,
                    "lat_max": 25.0,
                    "lon_min": 68.0,
                    "lon_max": 72.0,
                },
                "avg_annual_rate": 20,
                "max_historical": 7.7,  # 2001 Bhuj
            },
            "andaman_nicobar": {
                "name": "Andaman-Nicobar",
                "description": "Subduction zone, 2004 Sumatra megathrust",
                "bbox": {
                    "lat_min": 6.0,
                    "lat_max": 14.0,
                    "lon_min": 92.0,
                    "lon_max": 94.0,
                },
                "avg_annual_rate": 100,
                "max_historical": 9.1,  # 2004 (Sumatra)
            },
            "koyna": {
                "name": "Koyna Region",
                "description": "Reservoir-induced seismicity",
                "bbox": {
                    "lat_min": 17.0,
                    "lat_max": 18.0,
                    "lon_min": 73.5,
                    "lon_max": 74.5,
                },
                "avg_annual_rate": 30,
                "max_historical": 6.3,  # 1967 Koyna
            },
        }

        return regions

    def _create_mock_events(
        self,
        hours: int,
        min_magnitude: float,
    ) -> pd.DataFrame:
        """Create mock recent events."""
        import numpy as np

        np.random.seed(42)

        # Generate random events
        num_events = np.random.poisson(hours * 0.5)  # ~0.5 events per hour

        if num_events == 0:
            return pd.DataFrame()

        events = []
        regions = self.get_seismic_regions()

        for i in range(num_events):
            # Random region
            region = np.random.choice(list(regions.keys()))
            region_info = regions[region]
            bbox = region_info["bbox"]

            # Random location in region
            lat = np.random.uniform(bbox["lat_min"], bbox["lat_max"])
            lon = np.random.uniform(bbox["lon_min"], bbox["lon_max"])

            # Random magnitude (exponential distribution)
            mag = np.random.exponential(1.0) + min_magnitude
            mag = min(mag, 7.0)  # Cap at 7.0

            # Random time
            time_offset = timedelta(hours=np.random.uniform(0, hours))
            event_time = datetime.utcnow() - time_offset

            # Random depth
            depth = np.random.uniform(5, 40)  # km

            events.append({
                "event_id": f"ncs_{event_time.strftime('%Y%m%d')}_{i:04d}",
                "time": event_time,
                "latitude": lat,
                "longitude": lon,
                "depth_km": depth,
                "magnitude": mag,
                "magnitude_type": "ML" if mag < 5.0 else "Mw",
                "region": region,
                "location": region_info["name"],
                "source": "NCS",
            })

        df = pd.DataFrame(events)
        df = df[df.magnitude >= min_magnitude].sort_values("time", ascending=False)

        return df

    def _create_mock_catalog(
        self,
        start_date: datetime,
        end_date: datetime,
        min_magnitude: float,
        bbox: Dict,
    ) -> pd.DataFrame:
        """Create mock historical catalog."""
        import numpy as np

        # Gutenberg-Richter: log10(N) = a - b*M
        # For India, roughly: a ≈ 7, b ≈ 1

        days = (end_date - start_date).days
        avg_rate_per_day = 10 ** (7 - min_magnitude)  # Very simplified

        num_events = int(avg_rate_per_day * days)

        if num_events == 0:
            return pd.DataFrame()

        # Random magnitudes following exponential
        magnitudes = np.random.exponential(1.0, num_events) + min_magnitude
        magnitudes = magnitudes[magnitudes < 8.0]  # Cap

        num_events = len(magnitudes)

        # Random times
        timestamps = [
            start_date + timedelta(seconds=np.random.uniform(0, days * 86400))
            for _ in range(num_events)
        ]

        # Random locations in bbox
        lats = np.random.uniform(bbox["lat_min"], bbox["lat_max"], num_events)
        lons = np.random.uniform(bbox["lon_min"], bbox["lon_max"], num_events)
        depths = np.random.uniform(5, 50, num_events)

        df = pd.DataFrame({
            "event_id": [f"ncs_{i:06d}" for i in range(num_events)],
            "time": timestamps,
            "latitude": lats,
            "longitude": lons,
            "depth_km": depths,
            "magnitude": magnitudes,
            "magnitude_type": ["ML" if m < 5 else "Mw" for m in magnitudes],
            "source": "NCS",
        })

        df = df.sort_values("time")

        return df
