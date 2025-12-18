"""Earthquake impact and aftershock prediction models."""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional
import math


class SpectralAttention(nn.Module):
    """
    Spectral attention mechanism for frequency-dependent feature weighting.

    Learns to weight different frequency bands based on earthquake characteristics.
    """

    def __init__(self, spectral_dim: int = 10, hidden_dim: int = 32):
        """
        Initialize spectral attention.

        Args:
            spectral_dim: Number of spectral features
            hidden_dim: Hidden dimension for attention network
        """
        super().__init__()

        self.attention_net = nn.Sequential(
            nn.Linear(spectral_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, spectral_dim),
            nn.Softmax(dim=-1),
        )

    def forward(self, spectral_features: torch.Tensor) -> torch.Tensor:
        """
        Compute attention-weighted spectral features.

        Args:
            spectral_features: [B, spectral_dim]

        Returns:
            Weighted spectral features [B, spectral_dim]
        """
        attention_weights = self.attention_net(spectral_features)
        return spectral_features * attention_weights


class GroundMotionModel(nn.Module):
    """
    Ground Motion Prediction Equation (GMPE) style model for shaking intensity.

    Enhanced with frequency-dependent site response and spectral attention.
    Predicts MMI (Modified Mercalli Intensity) distribution at a location.
    """

    def __init__(
        self,
        hidden_dims: list[int] = [128, 128, 64],
        dropout: float = 0.1,
        use_spectral_features: bool = True,
    ):
        """
        Initialize GMPE model.

        Args:
            hidden_dims: Hidden layer dimensions
            dropout: Dropout rate
            use_spectral_features: Use enhanced spectral site response features
        """
        super().__init__()

        self.use_spectral_features = use_spectral_features

        # Input features dimensions
        base_dim = 9  # Original features
        spectral_dim = 10  # Spectral response features (if enabled)
        input_dim = base_dim + (spectral_dim if use_spectral_features else 0)

        self.base_dim = base_dim
        self.spectral_dim = spectral_dim

        # Spectral attention (if using spectral features)
        if use_spectral_features:
            self.spectral_attention = SpectralAttention(spectral_dim)
        else:
            self.spectral_attention = None

        layers = []
        prev_dim = input_dim

        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout),
            ])
            prev_dim = hidden_dim

        self.encoder = nn.Sequential(*layers)

        # Output: Gaussian distribution parameters for MMI
        self.mean_head = nn.Linear(prev_dim, 1)
        self.std_head = nn.Linear(prev_dim, 1)

    def forward(self, event_features: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass with spectral attention.

        Args:
            event_features: Event and site features [B, N_cells, F]
                           If use_spectral_features=True, F=19 (9 base + 10 spectral)
                           Otherwise, F=9

        Returns:
            Tuple of (mmi_mean [B, N_cells], mmi_std [B, N_cells])
        """
        # Apply spectral attention if enabled
        if self.use_spectral_features and self.spectral_attention is not None:
            # Split features into base and spectral
            base_features = event_features[..., :self.base_dim]
            spectral_features = event_features[..., self.base_dim:]

            # Apply attention to spectral features
            spectral_attended = self.spectral_attention(spectral_features)

            # Recombine
            features = torch.cat([base_features, spectral_attended], dim=-1)
        else:
            features = event_features

        h = self.encoder(features)

        mmi_mean = self.mean_head(h).squeeze(-1)  # [B, N_cells]
        mmi_std = F.softplus(self.std_head(h)).squeeze(-1) + 1e-3  # [B, N_cells]

        return mmi_mean, mmi_std


class NeuralHawkesProcess(nn.Module):
    """
    Neural Hawkes process for aftershock sequence modeling.

    Models the conditional intensity function λ(t) using RNN.
    """

    def __init__(
        self,
        event_dim: int = 5,  # [Δt, magnitude, depth, lat, lon]
        hidden_dim: int = 128,
        num_layers: int = 3,
        dropout: float = 0.1,
    ):
        """
        Initialize neural Hawkes process.

        Args:
            event_dim: Event feature dimension
            hidden_dim: Hidden dimension
            num_layers: Number of RNN layers
            dropout: Dropout rate
        """
        super().__init__()

        # Event embedding
        self.event_emb = nn.Linear(event_dim, hidden_dim)

        # RNN for sequence modeling
        self.rnn = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )

        # Intensity function output
        self.intensity_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Softplus(),  # Ensure positive intensity
        )

    def forward(
        self,
        event_sequence: torch.Tensor,
        horizons_hours: list[float] = [1.0, 24.0, 168.0],
    ) -> dict[str, torch.Tensor]:
        """
        Forward pass.

        Args:
            event_sequence: Sequence of events [B, N_events, event_dim]
                            Features: [Δt, magnitude, depth, lat, lon]
            horizons_hours: Forecast horizons in hours

        Returns:
            Dict of aftershock probabilities per horizon
        """
        # Embed events
        h = self.event_emb(event_sequence)  # [B, N_events, H]

        # RNN encoding
        out, (h_n, c_n) = self.rnn(h)  # out: [B, N_events, H]

        # Use final hidden state for prediction
        h_final = h_n[-1]  # [B, H]

        # Predict integrated intensity (cumulative hazard) for each horizon
        predictions = {}

        for horizon in horizons_hours:
            # Expand for horizon dimension
            h_horizon = torch.cat([h_final, torch.full_like(h_final[:, :1], horizon)], dim=1)

            # Predict log-intensity
            log_lambda = self.intensity_head(h_final)  # [B, 1]

            # Convert to probability: P(N >= 1) = 1 - exp(-∫λ(t)dt)
            # Approximation: ∫λ(t)dt ≈ λ * horizon
            integrated_intensity = torch.exp(log_lambda) * horizon
            prob = 1 - torch.exp(-integrated_intensity)  # [B, 1]

            horizon_str = f"{int(horizon)}h"
            predictions[f"{horizon_str}_aftershock_prob"] = prob.squeeze(-1)

        return predictions


class ETASModel(nn.Module):
    """
    ETAS-style aftershock model with learned parameters.

    Epidemic Type Aftershock Sequence (ETAS) model.
    """

    def __init__(self, hidden_dim: int = 64):
        """
        Initialize ETAS model.

        Args:
            hidden_dim: Hidden dimension for parameter prediction
        """
        super().__init__()

        # Learn ETAS parameters conditioned on mainshock
        # Input: [magnitude, depth, region_features]
        self.param_net = nn.Sequential(
            nn.Linear(10, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 5),  # [K, c, α, p, m_min]
        )

    def forward(
        self,
        mainshock_features: torch.Tensor,
        horizon_hours: float = 24.0,
    ) -> torch.Tensor:
        """
        Predict aftershock rate.

        Args:
            mainshock_features: Mainshock features [B, F]
            horizon_hours: Forecast horizon

        Returns:
            Expected number of aftershocks [B]
        """
        # Predict ETAS parameters
        params = self.param_net(mainshock_features)  # [B, 5]

        K = F.softplus(params[:, 0])  # Productivity
        c = F.softplus(params[:, 1]) + 1e-3  # Time offset
        alpha = torch.sigmoid(params[:, 2]) * 2.0  # Magnitude sensitivity
        p = F.softplus(params[:, 3]) + 1.0  # Temporal decay
        m_min = params[:, 4] + 3.0  # Minimum magnitude

        # Omori law: λ(t) = K / (t + c)^p
        # Integrated over [0, horizon]: K * [(horizon + c)^(1-p) - c^(1-p)] / (1 - p)

        t_h = horizon_hours * 3600  # Convert to seconds

        if p.mean() != 1.0:
            integral = K * ((t_h + c) ** (1 - p) - c ** (1 - p)) / (1 - p)
        else:
            integral = K * torch.log((t_h + c) / c)

        # Convert to probability
        prob = 1 - torch.exp(-integral)

        return prob


class EarthquakeModel(nn.Module):
    """
    Combined earthquake impact and aftershock model.

    Enhanced with spectral site response for improved ground motion prediction.
    """

    def __init__(
        self,
        d_model: int = 192,
        mmi_hidden_dims: list[int] = [128, 128, 64],
        hawkes_hidden: int = 128,
        hawkes_layers: int = 3,
        dropout: float = 0.1,
        use_spectral_features: bool = True,
    ):
        """
        Initialize earthquake model.

        Args:
            d_model: Model dimension
            mmi_hidden_dims: Hidden dims for MMI model
            hawkes_hidden: Hidden dim for Hawkes process
            hawkes_layers: Number of Hawkes RNN layers
            dropout: Dropout rate
            use_spectral_features: Enable spectral site response features
        """
        super().__init__()

        # Ground motion model with spectral enhancement
        self.gmpe = GroundMotionModel(
            mmi_hidden_dims,
            dropout,
            use_spectral_features=use_spectral_features,
        )

        # Aftershock model
        self.hawkes = NeuralHawkesProcess(
            event_dim=5,
            hidden_dim=hawkes_hidden,
            num_layers=hawkes_layers,
            dropout=dropout,
        )

    def forward(
        self,
        event_features: Optional[torch.Tensor] = None,
        event_sequence: Optional[torch.Tensor] = None,
        predict_shaking: bool = True,
        predict_aftershock: bool = True,
    ) -> dict[str, torch.Tensor]:
        """
        Forward pass.

        Args:
            event_features: Features for MMI prediction [B, N_cells, F]
            event_sequence: Event sequence for aftershock [B, N_events, 5]
            predict_shaking: Whether to predict shaking
            predict_aftershock: Whether to predict aftershock

        Returns:
            Dict of predictions
        """
        predictions = {}

        if predict_shaking and event_features is not None:
            mmi_mean, mmi_std = self.gmpe(event_features)
            predictions["mmi_mean"] = mmi_mean
            predictions["mmi_std"] = mmi_std

        if predict_aftershock and event_sequence is not None:
            aftershock_preds = self.hawkes(event_sequence)
            predictions.update(aftershock_preds)

        return predictions
