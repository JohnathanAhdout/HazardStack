"""Synthetic data generation for testing and development."""

import torch
import numpy as np
from pathlib import Path
import pickle
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class SyntheticDataGenerator:
    """Generate realistic synthetic data for hazard models."""

    def __init__(self, seed: int = 42):
        """Initialize generator with random seed."""
        self.rng = np.random.RandomState(seed)
        torch.manual_seed(seed)

    def generate_rain_data(
        self,
        num_samples: int = 1000,
        num_timesteps: int = 12,
        num_cells: int = 100,
        feature_dim: int = 20,
        output_dir: str = "data/synthetic/rain",
    ) -> Dict:
        """
        Generate synthetic rain data.

        Args:
            num_samples: Number of training samples
            num_timesteps: Timesteps in input window
            num_cells: Number of spatial cells
            feature_dim: Feature dimension
            output_dir: Output directory

        Returns:
            Metadata dict
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Generating {num_samples} synthetic rain samples...")

        samples = []
        for i in range(num_samples):
            # Generate spatiotemporal features with realistic patterns
            # Add spatial correlation and temporal evolution
            features = self._generate_spatiotemporal_features(
                num_timesteps, num_cells, feature_dim
            )

            # Generate mask (simulate missing data ~5%)
            mask = self.rng.rand(num_timesteps, num_cells, feature_dim) > 0.05

            # Generate targets for different horizons
            # Rainfall accumulation and exceedance
            targets = self._generate_rain_targets(features)

            # Save to disk
            sample_id = f"rain_sample_{i:06d}"
            np.savez_compressed(
                output_path / f"features/{sample_id}.npz",
                features=features.astype(np.float32),
                mask=mask.astype(np.float32),
                **targets,
            )

            samples.append({
                "sample_id": sample_id,
                "timestamp": f"2020-01-01T{i % 24:02d}:00:00",
            })

        # Save metadata
        metadata = {
            "samples": samples,
            "cell_list": [f"cell_{i}" for i in range(num_cells)],
            "num_samples": num_samples,
            "num_timesteps": num_timesteps,
            "num_cells": num_cells,
            "feature_dim": feature_dim,
        }

        return metadata

    def generate_flood_data(
        self,
        num_samples: int = 800,
        num_timesteps: int = 72,
        num_basins: int = 50,
        feature_dim: int = 15,
        output_dir: str = "data/synthetic/flood",
    ) -> Dict:
        """
        Generate synthetic flood data.

        Args:
            num_samples: Number of samples
            num_timesteps: Timesteps in window
            num_basins: Number of river basins
            feature_dim: Feature dimension
            output_dir: Output directory

        Returns:
            Metadata dict
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Generating {num_samples} synthetic flood samples...")

        # Generate basin topology (directed graph: upstream -> downstream)
        adjacency = self._generate_basin_topology(num_basins)

        samples = []
        for i in range(num_samples):
            # Generate features with flow propagation
            features = self._generate_basin_features(
                num_timesteps, num_basins, feature_dim, adjacency
            )

            mask = self.rng.rand(num_timesteps, num_basins, feature_dim) > 0.03

            # Generate flood exceedance targets
            targets = self._generate_flood_targets(features, adjacency)

            sample_id = f"flood_sample_{i:06d}"
            np.savez_compressed(
                output_path / f"features/{sample_id}.npz",
                features=features.astype(np.float32),
                mask=mask.astype(np.float32),
                adjacency=adjacency.astype(np.float32),
                **targets,
            )

            samples.append({
                "sample_id": sample_id,
                "timestamp": f"2020-01-{(i % 28) + 1:02d}T00:00:00",
            })

        metadata = {
            "samples": samples,
            "basin_list": [f"basin_{i}" for i in range(num_basins)],
            "num_samples": num_samples,
            "num_basins": num_basins,
            "adjacency": adjacency,
        }

        return metadata

    def generate_earthquake_data(
        self,
        num_events: int = 500,
        num_cells_per_event: int = 200,
        output_dir: str = "data/synthetic/earthquake",
    ) -> Dict:
        """
        Generate synthetic earthquake data.

        Args:
            num_events: Number of earthquake events
            num_cells_per_event: Spatial cells per event
            output_dir: Output directory

        Returns:
            Metadata dict
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Generating {num_events} synthetic earthquake events...")

        events = []
        for i in range(num_events):
            # Event parameters
            magnitude = 4.0 + self.rng.exponential(1.5)  # M4+
            magnitude = min(magnitude, 8.0)
            depth = self.rng.uniform(5, 50)  # km
            epicenter_lat = self.rng.uniform(20, 30)
            epicenter_lon = self.rng.uniform(75, 85)

            # Generate shaking intensity features for cells
            features, mmi = self._generate_shaking_features(
                magnitude, depth, epicenter_lat, epicenter_lon, num_cells_per_event
            )

            # Save shaking data
            event_id = f"eq_event_{i:06d}"
            shaking_dir = output_path / "shaking"
            shaking_dir.mkdir(parents=True, exist_ok=True)

            np.savez_compressed(
                shaking_dir / f"{event_id}.npz",
                features=features.astype(np.float32),
                mmi=mmi.astype(np.float32),
            )

            # Generate aftershock sequence
            aftershock_seq, aftershock_occurred = self._generate_aftershock_sequence(
                magnitude, depth
            )

            aftershock_dir = output_path / "aftershock"
            aftershock_dir.mkdir(parents=True, exist_ok=True)

            np.savez_compressed(
                aftershock_dir / f"{event_id}.npz",
                sequence=aftershock_seq.astype(np.float32),
                aftershock_occurred=aftershock_occurred.astype(np.float32),
            )

            events.append({
                "event_id": event_id,
                "magnitude": magnitude,
                "depth": depth,
                "latitude": epicenter_lat,
                "longitude": epicenter_lon,
            })

        metadata = {
            "events": events,
            "num_events": num_events,
        }

        return metadata

    def _generate_spatiotemporal_features(
        self, num_timesteps: int, num_cells: int, feature_dim: int
    ) -> np.ndarray:
        """Generate realistic spatiotemporal features with correlations."""
        features = np.zeros((num_timesteps, num_cells, feature_dim))

        # Create spatial correlation structure
        spatial_coords = self.rng.rand(num_cells, 2) * 10  # 2D coordinates
        spatial_dist = np.sum(
            (spatial_coords[:, None, :] - spatial_coords[None, :, :]) ** 2, axis=-1
        )
        spatial_cov = np.exp(-spatial_dist / 2.0)

        # Generate correlated features over space and time
        for t in range(num_timesteps):
            for d in range(feature_dim):
                # Temporal evolution + spatial correlation
                if t == 0:
                    base = self.rng.randn(num_cells)
                else:
                    # AR(1) temporal dynamics
                    base = 0.8 * features[t - 1, :, d] + 0.2 * self.rng.randn(num_cells)

                # Apply spatial smoothing
                features[t, :, d] = spatial_cov @ base / spatial_cov.sum(axis=1)

        # Add some features that represent rainfall intensity, humidity, etc.
        features = np.abs(features) * 10  # Scale appropriately

        return features

    def _generate_rain_targets(self, features: np.ndarray) -> Dict:
        """Generate rain accumulation and exceedance targets."""
        targets = {}
        num_cells = features.shape[1]

        horizons = ["1h", "6h", "12h", "24h"]

        for horizon in horizons:
            # Accumulation: use last timestep features as proxy
            intensity = features[-1, :, 0]  # Use first feature as rainfall proxy

            # Gamma distribution parameters for accumulation
            shape = 2.0 + self.rng.rand(num_cells) * 3.0
            rate = 1.0 / (intensity + 1.0)  # Rate inversely related to intensity

            targets[f"target_{horizon}_accum_shape"] = shape
            targets[f"target_{horizon}_accum_rate"] = rate

            # Exceedance probability (binary for extreme rainfall)
            threshold = 50  # mm
            exceedance = (intensity > threshold).astype(np.float32)
            targets[f"target_{horizon}_exceed"] = exceedance

        return targets

    def _generate_basin_topology(self, num_basins: int) -> np.ndarray:
        """Generate realistic river basin topology as directed graph."""
        adjacency = np.zeros((num_basins, num_basins))

        # Create tree-like structure (river network)
        for i in range(1, num_basins):
            # Each basin flows to a downstream basin
            parent = self.rng.randint(0, i)
            adjacency[i, parent] = 1  # i flows into parent

        # Add some lateral connections
        num_lateral = num_basins // 10
        for _ in range(num_lateral):
            i, j = self.rng.choice(num_basins, 2, replace=False)
            adjacency[i, j] = 1

        # Add self-loops
        adjacency += np.eye(num_basins)

        return adjacency

    def _generate_basin_features(
        self,
        num_timesteps: int,
        num_basins: int,
        feature_dim: int,
        adjacency: np.ndarray,
    ) -> np.ndarray:
        """Generate basin features with flow propagation."""
        features = np.zeros((num_timesteps, num_basins, feature_dim))

        # Initialize with upstream rainfall
        features[0] = self.rng.rand(num_basins, feature_dim) * 10

        # Propagate flow downstream over time
        for t in range(1, num_timesteps):
            # Temporal evolution
            features[t] = 0.9 * features[t - 1] + 0.1 * self.rng.randn(
                num_basins, feature_dim
            )

            # Flow propagation (simple diffusion)
            flow = adjacency @ features[t] / (adjacency.sum(axis=1, keepdims=True) + 1e-6)
            features[t] = 0.7 * features[t] + 0.3 * flow

        return np.abs(features) * 5

    def _generate_flood_targets(
        self, features: np.ndarray, adjacency: np.ndarray
    ) -> Dict:
        """Generate flood exceedance targets."""
        targets = {}
        num_basins = features.shape[1]

        # Aggregate features along basin network
        network_influence = (adjacency > 0).sum(axis=0)  # Upstream basins
        discharge_proxy = features[-1, :, 0] * (1 + 0.1 * network_influence)

        horizons = ["12h", "24h"]
        for horizon in horizons:
            # Exceedance probability
            threshold = np.percentile(discharge_proxy, 75)
            exceedance = (discharge_proxy > threshold).astype(np.float32)
            targets[f"target_{horizon}"] = exceedance

        return targets

    def _generate_shaking_features(
        self,
        magnitude: float,
        depth: float,
        epicenter_lat: float,
        epicenter_lon: float,
        num_cells: int,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Generate ground shaking features and MMI values."""
        # Generate cell locations around epicenter
        distances = self.rng.exponential(20, num_cells)  # km
        azimuths = self.rng.uniform(0, 360, num_cells)

        cell_lats = epicenter_lat + distances * np.cos(np.radians(azimuths)) / 111
        cell_lons = epicenter_lon + distances * np.sin(np.radians(azimuths)) / (
            111 * np.cos(np.radians(epicenter_lat))
        )

        # Compute MMI using simplified attenuation
        # MMI ≈ 1.5 * M - 3.5 * log10(R) + site_effects
        R = np.sqrt(distances**2 + depth**2)  # Hypocentral distance
        site_effects = self.rng.randn(num_cells) * 0.5

        mmi = 1.5 * magnitude - 3.5 * np.log10(R + 1) + site_effects
        mmi = np.clip(mmi, 1, 10)

        # Features: [magnitude, depth, distance, lat, lon, vs30, elevation, ...]
        # Including spectral response features (10 additional)
        base_features = np.column_stack([
            np.full(num_cells, magnitude),
            np.full(num_cells, depth),
            distances,
            cell_lats,
            cell_lons,
            self.rng.uniform(150, 800, num_cells),  # Vs30 (site condition)
            self.rng.uniform(0, 1000, num_cells),  # Elevation
            self.rng.randn(num_cells),  # Azimuth effects
            self.rng.rand(num_cells),  # Basin depth
        ])

        # Add spectral response features (10 frequencies)
        spectral_features = np.column_stack([
            mmi[:, None] * self.rng.uniform(0.8, 1.2, (num_cells, 10))
        ])

        features = np.concatenate([base_features, spectral_features], axis=1)

        return features, mmi

    def _generate_aftershock_sequence(
        self, mainshock_magnitude: float, depth: float, max_events: int = 50
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Generate aftershock sequence using Omori's law."""
        # Productivity (number of aftershocks)
        productivity = 10 ** (mainshock_magnitude - 5.0)
        num_aftershocks = int(self.rng.poisson(productivity))
        num_aftershocks = min(num_aftershocks, max_events)

        if num_aftershocks == 0:
            # No aftershocks
            sequence = np.zeros((1, 5))
            sequence[0] = [0, mainshock_magnitude, depth, 0, 0]
            return sequence, np.array([0.0])

        # Generate aftershock times (Omori's law)
        c = 0.05  # days
        p = 1.1
        t_max = 30  # days

        times = []
        for _ in range(num_aftershocks):
            u = self.rng.rand()
            t = c * ((1 - u) ** (-1 / (p - 1)) - 1)
            if t < t_max:
                times.append(t)

        times = sorted(times)

        # Generate magnitudes (Gutenberg-Richter)
        b_value = 1.0
        min_mag = 3.0
        max_mag = mainshock_magnitude - 1.0

        magnitudes = []
        for _ in range(len(times)):
            u = self.rng.rand()
            mag = min_mag - (1 / b_value) * np.log10(u)
            mag = min(mag, max_mag)
            magnitudes.append(mag)

        # Generate locations (near mainshock)
        lat_offsets = self.rng.randn(len(times)) * 0.1
        lon_offsets = self.rng.randn(len(times)) * 0.1
        depths = depth + self.rng.randn(len(times)) * 5

        # Build sequence: [Δt, magnitude, depth, Δlat, Δlon]
        sequence = np.zeros((len(times) + 1, 5))

        # Mainshock
        sequence[0] = [0, mainshock_magnitude, depth, 0, 0]

        # Aftershocks
        for i, (t, m, d, dlat, dlon) in enumerate(
            zip(times, magnitudes, depths, lat_offsets, lon_offsets)
        ):
            dt = t * 24  # Convert to hours
            sequence[i + 1] = [dt, m, d, dlat, dlon]

        aftershock_occurred = np.array([1.0])  # At least one aftershock

        return sequence, aftershock_occurred


def create_synthetic_datasets(output_base: str = "hazardstack/data/synthetic"):
    """Create all synthetic datasets for training."""
    generator = SyntheticDataGenerator(seed=42)

    # Create directories
    base_path = Path(output_base)
    base_path.mkdir(parents=True, exist_ok=True)

    # Generate rain data
    logger.info("Generating rain datasets...")
    for split, num_samples in [("train", 1000), ("val", 200), ("test", 200)]:
        rain_dir = base_path / "rain" / split / "features"
        rain_dir.mkdir(parents=True, exist_ok=True)

        metadata = generator.generate_rain_data(
            num_samples=num_samples,
            output_dir=str(base_path / "rain" / split),
        )

        with open(base_path / "rain" / f"{split}_metadata.pkl", "wb") as f:
            pickle.dump(metadata, f)

    # Generate flood data
    logger.info("Generating flood datasets...")
    for split, num_samples in [("train", 800), ("val", 150), ("test", 150)]:
        flood_dir = base_path / "flood" / split / "features"
        flood_dir.mkdir(parents=True, exist_ok=True)

        metadata = generator.generate_flood_data(
            num_samples=num_samples,
            output_dir=str(base_path / "flood" / split),
        )

        with open(base_path / "flood" / f"{split}_metadata.pkl", "wb") as f:
            pickle.dump(metadata, f)

    # Generate earthquake data
    logger.info("Generating earthquake datasets...")
    for split, num_events in [("train", 500), ("val", 100), ("test", 100)]:
        eq_dir = base_path / "earthquake" / split
        eq_dir.mkdir(parents=True, exist_ok=True)

        metadata = generator.generate_earthquake_data(
            num_events=num_events,
            output_dir=str(base_path / "earthquake" / split),
        )

        with open(base_path / "earthquake" / f"{split}_events.pkl", "wb") as f:
            pickle.dump(metadata["events"], f)

    logger.info(f"✓ All synthetic datasets created in {output_base}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_synthetic_datasets()
