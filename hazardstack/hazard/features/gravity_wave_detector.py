"""
Atmospheric Gravity Wave Detection for Precipitation Forecasting.

Based on peer-reviewed research:
- Machine Learning Emulation of Gravity Wave Drag (Chantry et al., 2021)
- Gravity Wave Parameterization in Climate Models (Espinosa et al., 2022)
- Atmospheric Gravity Wave Detection Methods (Frontiers, 2022)
- Realistic Simulation of Tropical Atmospheric Gravity Waves (NCBI, 2020)

Atmospheric gravity waves (not to be confused with gravitational waves from space-time)
are buoyancy oscillations in the atmosphere caused by disturbances like mountains,
convection, or weather fronts. They manifest as ripples in the atmosphere that affect:
- Air pressure perturbations
- Temperature oscillations
- Vertical wind patterns
- Cloud formation (lenticular clouds)

These waves are critical precursors to convective precipitation and extreme rainfall events.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import warnings


class GravityWaveDetector:
    """
    Detect and characterize atmospheric gravity waves from meteorological data.

    Implements physics-based detection methods validated in:
    - GPS radio occultation studies
    - Weather radar Doppler velocity analysis
    - Satellite temperature perturbation methods
    - Ground-based atmospheric radar measurements
    """

    # Physical constants
    G = 9.81  # Gravitational acceleration (m/s²)
    R_d = 287.05  # Gas constant for dry air (J/(kg·K))
    C_p = 1004.0  # Specific heat at constant pressure (J/(kg·K))
    GAMMA = 0.0098  # Atmospheric lapse rate (K/m)

    def __init__(
        self,
        reference_pressure: float = 1013.25,  # hPa (sea level)
        reference_temp: float = 288.15,  # K (15°C)
        wave_period_range: Tuple[float, float] = (10, 120),  # minutes
        wavelength_range: Tuple[float, float] = (10, 1000),  # km
    ):
        """
        Initialize gravity wave detector.

        Args:
            reference_pressure: Reference pressure for perturbation calculations (hPa)
            reference_temp: Reference temperature for perturbation calculations (K)
            wave_period_range: Min/max wave periods to detect (minutes)
            wavelength_range: Min/max horizontal wavelengths (km)
        """
        self.p_ref = reference_pressure
        self.T_ref = reference_temp
        self.period_min, self.period_max = wave_period_range
        self.wl_min, self.wl_max = wavelength_range

    def compute_brunt_vaisala_frequency(
        self,
        temperature: float,  # K
        pressure: float,  # hPa
        height: float = 0.0,  # meters above sea level
    ) -> float:
        """
        Compute Brunt-Väisälä frequency (N²), the fundamental parameter for
        atmospheric wave propagation.

        N² = (g/θ) * dθ/dz

        where θ is potential temperature and z is height.

        This frequency determines whether the atmosphere can support
        vertical wave propagation. Positive N² indicates stable stratification
        where gravity waves can propagate.

        Args:
            temperature: Air temperature (K)
            pressure: Atmospheric pressure (hPa)
            height: Height above sea level (m)

        Returns:
            N² value (1/s²). Typical range: 1e-5 to 1e-3
        """
        # Potential temperature: θ = T * (p0/p)^(R/Cp)
        theta = temperature * (1000.0 / pressure) ** (self.R_d / self.C_p)

        # Approximate vertical gradient using standard atmosphere
        # dθ/dz ≈ (θ/T) * (g/Cp)
        dtheta_dz = (theta / temperature) * (self.G / self.C_p)

        # Brunt-Väisälä frequency squared
        N_squared = (self.G / theta) * dtheta_dz

        return max(N_squared, 0.0)  # Ensure non-negative

    def detect_temperature_perturbations(
        self,
        temperature_series: np.ndarray,  # Time series of temps (K)
        timestamps: np.ndarray,  # Unix timestamps
        detrend: bool = True,
    ) -> Dict[str, float]:
        """
        Detect gravity waves from temperature perturbations.

        Method based on satellite AIRS measurements (NCBI/PMC research).
        Temperature oscillations are a primary signature of gravity waves.

        Args:
            temperature_series: Temperature time series (K)
            timestamps: Corresponding timestamps
            detrend: Remove linear trend before analysis

        Returns:
            Dictionary containing:
                - amplitude: Temperature perturbation amplitude (K)
                - variance: Temperature variance (K²)
                - dominant_period: Dominant oscillation period (minutes)
                - wave_energy: Relative wave energy metric
        """
        if len(temperature_series) < 3:
            return {'amplitude': 0.0, 'variance': 0.0, 'dominant_period': 0.0, 'wave_energy': 0.0}

        T = temperature_series.copy()

        # Remove mean and trend
        if detrend:
            time_idx = np.arange(len(T))
            coeffs = np.polyfit(time_idx, T, 1)
            trend = np.polyval(coeffs, time_idx)
            T_prime = T - trend
        else:
            T_prime = T - np.mean(T)

        # Perturbation amplitude (RMS)
        amplitude = np.sqrt(np.mean(T_prime**2))
        variance = np.var(T_prime)

        # Estimate dominant period using autocorrelation
        if len(T_prime) > 5:
            autocorr = np.correlate(T_prime, T_prime, mode='full')[len(T_prime)-1:]
            autocorr = autocorr / autocorr[0]  # Normalize

            # Find first minimum (half period)
            peaks = []
            for i in range(1, min(len(autocorr)-1, 20)):
                if autocorr[i-1] > autocorr[i] < autocorr[i+1]:
                    peaks.append(i)

            if peaks:
                half_period_idx = peaks[0]
                time_step = np.median(np.diff(timestamps)) / 60  # Convert to minutes
                dominant_period = 2 * half_period_idx * time_step
            else:
                dominant_period = 0.0
        else:
            dominant_period = 0.0

        # Wave energy (normalized by mean temperature)
        mean_T = np.mean(temperature_series)
        if mean_T > 0:
            wave_energy = variance / mean_T
        else:
            wave_energy = 0.0

        return {
            'amplitude': float(amplitude),
            'variance': float(variance),
            'dominant_period': float(dominant_period),
            'wave_energy': float(wave_energy)
        }

    def detect_pressure_perturbations(
        self,
        pressure_series: np.ndarray,  # hPa
        timestamps: np.ndarray,
    ) -> Dict[str, float]:
        """
        Detect gravity waves from atmospheric pressure perturbations.

        Ground-based pressure measurements are excellent gravity wave indicators.
        Research shows pressure perturbations correlate with convective activity.

        Args:
            pressure_series: Pressure time series (hPa)
            timestamps: Corresponding timestamps

        Returns:
            Dictionary containing:
                - amplitude: Pressure perturbation amplitude (hPa)
                - tendency: Pressure tendency (hPa/hour)
                - oscillation_strength: Strength of periodic oscillations
        """
        if len(pressure_series) < 3:
            return {'amplitude': 0.0, 'tendency': 0.0, 'oscillation_strength': 0.0}

        P = pressure_series.copy()

        # Remove linear trend
        time_idx = np.arange(len(P))
        coeffs = np.polyfit(time_idx, P, 1)
        trend = np.polyval(coeffs, time_idx)
        P_prime = P - trend

        # Perturbation amplitude
        amplitude = np.sqrt(np.mean(P_prime**2))

        # Pressure tendency (rate of change)
        if len(timestamps) > 1:
            dt = (timestamps[-1] - timestamps[0]) / 3600  # hours
            if dt > 0:
                dp = P[-1] - P[0]
                tendency = dp / dt
            else:
                tendency = 0.0
        else:
            tendency = 0.0

        # Oscillation strength (high-frequency variance)
        if len(P_prime) > 4:
            diffs = np.diff(P_prime)
            oscillation_strength = np.std(diffs)
        else:
            oscillation_strength = 0.0

        return {
            'amplitude': float(amplitude),
            'tendency': float(tendency),
            'oscillation_strength': float(oscillation_strength)
        }

    def compute_wave_momentum_flux(
        self,
        u_wind: np.ndarray,  # Zonal wind (m/s)
        v_wind: np.ndarray,  # Meridional wind (m/s)
        w_wind: np.ndarray,  # Vertical wind (m/s)
    ) -> float:
        """
        Compute gravity wave momentum flux.

        Momentum flux = ρ * <u'w'> where u' and w' are wind perturbations.
        This is a key parameter in gravity wave parameterization schemes.

        Based on WaveNet ML research and ECMWF IFS gravity wave parameterizations.

        Args:
            u_wind: Zonal (east-west) wind component (m/s)
            v_wind: Meridional (north-south) wind component (m/s)
            w_wind: Vertical wind component (m/s)

        Returns:
            Momentum flux magnitude (m²/s²)
        """
        if len(u_wind) < 2 or len(w_wind) < 2:
            return 0.0

        # Remove mean to get perturbations
        u_prime = u_wind - np.mean(u_wind)
        v_prime = v_wind - np.mean(v_wind)
        w_prime = w_wind - np.mean(w_wind)

        # Compute momentum flux components
        # <u'w'> in zonal direction
        uw_flux = np.mean(u_prime * w_prime)

        # <v'w'> in meridional direction
        vw_flux = np.mean(v_prime * w_prime)

        # Total momentum flux magnitude
        momentum_flux = np.sqrt(uw_flux**2 + vw_flux**2)

        return float(momentum_flux)

    def estimate_convective_gravity_wave_source(
        self,
        precipitation_rate: float,  # mm/hour
        convective_available_potential_energy: float,  # CAPE, J/kg
        cloud_top_height: float,  # meters
    ) -> float:
        """
        Estimate gravity wave generation from convection.

        Based on research showing gravity waves in tropics are primarily
        generated by moist convective activity. Uses precipitation as a
        proxy for convective source strength.

        Reference: "Realistic Simulation of Tropical Atmospheric Gravity Waves
        Using Radar-Observed Precipitation Rate and Echo Top Height" (NCBI, 2020)

        Args:
            precipitation_rate: Current rainfall rate (mm/hour)
            convective_available_potential_energy: CAPE (J/kg)
            cloud_top_height: Height of cloud top (meters)

        Returns:
            Source term strength (dimensionless, 0-1 scale)
        """
        # Normalize precipitation rate (typical range 0-50 mm/h)
        precip_factor = min(precipitation_rate / 50.0, 1.0)

        # CAPE factor (typical range 0-3000 J/kg)
        cape_factor = min(convective_available_potential_energy / 3000.0, 1.0)

        # Cloud height factor (higher clouds = stronger waves)
        # Typical convective cloud tops: 5-15 km
        height_factor = min(cloud_top_height / 15000.0, 1.0)

        # Combined source term (geometric mean for balance)
        source_strength = (precip_factor * cape_factor * height_factor) ** (1/3)

        return float(source_strength)

    def compute_wave_activity_flux(
        self,
        temperature_perturbation: float,  # K
        pressure_perturbation: float,  # hPa
        wind_divergence: float,  # 1/s
    ) -> float:
        """
        Compute wave activity flux density.

        Wave activity flux represents the propagation of wave energy and
        is used in modern gravity wave parameterizations.

        Args:
            temperature_perturbation: Temperature anomaly (K)
            pressure_perturbation: Pressure anomaly (hPa)
            wind_divergence: Horizontal wind divergence (1/s)

        Returns:
            Wave activity flux (normalized, 0-1 scale)
        """
        # Normalize perturbations
        T_norm = abs(temperature_perturbation) / 5.0  # Typical GW: 1-5 K
        P_norm = abs(pressure_perturbation) / 2.0  # Typical GW: 0.5-2 hPa
        div_norm = abs(wind_divergence) / 1e-4  # Typical: 1e-5 to 1e-4

        # Combined flux (average of normalized components)
        flux = (T_norm + P_norm + div_norm) / 3.0

        return float(min(flux, 1.0))

    def extract_features(
        self,
        temperature: float,  # Current temperature (K)
        pressure: float,  # Current pressure (hPa)
        temperature_history: Optional[np.ndarray] = None,  # Last N temps
        pressure_history: Optional[np.ndarray] = None,  # Last N pressures
        timestamp_history: Optional[np.ndarray] = None,  # Timestamps
        precipitation_rate: float = 0.0,  # mm/hour
        u_wind: Optional[np.ndarray] = None,  # Zonal wind series (m/s)
        v_wind: Optional[np.ndarray] = None,  # Meridional wind series (m/s)
        w_wind: Optional[np.ndarray] = None,  # Vertical wind series (m/s)
        cape: float = 0.0,  # J/kg
        cloud_top: float = 5000.0,  # meters
        height: float = 0.0,  # meters above sea level
    ) -> Dict[str, float]:
        """
        Extract all gravity wave features for machine learning.

        This is the main interface for integrating gravity wave detection
        into the rain prediction model.

        Args:
            temperature: Current temperature (K)
            pressure: Current pressure (hPa)
            temperature_history: Time series of temperatures
            pressure_history: Time series of pressures
            timestamp_history: Corresponding timestamps (Unix time)
            precipitation_rate: Current rainfall rate (mm/hour)
            u_wind: Zonal wind time series (m/s)
            v_wind: Meridional wind time series (m/s)
            w_wind: Vertical wind time series (m/s)
            cape: Convective Available Potential Energy (J/kg)
            cloud_top: Cloud top height (m)
            height: Altitude above sea level (m)

        Returns:
            Dictionary of gravity wave features (11 total features)
        """
        features = {}

        # 1. Brunt-Väisälä frequency (atmospheric stability)
        N_squared = self.compute_brunt_vaisala_frequency(temperature, pressure, height)
        features['gw_buoyancy_frequency'] = float(np.sqrt(max(N_squared, 0)))

        # 2-5. Temperature perturbation features
        if temperature_history is not None and len(temperature_history) > 2:
            temp_features = self.detect_temperature_perturbations(
                temperature_history,
                timestamp_history if timestamp_history is not None else np.arange(len(temperature_history))
            )
            features['gw_temp_amplitude'] = temp_features['amplitude']
            features['gw_temp_variance'] = temp_features['variance']
            features['gw_dominant_period'] = temp_features['dominant_period']
            features['gw_temp_energy'] = temp_features['wave_energy']
        else:
            features['gw_temp_amplitude'] = 0.0
            features['gw_temp_variance'] = 0.0
            features['gw_dominant_period'] = 0.0
            features['gw_temp_energy'] = 0.0

        # 6-8. Pressure perturbation features
        if pressure_history is not None and len(pressure_history) > 2:
            pres_features = self.detect_pressure_perturbations(
                pressure_history,
                timestamp_history if timestamp_history is not None else np.arange(len(pressure_history))
            )
            features['gw_pressure_amplitude'] = pres_features['amplitude']
            features['gw_pressure_tendency'] = pres_features['tendency']
            features['gw_pressure_oscillation'] = pres_features['oscillation_strength']
        else:
            features['gw_pressure_amplitude'] = 0.0
            features['gw_pressure_tendency'] = 0.0
            features['gw_pressure_oscillation'] = 0.0

        # 9. Momentum flux (if wind data available)
        if u_wind is not None and v_wind is not None and w_wind is not None:
            if len(u_wind) > 1 and len(w_wind) > 1:
                features['gw_momentum_flux'] = self.compute_wave_momentum_flux(u_wind, v_wind, w_wind)
            else:
                features['gw_momentum_flux'] = 0.0
        else:
            features['gw_momentum_flux'] = 0.0

        # 10. Convective source term
        features['gw_convective_source'] = self.estimate_convective_gravity_wave_source(
            precipitation_rate, cape, cloud_top
        )

        # 11. Wave activity indicator
        # Use current perturbations from reference values
        T_pert = temperature - self.T_ref
        P_pert = pressure - self.p_ref
        # Approximate divergence from pressure tendency (simple proxy)
        if pressure_history is not None and len(pressure_history) > 1:
            div_approx = abs(pressure_history[-1] - pressure_history[-2]) / 1000.0
        else:
            div_approx = 0.0
        features['gw_wave_activity'] = self.compute_wave_activity_flux(T_pert, P_pert, div_approx)

        return features

    def get_feature_names(self) -> List[str]:
        """Get list of all gravity wave feature names."""
        return [
            'gw_buoyancy_frequency',  # Brunt-Väisälä N
            'gw_temp_amplitude',  # Temperature perturbation RMS
            'gw_temp_variance',  # Temperature variance
            'gw_dominant_period',  # Dominant wave period
            'gw_temp_energy',  # Normalized wave energy from temp
            'gw_pressure_amplitude',  # Pressure perturbation RMS
            'gw_pressure_tendency',  # Pressure rate of change
            'gw_pressure_oscillation',  # High-frequency pressure variations
            'gw_momentum_flux',  # Vertical momentum flux
            'gw_convective_source',  # Convective wave generation
            'gw_wave_activity',  # Combined wave activity metric
        ]
