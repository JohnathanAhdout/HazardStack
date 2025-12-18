"""
Spectral site response analysis for frequency-dependent ground motion amplification.

This module implements physics-based transfer functions and site amplification
factors based on geological proxies, without requiring real-time waveform data.
"""

import numpy as np
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class SiteResponseParams:
    """Parameters for site response calculation."""

    vs30: float  # Shear wave velocity in top 30m (m/s)
    sediment_depth: float  # Depth to bedrock (m)
    basin_depth: Optional[float] = None  # Basin depth (m) if in basin
    kappa: float = 0.03  # High-frequency attenuation parameter (s)
    geology_class: int = 0  # 0=soil, 1=rock, 2=soft_soil


class SpectralSiteResponse:
    """
    Compute frequency-dependent site amplification factors.

    Based on established seismological relationships:
    - Boore & Atkinson (2008) site response
    - Basin amplification effects (Day et al., 2008)
    - Quarter-wavelength approximation for resonance
    """

    # Reference frequencies for spectral analysis (Hz)
    FREQ_BANDS = np.array([0.5, 1.0, 2.0, 5.0, 10.0])

    # Reference Vs30 for rock site (m/s)
    VS30_ROCK = 760.0

    def __init__(self):
        """Initialize spectral site response calculator."""
        pass

    def compute_dominant_frequency(self, vs30: float, sediment_depth: float) -> float:
        """
        Compute site dominant frequency using quarter-wavelength approximation.

        f0 = Vs / (4 * H)
        where Vs is average shear wave velocity, H is sediment depth

        Args:
            vs30: Shear wave velocity (m/s)
            sediment_depth: Depth to bedrock (m)

        Returns:
            Dominant frequency (Hz)
        """
        if sediment_depth < 1.0:
            # Rock site - high frequency
            return 10.0

        # Approximate average Vs as Vs30 for shallow sites
        # For deep sites, adjust for velocity gradient
        if sediment_depth > 100:
            vs_avg = vs30 * 1.2  # Velocity increases with depth
        else:
            vs_avg = vs30

        f0 = vs_avg / (4.0 * sediment_depth)

        # Clip to reasonable range
        return np.clip(f0, 0.1, 20.0)

    def compute_amplification_factors(
        self,
        params: SiteResponseParams,
        frequencies: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute frequency-dependent amplification factors.

        Args:
            params: Site response parameters
            frequencies: Frequency array (Hz). If None, uses default bands.

        Returns:
            Tuple of (frequencies, amplification_factors)
        """
        if frequencies is None:
            frequencies = self.FREQ_BANDS

        # 1. Linear site amplification (Boore & Atkinson 2008 style)
        # F_lin = (Vs30_ref / Vs30)^0.25 for low frequencies
        vs_ratio = self.VS30_ROCK / params.vs30
        linear_amp = vs_ratio ** 0.25

        # 2. Frequency-dependent term
        # Amplification peaks near resonance frequency
        f0 = self.compute_dominant_frequency(params.vs30, params.sediment_depth)

        # Gaussian-like peak around f0
        freq_factor = np.exp(-0.5 * ((np.log(frequencies / f0)) / 0.6) ** 2)

        # 3. High-frequency attenuation (kappa effect)
        # A(f) = exp(-π * kappa * f)
        kappa_atten = np.exp(-np.pi * params.kappa * frequencies)

        # 4. Basin amplification for low frequencies
        if params.basin_depth is not None and params.basin_depth > 200:
            # Basin amplifies long-period (low-frequency) motions
            basin_factor = 1.0 + 0.5 * np.exp(-frequencies / 0.5) * (params.basin_depth / 1000)
        else:
            basin_factor = 1.0

        # 5. Combine factors
        amplification = linear_amp * (1.0 + freq_factor) * kappa_atten * basin_factor

        # 6. Nonlinear soil response (reduces amplification for soft soils at high shaking)
        # This would normally depend on input ground motion, but we use conservative estimate
        if params.vs30 < 300:
            # Soft soil - apply nonlinear reduction
            nl_factor = 0.7 + 0.3 * (params.vs30 / 300)
            amplification *= nl_factor

        return frequencies, amplification

    def compute_spectral_features(
        self,
        params: SiteResponseParams,
    ) -> np.ndarray:
        """
        Compute spectral features for neural network input.

        Returns fixed-length feature vector for model input.

        Args:
            params: Site response parameters

        Returns:
            Feature vector [f0, A_0.5Hz, A_1Hz, A_2Hz, A_5Hz, A_10Hz, basin_flag, kappa]
        """
        freqs, amps = self.compute_amplification_factors(params)

        f0 = self.compute_dominant_frequency(params.vs30, params.sediment_depth)
        basin_flag = 1.0 if params.basin_depth and params.basin_depth > 200 else 0.0

        features = np.array([
            f0,  # Dominant frequency
            *amps,  # Amplification at 5 frequency bands
            basin_flag,  # Basin indicator
            params.kappa,  # High-frequency attenuation
        ], dtype=np.float32)

        return features

    def estimate_mmi_modification(
        self,
        base_mmi: float,
        params: SiteResponseParams,
        dominant_freq: float = 2.0,  # Frequency of peak ground motion
    ) -> float:
        """
        Estimate MMI modification due to site effects.

        Args:
            base_mmi: Base MMI on rock
            params: Site response parameters
            dominant_freq: Dominant frequency of ground motion (Hz)

        Returns:
            Modified MMI accounting for site amplification
        """
        _, amps = self.compute_amplification_factors(params)

        # Find amplification closest to dominant frequency
        freq_idx = np.argmin(np.abs(self.FREQ_BANDS - dominant_freq))
        amp_factor = amps[freq_idx]

        # Convert amplification to MMI increment
        # MMI scales roughly as log10(PGA)
        # Amplification is linear in PGA
        mmi_increment = np.log10(amp_factor) * 3.0  # Empirical scaling

        # Clip to reasonable bounds
        mmi_increment = np.clip(mmi_increment, -1.0, 2.0)

        return base_mmi + mmi_increment


class GeologicalProxyEstimator:
    """
    Estimate geological parameters from available data.

    For use when detailed site data is unavailable, estimates from:
    - Geographic location
    - Elevation
    - Regional geology databases
    """

    def __init__(self):
        """Initialize proxy estimator."""
        # Regional sediment depth estimates for major Indian basins
        self.basin_sediment_depths = {
            'indo_gangetic': 2500.0,  # Deep alluvial basin
            'bengal': 3000.0,  # Very deep sediments
            'kutch': 1500.0,  # Gujarat sedimentary basin
            'coastal_plains': 500.0,  # Thin coastal sediments
            'deccan': 50.0,  # Peninsular shield - thin cover
            'himalayan_foothill': 1000.0,  # Intermontane basins
        }

    def estimate_from_location(
        self,
        lat: float,
        lon: float,
        elevation: Optional[float] = None,
    ) -> SiteResponseParams:
        """
        Estimate site response parameters from location.

        Args:
            lat: Latitude
            lon: Longitude
            elevation: Elevation (m), if available

        Returns:
            Estimated site response parameters
        """
        # Determine region and geology
        region, geology_class = self._classify_region(lat, lon, elevation)

        # Estimate Vs30
        vs30 = self._estimate_vs30(lat, lon, elevation, geology_class)

        # Estimate sediment depth
        sediment_depth = self.basin_sediment_depths.get(region, 100.0)

        # Basin depth (only for major basins)
        basin_depth = None
        if region in ['indo_gangetic', 'bengal', 'kutch']:
            basin_depth = sediment_depth

        # Kappa (attenuation parameter)
        # Higher for soft soils, lower for rock
        if vs30 < 300:
            kappa = 0.04
        elif vs30 < 500:
            kappa = 0.03
        else:
            kappa = 0.02

        return SiteResponseParams(
            vs30=vs30,
            sediment_depth=sediment_depth,
            basin_depth=basin_depth,
            kappa=kappa,
            geology_class=geology_class,
        )

    def _classify_region(
        self,
        lat: float,
        lon: float,
        elevation: Optional[float],
    ) -> Tuple[str, int]:
        """
        Classify geographic region and geology class.

        Returns:
            Tuple of (region_name, geology_class)
            geology_class: 0=soil, 1=rock, 2=soft_soil
        """
        # Himalayas and mountains
        if lat > 28.0:
            if elevation and elevation > 2000:
                return 'himalayan_foothill', 1  # Rock
            else:
                return 'himalayan_foothill', 0  # Intermontane valleys

        # Indo-Gangetic Plains
        if 24.0 < lat < 28.0 and 75.0 < lon < 88.0:
            return 'indo_gangetic', 2  # Soft soil

        # Bengal Basin
        if 21.0 < lat < 26.0 and 88.0 < lon < 92.0:
            return 'bengal', 2  # Very soft soil

        # Kutch Basin
        if 22.5 < lat < 24.5 and 69.0 < lon < 71.5:
            return 'kutch', 0  # Sedimentary

        # Coastal plains
        if elevation and elevation < 50:
            return 'coastal_plains', 0  # Soil

        # Deccan Plateau (default for peninsular India)
        return 'deccan', 1  # Hard rock

    def _estimate_vs30(
        self,
        lat: float,
        lon: float,
        elevation: Optional[float],
        geology_class: int,
    ) -> float:
        """
        Estimate Vs30 from location and geology.

        Args:
            lat: Latitude
            lon: Longitude
            elevation: Elevation (m)
            geology_class: Geology classification

        Returns:
            Estimated Vs30 (m/s)
        """
        # Base values by geology class
        if geology_class == 1:  # Rock
            base_vs30 = 600.0
        elif geology_class == 2:  # Soft soil
            base_vs30 = 200.0
        else:  # Regular soil
            base_vs30 = 300.0

        # Adjust for elevation (proxy for compaction/lithology)
        if elevation is not None:
            if elevation > 1000:
                base_vs30 *= 1.3  # Mountain rock
            elif elevation < 10:
                base_vs30 *= 0.9  # Low-lying soft sediments

        # Add some regional variation
        # Indo-Gangetic Plains: softer
        if 24.0 < lat < 28.0 and 75.0 < lon < 88.0:
            base_vs30 *= 0.85

        return np.clip(base_vs30, 150.0, 1500.0)


def compute_directivity_factor(
    source_lat: float,
    source_lon: float,
    source_strike: float,
    site_lat: float,
    site_lon: float,
    rupture_length_km: float,
) -> float:
    """
    Compute directivity amplification factor.

    Sites in the direction of rupture propagation experience stronger shaking.

    Args:
        source_lat: Earthquake latitude
        source_lon: Earthquake longitude
        source_strike: Fault strike angle (degrees from north)
        site_lat: Site latitude
        site_lon: Site longitude
        rupture_length_km: Rupture length

    Returns:
        Directivity factor (1.0 = no effect, >1 = amplification)
    """
    # Compute azimuth from source to site
    dlat = site_lat - source_lat
    dlon = site_lon - source_lon
    azimuth = np.degrees(np.arctan2(dlon, dlat))

    # Angle between rupture direction and site azimuth
    # Rupture propagates along strike
    angle_diff = abs(azimuth - source_strike)
    angle_diff = min(angle_diff, 360 - angle_diff)  # Use acute angle

    # Maximum directivity effect along strike direction
    # Falls off with angle
    directivity = 1.0 + 0.3 * np.cos(np.radians(angle_diff)) * min(rupture_length_km / 50, 1.0)

    return directivity
