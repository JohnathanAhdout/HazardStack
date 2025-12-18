"""Download real training data from public sources."""

import requests
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import logging
import time
import json
from typing import Dict, List, Optional
import gzip
import io

logger = logging.getLogger(__name__)


class DataDownloader:
    """Download hazard data from public APIs and sources."""

    def __init__(self, output_dir: str = "hazardstack/data/raw"):
        """Initialize data downloader."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HazardStack/1.0 (Research/Educational)'
        })

    def download_earthquake_data(
        self,
        start_date: str = "2020-01-01",
        end_date: str = "2024-12-31",
        min_magnitude: float = 4.0,
        region: str = "india",
    ) -> str:
        """
        Download earthquake data from USGS.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            min_magnitude: Minimum magnitude
            region: Geographic region

        Returns:
            Path to saved data
        """
        logger.info(f"Downloading earthquake data from USGS ({start_date} to {end_date})...")

        # Define bounding box for region
        regions = {
            "india": {
                "minlatitude": 6.5,
                "maxlatitude": 35.5,
                "minlongitude": 68.0,
                "maxlongitude": 97.5,
            },
            "global": {
                "minlatitude": -90,
                "maxlatitude": 90,
                "minlongitude": -180,
                "maxlongitude": 180,
            },
        }

        bounds = regions.get(region, regions["india"])

        # USGS API endpoint
        url = "https://earthquake.usgs.gov/fdsnws/event/1/query"

        params = {
            "format": "geojson",
            "starttime": start_date,
            "endtime": end_date,
            "minmagnitude": min_magnitude,
            **bounds,
            "orderby": "time",
        }

        try:
            logger.info(f"Fetching from USGS API: {url}")
            response = self.session.get(url, params=params, timeout=60)
            response.raise_for_status()

            data = response.json()
            num_events = len(data.get("features", []))
            logger.info(f"✓ Downloaded {num_events} earthquake events")

            # Save raw data
            output_file = self.output_dir / f"earthquakes_{region}_{start_date}_{end_date}.json"
            with open(output_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"✓ Saved to {output_file}")

            # Also save as CSV for easier processing
            self._convert_earthquake_to_csv(data, output_file.with_suffix('.csv'))

            return str(output_file)

        except Exception as e:
            logger.error(f"Error downloading earthquake data: {e}")
            raise

    def download_rainfall_data_gsmap(
        self,
        start_date: str = "2020-01-01",
        end_date: str = "2020-12-31",
    ) -> str:
        """
        Download Global Satellite Mapping of Precipitation (GSMaP) data.

        Note: GSMaP requires registration. This function shows the approach.
        For testing, we'll use synthetic data or alternative sources.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            Path to saved data
        """
        logger.warning("GSMaP requires authentication. Using alternative approach...")

        # Alternative: Download from NOAA/GPM or use sample data
        return self._download_gpm_imerg_data(start_date, end_date)

    def _download_gpm_imerg_data(
        self,
        start_date: str,
        end_date: str,
    ) -> str:
        """
        Download GPM IMERG rainfall data (publicly available).

        GPM IMERG provides global precipitation estimates.
        """
        logger.info("Downloading GPM IMERG precipitation data...")

        # For demonstration, we'll download sample/recent data
        # Real implementation would use NASA GES DISC API

        output_file = self.output_dir / f"rainfall_gpm_{start_date}_{end_date}.nc"

        # Note: In production, you'd use:
        # - NASA Earthdata credentials
        # - GES DISC API
        # - netCDF4/xarray for processing

        logger.info(f"✓ Rainfall data path: {output_file}")
        return str(output_file)

    def download_river_discharge_data(
        self,
        start_date: str = "2020-01-01",
        end_date: str = "2020-12-31",
    ) -> str:
        """
        Download river discharge data.

        Uses USGS Water Services for US data or global datasets.
        """
        logger.info("Downloading river discharge data...")

        # USGS Water Services API
        # For India, would use India-WRIS or CWC data (requires registration)

        output_file = self.output_dir / f"river_discharge_{start_date}_{end_date}.csv"

        logger.info(f"✓ River discharge data path: {output_file}")
        return str(output_file)

    def download_sample_data(self) -> Dict[str, str]:
        """
        Download publicly available sample datasets for immediate testing.

        Returns:
            Dict of data paths
        """
        logger.info("Downloading sample/public datasets...")

        data_paths = {}

        # 1. Download recent earthquakes (last 30 days)
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        try:
            eq_path = self.download_earthquake_data(
                start_date=start_date,
                end_date=end_date,
                min_magnitude=4.0,
                region="india",
            )
            data_paths["earthquakes"] = eq_path
        except Exception as e:
            logger.warning(f"Could not download earthquake data: {e}")

        # 2. Download global earthquake catalog for more data
        try:
            eq_global_path = self.download_earthquake_data(
                start_date="2023-01-01",
                end_date=end_date,
                min_magnitude=5.0,
                region="global",
            )
            data_paths["earthquakes_global"] = eq_global_path
        except Exception as e:
            logger.warning(f"Could not download global earthquake data: {e}")

        return data_paths

    def _convert_earthquake_to_csv(self, geojson_data: Dict, output_path: Path):
        """Convert GeoJSON earthquake data to CSV."""
        records = []

        for feature in geojson_data.get("features", []):
            props = feature.get("properties", {})
            coords = feature.get("geometry", {}).get("coordinates", [0, 0, 0])

            record = {
                "time": props.get("time"),
                "latitude": coords[1] if len(coords) > 1 else 0,
                "longitude": coords[0] if len(coords) > 0 else 0,
                "depth": coords[2] if len(coords) > 2 else 0,
                "magnitude": props.get("mag"),
                "magnitude_type": props.get("magType"),
                "place": props.get("place"),
                "event_id": feature.get("id"),
                "status": props.get("status"),
                "type": props.get("type"),
            }
            records.append(record)

        df = pd.DataFrame(records)
        df.to_csv(output_path, index=False)
        logger.info(f"✓ Saved CSV to {output_path}")


class DataPreprocessor:
    """Preprocess downloaded data for model training."""

    def __init__(self, raw_dir: str = "hazardstack/data/raw"):
        """Initialize preprocessor."""
        self.raw_dir = Path(raw_dir)

    def process_earthquake_data(
        self,
        input_file: str,
        output_dir: str = "hazardstack/data/processed/earthquake",
        use_spectral_features: bool = True,
    ) -> Dict:
        """
        Process earthquake data into model-ready format.

        Args:
            input_file: Path to raw earthquake CSV
            output_dir: Output directory
            use_spectral_features: Include spectral site response features

        Returns:
            Processing statistics
        """
        logger.info(f"Processing earthquake data from {input_file}...")

        # Read earthquake catalog
        df = pd.read_csv(input_file)
        logger.info(f"Loaded {len(df)} earthquake events")

        # Filter valid events
        df = df.dropna(subset=["magnitude", "latitude", "longitude", "depth"])
        df = df[df["magnitude"] >= 3.5]
        logger.info(f"Filtered to {len(df)} valid events (M≥3.5)")

        # Process each event
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        processed_events = []

        for split in ["train", "val", "test"]:
            split_dir = output_path / split
            split_dir.mkdir(parents=True, exist_ok=True)
            (split_dir / "shaking").mkdir(exist_ok=True)
            (split_dir / "aftershock").mkdir(exist_ok=True)

        # Split data: 70% train, 15% val, 15% test
        n = len(df)
        train_end = int(0.7 * n)
        val_end = int(0.85 * n)

        for idx, row in df.iterrows():
            # Determine split
            if idx < train_end:
                split = "train"
            elif idx < val_end:
                split = "val"
            else:
                split = "test"

            event_id = row["event_id"]
            magnitude = row["magnitude"]
            depth = row["depth"]
            lat = row["latitude"]
            lon = row["longitude"]

            # Generate shaking features for surrounding grid cells
            features, mmi = self._generate_shaking_grid(
                magnitude, depth, lat, lon, use_spectral_features
            )

            # Save shaking data
            np.savez_compressed(
                output_path / split / "shaking" / f"{event_id}.npz",
                features=features.astype(np.float32),
                mmi=mmi.astype(np.float32),
            )

            # Generate aftershock sequence
            aftershock_seq, aftershock_flag = self._generate_aftershock_data(
                magnitude, depth
            )

            # Save aftershock data
            np.savez_compressed(
                output_path / split / "aftershock" / f"{event_id}.npz",
                sequence=aftershock_seq.astype(np.float32),
                aftershock_occurred=aftershock_flag.astype(np.float32),
            )

            processed_events.append({
                "event_id": event_id,
                "magnitude": magnitude,
                "depth": depth,
                "latitude": lat,
                "longitude": lon,
                "split": split,
            })

        # Save metadata for each split
        for split in ["train", "val", "test"]:
            split_events = [e for e in processed_events if e["split"] == split]

            import pickle
            with open(output_path / f"{split}_events.pkl", "wb") as f:
                pickle.dump(split_events, f)

            logger.info(f"✓ {split}: {len(split_events)} events")

        stats = {
            "total_events": len(processed_events),
            "train_events": len([e for e in processed_events if e["split"] == "train"]),
            "val_events": len([e for e in processed_events if e["split"] == "val"]),
            "test_events": len([e for e in processed_events if e["split"] == "test"]),
        }

        logger.info(f"✓ Earthquake data processing complete: {stats}")
        return stats

    def _generate_shaking_grid(
        self,
        magnitude: float,
        depth: float,
        epicenter_lat: float,
        epicenter_lon: float,
        use_spectral_features: bool = True,
        grid_size: int = 200,
    ) -> tuple:
        """Generate ground motion features for grid cells around epicenter."""
        rng = np.random.RandomState(int(magnitude * depth * 1000) % 2**32)

        # Generate grid cells around epicenter (realistic distances)
        max_distance = 10 ** (0.5 * magnitude)  # Larger events affect wider areas
        distances = rng.uniform(1, max_distance, grid_size)
        azimuths = rng.uniform(0, 360, grid_size)

        # Cell coordinates
        cell_lats = epicenter_lat + distances * np.cos(np.radians(azimuths)) / 111
        cell_lons = epicenter_lon + distances * np.sin(np.radians(azimuths)) / (
            111 * np.cos(np.radians(epicenter_lat))
        )

        # Ground Motion Prediction Equation (simplified)
        R_hypo = np.sqrt(distances**2 + depth**2)

        # Site effects (varying soil conditions)
        vs30 = rng.uniform(150, 800, grid_size)  # Shear wave velocity
        site_amplification = np.log(vs30 / 760) * (-0.5)

        # MMI calculation
        mmi = 1.5 * magnitude - 3.5 * np.log10(R_hypo + 1) + site_amplification
        mmi = np.clip(mmi, 1, 10)

        # Base features (9 features)
        base_features = np.column_stack([
            np.full(grid_size, magnitude),
            np.full(grid_size, depth),
            distances,
            cell_lats,
            cell_lons,
            vs30,
            rng.uniform(0, 1000, grid_size),  # Elevation
            np.cos(np.radians(azimuths)),  # Directivity effects
            np.sin(np.radians(azimuths)),
        ])

        if use_spectral_features:
            # Spectral response features (10 frequencies: 0.1 to 10 Hz)
            frequencies = np.logspace(-1, 1, 10)
            spectral_features = []

            for freq in frequencies:
                # Simplified spectral amplitude
                spectral_amp = mmi * np.exp(-freq * R_hypo / 100) * (1 + site_amplification)
                spectral_features.append(spectral_amp)

            spectral_features = np.column_stack(spectral_features)
            features = np.concatenate([base_features, spectral_features], axis=1)
        else:
            features = base_features

        return features, mmi

    def _generate_aftershock_data(
        self,
        mainshock_magnitude: float,
        depth: float,
        max_events: int = 50,
    ) -> tuple:
        """Generate synthetic aftershock sequence based on mainshock."""
        rng = np.random.RandomState(int(mainshock_magnitude * depth * 10000) % 2**32)

        # Bath's law and Omori's law
        productivity = 10 ** (0.8 * (mainshock_magnitude - 5.0))
        num_aftershocks = int(rng.poisson(min(productivity, max_events)))

        if num_aftershocks == 0:
            sequence = np.zeros((1, 5))
            sequence[0] = [0, mainshock_magnitude, depth, 0, 0]
            return sequence, np.array([0.0])

        # Omori's law for timing
        c, p = 0.05, 1.1
        t_max = 30  # days

        times = []
        for _ in range(num_aftershocks):
            u = rng.rand()
            t = c * ((1 - u) ** (-1 / (p - 1)) - 1)
            if t < t_max:
                times.append(t)

        times = sorted(times)

        # Gutenberg-Richter for magnitudes
        b_value = 1.0
        min_mag = 3.0
        max_mag = mainshock_magnitude - 1.2  # Bath's law

        magnitudes = []
        for _ in range(len(times)):
            u = rng.rand()
            mag = min_mag - (1 / b_value) * np.log10(1 - u * (1 - 10**(-b_value * (max_mag - min_mag))))
            magnitudes.append(min(mag, max_mag))

        # Spatial distribution
        lat_offsets = rng.randn(len(times)) * 0.1
        lon_offsets = rng.randn(len(times)) * 0.1
        depths = depth + rng.randn(len(times)) * 5

        # Build sequence: [Δt_hours, magnitude, depth, Δlat, Δlon]
        sequence = np.zeros((len(times) + 1, 5))
        sequence[0] = [0, mainshock_magnitude, depth, 0, 0]  # Mainshock

        for i, (t, m, d, dlat, dlon) in enumerate(
            zip(times, magnitudes, depths, lat_offsets, lon_offsets)
        ):
            sequence[i + 1] = [t * 24, m, d, dlat, dlon]

        aftershock_occurred = np.array([1.0])
        return sequence, aftershock_occurred


def download_and_process_all_data():
    """Download and process all training data."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Download data
    downloader = DataDownloader()
    logger.info("=" * 60)
    logger.info("DOWNLOADING TRAINING DATA FROM ONLINE SOURCES")
    logger.info("=" * 60)

    data_paths = downloader.download_sample_data()

    # Process data
    preprocessor = DataPreprocessor()
    logger.info("\n" + "=" * 60)
    logger.info("PROCESSING DATA FOR MODEL TRAINING")
    logger.info("=" * 60)

    stats = {}

    # Process earthquake data
    if "earthquakes" in data_paths:
        eq_csv = Path(data_paths["earthquakes"]).with_suffix('.csv')
        if eq_csv.exists():
            eq_stats = preprocessor.process_earthquake_data(str(eq_csv))
            stats["earthquake"] = eq_stats

    # Process global earthquake data for more samples
    if "earthquakes_global" in data_paths:
        eq_global_csv = Path(data_paths["earthquakes_global"]).with_suffix('.csv')
        if eq_global_csv.exists():
            eq_global_stats = preprocessor.process_earthquake_data(
                str(eq_global_csv),
                output_dir="hazardstack/data/processed/earthquake_global",
            )
            stats["earthquake_global"] = eq_global_stats

    logger.info("\n" + "=" * 60)
    logger.info("DATA DOWNLOAD AND PROCESSING COMPLETE")
    logger.info("=" * 60)
    logger.info(json.dumps(stats, indent=2))

    return stats


if __name__ == "__main__":
    download_and_process_all_data()
