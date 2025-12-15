"""MOSDAC GSMaP_ISRO rainfall data client."""

import requests
import xarray as xr
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class MOSDACClient:
    """
    Client for MOSDAC GSMaP_ISRO satellite rainfall data.

    GSMaP_ISRO provides hourly rainfall estimates at 0.1° resolution
    over the Indian subcontinent.
    """

    def __init__(
        self,
        base_url: str = "https://www.mosdac.gov.in/gsmap-isro-rain",
        cache_dir: Optional[str] = None,
    ):
        """
        Initialize MOSDAC client.

        Args:
            base_url: Base URL for MOSDAC API
            cache_dir: Directory to cache downloaded files
        """
        self.base_url = base_url
        self.cache_dir = Path(cache_dir) if cache_dir else Path("data/raw/mosdac")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "HazardStack/0.1.0 (Research; hazardstack@example.com)"
        })

    def get_latest(self) -> Optional[xr.Dataset]:
        """
        Get latest available rainfall data.

        Returns:
            xarray Dataset with rainfall rate (mm/h) or None if unavailable
        """
        try:
            # In production, this would call the actual MOSDAC API
            # For now, return mock data structure
            logger.info("Fetching latest GSMaP_ISRO data...")

            # Mock data (replace with actual API call)
            return self._create_mock_dataset(datetime.utcnow())

        except Exception as e:
            logger.error(f"Error fetching latest MOSDAC data: {e}")
            return None

    def get_historical(
        self,
        start_time: datetime,
        end_time: datetime,
        bbox: Optional[dict] = None,
    ) -> List[xr.Dataset]:
        """
        Get historical rainfall data for a time range.

        Args:
            start_time: Start datetime (UTC)
            end_time: End datetime (UTC)
            bbox: Bounding box dict with lat_min, lat_max, lon_min, lon_max

        Returns:
            List of xarray Datasets
        """
        if bbox is None:
            bbox = {
                "lat_min": 6.5,
                "lat_max": 35.5,
                "lon_min": 68.0,
                "lon_max": 97.5,
            }

        datasets = []
        current_time = start_time

        while current_time <= end_time:
            # Check cache first
            cache_path = self._get_cache_path(current_time)

            if cache_path.exists():
                logger.info(f"Loading from cache: {cache_path}")
                ds = xr.open_dataset(cache_path)
                datasets.append(ds)
            else:
                # Fetch from API
                logger.info(f"Fetching data for {current_time}")
                ds = self._fetch_data(current_time, bbox)

                if ds is not None:
                    # Save to cache
                    ds.to_netcdf(cache_path)
                    datasets.append(ds)

            current_time += timedelta(hours=1)

        return datasets

    def _fetch_data(
        self,
        timestamp: datetime,
        bbox: dict,
    ) -> Optional[xr.Dataset]:
        """
        Fetch data from MOSDAC API.

        Args:
            timestamp: Timestamp to fetch
            bbox: Bounding box

        Returns:
            xarray Dataset or None
        """
        try:
            # TODO: Implement actual MOSDAC API call
            # This requires authentication and proper API endpoint
            # For now, return mock data

            return self._create_mock_dataset(timestamp, bbox)

        except Exception as e:
            logger.error(f"Error fetching data for {timestamp}: {e}")
            return None

    def _create_mock_dataset(
        self,
        timestamp: datetime,
        bbox: Optional[dict] = None,
    ) -> xr.Dataset:
        """Create mock dataset for testing."""
        if bbox is None:
            bbox = {
                "lat_min": 6.5,
                "lat_max": 35.5,
                "lon_min": 68.0,
                "lon_max": 97.5,
            }

        # Create grid at 0.1° resolution
        lats = np.arange(bbox["lat_min"], bbox["lat_max"], 0.1)
        lons = np.arange(bbox["lon_min"], bbox["lon_max"], 0.1)

        # Mock rainfall data (random with spatial correlation)
        np.random.seed(int(timestamp.timestamp()) % (2**32))
        rain = np.random.gamma(2, 2, size=(len(lats), len(lons)))  # mm/h
        rain = np.where(rain < 0.1, 0.0, rain)  # Zero out low values

        ds = xr.Dataset(
            {
                "rainfall_rate": (["lat", "lon"], rain),
            },
            coords={
                "lat": lats,
                "lon": lons,
                "time": timestamp,
            },
            attrs={
                "source": "GSMaP_ISRO",
                "resolution": "0.1 degrees",
                "units": "mm/h",
                "description": "Hourly rainfall rate",
            },
        )

        return ds

    def _get_cache_path(self, timestamp: datetime) -> Path:
        """Get cache file path for a timestamp."""
        date_str = timestamp.strftime("%Y%m%d")
        hour_str = timestamp.strftime("%H")
        filename = f"gsmap_{date_str}_{hour_str}00.nc"
        return self.cache_dir / date_str / filename

    def to_h3_grid(
        self,
        dataset: xr.Dataset,
        h3_cells: List[str],
    ) -> dict[str, float]:
        """
        Convert gridded data to H3 cell values.

        Args:
            dataset: xarray Dataset with rainfall
            h3_cells: List of H3 cell IDs

        Returns:
            Dict mapping H3 cell ID to rainfall rate
        """
        import h3

        cell_values = {}

        for cell in h3_cells:
            lat, lon = h3.h3_to_geo(cell)

            # Find nearest grid point
            lat_idx = np.abs(dataset.lat.values - lat).argmin()
            lon_idx = np.abs(dataset.lon.values - lon).argmin()

            value = float(dataset.rainfall_rate.values[lat_idx, lon_idx])
            cell_values[cell] = value

        return cell_values
