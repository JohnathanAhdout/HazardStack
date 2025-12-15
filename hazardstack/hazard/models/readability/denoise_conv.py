"""Causal denoising convolutional network with missing data handling."""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional


class GatedResidualBlock(nn.Module):
    """Gated residual convolution block with GLU activation."""

    def __init__(
        self,
        channels: int,
        kernel_size: int = 3,
        dilation: int = 1,
        dropout: float = 0.1,
    ):
        """
        Initialize gated residual block.

        Args:
            channels: Number of channels
            kernel_size: Convolution kernel size
            dilation: Dilation rate
            dropout: Dropout rate
        """
        super().__init__()

        # Ensure causal padding
        self.padding = (kernel_size - 1) * dilation

        # Main convolution (outputs 2x channels for gating)
        self.conv = nn.Conv1d(
            channels,
            2 * channels,
            kernel_size=kernel_size,
            dilation=dilation,
            padding=self.padding,
        )

        # Normalization
        self.norm = nn.GroupNorm(min(32, channels), channels)

        # Dropout
        self.dropout = nn.Dropout(dropout)

        # Projection if needed
        self.projection = nn.Conv1d(channels, channels, kernel_size=1)

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input [B, C, T]
            mask: Optional missing data mask [B, C, T] (1 = valid, 0 = missing)

        Returns:
            Output [B, C, T]
        """
        residual = x

        # Apply mask if provided
        if mask is not None:
            x = x * mask

        # Convolution
        h = self.conv(x)

        # Remove future context (causal)
        if self.padding > 0:
            h = h[:, :, : -self.padding]

        # Split for gating (GLU)
        h_linear, h_gate = h.chunk(2, dim=1)
        h = h_linear * torch.sigmoid(h_gate)

        # Dropout
        h = self.dropout(h)

        # Projection
        h = self.projection(h)

        # Residual connection
        h = self.norm(h + residual)

        return h


class MaskAwareDenoiser(nn.Module):
    """
    Causal denoising network that handles missing data.

    Uses dilated convolutions with gating for temporal modeling.
    """

    def __init__(
        self,
        input_dim: int,
        hidden_channels: int = 128,
        num_layers: int = 6,
        kernel_size: int = 3,
        dilation_rates: Optional[list[int]] = None,
        dropout: float = 0.1,
    ):
        """
        Initialize mask-aware denoiser.

        Args:
            input_dim: Input feature dimension
            hidden_channels: Hidden channel dimension
            num_layers: Number of conv layers
            kernel_size: Convolution kernel size
            dilation_rates: List of dilation rates (default: exponential)
            dropout: Dropout rate
        """
        super().__init__()
        self.input_dim = input_dim
        self.hidden_channels = hidden_channels

        # Default exponential dilation
        if dilation_rates is None:
            dilation_rates = [2**i for i in range(num_layers)]
        else:
            assert len(dilation_rates) == num_layers

        # Input projection
        self.input_proj = nn.Conv1d(input_dim, hidden_channels, kernel_size=1)

        # Mask projection (treat mask as auxiliary channel)
        self.mask_proj = nn.Conv1d(input_dim, hidden_channels, kernel_size=1)

        # Dilated conv blocks
        self.blocks = nn.ModuleList(
            [
                GatedResidualBlock(
                    hidden_channels, kernel_size, dilation, dropout
                )
                for dilation in dilation_rates
            ]
        )

        # Output projection
        self.output_proj = nn.Conv1d(hidden_channels, input_dim, kernel_size=1)

        # Uncertainty estimation head
        self.uncertainty_head = nn.Conv1d(hidden_channels, input_dim, kernel_size=1)

    def forward(
        self, x: torch.Tensor, mask: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Denoise input with missing data handling.

        Args:
            x: Input features [B, T, D]
            mask: Missing data mask [B, T, D] (1 = valid, 0 = missing)

        Returns:
            Tuple of (denoised [B, T, D], uncertainty [B, T, D])
        """
        # Transpose to [B, D, T] for Conv1d
        x = x.transpose(1, 2)
        mask = mask.transpose(1, 2).float()

        # Replace missing values with zeros (masked conv will handle)
        x_masked = x * mask

        # Project input + mask info
        h = self.input_proj(x_masked) + self.mask_proj(mask)

        # Pass through dilated conv blocks
        for block in self.blocks:
            h = block(h, mask)

        # Output
        denoised = self.output_proj(h)

        # Uncertainty (higher for missing/noisy data)
        uncertainty = torch.sigmoid(self.uncertainty_head(h))

        # Transpose back to [B, T, D]
        denoised = denoised.transpose(1, 2)
        uncertainty = uncertainty.transpose(1, 2)

        # For missing values, copy input (conservative)
        denoised = torch.where(mask.transpose(1, 2).bool(), denoised, x.transpose(1, 2))

        return denoised, uncertainty


class ReadabilityDenoiser(nn.Module):
    """
    Readability-focused denoiser that outputs stable representations.

    Combines denoising with an instability score for downstream attention weighting.
    """

    def __init__(
        self,
        input_dim: int,
        hidden_channels: int = 128,
        num_layers: int = 6,
        dropout: float = 0.1,
    ):
        """Initialize readability denoiser."""
        super().__init__()

        self.denoiser = MaskAwareDenoiser(
            input_dim=input_dim,
            hidden_channels=hidden_channels,
            num_layers=num_layers,
            dropout=dropout,
        )

        # Instability score head (for readability)
        self.instability_head = nn.Sequential(
            nn.Linear(input_dim, hidden_channels),
            nn.ReLU(),
            nn.Linear(hidden_channels, 1),
            nn.Sigmoid(),
        )

    def forward(
        self, x: torch.Tensor, mask: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Forward pass.

        Args:
            x: Input features [B, T, D]
            mask: Missing data mask [B, T, D]

        Returns:
            Tuple of (denoised [B, T, D], uncertainty [B, T, D], instability [B, T, 1])
        """
        # Denoise
        denoised, uncertainty = self.denoiser(x, mask)

        # Compute instability score (for attention weighting)
        # High instability = noisy/unreliable input
        instability = self.instability_head(uncertainty)

        return denoised, uncertainty, instability
