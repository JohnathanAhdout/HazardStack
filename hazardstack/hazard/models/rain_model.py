"""Rain nowcast and forecast model with spatiotemporal transformer."""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional
import math


class LocalSpatialAttention(nn.Module):
    """
    Local spatial attention over neighboring H3 cells.

    Only attends to k-ring neighbors for efficiency.
    """

    def __init__(
        self,
        d_model: int,
        num_heads: int = 6,
        dropout: float = 0.1,
    ):
        """
        Initialize local spatial attention.

        Args:
            d_model: Model dimension
            num_heads: Number of attention heads
            dropout: Dropout rate
        """
        super().__init__()
        self.d_model = d_model
        self.num_heads = num_heads
        self.head_dim = d_model // num_heads

        assert d_model % num_heads == 0

        # Q, K, V projections
        self.q_proj = nn.Linear(d_model, d_model)
        self.k_proj = nn.Linear(d_model, d_model)
        self.v_proj = nn.Linear(d_model, d_model)

        # Output projection
        self.out_proj = nn.Linear(d_model, d_model)

        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        x: torch.Tensor,
        adjacency_mask: Optional[torch.Tensor] = None,
        instability: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input tokens [B, N, D] where N is number of cells
            adjacency_mask: Attention mask [B, N, N] (1 = attend, 0 = mask)
            instability: Instability scores [B, N, 1] for weighting

        Returns:
            Output [B, N, D]
        """
        B, N, D = x.shape

        # Project to Q, K, V
        Q = self.q_proj(x).view(B, N, self.num_heads, self.head_dim).transpose(1, 2)
        K = self.k_proj(x).view(B, N, self.num_heads, self.head_dim).transpose(1, 2)
        V = self.v_proj(x).view(B, N, self.num_heads, self.head_dim).transpose(1, 2)
        # Q, K, V: [B, H, N, D/H]

        # Scaled dot-product attention
        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.head_dim)
        # scores: [B, H, N, N]

        # Apply adjacency mask (only attend to neighbors)
        if adjacency_mask is not None:
            # Expand for heads
            mask = adjacency_mask.unsqueeze(1)  # [B, 1, N, N]
            scores = scores.masked_fill(mask == 0, float("-inf"))

        # Apply instability weighting (downweight unreliable cells)
        if instability is not None:
            # instability: [B, N, 1] -> [B, 1, 1, N]
            inst_weight = (1 - instability).transpose(-2, -1).unsqueeze(1)
            scores = scores * inst_weight

        # Softmax
        attn = F.softmax(scores, dim=-1)
        attn = self.dropout(attn)

        # Apply attention to values
        out = torch.matmul(attn, V)  # [B, H, N, D/H]

        # Concatenate heads
        out = out.transpose(1, 2).contiguous().view(B, N, D)

        # Output projection
        out = self.out_proj(out)

        return out


class SpatiotemporalTransformerBlock(nn.Module):
    """Transformer block with separate temporal and spatial attention."""

    def __init__(
        self,
        d_model: int,
        num_heads: int = 6,
        dim_feedforward: int = 768,
        dropout: float = 0.1,
    ):
        """Initialize spatiotemporal transformer block."""
        super().__init__()

        # Temporal self-attention
        self.temporal_attn = nn.MultiheadAttention(
            d_model, num_heads, dropout=dropout, batch_first=True
        )

        # Spatial attention
        self.spatial_attn = LocalSpatialAttention(d_model, num_heads, dropout)

        # Feedforward
        self.ffn = nn.Sequential(
            nn.Linear(d_model, dim_feedforward),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(dim_feedforward, d_model),
        )

        # Normalization
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.norm3 = nn.LayerNorm(d_model)

        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        x: torch.Tensor,
        adjacency_mask: Optional[torch.Tensor] = None,
        instability: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input [B, T, N, D]
            adjacency_mask: Spatial adjacency [B, N, N]
            instability: Instability scores [B, T, N, 1]

        Returns:
            Output [B, T, N, D]
        """
        B, T, N, D = x.shape

        # Temporal attention (across time for each cell)
        # Reshape: [B, T, N, D] -> [B*N, T, D]
        x_flat = x.transpose(1, 2).reshape(B * N, T, D)
        attn_out, _ = self.temporal_attn(x_flat, x_flat, x_flat)
        attn_out = attn_out.view(B, N, T, D).transpose(1, 2)  # -> [B, T, N, D]
        x = self.norm1(x + self.dropout(attn_out))

        # Spatial attention (across cells for each timestep)
        # Reshape: [B, T, N, D] -> [B*T, N, D]
        x_flat = x.reshape(B * T, N, D)

        # Expand adjacency mask and instability for batch*time
        if adjacency_mask is not None:
            adj_expanded = adjacency_mask.unsqueeze(1).expand(B, T, N, N).reshape(B * T, N, N)
        else:
            adj_expanded = None

        if instability is not None:
            inst_expanded = instability.reshape(B * T, N, 1)
        else:
            inst_expanded = None

        attn_out = self.spatial_attn(x_flat, adj_expanded, inst_expanded)
        attn_out = attn_out.view(B, T, N, D)
        x = self.norm2(x + self.dropout(attn_out))

        # Feedforward
        ffn_out = self.ffn(x)
        x = self.norm3(x + self.dropout(ffn_out))

        return x


class RainModel(nn.Module):
    """
    Rain nowcast/forecast model.

    Predicts:
    - Rainfall accumulation distribution (Gamma parameters)
    - Extreme rainfall exceedance probabilities
    """

    def __init__(
        self,
        d_model: int = 192,
        num_layers: int = 4,
        num_heads: int = 6,
        dim_feedforward: int = 768,
        horizons: list[str] = ["1h", "6h", "12h", "24h"],
        distribution: str = "gamma",
        dropout: float = 0.1,
    ):
        """
        Initialize rain model.

        Args:
            d_model: Model dimension
            num_layers: Number of transformer layers
            num_heads: Number of attention heads
            dim_feedforward: Feedforward dimension
            horizons: Forecast horizons
            distribution: "gamma" or "lognormal"
            dropout: Dropout rate
        """
        super().__init__()
        self.d_model = d_model
        self.horizons = horizons
        self.distribution = distribution

        # Transformer backbone
        self.layers = nn.ModuleList(
            [
                SpatiotemporalTransformerBlock(
                    d_model, num_heads, dim_feedforward, dropout
                )
                for _ in range(num_layers)
            ]
        )

        # Prediction heads (one per horizon)
        self.accumulation_heads = nn.ModuleDict()
        self.exceedance_heads = nn.ModuleDict()

        for horizon in horizons:
            # Accumulation: predict distribution parameters
            if distribution == "gamma":
                # Gamma: shape (k) and rate (θ^-1)
                self.accumulation_heads[horizon] = nn.Linear(d_model, 2)
            elif distribution == "lognormal":
                # LogNormal: mu and sigma
                self.accumulation_heads[horizon] = nn.Linear(d_model, 2)
            else:
                raise ValueError(f"Unknown distribution: {distribution}")

            # Exceedance: binary classification
            self.exceedance_heads[horizon] = nn.Linear(d_model, 1)

    def forward(
        self,
        tokens: torch.Tensor,
        adjacency_mask: Optional[torch.Tensor] = None,
        instability: Optional[torch.Tensor] = None,
    ) -> dict[str, torch.Tensor]:
        """
        Forward pass.

        Args:
            tokens: Input tokens [B, T, N, D] from readability encoder
            adjacency_mask: Spatial adjacency [B, N, N]
            instability: Instability scores [B, T, N, 1]

        Returns:
            Dict of predictions per horizon
        """
        # Pass through transformer
        h = tokens
        for layer in self.layers:
            h = layer(h, adjacency_mask, instability)

        # Use final timestep representation for predictions
        h_final = h[:, -1, :, :]  # [B, N, D]

        predictions = {}

        for horizon in self.horizons:
            # Accumulation distribution
            dist_params = self.accumulation_heads[horizon](h_final)  # [B, N, 2]

            if self.distribution == "gamma":
                shape, rate = dist_params.chunk(2, dim=-1)
                predictions[f"{horizon}_shape"] = shape
                predictions[f"{horizon}_rate"] = rate
            else:  # lognormal
                mu, sigma = dist_params.chunk(2, dim=-1)
                predictions[f"{horizon}_mu"] = mu
                predictions[f"{horizon}_sigma"] = sigma

            # Exceedance probability
            exceedance_logits = self.exceedance_heads[horizon](h_final)  # [B, N, 1]
            predictions[f"{horizon}_exceedance_logits"] = exceedance_logits.squeeze(-1)

        return predictions
