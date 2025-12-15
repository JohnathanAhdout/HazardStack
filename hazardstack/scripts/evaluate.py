"""Comprehensive evaluation script."""

import argparse
import sys
from pathlib import Path
import torch
import json
import numpy as np
from datetime import datetime
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from hazard.common.io import load_config
from hazard.common.metrics import (
    brier_score,
    log_loss,
    expected_calibration_error,
    reliability_curve,
    lead_time_at_false_alarm_rate,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def evaluate_rain_model(model_path: str, test_loader, config: dict) -> dict:
    """
    Evaluate rain model on test set.

    Args:
        model_path: Path to trained model
        test_loader: Test data loader
        config: Configuration dict

    Returns:
        Dict of evaluation metrics
    """
    logger.info("Evaluating rain model...")

    # Load model
    # TODO: Implement model loading

    metrics = {}

    # For each horizon
    for horizon in config["time"]["horizons"]:
        logger.info(f"  Evaluating horizon: {horizon}")

        y_true_exceedance = []
        y_pred_exceedance = []
        lead_times = []

        # Run inference on test set
        # TODO: Implement inference loop

        # Compute metrics
        if len(y_true_exceedance) > 0:
            y_true = np.array(y_true_exceedance)
            y_pred = np.array(y_pred_exceedance)

            metrics[f"{horizon}_brier"] = brier_score(y_true, y_pred)
            metrics[f"{horizon}_log_loss"] = log_loss(y_true, y_pred)

            ece, acc, conf, counts = expected_calibration_error(y_true, y_pred)
            metrics[f"{horizon}_ece"] = ece

            # Lead time at fixed FAR
            for far in config["evaluation"]["false_alarm_rates"]:
                threshold, mean_lead = lead_time_at_false_alarm_rate(
                    y_true, y_pred, np.array(lead_times), target_far=far
                )
                metrics[f"{horizon}_lead_time_far{far}"] = mean_lead

    return metrics


def evaluate_flood_model(model_path: str, test_loader, config: dict) -> dict:
    """Evaluate flood model."""
    logger.info("Evaluating flood model...")

    metrics = {}

    # TODO: Implement flood evaluation

    return metrics


def evaluate_earthquake_model(model_path: str, test_loader, config: dict) -> dict:
    """Evaluate earthquake model."""
    logger.info("Evaluating earthquake model...")

    metrics = {}

    # TODO: Implement earthquake evaluation

    return metrics


def regional_backtesting(config: dict) -> dict:
    """
    Backtest on historical disasters.

    Test performance on known historical events:
    - 2018 Kerala floods
    - 2013 Uttarakhand floods
    - 2001 Bhuj earthquake
    - 2004 Sumatra earthquake (Andaman impact)
    """
    logger.info("Running regional backtesting...")

    results = {}

    regions = config["evaluation"]["backtesting_regions"]

    for region in regions:
        logger.info(f"  Testing region: {region}")

        # TODO: Load historical event data for region
        # TODO: Run model inference
        # TODO: Compute metrics

        results[region] = {
            "brier": 0.0,
            "ece": 0.0,
            "lead_time": 0.0,
        }

    return results


def main():
    parser = argparse.ArgumentParser(description="Comprehensive evaluation")
    parser.add_argument(
        "--config",
        default="configs/india_v1.yaml",
        help="Config file",
    )
    parser.add_argument(
        "--models",
        default="models/",
        help="Directory with trained models",
    )
    parser.add_argument(
        "--test-data",
        default="data/processed/test/",
        help="Test data directory",
    )
    parser.add_argument(
        "--output",
        default="results/evaluation_report.json",
        help="Output JSON file",
    )

    args = parser.parse_args()

    # Load config
    config = load_config(args.config)

    logger.info("Starting comprehensive evaluation...")
    logger.info(f"Models: {args.models}")
    logger.info(f"Test data: {args.test_data}")

    # Initialize results
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "config": args.config,
        "models_dir": args.models,
        "metrics": {},
    }

    # Evaluate rain model
    rain_model_path = Path(args.models) / "rain/best_model.pt"
    if rain_model_path.exists():
        # TODO: Create test loader
        rain_metrics = evaluate_rain_model(str(rain_model_path), None, config)
        results["metrics"]["rain"] = rain_metrics
    else:
        logger.warning(f"Rain model not found: {rain_model_path}")

    # Evaluate flood model
    flood_model_path = Path(args.models) / "flood/best_model.pt"
    if flood_model_path.exists():
        flood_metrics = evaluate_flood_model(str(flood_model_path), None, config)
        results["metrics"]["flood"] = flood_metrics
    else:
        logger.warning(f"Flood model not found: {flood_model_path}")

    # Evaluate earthquake model
    eq_model_path = Path(args.models) / "eq/best_model.pt"
    if eq_model_path.exists():
        eq_metrics = evaluate_earthquake_model(str(eq_model_path), None, config)
        results["metrics"]["earthquake"] = eq_metrics
    else:
        logger.warning(f"Earthquake model not found: {eq_model_path}")

    # Regional backtesting
    regional_results = regional_backtesting(config)
    results["regional_backtesting"] = regional_results

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"\n✓ Evaluation complete!")
    logger.info(f"Results saved to: {output_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(json.dumps(results["metrics"], indent=2))
    print("=" * 60)


if __name__ == "__main__":
    main()
