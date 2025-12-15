"""Loss functions for hazard prediction."""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional


class GammaLoss(nn.Module):
    """Negative log-likelihood loss for Gamma distribution."""

    def __init__(self, eps: float = 1e-6):
        """
        Initialize Gamma loss.

        Args:
            eps: Small constant for numerical stability
        """
        super().__init__()
        self.eps = eps

    def forward(
        self, shape: torch.Tensor, rate: torch.Tensor, target: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute Gamma NLL loss.

        Args:
            shape: Shape parameter (k), shape [B, ...]
            rate: Rate parameter (θ^-1), shape [B, ...]
            target: Ground truth values, shape [B, ...]

        Returns:
            Loss scalar
        """
        # Ensure positive parameters
        shape = F.softplus(shape) + self.eps
        rate = F.softplus(rate) + self.eps

        # Gamma NLL: -log p(x|k,θ) = -(-k*log(θ) - log(Γ(k)) + (k-1)*log(x) - x/θ)
        # With rate = 1/θ: -log p(x|k,rate) = k*log(rate) + log(Γ(k)) - (k-1)*log(x) + x*rate

        target = torch.clamp(target, min=self.eps)

        nll = (
            shape * torch.log(rate)
            + torch.lgamma(shape)
            - (shape - 1) * torch.log(target)
            + target * rate
        )

        return nll.mean()


class LogNormalLoss(nn.Module):
    """Negative log-likelihood loss for LogNormal distribution."""

    def __init__(self, eps: float = 1e-6):
        """
        Initialize LogNormal loss.

        Args:
            eps: Small constant for numerical stability
        """
        super().__init__()
        self.eps = eps

    def forward(
        self, mu: torch.Tensor, sigma: torch.Tensor, target: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute LogNormal NLL loss.

        Args:
            mu: Location parameter, shape [B, ...]
            sigma: Scale parameter, shape [B, ...]
            target: Ground truth values, shape [B, ...]

        Returns:
            Loss scalar
        """
        # Ensure positive sigma and target
        sigma = F.softplus(sigma) + self.eps
        target = torch.clamp(target, min=self.eps)

        # LogNormal NLL
        nll = (
            torch.log(target * sigma * torch.sqrt(2 * torch.tensor(torch.pi)))
            + 0.5 * ((torch.log(target) - mu) / sigma) ** 2
        )

        return nll.mean()


class CRPSLoss(nn.Module):
    """Continuous Ranked Probability Score loss for Gaussian distributions."""

    def __init__(self):
        """Initialize CRPS loss."""
        super().__init__()

    def forward(
        self, mean: torch.Tensor, std: torch.Tensor, target: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute CRPS for Gaussian distribution.

        Args:
            mean: Predicted mean, shape [B, ...]
            std: Predicted std, shape [B, ...]
            target: Ground truth, shape [B, ...]

        Returns:
            Loss scalar
        """
        std = F.softplus(std) + 1e-6

        # Standardize
        z = (target - mean) / std

        # CRPS for standard normal
        normal = torch.distributions.Normal(0, 1)
        pdf = torch.exp(normal.log_prob(z))
        cdf = normal.cdf(z)

        crps = std * (z * (2 * cdf - 1) + 2 * pdf - 1 / torch.sqrt(torch.tensor(torch.pi)))

        return crps.mean()


class FocalLoss(nn.Module):
    """Focal loss for imbalanced binary classification."""

    def __init__(self, alpha: float = 0.25, gamma: float = 2.0):
        """
        Initialize focal loss.

        Args:
            alpha: Weighting factor for positive class
            gamma: Focusing parameter (higher = more focus on hard examples)
        """
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma

    def forward(self, logits: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        """
        Compute focal loss.

        Args:
            logits: Predicted logits, shape [B, ...]
            target: Binary ground truth (0 or 1), shape [B, ...]

        Returns:
            Loss scalar
        """
        probs = torch.sigmoid(logits)
        ce_loss = F.binary_cross_entropy_with_logits(logits, target, reduction="none")

        # Focal weight
        p_t = probs * target + (1 - probs) * (1 - target)
        focal_weight = (1 - p_t) ** self.gamma

        # Alpha weighting
        alpha_t = self.alpha * target + (1 - self.alpha) * (1 - target)

        loss = alpha_t * focal_weight * ce_loss

        return loss.mean()


class QuantileLoss(nn.Module):
    """Quantile regression loss (pinball loss)."""

    def __init__(self, quantiles: list[float]):
        """
        Initialize quantile loss.

        Args:
            quantiles: List of quantiles to predict (e.g., [0.1, 0.5, 0.9])
        """
        super().__init__()
        self.quantiles = torch.tensor(quantiles)

    def forward(
        self, predictions: torch.Tensor, target: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute quantile loss.

        Args:
            predictions: Predicted quantiles, shape [B, num_quantiles, ...]
            target: Ground truth, shape [B, ...]

        Returns:
            Loss scalar
        """
        # Expand target to match predictions
        target = target.unsqueeze(1)  # [B, 1, ...]

        errors = target - predictions  # [B, num_quantiles, ...]

        # Move quantiles to same device
        quantiles = self.quantiles.to(predictions.device).view(1, -1, 1)

        # Quantile loss
        loss = torch.max((quantiles - 1) * errors, quantiles * errors)

        return loss.mean()


class MonotonicityRegularizer(nn.Module):
    """Regularizer to enforce monotonic relationships."""

    def __init__(self, weight: float = 0.1):
        """
        Initialize monotonicity regularizer.

        Args:
            weight: Weight for the regularization term
        """
        super().__init__()
        self.weight = weight

    def forward(
        self, x: torch.Tensor, y: torch.Tensor, increasing: bool = True
    ) -> torch.Tensor:
        """
        Penalize violations of monotonicity.

        Args:
            x: Input variable, shape [B, ...]
            y: Output variable, shape [B, ...]
            increasing: If True, enforce y increases with x

        Returns:
            Regularization loss
        """
        # Sort by x
        sorted_idx = torch.argsort(x.flatten())
        x_sorted = x.flatten()[sorted_idx]
        y_sorted = y.flatten()[sorted_idx]

        # Compute differences
        dy = y_sorted[1:] - y_sorted[:-1]

        if increasing:
            # Penalize negative slopes
            violations = F.relu(-dy)
        else:
            # Penalize positive slopes
            violations = F.relu(dy)

        return self.weight * violations.mean()


class TemporalSmoothnessRegularizer(nn.Module):
    """Regularizer to enforce temporal smoothness."""

    def __init__(self, weight: float = 0.01):
        """
        Initialize temporal smoothness regularizer.

        Args:
            weight: Weight for the regularization term
        """
        super().__init__()
        self.weight = weight

    def forward(self, predictions: torch.Tensor) -> torch.Tensor:
        """
        Penalize large temporal variations.

        Args:
            predictions: Time series predictions, shape [B, T, ...]

        Returns:
            Regularization loss (total variation)
        """
        # Total variation in time dimension
        tv = torch.abs(predictions[:, 1:, ...] - predictions[:, :-1, ...])
        return self.weight * tv.mean()


class CombinedHazardLoss(nn.Module):
    """Combined loss for multi-hazard prediction."""

    def __init__(
        self,
        rain_weight: float = 1.0,
        flood_weight: float = 1.5,
        eq_weight: float = 1.0,
        temporal_smoothness_weight: float = 0.01,
        monotonicity_weight: float = 0.1,
    ):
        """
        Initialize combined hazard loss.

        Args:
            rain_weight: Weight for rain loss
            flood_weight: Weight for flood loss
            eq_weight: Weight for earthquake loss
            temporal_smoothness_weight: Weight for temporal smoothness
            monotonicity_weight: Weight for monotonicity constraint
        """
        super().__init__()
        self.rain_weight = rain_weight
        self.flood_weight = flood_weight
        self.eq_weight = eq_weight

        # Individual losses
        self.gamma_loss = GammaLoss()
        self.focal_loss = FocalLoss()
        self.crps_loss = CRPSLoss()

        # Regularizers
        self.temporal_reg = TemporalSmoothnessRegularizer(temporal_smoothness_weight)
        self.monotonic_reg = MonotonicityRegularizer(monotonicity_weight)

    def forward(self, predictions: dict, targets: dict) -> tuple[torch.Tensor, dict]:
        """
        Compute combined loss.

        Args:
            predictions: Dict of predictions with keys:
                - rain_shape, rain_rate: Gamma parameters for rain
                - rain_exceedance_logits: Logits for rain exceedance
                - flood_logits: Logits for flood exceedance
                - eq_mmi_mean, eq_mmi_std: Gaussian params for MMI
                - aftershock_logits: Logits for aftershock
            targets: Dict of targets with corresponding keys

        Returns:
            Tuple of (total_loss, loss_dict)
        """
        loss_dict = {}
        total_loss = 0.0

        # Rain losses
        if "rain_shape" in predictions:
            rain_loss = self.gamma_loss(
                predictions["rain_shape"],
                predictions["rain_rate"],
                targets["rain_accumulation"],
            )
            loss_dict["rain_accumulation"] = rain_loss.item()
            total_loss += self.rain_weight * rain_loss

        if "rain_exceedance_logits" in predictions:
            rain_exc_loss = self.focal_loss(
                predictions["rain_exceedance_logits"], targets["rain_exceedance"]
            )
            loss_dict["rain_exceedance"] = rain_exc_loss.item()
            total_loss += self.rain_weight * rain_exc_loss

        # Flood loss
        if "flood_logits" in predictions:
            flood_loss = self.focal_loss(predictions["flood_logits"], targets["flood_exceedance"])
            loss_dict["flood"] = flood_loss.item()
            total_loss += self.flood_weight * flood_loss

        # Earthquake losses
        if "eq_mmi_mean" in predictions:
            eq_loss = self.crps_loss(
                predictions["eq_mmi_mean"], predictions["eq_mmi_std"], targets["eq_mmi"]
            )
            loss_dict["eq_mmi"] = eq_loss.item()
            total_loss += self.eq_weight * eq_loss

        if "aftershock_logits" in predictions:
            aftershock_loss = self.focal_loss(
                predictions["aftershock_logits"], targets["aftershock"]
            )
            loss_dict["aftershock"] = aftershock_loss.item()
            total_loss += self.eq_weight * aftershock_loss

        # Regularization
        if "rain_exceedance_probs_temporal" in predictions:
            temp_reg = self.temporal_reg(predictions["rain_exceedance_probs_temporal"])
            loss_dict["temporal_smoothness"] = temp_reg.item()
            total_loss += temp_reg

        return total_loss, loss_dict
