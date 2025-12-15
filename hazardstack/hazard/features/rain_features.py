"""Feature engineering for rain nowcast/forecast."""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import xarray as xr

from hazard.common.time import get_season_embedding, get_monsoon_phase


class RainFeatureBuilder:
    """
    Build physics-guided features for rain prediction.

    Features include:
    - Antecedent Precipitation Index (API)
    - Climatological percentiles
    - Seasonal embeddings
    - Storm motion proxies
    - Accumulation windows
    """

    def __init__(
        self,
        climatology_data: Optional[pd.DataFrame] = None,
        api_decay: float = 0.85,
    ):
        """
        Initialize feature builder.

        Args:
            climatology_data: Historical climatology (mean, percentiles per month/cell)
            api_decay: Decay factor for API (default 0.85)
        """
        self.climatology = climatology_data
        self.api_decay = api_decay

    def build_features(
        self,
        current_rainfall: Dict[str, float],  # h3_cell -> rainfall_rate (mm/h)
        historical_rainfall: pd.DataFrame,  # Past rainfall time series
        timestamp: datetime,
        h3_cell: str,
    ) -> np.ndarray:
        """
        Build feature vector for a single cell at a timestamp.

        Args:
            current_rainfall: Current rainfall rates
            historical_rainfall: Historical data for lookback window
            timestamp: Current timestamp
            h3_cell: H3 cell ID

        Returns:
            Feature vector [D]
        """
        features = []

        # 1. Current rainfall rate
        R_now = current_rainfall.get(h3_cell, 0.0)
        features.append(R_now)

        # 2. Accumulation windows
        accumulations = self._compute_accumulations(
            historical_rainfall, h3_cell, timestamp, windows_hours=[1, 3, 6, 12, 24]
        )
        features.extend(accumulations)

        # 3. Antecedent Precipitation Index (API)
        api_3d = self._compute_api(historical_rainfall, h3_cell, timestamp, days=3)
        api_7d = self._compute_api(historical_rainfall, h3_cell, timestamp, days=7)
        api_14d = self._compute_api(historical_rainfall, h3_cell, timestamp, days=14)
        features.extend([api_3d, api_7d, api_14d])

        # 4. Climatology features
        if self.climatology is not None:
            climo_mean, climo_p95, climo_p99 = self._get_climatology(h3_cell, timestamp.month)
        else:
            climo_mean, climo_p95, climo_p99 = 5.0, 20.0, 40.0  # Fallback

        features.extend([climo_mean, climo_p95, climo_p99])

        # 5. Seasonal embeddings
        season_sin, season_cos = get_season_embedding(timestamp)
        features.extend([season_sin, season_cos])

        # 6. Monsoon phase encoding (one-hot)
        phase = get_monsoon_phase(timestamp)
        phase_encoding = self._encode_monsoon_phase(phase)
        features.extend(phase_encoding)

        # 7. Time of day
        hour = timestamp.hour
        hour_sin = np.sin(2 * np.pi * hour / 24)
        hour_cos = np.cos(2 * np.pi * hour / 24)
        features.extend([hour_sin, hour_cos])

        # 8. Storm motion proxy (simple: change over last hour)
        if len(historical_rainfall) > 1:
            rain_1h_ago = historical_rainfall[
                historical_rainfall["h3_id"] == h3_cell
            ].iloc[-2]["rainfall_rate"]
            storm_tendency = R_now - rain_1h_ago
        else:
            storm_tendency = 0.0

        features.append(storm_tendency)

        return np.array(features, dtype=np.float32)

    def _compute_accumulations(
        self,
        df: pd.DataFrame,
        h3_cell: str,
        timestamp: datetime,
        windows_hours: List[int],
    ) -> List[float]:
        """Compute rainfall accumulation over multiple windows."""
        cell_data = df[df["h3_id"] == h3_cell].sort_values("timestamp")

        accumulations = []

        for window_h in windows_hours:
            cutoff = timestamp - timedelta(hours=window_h)
            window_data = cell_data[cell_data["timestamp"] >= cutoff]

            if len(window_data) > 0:
                # Sum rainfall * dt (assuming hourly data, dt=1h)
                accum = window_data["rainfall_rate"].sum()
            else:
                accum = 0.0

            accumulations.append(accum)

        return accumulations

    def _compute_api(
        self,
        df: pd.DataFrame,
        h3_cell: str,
        timestamp: datetime,
        days: int,
    ) -> float:
        """
        Compute Antecedent Precipitation Index.

        API = Σ (α^i * P_{t-i}) for i=1..days

        where α is decay factor (0.85 typical), P is daily rainfall
        """
        cell_data = df[df["h3_id"] == h3_cell].sort_values("timestamp")

        # Get daily totals for past N days
        cutoff = timestamp - timedelta(days=days)
        past_data = cell_data[cell_data["timestamp"] >= cutoff]

        if len(past_data) == 0:
            return 0.0

        # Group by day
        past_data = past_data.copy()
        past_data["date"] = past_data["timestamp"].dt.date
        daily = past_data.groupby("date")["rainfall_rate"].sum()

        # Compute API
        api = 0.0
        for i, (date, rain) in enumerate(daily.items()):
            days_ago = (timestamp.date() - date).days
            if days_ago > 0:
                api += (self.api_decay ** days_ago) * rain

        return api

    def _get_climatology(self, h3_cell: str, month: int) -> tuple[float, float, float]:
        """Get climatological statistics for cell and month."""
        if self.climatology is None:
            return 5.0, 20.0, 40.0

        clim = self.climatology[
            (self.climatology["h3_id"] == h3_cell) & (self.climatology["month"] == month)
        ]

        if len(clim) == 0:
            return 5.0, 20.0, 40.0

        row = clim.iloc[0]
        return row["mean"], row["p95"], row["p99"]

    def _encode_monsoon_phase(self, phase: str) -> List[float]:
        """One-hot encode monsoon phase."""
        phases = ["pre_monsoon", "southwest_monsoon", "post_monsoon", "winter"]
        encoding = [1.0 if p == phase else 0.0 for p in phases]
        return encoding

    def get_feature_names(self) -> List[str]:
        """Get feature names for logging/debugging."""
        names = [
            "R_now",
            "R_acc_1h",
            "R_acc_3h",
            "R_acc_6h",
            "R_acc_12h",
            "R_acc_24h",
            "API_3d",
            "API_7d",
            "API_14d",
            "climo_mean",
            "climo_p95",
            "climo_p99",
            "season_sin",
            "season_cos",
            "phase_pre_monsoon",
            "phase_sw_monsoon",
            "phase_post_monsoon",
            "phase_winter",
            "hour_sin",
            "hour_cos",
            "storm_tendency",
        ]
        return names


def build_climatology_from_imd(
    imd_data: xr.Dataset,
    h3_cells: List[str],
    years: range = range(1981, 2011),  # WMO standard: 1981-2010
) -> pd.DataFrame:
    """
    Build climatology statistics from IMD long-term data.

    Args:
        imd_data: IMD gridded rainfall dataset
        h3_cells: List of H3 cells
        years: Years to use for climatology

    Returns:
        DataFrame with climatology per cell and month
    """
    import h3

    climatology = []

    for cell in h3_cells:
        lat, lon = h3.h3_to_geo(cell)

        # Extract time series for this location
        # (simplified - in practice, interpolate from grid)
        lat_idx = np.abs(imd_data.lat.values - lat).argmin()
        lon_idx = np.abs(imd_data.lon.values - lon).argmin()

        ts = imd_data.rainfall.sel(lat=imd_data.lat[lat_idx], lon=imd_data.lon[lon_idx])

        # Group by month and compute statistics
        for month in range(1, 13):
            month_data = ts[ts["time"].dt.month == month]

            if len(month_data) > 0:
                climatology.append({
                    "h3_id": cell,
                    "month": month,
                    "mean": float(month_data.mean()),
                    "std": float(month_data.std()),
                    "p50": float(month_data.quantile(0.5)),
                    "p75": float(month_data.quantile(0.75)),
                    "p90": float(month_data.quantile(0.9)),
                    "p95": float(month_data.quantile(0.95)),
                    "p99": float(month_data.quantile(0.99)),
                })

    return pd.DataFrame(climatology)
