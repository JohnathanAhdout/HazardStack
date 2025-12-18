# Spectral Site Response Optimization for Earthquake Predictions

## Overview

This document describes the optimization of earthquake ground motion predictions using **frequency-dependent site response analysis** and **spectral attention mechanisms**. This enhancement improves Modified Mercalli Intensity (MMI) predictions by modeling how seismic waves of different frequencies interact with local geological conditions.

## Scientific Background

### Why Spectral Site Response?

Traditional Ground Motion Prediction Equations (GMPEs) use simple site proxies like Vs30 (shear wave velocity in top 30m) to characterize site effects. However, **site amplification is inherently frequency-dependent**:

1. **Soft soils amplify low-frequency waves** (0.5-2 Hz) due to resonance
2. **Shallow sediments amplify high-frequency waves** (5-10 Hz)
3. **Deep basins** trap and amplify long-period motion
4. **High-frequency attenuation** (kappa effect) varies by geology

### Physics-Based Features

Our optimization adds these physics-informed features:

| Feature | Description | Physics Basis |
|---------|-------------|---------------|
| **Site Dominant Frequency (f₀)** | Resonance frequency of sediment column | f₀ = Vs / (4H) quarter-wavelength |
| **Amplification @ 0.5-10 Hz** | Frequency-dependent amplification factors | Transfer function from bedrock to surface |
| **Basin Flag** | Deep basin indicator | Basin depth > 200m shows long-period amplification |
| **Kappa (κ)** | High-frequency attenuation | Anelastic attenuation in shallow crust |
| **Directivity Factor** | Rupture propagation effects | Sites in rupture direction see stronger shaking |
| **GM Dominant Frequency** | Expected ground motion frequency | Larger/distant events → lower frequency |

## Implementation Architecture

### 1. Spectral Site Response Module (`spectral_response.py`)

Core functionality for site response calculations:

```python
from hazardstack.hazard.common.spectral_response import SpectralSiteResponse

spectral = SpectralSiteResponse()

# Compute site response
params = SiteResponseParams(vs30=300, sediment_depth=200, basin_depth=500)
frequencies, amplifications = spectral.compute_amplification_factors(params)

# Get features for neural network
features = spectral.compute_spectral_features(params)
# Returns: [f0, amp_0.5Hz, amp_1Hz, ..., basin_flag, kappa]
```

**Key Components:**
- **Quarter-wavelength approximation** for dominant frequency
- **Boore & Atkinson (2008)** style linear amplification
- **Gaussian resonance peak** around f₀
- **Kappa attenuation** for high frequencies
- **Basin amplification** for low frequencies

### 2. Geological Proxy Estimator

Estimates site parameters when detailed data unavailable:

```python
from hazardstack.hazard.common.spectral_response import GeologicalProxyEstimator

geo_proxy = GeologicalProxyEstimator()
params = geo_proxy.estimate_from_location(lat=28.6, lon=77.2, elevation=216)
# Estimates Vs30, sediment depth, basin depth from geographic location
```

**Regional Classifications:**
- **Indo-Gangetic Plains**: Deep soft sediments (Vs30 ~ 200 m/s, depth ~ 2500m)
- **Deccan Plateau**: Hard rock (Vs30 ~ 600 m/s, thin cover)
- **Himalayan Foothills**: Variable (rock outcrops vs. intermontane valleys)
- **Bengal Basin**: Very deep soft sediments (Vs30 ~ 200 m/s, depth ~ 3000m)
- **Coastal Plains**: Moderate sediments (Vs30 ~ 300 m/s, depth ~ 500m)

### 3. Enhanced Feature Engineering

Updated `EarthquakeFeatureBuilder` to compute spectral features:

```python
from hazardstack.hazard.features.eq_features import EarthquakeFeatureBuilder

builder = EarthquakeFeatureBuilder(use_spectral_response=True)

features = builder.build_shaking_features(
    event_magnitude=6.8,
    event_depth_km=15.0,
    event_lat=30.5,
    event_lon=78.5,
    site_lat=28.6,
    site_lon=77.2,
    site_elevation=216,
    fault_strike=285.0,  # Enables directivity calculation
)

# Returns 19 features (9 base + 10 spectral)
```

**Feature Dimensions:**
- **Base GMPE**: 9 features (magnitude, depth, distance, Vs30, etc.)
- **Spectral Enhanced**: 19 features (+10 spectral features)

### 4. Spectral Attention Mechanism

Neural attention module to weight frequency bands:

```python
class SpectralAttention(nn.Module):
    """
    Learns to weight different frequency bands based on earthquake characteristics.

    For example:
    - Distant events: emphasize low-frequency features
    - Shallow sites: emphasize high-frequency resonance
    - Basin sites: emphasize long-period amplification
    """
```

Architecture:
```
spectral_features [B, 10]
    ↓
attention_net (MLP)
    ↓
attention_weights [B, 10]  (softmax normalized)
    ↓
weighted_features = features * weights
```

### 5. Enhanced Ground Motion Model

Updated `GroundMotionModel` with spectral processing:

```python
model = EarthquakeModel(use_spectral_features=True)

# Forward pass splits features
base_features = features[:, :9]      # magnitude, depth, distance, etc.
spectral_features = features[:, 9:]   # f0, amplifications, etc.

# Apply attention to spectral features
spectral_attended = spectral_attention(spectral_features)

# Combine and process
combined = concat([base_features, spectral_attended])
mmi_mean, mmi_std = encoder(combined)
```

### 6. Physics-Based Constraints

Regularization losses to enforce seismological principles:

```python
from hazardstack.hazard.common.physics_constraints import GroundMotionPhysicsConstraints

physics = GroundMotionPhysicsConstraints()

losses = physics.compute_total_physics_loss(
    mmi_predictions=mmi_pred,
    distances=distances,
    magnitudes=magnitudes,
)

# Returns:
# - distance_decay_loss: Penalizes MMI increasing with distance
# - magnitude_scaling_loss: Enforces larger M → larger MMI
# - amplification_bounds_loss: Keeps amplification realistic
```

**Training with constraints:**
```python
# Base prediction loss
pred_loss = F.mse_loss(mmi_pred, mmi_true)

# Add physics constraints
total_loss = pred_loss + physics_losses['total_physics']
```

## Expected Improvements

### 1. Site-Specific Accuracy

**Before (Basic GMPE):**
- Single Vs30 value captures all site effects
- Same amplification at all frequencies
- Misses basin amplification, resonance

**After (Spectral GMPE):**
- Frequency-dependent amplification
- Captures resonance at f₀
- Models basin long-period amplification
- Directivity effects included

**Expected MMI improvement**: ±0.5-1.0 MMI units at sites with strong amplification

### 2. Regional Performance

| Region | Site Characteristics | Expected Benefit |
|--------|---------------------|------------------|
| **Delhi (Indo-Gangetic)** | Deep soft sediments | High - captures basin resonance |
| **Mumbai (Coastal)** | Shallow sediments on rock | Moderate - high-freq amplification |
| **Kathmandu Valley** | Deep basin (500m+) | Very High - long-period amplification |
| **Peninsular India** | Hard rock | Low - minimal site effects |
| **NE India** | Variable geology | High - better site classification |

### 3. Frequency-Dependent Applications

- **Building damage**: Different building types vulnerable to different frequencies
  - Low-rise buildings: sensitive to high-frequency (5-10 Hz)
  - High-rise buildings: sensitive to long-period (0.5-2 Hz)
- **Liquefaction**: Related to amplification of specific frequency bands
- **Landslides**: Triggered by specific ground motion characteristics

## Usage Examples

### Basic Usage

```python
from hazardstack.hazard.features.eq_features import EarthquakeFeatureBuilder
from hazardstack.hazard.models.eq_model import EarthquakeModel
import torch

# Initialize with spectral features enabled
builder = EarthquakeFeatureBuilder(use_spectral_response=True)
model = EarthquakeModel(use_spectral_features=True)

# Build features
features = builder.build_shaking_features(
    event_magnitude=6.5,
    event_depth_km=10.0,
    event_lat=28.0,
    event_lon=85.0,
    site_lat=27.7,
    site_lon=85.3,
    site_elevation=1400,
)

# Predict
features_tensor = torch.tensor(features).unsqueeze(0).unsqueeze(0)
mmi_mean, mmi_std = model.gmpe(features_tensor)

print(f"Predicted MMI: {mmi_mean.item():.1f} ± {mmi_std.item():.1f}")
```

### Compare Basic vs. Spectral

```python
# Basic GMPE
builder_basic = EarthquakeFeatureBuilder(use_spectral_response=False)
model_basic = EarthquakeModel(use_spectral_features=False)

feat_basic = builder_basic.build_shaking_features(...)
mmi_basic, _ = model_basic.gmpe(feat_basic)

# Spectral GMPE
builder_spectral = EarthquakeFeatureBuilder(use_spectral_response=True)
model_spectral = EarthquakeModel(use_spectral_features=True)

feat_spectral = builder_spectral.build_shaking_features(..., site_elevation=1400)
mmi_spectral, _ = model_spectral.gmpe(feat_spectral)

difference = mmi_spectral - mmi_basic
print(f"Spectral correction: {difference:+.2f} MMI")
```

### Run Full Example

```bash
python scripts/example_spectral_gmpe.py
```

This demonstrates:
1. Single event prediction with/without spectral features
2. Spectral site response analysis
3. Geological proxy estimation
4. Physics-based constraints

## Training Recommendations

### 1. Feature Normalization

Spectral features have different scales - normalize appropriately:

```python
# Frequencies: log-scale
f0_norm = np.log10(f0)

# Amplifications: typically 0.5-3.0
amp_norm = (amp - 1.0) / 1.0

# Kappa: typically 0.01-0.05
kappa_norm = (kappa - 0.03) / 0.02
```

### 2. Loss Function

```python
# Prediction loss (Gaussian NLL)
nll_loss = -torch.distributions.Normal(mmi_mean, mmi_std).log_prob(mmi_true).mean()

# Physics constraints
physics_loss = physics_constraints.compute_total_physics_loss(...)['total_physics']

# Total
total_loss = nll_loss + physics_loss
```

### 3. Hyperparameters

Recommended settings:

```python
model = EarthquakeModel(
    mmi_hidden_dims=[128, 128, 64],  # Larger for 19 features
    dropout=0.1,
    use_spectral_features=True,
)

physics = GroundMotionPhysicsConstraints(
    distance_decay_weight=0.1,
    magnitude_scaling_weight=0.1,
    amplification_bounds_weight=0.05,
)
```

### 4. Data Augmentation

For sites without elevation/strike data:

```python
# Add noise to proxy estimates
if site_elevation is None:
    site_elevation = geo_proxy.estimate(...) + np.random.normal(0, 50)

# Use random strike if unavailable
if fault_strike is None:
    fault_strike = np.random.uniform(0, 360)  # Or regional default
```

## Validation

### Metrics

1. **MMI Prediction Error**: MAE, RMSE on test set
2. **Bias by Site Class**: Check systematic errors for soil/rock
3. **Residual Analysis**: Plot residuals vs. distance, magnitude
4. **Physics Constraint Violations**: Monitor constraint losses

### Test Cases

Use historical Indian earthquakes:

| Event | M | Region | Site Effects |
|-------|---|--------|--------------|
| 2015 Nepal | 7.8 | Kathmandu Valley | Strong basin amplification |
| 2001 Bhuj | 7.7 | Kutch Basin | Moderate amplification |
| 1991 Uttarkashi | 6.8 | Himalayas | Rock sites |
| 2011 Sikkim | 6.9 | NE India | Variable geology |

**Expected validation:**
- Spectral GMPE should better match observed MMI in basins
- Reduced bias for soft soil sites
- Better capture of spatial MMI patterns

## Limitations

1. **Requires elevation data**: Proxy estimation less accurate without
2. **1D site response**: Doesn't model 2D/3D basin edge effects
3. **Linear site response**: Nonlinear soil behavior simplified
4. **Frequency bands**: Discrete bands (5) vs. continuous spectrum
5. **Regional calibration**: Needs India-specific training data

## Future Enhancements

1. **Waveform integration**: Use actual seismograms when available
2. **Nonlinear site response**: Magnitude-dependent amplification
3. **2D/3D basin models**: Ray tracing for complex basins
4. **Conditional GMPEs**: Spectral acceleration at multiple periods
5. **Real-time Vs30 mapping**: Integrate with geological surveys

## References

### Seismological Basis

- Boore & Atkinson (2008): "Ground-Motion Prediction Equations for the Average Horizontal Component"
- Day et al. (2008): "Model for Basin Effects on Long-Period Response Spectra"
- Wells & Coppersmith (1994): "New Empirical Relationships among Magnitude, Rupture Length"

### Site Response

- Dobry et al. (2000): "New Site Coefficients and Site Classification System"
- Stewart et al. (2014): "Semi-Empirical Nonlinear Site Amplification"

### Indian Context

- Nath et al. (2014): "Seismic Hazard Scenario and Attenuation Model for Guwahati"
- Anbazhagan et al. (2013): "Seismic Site Classification and Correlation"

## Contact

For questions about this optimization:
- Review code: `hazardstack/hazard/common/spectral_response.py`
- Run example: `scripts/example_spectral_gmpe.py`
- Check tests: `tests/test_spectral_response.py` (to be added)

---

**Implementation Date**: December 2025
**Optimization Type**: Physics-informed feature engineering + attention mechanism
**Expected Improvement**: 15-25% reduction in MMI prediction error for sites with strong site effects
