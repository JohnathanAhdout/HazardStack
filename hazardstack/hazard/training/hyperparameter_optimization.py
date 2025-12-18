"""Hyperparameter optimization using Optuna."""

import optuna
from optuna.pruners import MedianPruner
from optuna.samplers import TPESampler
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import logging
from typing import Dict, Any, Callable
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class HyperparameterOptimizer:
    """Optimize model hyperparameters using Optuna."""

    def __init__(
        self,
        model_factory: Callable,
        train_loader: DataLoader,
        val_loader: DataLoader,
        device: str = "cuda",
        n_trials: int = 50,
        output_dir: str = "results/optuna",
    ):
        """
        Initialize optimizer.

        Args:
            model_factory: Function that creates model given hyperparameters
            train_loader: Training data loader
            val_loader: Validation data loader
            device: Device to train on
            n_trials: Number of optimization trials
            output_dir: Output directory for results
        """
        self.model_factory = model_factory
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.device = device
        self.n_trials = n_trials
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def optimize_earthquake_model(self) -> Dict[str, Any]:
        """Optimize earthquake model hyperparameters."""
        logger.info("Starting hyperparameter optimization for Earthquake model...")

        def objective(trial: optuna.Trial) -> float:
            # Suggest hyperparameters
            params = {
                "d_model": trial.suggest_categorical("d_model", [128, 192, 256]),
                "mmi_hidden_dims": [
                    trial.suggest_int("mmi_hidden_1", 64, 256),
                    trial.suggest_int("mmi_hidden_2", 64, 256),
                    trial.suggest_int("mmi_hidden_3", 32, 128),
                ],
                "hawkes_hidden": trial.suggest_int("hawkes_hidden", 64, 256),
                "hawkes_layers": trial.suggest_int("hawkes_layers", 2, 4),
                "dropout": trial.suggest_float("dropout", 0.05, 0.3),
                "use_spectral_features": trial.suggest_categorical("use_spectral", [True, False]),
                "learning_rate": trial.suggest_float("lr", 1e-5, 1e-3, log=True),
                "weight_decay": trial.suggest_float("weight_decay", 1e-5, 1e-2, log=True),
            }

            # Train and evaluate
            val_loss = self._train_and_evaluate(params, trial, max_epochs=20)

            return val_loss

        study = optuna.create_study(
            direction="minimize",
            sampler=TPESampler(seed=42),
            pruner=MedianPruner(n_startup_trials=5, n_warmup_steps=5),
        )

        study.optimize(objective, n_trials=self.n_trials, show_progress_bar=True)

        best_params = study.best_params
        logger.info(f"Best hyperparameters: {best_params}")
        logger.info(f"Best validation loss: {study.best_value:.4f}")

        # Save results
        self._save_optimization_results(study, "earthquake_model")

        return best_params

    def optimize_flood_model(self) -> Dict[str, Any]:
        """Optimize flood model hyperparameters."""
        logger.info("Starting hyperparameter optimization for Flood model...")

        def objective(trial: optuna.Trial) -> float:
            params = {
                "d_model": trial.suggest_categorical("d_model", [128, 192, 256]),
                "gnn_hidden": trial.suggest_int("gnn_hidden", 128, 384),
                "num_gnn_layers": trial.suggest_int("num_gnn_layers", 2, 5),
                "dropout": trial.suggest_float("dropout", 0.05, 0.3),
                "learning_rate": trial.suggest_float("lr", 1e-5, 1e-3, log=True),
                "weight_decay": trial.suggest_float("weight_decay", 1e-5, 1e-2, log=True),
            }

            val_loss = self._train_and_evaluate(params, trial, max_epochs=20)
            return val_loss

        study = optuna.create_study(
            direction="minimize",
            sampler=TPESampler(seed=42),
            pruner=MedianPruner(n_startup_trials=5, n_warmup_steps=5),
        )

        study.optimize(objective, n_trials=self.n_trials, show_progress_bar=True)

        best_params = study.best_params
        logger.info(f"Best hyperparameters: {best_params}")
        logger.info(f"Best validation loss: {study.best_value:.4f}")

        self._save_optimization_results(study, "flood_model")
        return best_params

    def optimize_rain_model(self) -> Dict[str, Any]:
        """Optimize rain model hyperparameters."""
        logger.info("Starting hyperparameter optimization for Rain model...")

        def objective(trial: optuna.Trial) -> float:
            params = {
                "d_model": trial.suggest_categorical("d_model", [128, 192, 256, 384]),
                "num_layers": trial.suggest_int("num_layers", 3, 6),
                "num_heads": trial.suggest_categorical("num_heads", [4, 6, 8]),
                "dim_feedforward": trial.suggest_int("dim_feedforward", 512, 1024, step=128),
                "dropout": trial.suggest_float("dropout", 0.05, 0.3),
                "learning_rate": trial.suggest_float("lr", 1e-5, 1e-3, log=True),
                "weight_decay": trial.suggest_float("weight_decay", 1e-5, 1e-2, log=True),
            }

            val_loss = self._train_and_evaluate(params, trial, max_epochs=20)
            return val_loss

        study = optuna.create_study(
            direction="minimize",
            sampler=TPESampler(seed=42),
            pruner=MedianPruner(n_startup_trials=5, n_warmup_steps=5),
        )

        study.optimize(objective, n_trials=self.n_trials, show_progress_bar=True)

        best_params = study.best_params
        logger.info(f"Best hyperparameters: {best_params}")
        logger.info(f"Best validation loss: {study.best_value:.4f}")

        self._save_optimization_results(study, "rain_model")
        return best_params

    def _train_and_evaluate(
        self,
        params: Dict[str, Any],
        trial: optuna.Trial,
        max_epochs: int = 20,
    ) -> float:
        """Train model with given hyperparameters and return validation loss."""
        # Create model
        model = self.model_factory(params).to(self.device)

        # Create optimizer
        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=params["learning_rate"],
            weight_decay=params["weight_decay"],
        )

        # Simple training loop
        best_val_loss = float("inf")

        for epoch in range(max_epochs):
            # Train
            model.train()
            train_loss = 0.0

            for batch in self.train_loader:
                optimizer.zero_grad()

                # Move to device
                batch = {
                    k: v.to(self.device) if isinstance(v, torch.Tensor) else v
                    for k, v in batch.items()
                }

                # Forward pass (simplified)
                try:
                    outputs = model(**batch)
                    loss = outputs["loss"] if isinstance(outputs, dict) and "loss" in outputs else outputs
                    loss.backward()
                    optimizer.step()

                    train_loss += loss.item()
                except Exception as e:
                    logger.warning(f"Training error in trial: {e}")
                    return float("inf")

            # Validate
            model.eval()
            val_loss = 0.0

            with torch.no_grad():
                for batch in self.val_loader:
                    batch = {
                        k: v.to(self.device) if isinstance(v, torch.Tensor) else v
                        for k, v in batch.items()
                    }

                    try:
                        outputs = model(**batch)
                        loss = outputs["loss"] if isinstance(outputs, dict) and "loss" in outputs else outputs
                        val_loss += loss.item()
                    except Exception as e:
                        logger.warning(f"Validation error in trial: {e}")
                        return float("inf")

            val_loss /= len(self.val_loader)

            if val_loss < best_val_loss:
                best_val_loss = val_loss

            # Report intermediate value for pruning
            trial.report(val_loss, epoch)

            # Check if trial should be pruned
            if trial.should_prune():
                raise optuna.TrialPruned()

        return best_val_loss

    def _save_optimization_results(self, study: optuna.Study, model_name: str):
        """Save optimization results."""
        # Save best parameters
        best_params_path = self.output_dir / f"{model_name}_best_params.json"
        with open(best_params_path, "w") as f:
            json.dump(study.best_params, f, indent=2)

        logger.info(f"✓ Saved best parameters: {best_params_path}")

        # Save study statistics
        stats = {
            "best_value": study.best_value,
            "best_params": study.best_params,
            "n_trials": len(study.trials),
            "datetime_start": str(study.trials[0].datetime_start) if study.trials else None,
            "datetime_complete": str(study.trials[-1].datetime_complete) if study.trials else None,
        }

        stats_path = self.output_dir / f"{model_name}_optimization_stats.json"
        with open(stats_path, "w") as f:
            json.dump(stats, f, indent=2)

        logger.info(f"✓ Saved optimization statistics: {stats_path}")

        # Save all trial results
        trials_data = []
        for trial in study.trials:
            trials_data.append({
                "number": trial.number,
                "value": trial.value,
                "params": trial.params,
                "state": trial.state.name,
            })

        trials_path = self.output_dir / f"{model_name}_all_trials.json"
        with open(trials_path, "w") as f:
            json.dump(trials_data, f, indent=2)

        logger.info(f"✓ Saved all trial results: {trials_path}")

    def plot_optimization_history(self, study: optuna.Study, model_name: str):
        """Plot optimization history."""
        try:
            from optuna.visualization import plot_optimization_history, plot_param_importances

            # Optimization history
            fig = plot_optimization_history(study)
            fig.write_image(str(self.output_dir / f"{model_name}_optimization_history.png"))

            # Parameter importances
            fig = plot_param_importances(study)
            fig.write_image(str(self.output_dir / f"{model_name}_param_importances.png"))

            logger.info(f"✓ Saved optimization plots for {model_name}")

        except Exception as e:
            logger.warning(f"Could not save optimization plots: {e}")
