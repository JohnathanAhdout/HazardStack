"""
Physics-based constraints for earthquake ground motion prediction.

Implements physics-guided regularization to ensure model predictions
follow established seismological principles.
"""

import torch
import torch.nn as nn
import numpy as np


class GroundMotionPhysicsConstraints:
    """
    Physics constraints for ground motion predictions.

    Enforces:
    1. Distance decay: MMI decreases with distance
    2. Magnitude scaling: Larger events produce stronger shaking
    3. Site amplification bounds: Soft soil amplifies but within limits
    4. Frequency consistency: Site response matches expected patterns
    """

    def __init__(
        self,
        distance_decay_weight: float = 0.1,
        magnitude_scaling_weight: float = 0.1,
        amplification_bounds_weight: float = 0.05,
    ):
        """
        Initialize physics constraints.

        Args:
            distance_decay_weight: Weight for distance decay constraint
            magnitude_scaling_weight: Weight for magnitude scaling constraint
            amplification_bounds_weight: Weight for amplification bounds constraint
        """
        self.distance_decay_weight = distance_decay_weight
        self.magnitude_scaling_weight = magnitude_scaling_weight
        self.amplification_bounds_weight = amplification_bounds_weight

    def compute_distance_decay_loss(
        self,
        mmi_predictions: torch.Tensor,
        distances: torch.Tensor,
    ) -> torch.Tensor:
        """
        Enforce that MMI decreases with distance.

        For a given event, MMI should decrease as distance increases.

        Args:
            mmi_predictions: Predicted MMI values [B, N_sites]
            distances: Distances from source [B, N_sites]

        Returns:
            Distance decay violation loss
        """
        # Compute gradients w.r.t distance (should be negative)
        # For each batch, compute correlation between distance and MMI
        # Penalize positive correlations

        batch_size = mmi_predictions.shape[0]
        losses = []

        for i in range(batch_size):
            mmi = mmi_predictions[i]
            dist = distances[i]

            # Compute Pearson correlation
            mmi_centered = mmi - mmi.mean()
            dist_centered = dist - dist.mean()

            correlation = (mmi_centered * dist_centered).sum() / (
                torch.sqrt((mmi_centered**2).sum() * (dist_centered**2).sum()) + 1e-6
            )

            # Penalize positive correlation (MMI increasing with distance)
            loss = torch.relu(correlation)  # Only penalize if positive
            losses.append(loss)

        return torch.stack(losses).mean()

    def compute_magnitude_scaling_loss(
        self,
        mmi_predictions: torch.Tensor,
        magnitudes: torch.Tensor,
    ) -> torch.Tensor:
        """
        Enforce that larger magnitudes produce higher MMI.

        Args:
            mmi_predictions: Predicted MMI values [B, N_sites]
            magnitudes: Event magnitudes [B]

        Returns:
            Magnitude scaling violation loss
        """
        # For pairs of events at similar distances, larger magnitude
        # should produce larger MMI

        batch_size = mmi_predictions.shape[0]

        if batch_size < 2:
            return torch.tensor(0.0, device=mmi_predictions.device)

        # Compare pairs of events
        loss = 0.0
        n_pairs = 0

        for i in range(batch_size):
            for j in range(i + 1, batch_size):
                mag_i = magnitudes[i]
                mag_j = magnitudes[j]
                mmi_i = mmi_predictions[i].mean()
                mmi_j = mmi_predictions[j].mean()

                # If mag_i > mag_j, then mmi_i should > mmi_j
                if mag_i > mag_j:
                    # Penalize if mmi_i <= mmi_j
                    violation = torch.relu(mmi_j - mmi_i + 0.5)  # Margin of 0.5 MMI
                    loss += violation
                    n_pairs += 1
                elif mag_j > mag_i:
                    violation = torch.relu(mmi_i - mmi_j + 0.5)
                    loss += violation
                    n_pairs += 1

        if n_pairs > 0:
            return loss / n_pairs
        else:
            return torch.tensor(0.0, device=mmi_predictions.device)

    def compute_amplification_bounds_loss(
        self,
        site_amplifications: torch.Tensor,
    ) -> torch.Tensor:
        """
        Enforce realistic bounds on site amplification factors.

        Amplification should be in range [0.5, 3.0] for most cases.

        Args:
            site_amplifications: Amplification factors [B, N_sites, N_freq]

        Returns:
            Amplification bounds violation loss
        """
        # Penalize amplifications outside [0.5, 3.0]
        lower_bound = 0.5
        upper_bound = 3.0

        below_lower = torch.relu(lower_bound - site_amplifications)
        above_upper = torch.relu(site_amplifications - upper_bound)

        loss = (below_lower + above_upper).mean()

        return loss

    def compute_total_physics_loss(
        self,
        mmi_predictions: torch.Tensor,
        distances: torch.Tensor,
        magnitudes: torch.Tensor,
        site_amplifications: torch.Tensor = None,
    ) -> dict[str, torch.Tensor]:
        """
        Compute total physics-based constraint loss.

        Args:
            mmi_predictions: Predicted MMI [B, N_sites]
            distances: Distances [B, N_sites]
            magnitudes: Event magnitudes [B]
            site_amplifications: Optional amplification factors [B, N_sites, N_freq]

        Returns:
            Dictionary of individual and total losses
        """
        losses = {}

        # Distance decay
        dist_loss = self.compute_distance_decay_loss(mmi_predictions, distances)
        losses["distance_decay"] = dist_loss

        # Magnitude scaling
        mag_loss = self.compute_magnitude_scaling_loss(mmi_predictions, magnitudes)
        losses["magnitude_scaling"] = mag_loss

        # Amplification bounds (if provided)
        if site_amplifications is not None:
            amp_loss = self.compute_amplification_bounds_loss(site_amplifications)
            losses["amplification_bounds"] = amp_loss
        else:
            amp_loss = torch.tensor(0.0, device=mmi_predictions.device)
            losses["amplification_bounds"] = amp_loss

        # Total weighted loss
        total = (
            self.distance_decay_weight * dist_loss
            + self.magnitude_scaling_weight * mag_loss
            + self.amplification_bounds_weight * amp_loss
        )

        losses["total_physics"] = total

        return losses


class SpectralConsistencyConstraint:
    """
    Enforce consistency in spectral site response predictions.

    Ensures that predicted amplification factors follow expected patterns:
    - Low frequency amplification for deep basins
    - High frequency amplification for shallow soft soils
    - Smooth frequency response (no sharp discontinuities)
    """

    def __init__(self, smoothness_weight: float = 0.05):
        """
        Initialize spectral consistency constraints.

        Args:
            smoothness_weight: Weight for smoothness constraint
        """
        self.smoothness_weight = smoothness_weight

    def compute_frequency_smoothness_loss(
        self,
        amplifications: torch.Tensor,
    ) -> torch.Tensor:
        """
        Penalize sharp discontinuities in frequency response.

        Amplification should vary smoothly across frequency bands.

        Args:
            amplifications: Amplification at frequency bands [B, N_freq]
                           Assumed ordered by increasing frequency

        Returns:
            Smoothness violation loss
        """
        # Compute second derivative (discrete approximation)
        # d²A/df² = A[i+1] - 2*A[i] + A[i-1]

        if amplifications.shape[-1] < 3:
            return torch.tensor(0.0, device=amplifications.device)

        second_deriv = (
            amplifications[..., 2:]
            - 2 * amplifications[..., 1:-1]
            + amplifications[..., :-2]
        )

        # Penalize large second derivatives
        smoothness_loss = (second_deriv**2).mean()

        return smoothness_loss

    def compute_basin_consistency_loss(
        self,
        amplifications: torch.Tensor,
        basin_flags: torch.Tensor,
        freq_bands: torch.Tensor,
    ) -> torch.Tensor:
        """
        Enforce that basin sites amplify low frequencies.

        Sites in basins should show higher amplification at low frequencies.

        Args:
            amplifications: Amplification factors [B, N_freq]
            basin_flags: Basin indicators [B] (1=basin, 0=no basin)
            freq_bands: Frequency values [N_freq]

        Returns:
            Basin consistency loss
        """
        # For basin sites, low-freq amp should be higher than high-freq amp
        basin_mask = basin_flags > 0.5

        if basin_mask.sum() == 0:
            return torch.tensor(0.0, device=amplifications.device)

        basin_amps = amplifications[basin_mask]

        # Find low and high frequency indices
        low_freq_idx = freq_bands < 1.0  # Below 1 Hz
        high_freq_idx = freq_bands > 5.0  # Above 5 Hz

        if low_freq_idx.sum() == 0 or high_freq_idx.sum() == 0:
            return torch.tensor(0.0, device=amplifications.device)

        low_freq_amp = basin_amps[:, low_freq_idx].mean(dim=-1)
        high_freq_amp = basin_amps[:, high_freq_idx].mean(dim=-1)

        # Penalize if high-freq amp >= low-freq amp for basin sites
        violation = torch.relu(high_freq_amp - low_freq_amp + 0.2)  # Margin

        return violation.mean()


def add_physics_constraints_to_loss(
    base_loss: torch.Tensor,
    mmi_predictions: torch.Tensor,
    features: torch.Tensor,
    feature_names: list[str],
    physics_constraints: GroundMotionPhysicsConstraints,
) -> tuple[torch.Tensor, dict]:
    """
    Add physics constraints to the base training loss.

    Args:
        base_loss: Base prediction loss (e.g., MSE, NLL)
        mmi_predictions: Predicted MMI values [B, N_sites]
        features: Input features [B, N_sites, F]
        feature_names: List of feature names
        physics_constraints: Physics constraints object

    Returns:
        Tuple of (total_loss, loss_dict)
    """
    # Extract relevant features
    try:
        magnitude_idx = feature_names.index("magnitude")
        distance_idx = feature_names.index("hypocentral_dist_km")

        magnitudes = features[:, 0, magnitude_idx]  # [B]
        distances = features[:, :, distance_idx]  # [B, N_sites]
    except ValueError:
        # Features not found, skip physics constraints
        return base_loss, {"base_loss": base_loss}

    # Compute physics losses
    physics_losses = physics_constraints.compute_total_physics_loss(
        mmi_predictions, distances, magnitudes
    )

    # Combine with base loss
    total_loss = base_loss + physics_losses["total_physics"]

    loss_dict = {
        "base_loss": base_loss,
        **physics_losses,
        "total_loss": total_loss,
    }

    return total_loss, loss_dict
