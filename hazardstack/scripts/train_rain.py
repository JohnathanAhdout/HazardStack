"""Train rain nowcast/forecast model."""

import argparse
import sys
from pathlib import Path
import torch
from torch.utils.data import DataLoader
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from hazard.common.io import load_config
from hazard.common.losses import CombinedHazardLoss
from hazard.models.readability.token_mixer import ReadabilityEncoder
from hazard.models.rain_model import RainModel
from hazard.training.datasets import RainDataset, collate_rain_batch
from hazard.training.train_loop import Trainer, create_optimizer, create_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Train rain model")
    parser.add_argument(
        "--config",
        default="configs/india_v1.yaml",
        help="Config file",
    )
    parser.add_argument(
        "--data-dir",
        default="data/processed/rain",
        help="Directory with processed tokens",
    )
    parser.add_argument(
        "--output",
        default="models/rain",
        help="Output directory for checkpoints",
    )
    parser.add_argument(
        "--device",
        default="cuda" if torch.cuda.is_available() else "cpu",
        help="Device to train on",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Batch size (default from config)",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=None,
        help="Max epochs (default from config)",
    )

    args = parser.parse_args()

    # Load config
    config = load_config(args.config)
    train_config = config["training"]
    model_config = config["models"]

    # Override config with CLI args
    batch_size = args.batch_size or train_config["batch_size"]
    max_epochs = args.epochs or train_config["max_epochs"]

    logger.info(f"Training rain model with config: {args.config}")
    logger.info(f"Device: {args.device}")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Max epochs: {max_epochs}")

    # Create datasets
    logger.info("Loading datasets...")

    train_dataset = RainDataset(
        data_dir=args.data_dir,
        window_steps=model_config["rain"]["window_steps"],
        horizons=config["time"]["horizons"],
        split="train",
    )

    val_dataset = RainDataset(
        data_dir=args.data_dir,
        window_steps=model_config["rain"]["window_steps"],
        horizons=config["time"]["horizons"],
        split="val",
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=4,
        collate_fn=collate_rain_batch,
        pin_memory=True,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=4,
        collate_fn=collate_rain_batch,
        pin_memory=True,
    )

    logger.info(f"Train samples: {len(train_dataset)}")
    logger.info(f"Val samples: {len(val_dataset)}")

    # Create model
    logger.info("Building model...")

    # Readability encoder
    input_dim = 20  # TODO: Get from config/data
    readability = ReadabilityEncoder(
        input_dim=input_dim,
        d_model=model_config["d_model"],
        hidden_channels=model_config["readability"]["causal_conv_channels"],
        num_denoise_layers=model_config["readability"]["causal_conv_layers"],
        dropout=model_config["dropout"],
    )

    # Rain model
    rain_model = RainModel(
        d_model=model_config["d_model"],
        num_layers=model_config["rain"]["backbone_layers"],
        num_heads=model_config["rain"]["attention_heads"],
        horizons=config["time"]["horizons"],
        distribution=model_config["rain"]["distribution"],
        dropout=model_config["dropout"],
    )

    # Combined model
    class CombinedRainModel(torch.nn.Module):
        def __init__(self, readability, rain_model):
            super().__init__()
            self.readability = readability
            self.rain_model = rain_model

        def forward(self, features, mask, **kwargs):
            # Dummy time/spatial coords for now
            B, T, N, D = features.shape
            time_idx = torch.arange(T, device=features.device).unsqueeze(0).expand(B, -1)
            lats = torch.zeros(B, N, device=features.device)
            lons = torch.zeros(B, N, device=features.device)
            season_sin = torch.zeros(B, T, device=features.device)
            season_cos = torch.zeros(B, T, device=features.device)

            tokens, uncertainty, instability = self.readability(
                features, mask, time_idx, lats, lons, season_sin, season_cos
            )

            return self.rain_model(tokens, instability=instability)

    model = CombinedRainModel(readability, rain_model)

    logger.info(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")

    # Create optimizer and scheduler
    optimizer = create_optimizer(
        model,
        learning_rate=train_config["learning_rate"],
        weight_decay=train_config["weight_decay"],
    )

    scheduler = create_scheduler(optimizer, max_epochs, scheduler_type="cosine")

    # Create loss
    criterion = CombinedHazardLoss(
        rain_weight=train_config["loss_weights"]["rain_accumulation"],
        temporal_smoothness_weight=train_config["regularization"]["temporal_smoothness"],
    )

    # Create trainer
    trainer = Trainer(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        criterion=criterion,
        optimizer=optimizer,
        scheduler=scheduler,
        device=args.device,
        output_dir=args.output,
        max_epochs=max_epochs,
        patience=train_config["patience"],
        gradient_clip=train_config["gradient_clip"],
    )

    # Train
    logger.info("\nStarting training...")
    trainer.train()

    logger.info(f"\n✓ Training complete! Models saved to: {args.output}")


if __name__ == "__main__":
    main()
