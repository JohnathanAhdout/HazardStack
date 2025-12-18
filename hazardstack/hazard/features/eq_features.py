"""Feature engineering for earthquake impact and aftershock prediction."""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional, Dict

from ..common.spectral_response import (
    SpectralSiteResponse,
    GeologicalProxyEstimator,
    SiteResponseParams,
    compute_directivity_factor,
)


class EarthquakeFeatureBuilder:
    """
    Build features for earthquake shaking estimation and aftershock forecasting.

    For shaking (GMPE-style):
    - Event parameters (magnitude, depth, distance)
    - Site proxy (Vs30 or geology/elevation)

    For aftershock (ETAS/Hawkes-style):
    - Event sequence history
    - Temporal clustering features
    - Spatial clustering features
    """

    def __init__(
        self,
        site_data: Optional[pd.DataFrame] = None,
        region_backgrounds: Optional[Dict] = None,
        use_spectral_response: bool = True,
    ):
        """
        Initialize earthquake feature builder.

        Args:
            site_data: Site characteristics (Vs30, geology) per H3 cell
            region_backgrounds: Background seismicity rates per region
            use_spectral_response: Enable spectral site response features
        """
        self.site_data = site_data
        self.region_backgrounds = region_backgrounds or {}
        self.use_spectral_response = use_spectral_response

        # Initialize spectral response calculators
        if use_spectral_response:
            self.spectral_calc = SpectralSiteResponse()
            self.geo_proxy = GeologicalProxyEstimator()
        else:
            self.spectral_calc = None
            self.geo_proxy = None

    def build_shaking_features(
        self,
        event_magnitude: float,
        event_depth_km: float,
        event_lat: float,
        event_lon: float,
        site_lat: float,
        site_lon: float,
        site_h3: Optional[str] = None,
        site_elevation: Optional[float] = None,
        fault_strike: Optional[float] = None,
    ) -> np.ndarray:
        """
        Build features for ground shaking estimation with spectral site response.

        Args:
            event_magnitude: Earthquake magnitude
            event_depth_km: Focal depth (km)
            event_lat: Event latitude
            event_lon: Event longitude
            site_lat: Site latitude
            site_lon: Site longitude
            site_h3: Optional H3 cell for site lookup
            site_elevation: Site elevation (m) for geological proxy
            fault_strike: Fault strike angle (degrees) for directivity

        Returns:
            Feature vector for MMI prediction (enhanced with spectral features)
        """
        features = []

        # 1. Event parameters
        features.append(event_magnitude)
        features.append(event_depth_km)

        # 2. Distance metrics
        epicentral_dist = self._haversine_distance(
            event_lat, event_lon, site_lat, site_lon
        )
        hypocentral_dist = np.sqrt(epicentral_dist**2 + event_depth_km**2)

        features.append(epicentral_dist)
        features.append(hypocentral_dist)
        features.append(np.log10(hypocentral_dist + 1))  # Log distance

        # 3. Site proxy
        if self.site_data is not None and site_h3 is not None:
            vs30, geology_class = self._get_site_characteristics(site_h3)
        else:
            # Fallback: estimate from elevation
            # Higher elevation in Himalayas -> rock site
            vs30 = self._estimate_vs30_from_location(site_lat, site_lon)
            geology_class = 1 if vs30 > 500 else 0  # 1=rock, 0=soil

        features.append(vs30)
        features.append(geology_class)

        # 4. Geometric spreading factor
        geometric_factor = 1 / (hypocentral_dist + 10)  # Avoid division by zero
        features.append(geometric_factor)

        # 5. Fault-type proxy (if available, else default)
        # In India: mostly thrust faults in Himalayas, strike-slip elsewhere
        is_thrust = 1.0 if event_lat > 25.0 else 0.0  # Simplified
        features.append(is_thrust)

        # 6. SPECTRAL SITE RESPONSE FEATURES (NEW)
        if self.use_spectral_response and self.spectral_calc is not None:
            # Get or estimate site response parameters
            site_params = self._get_site_response_params(
                site_lat, site_lon, site_h3, site_elevation, vs30, geology_class
            )

            # Compute spectral features
            spectral_features = self.spectral_calc.compute_spectral_features(site_params)
            features.extend(spectral_features.tolist())

            # Add directivity effects if fault strike available
            if fault_strike is not None:
                # Estimate rupture length from magnitude (Wells & Coppersmith, 1994)
                rupture_length = 10 ** (event_magnitude * 0.5 - 1.88)  # km
                directivity = compute_directivity_factor(
                    event_lat, event_lon, fault_strike,
                    site_lat, site_lon, rupture_length
                )
            else:
                directivity = 1.0  # No directivity effect

            features.append(directivity)

            # Estimate dominant ground motion frequency based on magnitude and distance
            # Larger events have lower frequency content
            # More distant sites receive lower frequencies (attenuation)
            gm_freq = 5.0 / (1 + 0.5 * event_magnitude) / (1 + hypocentral_dist / 50)
            features.append(gm_freq)

        return np.array(features, dtype=np.float32)

    def build_aftershock_features(
        self,
        mainshock: pd.Series,
        event_sequence: pd.DataFrame,
        current_time: datetime,
        region_id: str,
    ) -> np.ndarray:
        """
        Build features for aftershock probability forecasting.

        Args:
            mainshock: Mainshock event (magnitude, time, location)
            event_sequence: Sequence of all events in region
            current_time: Current time for forecast
            region_id: Seismic region identifier

        Returns:
            Feature vector for aftershock forecasting
        """
        features = []

        # 1. Mainshock parameters
        M_main = mainshock["magnitude"]
        t_since_main = (current_time - mainshock["time"]).total_seconds() / 3600  # hours

        features.append(M_main)
        features.append(mainshock["depth_km"])
        features.append(np.log10(t_since_main + 0.1))  # Log time since mainshock

        # 2. Clustering features (events in past windows)
        n_events_1h = self._count_events_in_window(event_sequence, current_time, hours=1)
        n_events_6h = self._count_events_in_window(event_sequence, current_time, hours=6)
        n_events_24h = self._count_events_in_window(event_sequence, current_time, hours=24)

        features.extend([n_events_1h, n_events_6h, n_events_24h])

        # 3. Magnitude distribution of recent aftershocks
        recent_aftershocks = event_sequence[
            event_sequence["time"] > (current_time - timedelta(hours=24))
        ]

        if len(recent_aftershocks) > 0:
            max_aftershock = recent_aftershocks["magnitude"].max()
            mean_aftershock = recent_aftershocks["magnitude"].mean()
        else:
            max_aftershock = 0.0
            mean_aftershock = 0.0

        features.extend([max_aftershock, mean_aftershock])

        # 4. Omori-law decay proxy
        # λ(t) ∝ 1 / (t + c)^p
        # Use c=0.1 days, p=1.1 (typical values)
        t_days = t_since_main / 24
        omori_intensity = 1 / (t_days + 0.1) ** 1.1

        features.append(omori_intensity)

        # 5. Background seismicity rate
        lambda_0 = self.region_backgrounds.get(region_id, {}).get("rate_per_day", 0.1)
        features.append(lambda_0)

        # 6. Spatial clustering (distance from mainshock)
        if len(recent_aftershocks) > 0:
            # Average distance of aftershocks from mainshock
            distances = [
                self._haversine_distance(
                    mainshock["latitude"],
                    mainshock["longitude"],
                    row["latitude"],
                    row["longitude"],
                )
                for _, row in recent_aftershocks.iterrows()
            ]
            mean_distance = np.mean(distances)
        else:
            mean_distance = 0.0

        features.append(mean_distance)

        return np.array(features, dtype=np.float32)

    def build_event_sequence_for_hawkes(
        self,
        events: pd.DataFrame,
        mainshock_time: datetime,
        max_events: int = 200,
    ) -> np.ndarray:
        """
        Build event sequence input for Neural Hawkes model.

        Args:
            events: Event catalog
            mainshock_time: Mainshock time (t=0 reference)
            max_events: Maximum number of events to include

        Returns:
            Event sequence array [N, 5] with [Δt, M, depth, lat, lon]
        """
        # Sort by time
        events = events.sort_values("time")

        # Compute time since mainshock
        events = events.copy()
        events["delta_t"] = (events["time"] - mainshock_time).dt.total_seconds() / 3600

        # Filter to aftershocks (Δt > 0) and limit
        aftershocks = events[events["delta_t"] > 0].head(max_events)

        if len(aftershocks) == 0:
            # Return dummy event
            return np.zeros((1, 5), dtype=np.float32)

        # Build sequence matrix
        sequence = np.column_stack([
            aftershocks["delta_t"].values,
            aftershocks["magnitude"].values,
            aftershocks["depth_km"].values,
            aftershocks["latitude"].values,
            aftershocks["longitude"].values,
        ])

        return sequence.astype(np.float32)

    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """Calculate Haversine distance in km."""
        R = 6371.0
        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        delta_lat = np.radians(lat2 - lat1)
        delta_lon = np.radians(lon2 - lon1)

        a = (
            np.sin(delta_lat / 2) ** 2
            + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon / 2) ** 2
        )
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

        return R * c

    def _get_site_characteristics(self, h3_cell: str) -> tuple[float, int]:
        """Get Vs30 and geology class for site."""
        if self.site_data is None:
            return 300.0, 0

        site = self.site_data[self.site_data["h3_id"] == h3_cell]

        if len(site) == 0:
            return 300.0, 0

        vs30 = site.iloc[0].get("vs30", 300.0)
        geology = site.iloc[0].get("geology_class", 0)

        return vs30, geology

    def _estimate_vs30_from_location(self, lat: float, lon: float) -> float:
        """Estimate Vs30 from location (rough proxy)."""
        # Himalayas: rock sites (high Vs30)
        if lat > 28.0:
            return 600.0
        # Indo-Gangetic plains: soft soil
        elif 24.0 < lat < 28.0:
            return 200.0
        # Peninsular India: mostly rock
        else:
            return 400.0

    def _get_site_response_params(
        self,
        site_lat: float,
        site_lon: float,
        site_h3: Optional[str],
        site_elevation: Optional[float],
        vs30: float,
        geology_class: int,
    ) -> SiteResponseParams:
        """
        Get or estimate site response parameters.

        Args:
            site_lat: Site latitude
            site_lon: Site longitude
            site_h3: H3 cell ID
            site_elevation: Site elevation (m)
            vs30: Shear wave velocity
            geology_class: Geology classification

        Returns:
            Site response parameters
        """
        # Try to get more detailed data from site database
        sediment_depth = 100.0  # Default
        basin_depth = None
        kappa = 0.03  # Default

        if self.site_data is not None and site_h3 is not None:
            site = self.site_data[self.site_data["h3_id"] == site_h3]
            if len(site) > 0:
                sediment_depth = site.iloc[0].get("sediment_depth", 100.0)
                basin_depth = site.iloc[0].get("basin_depth", None)
                kappa = site.iloc[0].get("kappa", 0.03)

        # If no detailed data, use geological proxy estimator
        if sediment_depth == 100.0 and self.geo_proxy is not None:
            proxy_params = self.geo_proxy.estimate_from_location(
                site_lat, site_lon, site_elevation
            )
            return proxy_params

        # Otherwise, construct from available data
        return SiteResponseParams(
            vs30=vs30,
            sediment_depth=sediment_depth,
            basin_depth=basin_depth,
            kappa=kappa,
            geology_class=geology_class,
        )

    def _count_events_in_window(
        self,
        events: pd.DataFrame,
        current_time: datetime,
        hours: int,
    ) -> int:
        """Count events in time window before current_time."""
        cutoff = current_time - timedelta(hours=hours)
        return len(events[(events["time"] >= cutoff) & (events["time"] < current_time)])

    def get_shaking_feature_names(self) -> List[str]:
        """Get feature names for shaking model."""
        base_features = [
            "magnitude",
            "depth_km",
            "epicentral_dist_km",
            "hypocentral_dist_km",
            "log_hypo_dist",
            "vs30",
            "geology_class",
            "geometric_factor",
            "is_thrust",
        ]

        if self.use_spectral_response:
            # Add spectral response features
            spectral_features = [
                "site_dominant_freq",  # f0
                "amp_0.5hz",  # Amplification at 0.5 Hz
                "amp_1.0hz",  # Amplification at 1.0 Hz
                "amp_2.0hz",  # Amplification at 2.0 Hz
                "amp_5.0hz",  # Amplification at 5.0 Hz
                "amp_10.0hz",  # Amplification at 10.0 Hz
                "basin_flag",  # Basin indicator
                "kappa",  # High-frequency attenuation
                "directivity_factor",  # Rupture directivity
                "gm_dominant_freq",  # Ground motion dominant frequency
            ]
            return base_features + spectral_features
        else:
            return base_features

    def get_aftershock_feature_names(self) -> List[str]:
        """Get feature names for aftershock model."""
        return [
            "M_mainshock",
            "depth_mainshock",
            "log_time_since_main",
            "n_events_1h",
            "n_events_6h",
            "n_events_24h",
            "max_aftershock_M",
            "mean_aftershock_M",
            "omori_intensity",
            "background_rate",
            "mean_distance_km",
        ]
