"""Feature engineering for rain nowcast/forecast."""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import xarray as xr

from hazard.common.time import get_season_embedding, get_monsoon_phase
from hazard.features.gravity_wave_detector import GravityWaveDetector


class RainFeatureBuilder:
    """
    Build physics-guided features for rain prediction.

    Features include:
    - Antecedent Precipitation Index (API)
    - Climatological percentiles
    - Seasonal embeddings
    - Storm motion proxies
    - Accumulation windows
    - Atmospheric Gravity Wave signatures (NEW OPTIMIZATION)
    """

    def __init__(
        self,
        climatology_data: Optional[pd.DataFrame] = None,
        api_decay: float = 0.85,
        enable_gravity_waves: bool = True,
    ):
        """
        Initialize feature builder.

        Args:
            climatology_data: Historical climatology (mean, percentiles per month/cell)
            api_decay: Decay factor for API (default 0.85)
            enable_gravity_waves: Enable atmospheric gravity wave detection (default True)
        """
        self.climatology = climatology_data
        self.api_decay = api_decay
        self.enable_gravity_waves = enable_gravity_waves

        # Initialize gravity wave detector
        if self.enable_gravity_waves:
            self.gw_detector = GravityWaveDetector()
        else:
            self.gw_detector = None

    def build_features(
        self,
        current_rainfall: Dict[str, float],  # h3_cell -> rainfall_rate (mm/h)
        historical_rainfall: pd.DataFrame,  # Past rainfall time series
        timestamp: datetime,
        h3_cell: str,
        meteorological_data: Optional[Dict[str, any]] = None,  # Weather data for GW detection
    ) -> np.ndarray:
        """
        Build feature vector for a single cell at a timestamp.

        Args:
            current_rainfall: Current rainfall rates
            historical_rainfall: Historical data for lookback window
            timestamp: Current timestamp
            h3_cell: H3 cell ID
            meteorological_data: Optional dict containing temperature, pressure, wind data
                for gravity wave detection. Keys:
                - 'temperature': current temp (K)
                - 'pressure': current pressure (hPa)
                - 'temperature_history': np.ndarray of past temps
                - 'pressure_history': np.ndarray of past pressures
                - 'timestamp_history': np.ndarray of timestamps
                - 'cape': Convective Available Potential Energy (J/kg)
                - 'cloud_top': Cloud top height (m)
                - 'u_wind', 'v_wind', 'w_wind': Wind components (m/s)

        Returns:
            Feature vector [D] - now includes 11 additional gravity wave features
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

        # 9. ATMOSPHERIC GRAVITY WAVE FEATURES (NEW OPTIMIZATION)
        if self.enable_gravity_waves and self.gw_detector is not None:
            gw_features = self._extract_gravity_wave_features(
                R_now, timestamp, meteorological_data
            )
            features.extend(gw_features)

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

    def _extract_gravity_wave_features(
        self,
        precipitation_rate: float,
        timestamp: datetime,
        meteorological_data: Optional[Dict] = None,
    ) -> List[float]:
        """
        Extract atmospheric gravity wave features.

        Args:
            precipitation_rate: Current rainfall rate (mm/h)
            timestamp: Current timestamp
            meteorological_data: Dict with temperature, pressure, wind data

        Returns:
            List of 11 gravity wave features
        """
        if meteorological_data is None:
            # Generate synthetic meteorological data based on rainfall
            # In production, this would come from weather data sources
            meteorological_data = self._generate_synthetic_weather_data(
                precipitation_rate, timestamp
            )

        # Extract all gravity wave features
        gw_feat_dict = self.gw_detector.extract_features(
            temperature=meteorological_data.get('temperature', 288.15),
            pressure=meteorological_data.get('pressure', 1013.25),
            temperature_history=meteorological_data.get('temperature_history'),
            pressure_history=meteorological_data.get('pressure_history'),
            timestamp_history=meteorological_data.get('timestamp_history'),
            precipitation_rate=precipitation_rate,
            u_wind=meteorological_data.get('u_wind'),
            v_wind=meteorological_data.get('v_wind'),
            w_wind=meteorological_data.get('w_wind'),
            cape=meteorological_data.get('cape', 0.0),
            cloud_top=meteorological_data.get('cloud_top', 5000.0),
            height=meteorological_data.get('height', 0.0),
        )

        # Return features in consistent order
        feature_names = self.gw_detector.get_feature_names()
        return [gw_feat_dict[name] for name in feature_names]

    def _generate_synthetic_weather_data(
        self,
        precipitation_rate: float,
        timestamp: datetime,
    ) -> Dict:
        """
        Generate synthetic meteorological data for gravity wave detection.

        This is a fallback for when real weather data is not available.
        In production, replace with actual weather API/model data.

        Args:
            precipitation_rate: Current rainfall (mm/h)
            timestamp: Current timestamp

        Returns:
            Dict with synthetic weather parameters
        """
        import random
        random.seed(int(timestamp.timestamp()))

        # Base temperature varies with season and time of day
        season_temp = 288.15 + 10 * np.sin(2 * np.pi * timestamp.month / 12)
        diurnal_temp = 5 * np.cos(2 * np.pi * timestamp.hour / 24)
        base_temp = season_temp + diurnal_temp

        # Rainfall correlates with lower pressure and temperature variations
        pressure_anomaly = -precipitation_rate * 0.5  # Heavy rain = low pressure
        base_pressure = 1013.25 + pressure_anomaly

        # Generate time series (last 12 hours, hourly)
        n_steps = 12
        temps = np.zeros(n_steps)
        pressures = np.zeros(n_steps)
        timestamps_unix = np.zeros(n_steps)

        for i in range(n_steps):
            hours_ago = n_steps - i - 1
            past_time = timestamp - timedelta(hours=hours_ago)

            # Temperature with realistic variations
            past_season = 288.15 + 10 * np.sin(2 * np.pi * past_time.month / 12)
            past_diurnal = 5 * np.cos(2 * np.pi * past_time.hour / 24)
            temps[i] = past_season + past_diurnal + random.gauss(0, 1.5)

            # Pressure with gravity wave oscillations
            wave_period = 45  # minutes
            wave_amplitude = 1.5  # hPa
            wave_phase = 2 * np.pi * hours_ago * 60 / wave_period
            pressures[i] = base_pressure + wave_amplitude * np.sin(wave_phase) + random.gauss(0, 0.5)

            timestamps_unix[i] = past_time.timestamp()

        # CAPE increases with instability (higher with rainfall)
        cape = min(precipitation_rate * 100, 2500)

        # Cloud top height increases with precipitation intensity
        cloud_top = 5000 + min(precipitation_rate * 300, 10000)

        # Synthetic wind data (simple model)
        u_wind = np.random.randn(n_steps) * 5 + precipitation_rate * 0.5
        v_wind = np.random.randn(n_steps) * 5
        w_wind = np.random.randn(n_steps) * 0.5 + precipitation_rate * 0.1

        return {
            'temperature': temps[-1],
            'pressure': pressures[-1],
            'temperature_history': temps,
            'pressure_history': pressures,
            'timestamp_history': timestamps_unix,
            'cape': cape,
            'cloud_top': cloud_top,
            'u_wind': u_wind,
            'v_wind': v_wind,
            'w_wind': w_wind,
            'height': 0.0,
        }

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

        # Add gravity wave features if enabled
        if self.enable_gravity_waves and self.gw_detector is not None:
            names.extend(self.gw_detector.get_feature_names())

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
