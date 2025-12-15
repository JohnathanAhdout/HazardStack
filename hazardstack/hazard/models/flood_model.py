"""Flood exceedance model using basin graph neural network."""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional


class GraphAttentionLayer(nn.Module):
    """Graph Attention Network layer for basin topology."""

    def __init__(self, in_features: int, out_features: int, dropout: float = 0.1):
        """
        Initialize GAT layer.

        Args:
            in_features: Input feature dimension
            out_features: Output feature dimension
            dropout: Dropout rate
        """
        super().__init__()

        # Linear transformations
        self.W = nn.Linear(in_features, out_features, bias=False)

        # Attention mechanism
        self.a = nn.Linear(2 * out_features, 1, bias=False)

        self.leakyrelu = nn.LeakyReLU(0.2)
        self.dropout = nn.Dropout(dropout)

    def forward(
        self,
        x: torch.Tensor,
        adjacency: torch.Tensor,
    ) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Node features [B, N, D_in]
            adjacency: Adjacency matrix [B, N, N] (1 = edge exists)

        Returns:
            Output features [B, N, D_out]
        """
        B, N, D_in = x.shape

        # Transform features
        h = self.W(x)  # [B, N, D_out]

        # Compute attention scores
        # For each pair (i, j), compute attention e_ij
        h_i = h.unsqueeze(2).expand(B, N, N, -1)  # [B, N, N, D_out]
        h_j = h.unsqueeze(1).expand(B, N, N, -1)  # [B, N, N, D_out]

        concat = torch.cat([h_i, h_j], dim=-1)  # [B, N, N, 2*D_out]
        e = self.leakyrelu(self.a(concat).squeeze(-1))  # [B, N, N]

        # Mask non-existent edges
        e = e.masked_fill(adjacency == 0, float("-inf"))

        # Softmax attention weights
        alpha = F.softmax(e, dim=-1)  # [B, N, N]
        alpha = self.dropout(alpha)

        # Aggregate neighbor features
        out = torch.bmm(alpha, h)  # [B, N, D_out]

        return out


class TemporalAggregator(nn.Module):
    """Aggregate temporal information for flood forecasting."""

    def __init__(self, d_model: int, hidden_dim: int = 256):
        """
        Initialize temporal aggregator.

        Args:
            d_model: Model dimension
            hidden_dim: Hidden dimension for LSTM
        """
        super().__init__()

        self.lstm = nn.LSTM(
            input_size=d_model,
            hidden_size=hidden_dim,
            num_layers=2,
            batch_first=True,
            bidirectional=False,  # Causal
            dropout=0.1,
        )

        self.proj = nn.Linear(hidden_dim, d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Aggregate temporal features.

        Args:
            x: Input [B, T, N, D]

        Returns:
            Output [B, N, D]
        """
        B, T, N, D = x.shape

        # Process each basin's time series
        # Reshape: [B, T, N, D] -> [B*N, T, D]
        x_flat = x.transpose(1, 2).reshape(B * N, T, D)

        # LSTM
        out, _ = self.lstm(x_flat)  # [B*N, T, H]

        # Use final timestep
        out_final = out[:, -1, :]  # [B*N, H]

        # Project
        out_final = self.proj(out_final)  # [B*N, D]

        # Reshape back
        out_final = out_final.view(B, N, D)

        return out_final


class FloodModel(nn.Module):
    """
    Flood exceedance prediction model.

    Uses Graph Neural Network to propagate information along river basin topology.
    """

    def __init__(
        self,
        d_model: int = 192,
        gnn_hidden: int = 256,
        num_gnn_layers: int = 3,
        horizons: list[str] = ["12h", "24h"],
        dropout: float = 0.1,
    ):
        """
        Initialize flood model.

        Args:
            d_model: Model dimension
            gnn_hidden: Hidden dimension for GNN
            num_gnn_layers: Number of GNN layers
            horizons: Forecast horizons
            dropout: Dropout rate
        """
        super().__init__()
        self.horizons = horizons

        # Temporal aggregator
        self.temporal_agg = TemporalAggregator(d_model, gnn_hidden)

        # GNN layers
        self.gnn_layers = nn.ModuleList()

        # First layer
        self.gnn_layers.append(GraphAttentionLayer(d_model, gnn_hidden, dropout))

        # Middle layers
        for _ in range(num_gnn_layers - 2):
            self.gnn_layers.append(GraphAttentionLayer(gnn_hidden, gnn_hidden, dropout))

        # Last layer
        self.gnn_layers.append(GraphAttentionLayer(gnn_hidden, d_model, dropout))

        # Layer norms
        self.norms = nn.ModuleList(
            [nn.LayerNorm(gnn_hidden if i < num_gnn_layers - 1 else d_model)
             for i in range(num_gnn_layers)]
        )

        # Prediction heads (one per horizon)
        self.exceedance_heads = nn.ModuleDict()
        for horizon in horizons:
            self.exceedance_heads[horizon] = nn.Sequential(
                nn.Linear(d_model, 128),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(128, 1),
            )

    def forward(
        self,
        tokens: torch.Tensor,
        basin_adjacency: torch.Tensor,
    ) -> dict[str, torch.Tensor]:
        """
        Forward pass.

        Args:
            tokens: Input tokens [B, T, N_basins, D] from readability encoder
            basin_adjacency: Basin adjacency matrix [B, N_basins, N_basins]
                             (upstream -> downstream edges)

        Returns:
            Dict of exceedance predictions per horizon
        """
        # Aggregate temporal information
        h = self.temporal_agg(tokens)  # [B, N, D]

        # Pass through GNN layers (message passing along basin topology)
        for gnn, norm in zip(self.gnn_layers, self.norms):
            h_new = gnn(h, basin_adjacency)
            h = norm(h + h_new)  # Residual connection

        # Predict exceedance for each horizon
        predictions = {}
        for horizon in self.horizons:
            logits = self.exceedance_heads[horizon](h)  # [B, N, 1]
            predictions[f"{horizon}_flood_logits"] = logits.squeeze(-1)

        return predictions
