"""Causal State Space Model for temporal sequence modeling."""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional


class CausalSSMBlock(nn.Module):
    """
    Causal State Space Model block for streaming time series.

    Based on S4/S5 architectures but simplified for real-time inference.
    """

    def __init__(
        self,
        d_model: int,
        d_state: int = 64,
        dropout: float = 0.1,
    ):
        """
        Initialize Causal SSM block.

        Args:
            d_model: Model dimension
            d_state: State dimension
            dropout: Dropout rate
        """
        super().__init__()
        self.d_model = d_model
        self.d_state = d_state

        # SSM parameters (simplified diagonal form for efficiency)
        self.A = nn.Parameter(torch.randn(d_state))  # State transition (diagonal)
        self.B = nn.Linear(d_model, d_state, bias=False)  # Input to state
        self.C = nn.Linear(d_state, d_model, bias=False)  # State to output
        self.D = nn.Parameter(torch.randn(d_model))  # Skip connection

        # Normalization
        self.norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

        # Initialize A to be stable (negative real parts)
        with torch.no_grad():
            self.A.data = -torch.exp(torch.randn(d_state))

    def forward(
        self, x: torch.Tensor, state: Optional[torch.Tensor] = None
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass.

        Args:
            x: Input tensor [B, T, D]
            state: Optional previous state [B, d_state]

        Returns:
            Tuple of (output [B, T, D], final_state [B, d_state])
        """
        B, T, D = x.shape

        # Initialize state if not provided
        if state is None:
            state = torch.zeros(B, self.d_state, device=x.device, dtype=x.dtype)

        outputs = []

        # Process sequence causally
        for t in range(T):
            x_t = x[:, t, :]  # [B, D]

            # SSM update: x_{t+1} = A * x_t + B * u_t
            state = torch.sigmoid(self.A) * state + self.B(x_t)

            # Output: y_t = C * x_t + D * u_t
            y_t = self.C(state) + self.D * x_t

            outputs.append(y_t)

        # Stack outputs
        y = torch.stack(outputs, dim=1)  # [B, T, D]

        # Residual + normalization
        y = self.norm(x + self.dropout(y))

        return y, state

    def step(self, x_t: torch.Tensor, state: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Single step (for streaming inference).

        Args:
            x_t: Input at time t [B, D]
            state: Current state [B, d_state]

        Returns:
            Tuple of (output [B, D], new_state [B, d_state])
        """
        # Update state
        new_state = torch.sigmoid(self.A) * state + self.B(x_t)

        # Compute output
        y_t = self.C(new_state) + self.D * x_t

        # Residual + norm
        y_t = self.norm(x_t + self.dropout(y_t))

        return y_t, new_state


class CausalSSM(nn.Module):
    """Multi-layer Causal State Space Model."""

    def __init__(
        self,
        d_model: int,
        d_state: int = 64,
        n_layers: int = 4,
        dropout: float = 0.1,
    ):
        """
        Initialize multi-layer Causal SSM.

        Args:
            d_model: Model dimension
            d_state: State dimension
            n_layers: Number of SSM layers
            dropout: Dropout rate
        """
        super().__init__()
        self.d_model = d_model
        self.n_layers = n_layers

        self.layers = nn.ModuleList(
            [CausalSSMBlock(d_model, d_state, dropout) for _ in range(n_layers)]
        )

    def forward(
        self, x: torch.Tensor, states: Optional[list[torch.Tensor]] = None
    ) -> tuple[torch.Tensor, list[torch.Tensor]]:
        """
        Forward pass through all layers.

        Args:
            x: Input [B, T, D]
            states: Optional list of previous states

        Returns:
            Tuple of (output [B, T, D], list of final states)
        """
        if states is None:
            states = [None] * self.n_layers

        new_states = []
        h = x

        for layer, state in zip(self.layers, states):
            h, new_state = layer(h, state)
            new_states.append(new_state)

        return h, new_states

    def init_states(self, batch_size: int, device: torch.device) -> list[torch.Tensor]:
        """Initialize zero states for streaming."""
        return [
            torch.zeros(
                batch_size, layer.d_state, device=device, dtype=torch.float32
            )
            for layer in self.layers
        ]
