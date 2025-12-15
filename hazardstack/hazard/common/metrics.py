"""Evaluation metrics for probabilistic forecasting."""

import numpy as np
import numpy.typing as npt
from typing import Tuple, Optional
from scipy import stats


def brier_score(y_true: npt.NDArray, y_pred: npt.NDArray) -> float:
    """
    Calculate Brier score for binary predictions.

    Args:
        y_true: Binary ground truth (0 or 1), shape [N]
        y_pred: Predicted probabilities [0, 1], shape [N]

    Returns:
        Brier score (lower is better, 0 is perfect)
    """
    return np.mean((y_pred - y_true) ** 2)


def log_loss(y_true: npt.NDArray, y_pred: npt.NDArray, eps: float = 1e-15) -> float:
    """
    Calculate log loss (cross-entropy) for binary predictions.

    Args:
        y_true: Binary ground truth (0 or 1), shape [N]
        y_pred: Predicted probabilities [0, 1], shape [N]
        eps: Small constant to avoid log(0)

    Returns:
        Log loss (lower is better)
    """
    y_pred = np.clip(y_pred, eps, 1 - eps)
    return -np.mean(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))


def crps_gaussian(
    y_true: npt.NDArray, mean: npt.NDArray, std: npt.NDArray
) -> npt.NDArray:
    """
    Calculate Continuous Ranked Probability Score for Gaussian distributions.

    Args:
        y_true: Ground truth values, shape [N]
        mean: Predicted mean, shape [N]
        std: Predicted standard deviation, shape [N]

    Returns:
        CRPS for each sample, shape [N]
    """
    # Standardize
    z = (y_true - mean) / std

    # CRPS for standard normal
    crps_std = std * (
        z * (2 * stats.norm.cdf(z) - 1)
        + 2 * stats.norm.pdf(z)
        - 1 / np.sqrt(np.pi)
    )

    return crps_std


def crps_ensemble(y_true: npt.NDArray, ensemble: npt.NDArray) -> npt.NDArray:
    """
    Calculate CRPS from ensemble forecasts.

    Args:
        y_true: Ground truth, shape [N]
        ensemble: Ensemble predictions, shape [N, M] where M is ensemble size

    Returns:
        CRPS for each sample, shape [N]
    """
    M = ensemble.shape[1]

    # Sort ensemble
    ensemble_sorted = np.sort(ensemble, axis=1)

    # Expected value term
    e1 = np.mean(np.abs(ensemble - y_true[:, None]), axis=1)

    # Pairwise differences term
    e2 = 0.0
    for i in range(M):
        for j in range(M):
            e2 += np.abs(ensemble[:, i] - ensemble[:, j])
    e2 = e2 / (2 * M * M)

    crps = e1 - e2
    return crps


def expected_calibration_error(
    y_true: npt.NDArray, y_pred: npt.NDArray, n_bins: int = 10
) -> Tuple[float, npt.NDArray, npt.NDArray, npt.NDArray]:
    """
    Calculate Expected Calibration Error (ECE).

    Args:
        y_true: Binary ground truth (0 or 1), shape [N]
        y_pred: Predicted probabilities [0, 1], shape [N]
        n_bins: Number of bins for calibration curve

    Returns:
        Tuple of (ECE, bin_accuracies, bin_confidences, bin_counts)
    """
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_lowers = bin_boundaries[:-1]
    bin_uppers = bin_boundaries[1:]

    accuracies = []
    confidences = []
    counts = []

    ece = 0.0
    n_total = len(y_pred)

    for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
        # Find samples in this bin
        in_bin = (y_pred > bin_lower) & (y_pred <= bin_upper)
        count = in_bin.sum()

        if count > 0:
            accuracy = y_true[in_bin].mean()
            confidence = y_pred[in_bin].mean()

            ece += (count / n_total) * np.abs(accuracy - confidence)

            accuracies.append(accuracy)
            confidences.append(confidence)
            counts.append(count)
        else:
            accuracies.append(0.0)
            confidences.append(0.0)
            counts.append(0)

    return ece, np.array(accuracies), np.array(confidences), np.array(counts)


def reliability_curve(
    y_true: npt.NDArray, y_pred: npt.NDArray, n_bins: int = 10
) -> Tuple[npt.NDArray, npt.NDArray]:
    """
    Calculate reliability curve (calibration curve).

    Args:
        y_true: Binary ground truth
        y_pred: Predicted probabilities
        n_bins: Number of bins

    Returns:
        Tuple of (mean_predicted_value, fraction_of_positives)
    """
    from sklearn.calibration import calibration_curve

    fraction_of_positives, mean_predicted_value = calibration_curve(
        y_true, y_pred, n_bins=n_bins, strategy="uniform"
    )

    return mean_predicted_value, fraction_of_positives


def lead_time_at_false_alarm_rate(
    y_true: npt.NDArray,
    y_pred: npt.NDArray,
    lead_times: npt.NDArray,
    target_far: float = 0.2,
) -> Tuple[float, float]:
    """
    Calculate lead time at a target false alarm rate.

    Args:
        y_true: Binary ground truth (0 or 1), shape [N]
        y_pred: Predicted probabilities, shape [N]
        lead_times: Lead time for each forecast in hours, shape [N]
        target_far: Target false alarm rate (e.g., 0.2 = 20%)

    Returns:
        Tuple of (threshold, mean_lead_time)
    """
    # Sort by prediction descending
    sorted_idx = np.argsort(y_pred)[::-1]
    y_true_sorted = y_true[sorted_idx]
    y_pred_sorted = y_pred[sorted_idx]
    lead_times_sorted = lead_times[sorted_idx]

    # Find threshold where FAR = target
    n_total = len(y_true)
    cumsum_positives = np.cumsum(y_true_sorted)
    cumsum_total = np.arange(1, n_total + 1)

    # False alarm rate = FP / (FP + TN) = (total_forecasts - TP) / total_forecasts
    # Actually, we want: FAR = FP / (TP + FP) = (forecasted_yes - TP) / forecasted_yes
    far = (cumsum_total - cumsum_positives) / cumsum_total

    # Find first index where FAR <= target
    valid_idx = np.where(far <= target_far)[0]

    if len(valid_idx) == 0:
        return y_pred.min(), 0.0

    idx = valid_idx[0]
    threshold = y_pred_sorted[idx]

    # Mean lead time for forecasts above threshold
    above_threshold = y_pred >= threshold
    if above_threshold.sum() == 0:
        return threshold, 0.0

    mean_lead = lead_times[above_threshold & (y_true == 1)].mean()

    return threshold, mean_lead


def skill_score(forecast: npt.NDArray, reference: npt.NDArray, observed: npt.NDArray) -> float:
    """
    Calculate skill score comparing forecast to reference.

    SS = 1 - (MSE_forecast / MSE_reference)

    Args:
        forecast: Forecast values
        reference: Reference (baseline) values
        observed: Observed values

    Returns:
        Skill score (>0 means forecast is better than reference)
    """
    mse_forecast = np.mean((forecast - observed) ** 2)
    mse_reference = np.mean((reference - observed) ** 2)

    if mse_reference == 0:
        return np.nan

    return 1 - (mse_forecast / mse_reference)


def roc_auc_score(y_true: npt.NDArray, y_pred: npt.NDArray) -> float:
    """
    Calculate ROC AUC score.

    Args:
        y_true: Binary ground truth
        y_pred: Predicted probabilities

    Returns:
        AUC score
    """
    from sklearn.metrics import roc_auc_score as sklearn_roc_auc

    return sklearn_roc_auc(y_true, y_pred)


def precision_recall_at_k(
    y_true: npt.NDArray, y_pred: npt.NDArray, k: int
) -> Tuple[float, float]:
    """
    Calculate precision and recall for top-k predictions.

    Args:
        y_true: Binary ground truth
        y_pred: Predicted probabilities
        k: Number of top predictions to consider

    Returns:
        Tuple of (precision, recall)
    """
    # Get top-k indices
    top_k_idx = np.argsort(y_pred)[-k:]

    # Calculate metrics
    tp = y_true[top_k_idx].sum()
    precision = tp / k if k > 0 else 0.0
    recall = tp / y_true.sum() if y_true.sum() > 0 else 0.0

    return precision, recall
