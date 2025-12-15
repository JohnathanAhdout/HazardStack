"""Token mixer that projects denoised features to model dimension with embeddings."""

import torch
import torch.nn as nn
import math
from typing import Optional


class PositionalEmbedding(nn.Module):
    """Sinusoidal positional embeddings for time and space."""

    def __init__(self, d_model: int, max_len: int = 5000):
        """
        Initialize positional embedding.

        Args:
            d_model: Model dimension
            max_len: Maximum sequence length
        """
        super().__init__()
        self.d_model = d_model

        # Create positional encoding matrix
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)

        # Register as buffer (not a parameter)
        self.register_buffer("pe", pe)

    def forward(self, t: torch.Tensor) -> torch.Tensor:
        """
        Get positional embeddings for given time indices.

        Args:
            t: Time indices [B, T] or [B]

        Returns:
            Positional embeddings [B, T, D] or [B, D]
        """
        if t.dim() == 1:
            # Single time step per batch
            return self.pe[t]  # [B, D]
        else:
            # Multiple time steps
            B, T = t.shape
            return self.pe[t.flatten()].view(B, T, self.d_model)


class LearnedSpatialEmbedding(nn.Module):
    """Learned embeddings for spatial locations (H3 cells)."""

    def __init__(self, d_model: int):
        """
        Initialize spatial embedding.

        Uses lat/lon as continuous coordinates.

        Args:
            d_model: Model dimension
        """
        super().__init__()
        self.d_model = d_model

        # Project (lat, lon) to d_model
        self.proj = nn.Sequential(
            nn.Linear(2, d_model // 2),
            nn.ReLU(),
            nn.Linear(d_model // 2, d_model),
        )

    def forward(self, lat: torch.Tensor, lon: torch.Tensor) -> torch.Tensor:
        """
        Get spatial embeddings from lat/lon.

        Args:
            lat: Latitude [B, N] or [B]
            lon: Longitude [B, N] or [B]

        Returns:
            Spatial embeddings [B, N, D] or [B, D]
        """
        # Stack lat/lon
        coords = torch.stack([lat, lon], dim=-1)  # [B, N, 2] or [B, 2]

        # Project
        return self.proj(coords)


class SeasonalEmbedding(nn.Module):
    """Seasonal (annual cycle) embedding."""

    def __init__(self, d_model: int):
        """
        Initialize seasonal embedding.

        Args:
            d_model: Model dimension
        """
        super().__init__()
        self.proj = nn.Linear(2, d_model)  # (sin, cos) -> d_model

    def forward(self, season_sin: torch.Tensor, season_cos: torch.Tensor) -> torch.Tensor:
        """
        Get seasonal embeddings.

        Args:
            season_sin: Sin component of day-of-year [B, T] or [B]
            season_cos: Cos component of day-of-year [B, T] or [B]

        Returns:
            Seasonal embeddings [B, T, D] or [B, D]
        """
        season = torch.stack([season_sin, season_cos], dim=-1)
        return self.proj(season)


class TokenMixer(nn.Module):
    """
    Token mixer that combines denoised features with positional/spatial/seasonal embeddings.

    Projects everything to d_model dimension for downstream transformer.
    """

    def __init__(self, input_dim: int, d_model: int, dropout: float = 0.1):
        """
        Initialize token mixer.

        Args:
            input_dim: Input feature dimension (from denoiser)
            d_model: Model dimension (for transformer)
            dropout: Dropout rate
        """
        super().__init__()
        self.d_model = d_model

        # Feature projection
        self.feature_proj = nn.Linear(input_dim, d_model)

        # Embeddings
        self.temporal_emb = PositionalEmbedding(d_model)
        self.spatial_emb = LearnedSpatialEmbedding(d_model)
        self.seasonal_emb = SeasonalEmbedding(d_model)

        # Combine embeddings
        self.combine = nn.Linear(4 * d_model, d_model)  # features + 3 embeddings

        # Normalization
        self.norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        features: torch.Tensor,
        time_idx: torch.Tensor,
        lat: torch.Tensor,
        lon: torch.Tensor,
        season_sin: torch.Tensor,
        season_cos: torch.Tensor,
    ) -> torch.Tensor:
        """
        Mix features with embeddings.

        Args:
            features: Denoised features [B, T, D_in] or [B, N, D_in]
            time_idx: Time indices [B, T] or [B]
            lat: Latitudes [B, N] or [B]
            lon: Longitudes [B, N] or [B]
            season_sin: Seasonal sin [B, T] or [B]
            season_cos: Seasonal cos [B, T] or [B]

        Returns:
            Mixed tokens [B, T, d_model] or [B, N, d_model]
        """
        # Project features
        h_feat = self.feature_proj(features)

        # Get embeddings
        h_time = self.temporal_emb(time_idx)
        h_space = self.spatial_emb(lat, lon)
        h_season = self.seasonal_emb(season_sin, season_cos)

        # Concatenate all
        h = torch.cat([h_feat, h_time, h_space, h_season], dim=-1)

        # Combine
        h = self.combine(h)

        # Normalize and dropout
        h = self.norm(h)
        h = self.dropout(h)

        return h


class ReadabilityEncoder(nn.Module):
    """
    Complete readability encoder: denoise -> mix -> stable representation.

    This is the core "readability layer" that produces stable, interpretable tokens
    from noisy streaming data.
    """

    def __init__(
        self,
        input_dim: int,
        d_model: int = 192,
        hidden_channels: int = 128,
        num_denoise_layers: int = 6,
        dropout: float = 0.1,
    ):
        """
        Initialize readability encoder.

        Args:
            input_dim: Input feature dimension
            d_model: Model dimension
            hidden_channels: Hidden channels for denoiser
            num_denoise_layers: Number of denoising layers
            dropout: Dropout rate
        """
        super().__init__()

        # Import here to avoid circular dependency
        from .denoise_conv import ReadabilityDenoiser

        # Denoiser
        self.denoiser = ReadabilityDenoiser(
            input_dim=input_dim,
            hidden_channels=hidden_channels,
            num_layers=num_denoise_layers,
            dropout=dropout,
        )

        # Token mixer
        self.mixer = TokenMixer(input_dim, d_model, dropout)

    def forward(
        self,
        x: torch.Tensor,
        mask: torch.Tensor,
        time_idx: torch.Tensor,
        lat: torch.Tensor,
        lon: torch.Tensor,
        season_sin: torch.Tensor,
        season_cos: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Encode raw features to stable tokens.

        Args:
            x: Raw features [B, T, D]
            mask: Missing data mask [B, T, D]
            time_idx: Time indices [B, T]
            lat: Latitudes [B] or [B, N]
            lon: Longitudes [B] or [B, N]
            season_sin: Seasonal sin [B, T]
            season_cos: Seasonal cos [B, T]

        Returns:
            Tuple of (tokens [B, T, d_model], uncertainty [B, T, D], instability [B, T, 1])
        """
        # Denoise
        denoised, uncertainty, instability = self.denoiser(x, mask)

        # Mix with embeddings
        tokens = self.mixer(denoised, time_idx, lat, lon, season_sin, season_cos)

        return tokens, uncertainty, instability
