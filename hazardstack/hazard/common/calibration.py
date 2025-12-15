"""Calibration methods for probabilistic forecasts."""

import numpy as np
import numpy.typing as npt
from typing import Optional, Literal
from scipy.optimize import minimize
from sklearn.isotonic import IsotonicRegression
import json


class TemperatureScaling:
    """Temperature scaling for calibrating neural network outputs."""

    def __init__(self):
        """Initialize temperature scaling."""
        self.temperature = 1.0

    def fit(self, logits: npt.NDArray, y_true: npt.NDArray):
        """
        Fit temperature parameter.

        Args:
            logits: Uncalibrated logits, shape [N]
            y_true: Binary ground truth, shape [N]
        """

        def nll_loss(T):
            """Negative log-likelihood with temperature."""
            scaled_probs = self._sigmoid(logits / T)
            eps = 1e-15
            scaled_probs = np.clip(scaled_probs, eps, 1 - eps)
            nll = -np.mean(
                y_true * np.log(scaled_probs) + (1 - y_true) * np.log(1 - scaled_probs)
            )
            return nll

        # Optimize temperature
        result = minimize(nll_loss, x0=1.0, bounds=[(0.1, 10.0)], method="L-BFGS-B")
        self.temperature = result.x[0]

    def transform(self, logits: npt.NDArray) -> npt.NDArray:
        """
        Apply temperature scaling.

        Args:
            logits: Uncalibrated logits

        Returns:
            Calibrated probabilities
        """
        return self._sigmoid(logits / self.temperature)

    def fit_transform(self, logits: npt.NDArray, y_true: npt.NDArray) -> npt.NDArray:
        """Fit and transform in one step."""
        self.fit(logits, y_true)
        return self.transform(logits)

    @staticmethod
    def _sigmoid(x):
        """Numerically stable sigmoid."""
        return np.where(
            x >= 0, 1 / (1 + np.exp(-x)), np.exp(x) / (1 + np.exp(x))
        )

    def save(self, path: str):
        """Save calibration parameters."""
        with open(path, "w") as f:
            json.dump({"temperature": float(self.temperature)}, f)

    def load(self, path: str):
        """Load calibration parameters."""
        with open(path, "r") as f:
            params = json.load(f)
        self.temperature = params["temperature"]


class IsotonicCalibration:
    """Isotonic regression calibration."""

    def __init__(self):
        """Initialize isotonic calibration."""
        self.calibrator = IsotonicRegression(out_of_bounds="clip")

    def fit(self, y_pred: npt.NDArray, y_true: npt.NDArray):
        """
        Fit isotonic regression.

        Args:
            y_pred: Predicted probabilities, shape [N]
            y_true: Binary ground truth, shape [N]
        """
        self.calibrator.fit(y_pred, y_true)

    def transform(self, y_pred: npt.NDArray) -> npt.NDArray:
        """
        Apply isotonic calibration.

        Args:
            y_pred: Uncalibrated probabilities

        Returns:
            Calibrated probabilities
        """
        return self.calibrator.transform(y_pred)

    def fit_transform(self, y_pred: npt.NDArray, y_true: npt.NDArray) -> npt.NDArray:
        """Fit and transform in one step."""
        self.fit(y_pred, y_true)
        return self.transform(y_pred)

    def save(self, path: str):
        """Save calibration parameters."""
        import pickle

        with open(path, "wb") as f:
            pickle.dump(self.calibrator, f)

    def load(self, path: str):
        """Load calibration parameters."""
        import pickle

        with open(path, "rb") as f:
            self.calibrator = pickle.load(f)


class BetaCalibration:
    """Beta calibration for binary classification."""

    def __init__(self):
        """Initialize beta calibration."""
        self.a = 1.0
        self.b = 1.0
        self.c = 0.0

    def fit(self, y_pred: npt.NDArray, y_true: npt.NDArray):
        """
        Fit beta calibration parameters.

        Args:
            y_pred: Predicted probabilities, shape [N]
            y_true: Binary ground truth, shape [N]
        """

        def nll_loss(params):
            """Negative log-likelihood."""
            a, b, c = params
            # Transform predictions
            calibrated = self._beta_transform(y_pred, a, b, c)
            eps = 1e-15
            calibrated = np.clip(calibrated, eps, 1 - eps)
            nll = -np.mean(
                y_true * np.log(calibrated) + (1 - y_true) * np.log(1 - calibrated)
            )
            return nll

        # Optimize parameters
        result = minimize(
            nll_loss,
            x0=[1.0, 1.0, 0.0],
            bounds=[(0.01, 100.0), (0.01, 100.0), (-10.0, 10.0)],
            method="L-BFGS-B",
        )
        self.a, self.b, self.c = result.x

    def transform(self, y_pred: npt.NDArray) -> npt.NDArray:
        """Apply beta calibration."""
        return self._beta_transform(y_pred, self.a, self.b, self.c)

    def fit_transform(self, y_pred: npt.NDArray, y_true: npt.NDArray) -> npt.NDArray:
        """Fit and transform in one step."""
        self.fit(y_pred, y_true)
        return self.transform(y_pred)

    @staticmethod
    def _beta_transform(p, a, b, c):
        """Beta transformation."""
        eps = 1e-15
        p = np.clip(p, eps, 1 - eps)
        logit_p = np.log(p / (1 - p))
        calibrated_logit = a * logit_p + b * np.log(np.maximum(p, eps)) + c
        return 1 / (1 + np.exp(-calibrated_logit))

    def save(self, path: str):
        """Save calibration parameters."""
        with open(path, "w") as f:
            json.dump({"a": float(self.a), "b": float(self.b), "c": float(self.c)}, f)

    def load(self, path: str):
        """Load calibration parameters."""
        with open(path, "r") as f:
            params = json.load(f)
        self.a = params["a"]
        self.b = params["b"]
        self.c = params["c"]


class PlattScaling:
    """Platt scaling (logistic calibration)."""

    def __init__(self):
        """Initialize Platt scaling."""
        self.a = 1.0
        self.b = 0.0

    def fit(self, scores: npt.NDArray, y_true: npt.NDArray):
        """
        Fit Platt scaling parameters.

        Args:
            scores: Uncalibrated scores (can be logits or probabilities)
            y_true: Binary ground truth
        """

        def nll_loss(params):
            """Negative log-likelihood."""
            a, b = params
            probs = 1 / (1 + np.exp(-(a * scores + b)))
            eps = 1e-15
            probs = np.clip(probs, eps, 1 - eps)
            nll = -np.mean(y_true * np.log(probs) + (1 - y_true) * np.log(1 - probs))
            return nll

        result = minimize(
            nll_loss, x0=[1.0, 0.0], bounds=[(-100, 100), (-100, 100)], method="L-BFGS-B"
        )
        self.a, self.b = result.x

    def transform(self, scores: npt.NDArray) -> npt.NDArray:
        """Apply Platt scaling."""
        return 1 / (1 + np.exp(-(self.a * scores + self.b)))

    def fit_transform(self, scores: npt.NDArray, y_true: npt.NDArray) -> npt.NDArray:
        """Fit and transform in one step."""
        self.fit(scores, y_true)
        return self.transform(scores)

    def save(self, path: str):
        """Save calibration parameters."""
        with open(path, "w") as f:
            json.dump({"a": float(self.a), "b": float(self.b)}, f)

    def load(self, path: str):
        """Load calibration parameters."""
        with open(path, "r") as f:
            params = json.load(f)
        self.a = params["a"]
        self.b = params["b"]


def get_calibrator(
    method: Literal["temperature", "isotonic", "beta", "platt"] = "temperature"
):
    """
    Get a calibrator instance.

    Args:
        method: Calibration method

    Returns:
        Calibrator instance
    """
    if method == "temperature":
        return TemperatureScaling()
    elif method == "isotonic":
        return IsotonicCalibration()
    elif method == "beta":
        return BetaCalibration()
    elif method == "platt":
        return PlattScaling()
    else:
        raise ValueError(f"Unknown calibration method: {method}")
