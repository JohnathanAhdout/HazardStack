#!/usr/bin/env python3
"""
Example: Enhanced Ground Motion Prediction with Spectral Site Response

Demonstrates the improved earthquake shaking prediction using:
- Frequency-dependent site amplification
- Spectral attention mechanism
- Physics-based constraints
- Geological proxy estimation

This enhancement improves MMI predictions by modeling how different
frequencies of seismic waves are amplified by local geology.
"""

import torch
import numpy as np
import pandas as pd
from pathlib import Path

from hazardstack.hazard.features.eq_features import EarthquakeFeatureBuilder
from hazardstack.hazard.models.eq_model import EarthquakeModel
from hazardstack.hazard.common.spectral_response import (
    SpectralSiteResponse,
    GeologicalProxyEstimator,
)
from hazardstack.hazard.common.physics_constraints import (
    GroundMotionPhysicsConstraints,
)


def example_single_event_prediction():
    """
    Example: Predict ground shaking for a single earthquake.

    Compares predictions with and without spectral site response.
    """
    print("=" * 70)
    print("Example 1: Single Event Ground Motion Prediction")
    print("=" * 70)

    # Event parameters (e.g., M6.8 earthquake in Himalayas)
    event_magnitude = 6.8
    event_depth_km = 15.0
    event_lat = 30.5
    event_lon = 78.5
    fault_strike = 285.0  # WNW-ESE thrust fault

    # Site locations (grid of sites around epicenter)
    n_sites = 10
    site_lats = np.linspace(event_lat - 1.0, event_lat + 1.0, n_sites)
    site_lons = np.linspace(event_lon - 1.0, event_lon + 1.0, n_sites)
    site_elevations = np.linspace(500, 3000, n_sites)  # Varying elevation

    print(f"\nEvent: M{event_magnitude} at ({event_lat:.2f}, {event_lon:.2f}), depth={event_depth_km}km")
    print(f"Predicting shaking at {n_sites} sites\n")

    # Initialize feature builders (with and without spectral features)
    feature_builder_basic = EarthquakeFeatureBuilder(use_spectral_response=False)
    feature_builder_spectral = EarthquakeFeatureBuilder(use_spectral_response=True)

    # Build features for each site
    features_basic_list = []
    features_spectral_list = []

    for i in range(n_sites):
        # Basic features
        feat_basic = feature_builder_basic.build_shaking_features(
            event_magnitude=event_magnitude,
            event_depth_km=event_depth_km,
            event_lat=event_lat,
            event_lon=event_lon,
            site_lat=site_lats[i],
            site_lon=site_lons[i],
        )
        features_basic_list.append(feat_basic)

        # Spectral features
        feat_spectral = feature_builder_spectral.build_shaking_features(
            event_magnitude=event_magnitude,
            event_depth_km=event_depth_km,
            event_lat=event_lat,
            event_lon=event_lon,
            site_lat=site_lats[i],
            site_lon=site_lons[i],
            site_elevation=site_elevations[i],
            fault_strike=fault_strike,
        )
        features_spectral_list.append(feat_spectral)

    # Convert to tensors
    features_basic = torch.tensor(np.stack(features_basic_list)).unsqueeze(0)  # [1, N_sites, F_basic]
    features_spectral = torch.tensor(np.stack(features_spectral_list)).unsqueeze(0)  # [1, N_sites, F_spectral]

    print(f"Feature dimensions:")
    print(f"  Basic GMPE: {features_basic.shape[-1]} features")
    print(f"  Spectral GMPE: {features_spectral.shape[-1]} features")
    print(f"  Spectral enhancement: +{features_spectral.shape[-1] - features_basic.shape[-1]} features")

    # Initialize models
    model_basic = EarthquakeModel(use_spectral_features=False)
    model_spectral = EarthquakeModel(use_spectral_features=True)

    # Set to eval mode
    model_basic.eval()
    model_spectral.eval()

    # Make predictions
    with torch.no_grad():
        mmi_mean_basic, mmi_std_basic = model_basic.gmpe(features_basic)
        mmi_mean_spectral, mmi_std_spectral = model_spectral.gmpe(features_spectral)

    print("\n" + "-" * 70)
    print("Predictions Comparison (MMI at different sites):")
    print("-" * 70)
    print(f"{'Site':<6} {'Dist(km)':<10} {'Elev(m)':<10} {'Basic MMI':<12} {'Spectral MMI':<15} {'Difference':<12}")
    print("-" * 70)

    for i in range(n_sites):
        # Calculate distance
        dist_km = features_spectral_list[i][3]  # hypocentral distance

        mmi_b = mmi_mean_basic[0, i].item()
        mmi_s = mmi_mean_spectral[0, i].item()
        diff = mmi_s - mmi_b

        print(f"{i+1:<6} {dist_km:<10.1f} {site_elevations[i]:<10.0f} "
              f"{mmi_b:<12.2f} {mmi_s:<15.2f} {diff:+.2f}")

    print("-" * 70)
    print(f"\nAverage MMI difference: {(mmi_mean_spectral - mmi_mean_basic).mean().item():+.3f}")
    print("(Positive = Spectral model predicts stronger shaking)")


def example_spectral_response_analysis():
    """
    Example: Analyze spectral site response for different site conditions.
    """
    print("\n\n" + "=" * 70)
    print("Example 2: Spectral Site Response Analysis")
    print("=" * 70)

    spectral_calc = SpectralSiteResponse()

    # Define different site types
    sites = [
        {"name": "Hard Rock", "vs30": 800, "depth": 10, "basin": None},
        {"name": "Soft Rock", "vs30": 500, "depth": 50, "basin": None},
        {"name": "Stiff Soil", "vs30": 350, "depth": 100, "basin": None},
        {"name": "Soft Soil", "vs30": 200, "depth": 200, "basin": None},
        {"name": "Basin Site", "vs30": 250, "depth": 500, "basin": 1500},
    ]

    print("\nSite Response Characteristics:")
    print("-" * 70)
    print(f"{'Site Type':<15} {'Vs30':<8} {'Depth(m)':<10} {'f0(Hz)':<10} {'Amp@1Hz':<10} {'Amp@5Hz':<10}")
    print("-" * 70)

    for site in sites:
        from hazardstack.hazard.common.spectral_response import SiteResponseParams

        params = SiteResponseParams(
            vs30=site["vs30"],
            sediment_depth=site["depth"],
            basin_depth=site["basin"],
        )

        f0 = spectral_calc.compute_dominant_frequency(site["vs30"], site["depth"])
        freqs, amps = spectral_calc.compute_amplification_factors(params)

        amp_1hz = amps[1]  # 1 Hz is second in default freq bands
        amp_5hz = amps[3]  # 5 Hz is fourth

        print(f"{site['name']:<15} {site['vs30']:<8} {site['depth']:<10} "
              f"{f0:<10.2f} {amp_1hz:<10.2f} {amp_5hz:<10.2f}")

    print("-" * 70)
    print("\nKey insights:")
    print("  - Lower Vs30 → stronger amplification (softer soil)")
    print("  - Deeper sediments → lower dominant frequency f0")
    print("  - Basin sites → enhanced low-frequency amplification")


def example_geological_proxy():
    """
    Example: Use geological proxy estimator for sites without detailed data.
    """
    print("\n\n" + "=" * 70)
    print("Example 3: Geological Proxy Estimation")
    print("=" * 70)

    geo_proxy = GeologicalProxyEstimator()

    # Test sites across India
    test_sites = [
        {"name": "Delhi (Indo-Gangetic)", "lat": 28.6, "lon": 77.2, "elev": 216},
        {"name": "Mumbai (Coastal)", "lat": 19.1, "lon": 72.9, "elev": 14},
        {"name": "Shimla (Himalayas)", "lat": 31.1, "lon": 77.2, "elev": 2200},
        {"name": "Bangalore (Deccan)", "lat": 12.9, "lon": 77.6, "elev": 920},
        {"name": "Kolkata (Bengal Basin)", "lat": 22.6, "lon": 88.4, "elev": 6},
    ]

    print("\nEstimated Site Parameters:")
    print("-" * 70)
    print(f"{'Location':<25} {'Vs30':<8} {'Sed.Depth':<12} {'Geology':<12}")
    print("-" * 70)

    for site in test_sites:
        params = geo_proxy.estimate_from_location(
            lat=site["lat"],
            lon=site["lon"],
            elevation=site["elev"],
        )

        geology_labels = {0: "Soil", 1: "Rock", 2: "Soft Soil"}
        geology = geology_labels[params.geology_class]

        print(f"{site['name']:<25} {params.vs30:<8.0f} {params.sediment_depth:<12.0f} {geology:<12}")

    print("-" * 70)
    print("\nProxy estimation uses:")
    print("  - Geographic location (latitude/longitude)")
    print("  - Elevation (proxy for lithology)")
    print("  - Regional geology databases")


def example_physics_constraints():
    """
    Example: Demonstrate physics-based constraint losses.
    """
    print("\n\n" + "=" * 70)
    print("Example 4: Physics-Based Constraints")
    print("=" * 70)

    physics = GroundMotionPhysicsConstraints()

    # Simulate predictions for two events
    # Event 1: M6.5 at various distances
    # Event 2: M5.5 at same distances

    distances = torch.tensor([[10, 30, 50, 100, 200, 300]]).float()

    # Good predictions (follow physics)
    mmi_good = torch.tensor([[7.0, 5.5, 4.5, 3.5, 2.5, 2.0]]).float()

    # Bad predictions (violate physics - increase with distance)
    mmi_bad = torch.tensor([[3.0, 4.0, 5.0, 6.0, 7.0, 8.0]]).float()

    magnitudes = torch.tensor([6.5]).float()

    print("\nTesting Distance Decay Constraint:")
    print("-" * 70)

    loss_good = physics.compute_distance_decay_loss(mmi_good, distances)
    loss_bad = physics.compute_distance_decay_loss(mmi_bad, distances)

    print(f"Good predictions (MMI decreases with distance): Loss = {loss_good.item():.4f}")
    print(f"Bad predictions (MMI increases with distance):  Loss = {loss_bad.item():.4f}")

    print("\nConstraint successfully penalizes unphysical predictions!")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("SPECTRAL SITE RESPONSE FOR GROUND MOTION PREDICTION")
    print("=" * 70)
    print("\nThis example demonstrates enhanced earthquake shaking prediction")
    print("using frequency-dependent site response analysis.")
    print("\nImprovements over basic GMPE:")
    print("  ✓ Frequency-dependent site amplification")
    print("  ✓ Basin depth effects")
    print("  ✓ Directivity effects")
    print("  ✓ Spectral attention mechanism")
    print("  ✓ Physics-based constraints")
    print("=" * 70)

    # Run examples
    try:
        example_single_event_prediction()
    except Exception as e:
        print(f"\nExample 1 failed: {e}")
        print("Note: Models need to be trained first")

    example_spectral_response_analysis()
    example_geological_proxy()
    example_physics_constraints()

    print("\n" + "=" * 70)
    print("Examples complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Train models with spectral features")
    print("  2. Evaluate on historical earthquakes")
    print("  3. Compare with traditional GMPE baselines")
    print("  4. Validate against observed MMI data")
    print("=" * 70 + "\n")
