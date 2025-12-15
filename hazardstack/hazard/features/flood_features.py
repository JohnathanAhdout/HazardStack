"""Feature engineering for flood prediction."""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from hazard.common.geo import BasinGraph


class FloodFeatureBuilder:
    """
    Build physics-guided features for flood prediction.

    Features include:
    - Basin-aggregated rainfall
    - Antecedent Precipitation Index (basin-wide)
    - Upstream accumulation
    - Gauge observations (if available)
    - Basin static descriptors
    """

    def __init__(
        self,
        basin_graph: BasinGraph,
        basin_descriptors: Optional[pd.DataFrame] = None,
        api_decay: float = 0.85,
    ):
        """
        Initialize flood feature builder.

        Args:
            basin_graph: River basin topology
            basin_descriptors: Static basin features (area, slope, etc.)
            api_decay: Decay factor for API
        """
        self.basin_graph = basin_graph
        self.basin_descriptors = basin_descriptors
        self.api_decay = api_decay

    def build_features(
        self,
        basin_id: str,
        timestamp: datetime,
        rainfall_by_cell: Dict[str, float],  # h3_cell -> rainfall
        cell_to_basin: Dict[str, str],  # h3_cell -> basin_id
        historical_rainfall: pd.DataFrame,
        gauge_data: Optional[pd.DataFrame] = None,
    ) -> np.ndarray:
        """
        Build feature vector for a basin.

        Args:
            basin_id: Basin identifier
            timestamp: Current timestamp
            rainfall_by_cell: Current rainfall by cell
            cell_to_basin: Mapping of cells to basins
            historical_rainfall: Historical rainfall time series
            gauge_data: Optional gauge discharge/level data

        Returns:
            Feature vector [D]
        """
        features = []

        # 1. Basin-aggregated current rainfall
        basin_rain_now = self._aggregate_rainfall_to_basin(
            basin_id, rainfall_by_cell, cell_to_basin
        )
        features.append(basin_rain_now)

        # 2. Rainfall accumulation windows (basin-averaged)
        accumulations = self._compute_basin_accumulations(
            basin_id,
            timestamp,
            historical_rainfall,
            cell_to_basin,
            windows_hours=[6, 12, 24, 48, 72],
        )
        features.extend(accumulations)

        # 3. Antecedent Precipitation Index (basin-wide)
        api_7d = self._compute_basin_api(
            basin_id, timestamp, historical_rainfall, cell_to_basin, days=7
        )
        api_14d = self._compute_basin_api(
            basin_id, timestamp, historical_rainfall, cell_to_basin, days=14
        )
        api_30d = self._compute_basin_api(
            basin_id, timestamp, historical_rainfall, cell_to_basin, days=30
        )
        features.extend([api_7d, api_14d, api_30d])

        # 4. Upstream rainfall accumulation
        upstream_rain = self._compute_upstream_rainfall(
            basin_id, timestamp, historical_rainfall, cell_to_basin, window_hours=24
        )
        features.append(upstream_rain)

        # 5. Gauge observations (if available)
        if gauge_data is not None:
            gauge_features = self._extract_gauge_features(basin_id, timestamp, gauge_data)
        else:
            gauge_features = [0.0, 0.0, 0.0]  # discharge, level, trend

        features.extend(gauge_features)

        # 6. Static basin descriptors
        if self.basin_descriptors is not None:
            static_features = self._get_basin_descriptors(basin_id)
        else:
            static_features = [100.0, 500.0, 0.5]  # area, elev, slope fallback

        features.extend(static_features)

        # 7. Temporal features
        hour = timestamp.hour
        hour_sin = np.sin(2 * np.pi * hour / 24)
        hour_cos = np.cos(2 * np.pi * hour / 24)

        day_of_year = timestamp.timetuple().tm_yday
        season_sin = np.sin(2 * np.pi * day_of_year / 365.25)
        season_cos = np.cos(2 * np.pi * day_of_year / 365.25)

        features.extend([hour_sin, hour_cos, season_sin, season_cos])

        return np.array(features, dtype=np.float32)

    def _aggregate_rainfall_to_basin(
        self,
        basin_id: str,
        rainfall_by_cell: Dict[str, float],
        cell_to_basin: Dict[str, str],
    ) -> float:
        """Area-weighted rainfall aggregation for basin."""
        basin_cells = [cell for cell, basin in cell_to_basin.items() if basin == basin_id]

        if not basin_cells:
            return 0.0

        # Simple average (in production, use area-weighted)
        total_rain = sum(rainfall_by_cell.get(cell, 0.0) for cell in basin_cells)
        return total_rain / len(basin_cells)

    def _compute_basin_accumulations(
        self,
        basin_id: str,
        timestamp: datetime,
        historical_rainfall: pd.DataFrame,
        cell_to_basin: Dict[str, str],
        windows_hours: List[int],
    ) -> List[float]:
        """Compute basin-aggregated accumulations."""
        basin_cells = [cell for cell, basin in cell_to_basin.items() if basin == basin_id]

        accumulations = []

        for window_h in windows_hours:
            cutoff = timestamp - timedelta(hours=window_h)
            window_data = historical_rainfall[
                (historical_rainfall["timestamp"] >= cutoff)
                & (historical_rainfall["h3_id"].isin(basin_cells))
            ]

            if len(window_data) > 0:
                # Average over basin
                accum = window_data.groupby("timestamp")["rainfall_rate"].mean().sum()
            else:
                accum = 0.0

            accumulations.append(accum)

        return accumulations

    def _compute_basin_api(
        self,
        basin_id: str,
        timestamp: datetime,
        historical_rainfall: pd.DataFrame,
        cell_to_basin: Dict[str, str],
        days: int,
    ) -> float:
        """Compute basin-wide Antecedent Precipitation Index."""
        basin_cells = [cell for cell, basin in cell_to_basin.items() if basin == basin_id]

        cutoff = timestamp - timedelta(days=days)
        past_data = historical_rainfall[
            (historical_rainfall["timestamp"] >= cutoff)
            & (historical_rainfall["h3_id"].isin(basin_cells))
        ]

        if len(past_data) == 0:
            return 0.0

        # Group by date and average over basin
        past_data = past_data.copy()
        past_data["date"] = past_data["timestamp"].dt.date
        daily = past_data.groupby("date")["rainfall_rate"].mean()

        # Compute API
        api = 0.0
        for date, rain in daily.items():
            days_ago = (timestamp.date() - date).days
            if days_ago > 0:
                api += (self.api_decay ** days_ago) * rain

        return api

    def _compute_upstream_rainfall(
        self,
        basin_id: str,
        timestamp: datetime,
        historical_rainfall: pd.DataFrame,
        cell_to_basin: Dict[str, str],
        window_hours: int,
    ) -> float:
        """Compute rainfall in upstream basins."""
        upstream_basins = self.basin_graph.get_upstream_basins(basin_id, recursive=True)

        if not upstream_basins:
            return 0.0

        # Get all cells in upstream basins
        upstream_cells = [
            cell for cell, basin in cell_to_basin.items() if basin in upstream_basins
        ]

        cutoff = timestamp - timedelta(hours=window_hours)
        upstream_data = historical_rainfall[
            (historical_rainfall["timestamp"] >= cutoff)
            & (historical_rainfall["h3_id"].isin(upstream_cells))
        ]

        if len(upstream_data) > 0:
            return upstream_data.groupby("timestamp")["rainfall_rate"].mean().sum()
        else:
            return 0.0

    def _extract_gauge_features(
        self,
        basin_id: str,
        timestamp: datetime,
        gauge_data: pd.DataFrame,
    ) -> List[float]:
        """Extract gauge-based features."""
        basin_gauges = gauge_data[gauge_data["basin_id"] == basin_id]

        if len(basin_gauges) == 0:
            return [0.0, 0.0, 0.0]

        latest = basin_gauges.iloc[-1]

        discharge = latest.get("discharge_m3s", 0.0)
        level = latest.get("level_m", 0.0)

        # Compute trend (change over last 6 hours)
        if len(basin_gauges) >= 2:
            prev = basin_gauges.iloc[-7] if len(basin_gauges) >= 7 else basin_gauges.iloc[0]
            trend = discharge - prev.get("discharge_m3s", discharge)
        else:
            trend = 0.0

        return [discharge, level, trend]

    def _get_basin_descriptors(self, basin_id: str) -> List[float]:
        """Get static basin features."""
        if self.basin_descriptors is None:
            return [100.0, 500.0, 0.5]

        desc = self.basin_descriptors[self.basin_descriptors["basin_id"] == basin_id]

        if len(desc) == 0:
            return [100.0, 500.0, 0.5]

        row = desc.iloc[0]
        area = row.get("area_km2", 100.0)
        elev = row.get("mean_elevation_m", 500.0)
        slope = row.get("mean_slope", 0.5)

        return [area, elev, slope]

    def get_feature_names(self) -> List[str]:
        """Get feature names."""
        return [
            "basin_rain_now",
            "basin_acc_6h",
            "basin_acc_12h",
            "basin_acc_24h",
            "basin_acc_48h",
            "basin_acc_72h",
            "API_7d",
            "API_14d",
            "API_30d",
            "upstream_rain_24h",
            "gauge_discharge",
            "gauge_level",
            "gauge_trend",
            "area_km2",
            "mean_elevation_m",
            "mean_slope",
            "hour_sin",
            "hour_cos",
            "season_sin",
            "season_cos",
        ]
