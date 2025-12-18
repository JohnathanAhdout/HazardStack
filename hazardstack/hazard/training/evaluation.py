"""Comprehensive evaluation metrics and testing."""

import torch
import numpy as np
from typing import Dict, List, Optional
import logging
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    log_loss,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from scipy.stats import spearmanr
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

logger = logging.getLogger(__name__)


class HazardEvaluator:
    """Comprehensive evaluation for hazard models."""

    def __init__(self, output_dir: str = "results"):
        """Initialize evaluator."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = {}

    def evaluate_probabilistic_predictions(
        self,
        y_true: np.ndarray,
        y_pred_prob: np.ndarray,
        threshold: float = 0.5,
        name: str = "model",
    ) -> Dict[str, float]:
        """
        Evaluate probabilistic binary predictions.

        Args:
            y_true: True binary labels [N]
            y_pred_prob: Predicted probabilities [N]
            threshold: Decision threshold
            name: Model/metric name

        Returns:
            Dict of metrics
        """
        metrics = {}

        # Brier score (lower is better)
        metrics["brier_score"] = brier_score_loss(y_true, y_pred_prob)

        # Log loss (lower is better)
        eps = 1e-15
        y_pred_prob_clipped = np.clip(y_pred_prob, eps, 1 - eps)
        metrics["log_loss"] = log_loss(y_true, y_pred_prob_clipped)

        # AUC-ROC
        if len(np.unique(y_true)) > 1:
            metrics["auc_roc"] = roc_auc_score(y_true, y_pred_prob)
            metrics["auc_pr"] = average_precision_score(y_true, y_pred_prob)
        else:
            metrics["auc_roc"] = np.nan
            metrics["auc_pr"] = np.nan

        # Classification metrics at threshold
        y_pred_binary = (y_pred_prob >= threshold).astype(int)

        tp = np.sum((y_pred_binary == 1) & (y_true == 1))
        fp = np.sum((y_pred_binary == 1) & (y_true == 0))
        tn = np.sum((y_pred_binary == 0) & (y_true == 0))
        fn = np.sum((y_pred_binary == 0) & (y_true == 1))

        metrics["accuracy"] = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
        metrics["precision"] = tp / (tp + fp) if (tp + fp) > 0 else 0
        metrics["recall"] = tp / (tp + fn) if (tp + fn) > 0 else 0
        metrics["f1_score"] = (
            2 * metrics["precision"] * metrics["recall"] / (metrics["precision"] + metrics["recall"])
            if (metrics["precision"] + metrics["recall"]) > 0
            else 0
        )
        metrics["false_alarm_rate"] = fp / (fp + tn) if (fp + tn) > 0 else 0

        # Expected Calibration Error (ECE)
        metrics["ece"] = self._compute_ece(y_true, y_pred_prob)

        logger.info(f"\n{name} - Probabilistic Metrics:")
        for key, value in metrics.items():
            logger.info(f"  {key}: {value:.4f}")

        self.results[name] = metrics
        return metrics

    def evaluate_regression(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        name: str = "regression",
    ) -> Dict[str, float]:
        """
        Evaluate regression predictions.

        Args:
            y_true: True values
            y_pred: Predicted values
            name: Metric name

        Returns:
            Dict of metrics
        """
        metrics = {}

        metrics["mae"] = mean_absolute_error(y_true, y_pred)
        metrics["rmse"] = np.sqrt(mean_squared_error(y_true, y_pred))
        metrics["mse"] = mean_squared_error(y_true, y_pred)
        metrics["r2"] = r2_score(y_true, y_pred)

        # Median Absolute Error
        metrics["median_ae"] = np.median(np.abs(y_true - y_pred))

        # Spearman correlation
        if len(y_true) > 1:
            metrics["spearman_r"], _ = spearmanr(y_true, y_pred)
        else:
            metrics["spearman_r"] = np.nan

        logger.info(f"\n{name} - Regression Metrics:")
        for key, value in metrics.items():
            logger.info(f"  {key}: {value:.4f}")

        self.results[name] = metrics
        return metrics

    def evaluate_distribution_predictions(
        self,
        y_true: np.ndarray,
        pred_mean: np.ndarray,
        pred_std: np.ndarray,
        name: str = "distribution",
    ) -> Dict[str, float]:
        """
        Evaluate probabilistic distribution predictions.

        Args:
            y_true: True values
            pred_mean: Predicted means
            pred_std: Predicted standard deviations
            name: Metric name

        Returns:
            Dict of metrics
        """
        metrics = {}

        # Negative Log-Likelihood (Gaussian assumption)
        nll = 0.5 * np.log(2 * np.pi * pred_std**2) + 0.5 * ((y_true - pred_mean) / pred_std) ** 2
        metrics["nll"] = np.mean(nll)

        # Continuous Ranked Probability Score (CRPS) - Gaussian
        crps = self._compute_crps_gaussian(y_true, pred_mean, pred_std)
        metrics["crps"] = np.mean(crps)

        # Coverage (fraction of true values within prediction intervals)
        z_scores = np.abs(y_true - pred_mean) / pred_std
        metrics["coverage_68"] = np.mean(z_scores <= 1.0)  # ±1σ
        metrics["coverage_95"] = np.mean(z_scores <= 1.96)  # ±2σ

        # Calibration (Probability Integral Transform)
        pit = self._compute_pit(y_true, pred_mean, pred_std)
        metrics["pit_uniformity"] = self._test_pit_uniformity(pit)

        logger.info(f"\n{name} - Distribution Metrics:")
        for key, value in metrics.items():
            logger.info(f"  {key}: {value:.4f}")

        self.results[name] = metrics
        return metrics

    def _compute_ece(
        self,
        y_true: np.ndarray,
        y_pred_prob: np.ndarray,
        n_bins: int = 10,
    ) -> float:
        """Compute Expected Calibration Error."""
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        ece = 0.0

        for i in range(n_bins):
            bin_lower = bin_boundaries[i]
            bin_upper = bin_boundaries[i + 1]

            in_bin = (y_pred_prob > bin_lower) & (y_pred_prob <= bin_upper)
            prob_in_bin = np.sum(in_bin) / len(y_pred_prob)

            if prob_in_bin > 0:
                accuracy_in_bin = np.mean(y_true[in_bin])
                confidence_in_bin = np.mean(y_pred_prob[in_bin])
                ece += prob_in_bin * np.abs(accuracy_in_bin - confidence_in_bin)

        return ece

    def _compute_crps_gaussian(
        self,
        y_true: np.ndarray,
        pred_mean: np.ndarray,
        pred_std: np.ndarray,
    ) -> np.ndarray:
        """Compute CRPS for Gaussian distributions."""
        from scipy.stats import norm

        z = (y_true - pred_mean) / pred_std
        crps = pred_std * (
            z * (2 * norm.cdf(z) - 1) + 2 * norm.pdf(z) - 1 / np.sqrt(np.pi)
        )
        return crps

    def _compute_pit(
        self,
        y_true: np.ndarray,
        pred_mean: np.ndarray,
        pred_std: np.ndarray,
    ) -> np.ndarray:
        """Compute Probability Integral Transform."""
        from scipy.stats import norm

        pit = norm.cdf(y_true, loc=pred_mean, scale=pred_std)
        return pit

    def _test_pit_uniformity(self, pit: np.ndarray) -> float:
        """Test if PIT values are uniform (Kolmogorov-Smirnov test)."""
        from scipy.stats import kstest

        stat, _ = kstest(pit, 'uniform')
        return stat  # Lower is better (closer to uniform)

    def plot_calibration_curve(
        self,
        y_true: np.ndarray,
        y_pred_prob: np.ndarray,
        name: str = "calibration",
        n_bins: int = 10,
    ):
        """Plot calibration curve (reliability diagram)."""
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        bin_centers = (bin_boundaries[:-1] + bin_boundaries[1:]) / 2

        true_fractions = []
        pred_fractions = []

        for i in range(n_bins):
            bin_lower = bin_boundaries[i]
            bin_upper = bin_boundaries[i + 1]

            in_bin = (y_pred_prob > bin_lower) & (y_pred_prob <= bin_upper)

            if np.sum(in_bin) > 0:
                true_fractions.append(np.mean(y_true[in_bin]))
                pred_fractions.append(np.mean(y_pred_prob[in_bin]))
            else:
                true_fractions.append(np.nan)
                pred_fractions.append(bin_centers[i])

        plt.figure(figsize=(8, 8))
        plt.plot([0, 1], [0, 1], 'k--', label='Perfect calibration')
        plt.plot(pred_fractions, true_fractions, 'o-', label=name)
        plt.xlabel('Predicted Probability')
        plt.ylabel('True Fraction')
        plt.title(f'Calibration Curve - {name}')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        output_path = self.output_dir / f"{name}_calibration.png"
        plt.savefig(output_path, dpi=150)
        plt.close()

        logger.info(f"✓ Saved calibration plot: {output_path}")

    def plot_roc_curve(
        self,
        y_true: np.ndarray,
        y_pred_prob: np.ndarray,
        name: str = "roc",
    ):
        """Plot ROC curve."""
        from sklearn.metrics import roc_curve

        fpr, tpr, _ = roc_curve(y_true, y_pred_prob)
        auc = roc_auc_score(y_true, y_pred_prob)

        plt.figure(figsize=(8, 8))
        plt.plot(fpr, tpr, label=f'{name} (AUC = {auc:.3f})')
        plt.plot([0, 1], [0, 1], 'k--', label='Random')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title(f'ROC Curve - {name}')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        output_path = self.output_dir / f"{name}_roc.png"
        plt.savefig(output_path, dpi=150)
        plt.close()

        logger.info(f"✓ Saved ROC curve: {output_path}")

    def save_results(self, filename: str = "evaluation_results.json"):
        """Save all evaluation results to JSON."""
        import json

        output_path = self.output_dir / filename

        with open(output_path, "w") as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"✓ Saved evaluation results: {output_path}")

    def generate_summary_report(self, model_name: str = "HazardStack") -> str:
        """Generate comprehensive summary report."""
        report_lines = []
        report_lines.append("=" * 70)
        report_lines.append(f"EVALUATION REPORT: {model_name}")
        report_lines.append("=" * 70)
        report_lines.append("")

        for metric_group, metrics in self.results.items():
            report_lines.append(f"\n{metric_group.upper()}:")
            report_lines.append("-" * 50)
            for metric_name, value in metrics.items():
                report_lines.append(f"  {metric_name:25s}: {value:10.4f}")

        report_lines.append("\n" + "=" * 70)

        report = "\n".join(report_lines)

        # Save to file
        output_path = self.output_dir / f"{model_name}_evaluation_report.txt"
        with open(output_path, "w") as f:
            f.write(report)

        logger.info(f"✓ Saved evaluation report: {output_path}")
        print(report)

        return report
