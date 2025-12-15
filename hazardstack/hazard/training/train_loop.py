"""Training loop utilities."""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from pathlib import Path
import logging
from typing import Dict, Optional
from tqdm import tqdm
import json

from hazard.common.losses import CombinedHazardLoss
from hazard.common.metrics import brier_score, log_loss

logger = logging.getLogger(__name__)


class Trainer:
    """Generic trainer for hazard models."""

    def __init__(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        val_loader: DataLoader,
        criterion: nn.Module,
        optimizer: torch.optim.Optimizer,
        scheduler: Optional[torch.optim.lr_scheduler._LRScheduler] = None,
        device: str = "cuda",
        output_dir: str = "models/",
        max_epochs: int = 100,
        patience: int = 10,
        gradient_clip: float = 1.0,
    ):
        """
        Initialize trainer.

        Args:
            model: Model to train
            train_loader: Training data loader
            val_loader: Validation data loader
            criterion: Loss function
            optimizer: Optimizer
            scheduler: Optional learning rate scheduler
            device: Device to train on
            output_dir: Directory to save checkpoints
            max_epochs: Maximum training epochs
            patience: Early stopping patience
            gradient_clip: Gradient clipping threshold
        """
        self.model = model.to(device)
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.criterion = criterion
        self.optimizer = optimizer
        self.scheduler = scheduler
        self.device = device
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_epochs = max_epochs
        self.patience = patience
        self.gradient_clip = gradient_clip

        self.best_val_loss = float("inf")
        self.epochs_without_improvement = 0
        self.history = {"train_loss": [], "val_loss": [], "learning_rate": []}

    def train_epoch(self) -> Dict[str, float]:
        """Train for one epoch."""
        self.model.train()
        total_loss = 0.0
        loss_components = {}

        pbar = tqdm(self.train_loader, desc="Training")

        for batch in pbar:
            # Move batch to device
            batch = self._to_device(batch)

            # Forward pass
            self.optimizer.zero_grad()

            predictions = self.model(**self._get_model_inputs(batch))

            # Compute loss
            loss, loss_dict = self.criterion(predictions, batch["targets"])

            # Backward pass
            loss.backward()

            # Gradient clipping
            if self.gradient_clip > 0:
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.gradient_clip)

            self.optimizer.step()

            # Accumulate metrics
            total_loss += loss.item()
            for key, value in loss_dict.items():
                loss_components[key] = loss_components.get(key, 0.0) + value

            pbar.set_postfix({"loss": loss.item()})

        # Average losses
        avg_loss = total_loss / len(self.train_loader)
        avg_components = {k: v / len(self.train_loader) for k, v in loss_components.items()}

        return {"total": avg_loss, **avg_components}

    @torch.no_grad()
    def validate(self) -> Dict[str, float]:
        """Validate on validation set."""
        self.model.eval()
        total_loss = 0.0
        loss_components = {}

        pbar = tqdm(self.val_loader, desc="Validation")

        for batch in pbar:
            batch = self._to_device(batch)

            predictions = self.model(**self._get_model_inputs(batch))

            loss, loss_dict = self.criterion(predictions, batch["targets"])

            total_loss += loss.item()
            for key, value in loss_dict.items():
                loss_components[key] = loss_components.get(key, 0.0) + value

            pbar.set_postfix({"loss": loss.item()})

        avg_loss = total_loss / len(self.val_loader)
        avg_components = {k: v / len(self.val_loader) for k, v in loss_components.items()}

        return {"total": avg_loss, **avg_components}

    def train(self):
        """Full training loop with early stopping."""
        logger.info(f"Starting training for {self.max_epochs} epochs...")

        for epoch in range(self.max_epochs):
            logger.info(f"\nEpoch {epoch + 1}/{self.max_epochs}")

            # Train
            train_metrics = self.train_epoch()
            logger.info(f"Train loss: {train_metrics['total']:.4f}")

            # Validate
            val_metrics = self.validate()
            logger.info(f"Val loss: {val_metrics['total']:.4f}")

            # Update scheduler
            if self.scheduler is not None:
                self.scheduler.step()
                current_lr = self.scheduler.get_last_lr()[0]
                logger.info(f"Learning rate: {current_lr:.6f}")
                self.history["learning_rate"].append(current_lr)

            # Save history
            self.history["train_loss"].append(train_metrics["total"])
            self.history["val_loss"].append(val_metrics["total"])

            # Check for improvement
            if val_metrics["total"] < self.best_val_loss:
                self.best_val_loss = val_metrics["total"]
                self.epochs_without_improvement = 0

                # Save best model
                self.save_checkpoint("best_model.pt", epoch, val_metrics["total"])
                logger.info("✓ Saved best model")

            else:
                self.epochs_without_improvement += 1
                logger.info(
                    f"No improvement for {self.epochs_without_improvement} epochs "
                    f"(best: {self.best_val_loss:.4f})"
                )

                # Early stopping
                if self.epochs_without_improvement >= self.patience:
                    logger.info(f"Early stopping triggered after {epoch + 1} epochs")
                    break

            # Save checkpoint every 10 epochs
            if (epoch + 1) % 10 == 0:
                self.save_checkpoint(f"checkpoint_epoch_{epoch+1}.pt", epoch, val_metrics["total"])

        # Save final checkpoint and history
        self.save_checkpoint("final_model.pt", epoch, val_metrics["total"])
        self.save_history()

        logger.info(f"\nTraining complete. Best val loss: {self.best_val_loss:.4f}")

    def save_checkpoint(self, filename: str, epoch: int, val_loss: float):
        """Save model checkpoint."""
        checkpoint = {
            "epoch": epoch,
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "val_loss": val_loss,
            "best_val_loss": self.best_val_loss,
        }

        if self.scheduler is not None:
            checkpoint["scheduler_state_dict"] = self.scheduler.state_dict()

        torch.save(checkpoint, self.output_dir / filename)

    def save_history(self):
        """Save training history."""
        with open(self.output_dir / "training_history.json", "w") as f:
            json.dump(self.history, f, indent=2)

    def _to_device(self, batch: Dict) -> Dict:
        """Move batch to device recursively."""
        result = {}
        for key, value in batch.items():
            if isinstance(value, torch.Tensor):
                result[key] = value.to(self.device)
            elif isinstance(value, dict):
                result[key] = self._to_device(value)
            else:
                result[key] = value
        return result

    def _get_model_inputs(self, batch: Dict) -> Dict:
        """Extract model inputs from batch."""
        # Override in subclass if needed
        return {
            "features": batch.get("features"),
            "mask": batch.get("mask"),
        }


def create_optimizer(model: nn.Module, learning_rate: float = 1e-4, weight_decay: float = 0.01):
    """Create AdamW optimizer with proper weight decay."""
    # Separate parameters that should and shouldn't have weight decay
    decay_params = []
    no_decay_params = []

    for name, param in model.named_parameters():
        if not param.requires_grad:
            continue

        # Don't apply weight decay to biases and layer norms
        if "bias" in name or "norm" in name or "bn" in name:
            no_decay_params.append(param)
        else:
            decay_params.append(param)

    optimizer = AdamW(
        [
            {"params": decay_params, "weight_decay": weight_decay},
            {"params": no_decay_params, "weight_decay": 0.0},
        ],
        lr=learning_rate,
    )

    return optimizer


def create_scheduler(
    optimizer: torch.optim.Optimizer,
    num_epochs: int,
    scheduler_type: str = "cosine",
):
    """Create learning rate scheduler."""
    if scheduler_type == "cosine":
        return CosineAnnealingLR(optimizer, T_max=num_epochs, eta_min=1e-6)
    elif scheduler_type == "step":
        return torch.optim.lr_scheduler.StepLR(optimizer, step_size=30, gamma=0.1)
    else:
        raise ValueError(f"Unknown scheduler: {scheduler_type}")
