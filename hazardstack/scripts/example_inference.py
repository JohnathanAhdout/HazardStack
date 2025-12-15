"""Example inference script demonstrating the full pipeline."""

import sys
from pathlib import Path
import torch
import numpy as np
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from hazard.common.geo import H3Grid
from hazard.common.time import get_season_embedding
from hazard.common.io import load_config
from hazard.models.readability.token_mixer import ReadabilityEncoder
from hazard.models.rain_model import RainModel


def main():
    """Example end-to-end inference."""
    print("🌍 HazardStack Inference Example\n")

    # 1. Load configuration
    print("Loading configuration...")
    config = load_config("configs/india_v1.yaml")

    # 2. Initialize H3 grid
    print("Initializing H3 grid...")
    grid = H3Grid(
        resolution=config["grid"]["h3_resolution"],
        bounds=config["grid"]["india_bounds"],
    )
    print(f"   Grid has {len(grid.cells)} cells")

    # 3. Initialize models (normally loaded from checkpoint)
    print("\nInitializing models...")
    d_model = config["models"]["d_model"]

    # Readability encoder
    readability_encoder = ReadabilityEncoder(
        input_dim=20,  # Example: 20 raw features per cell
        d_model=d_model,
        hidden_channels=config["models"]["readability"]["causal_conv_channels"],
        num_denoise_layers=config["models"]["readability"]["causal_conv_layers"],
    )

    # Rain model
    rain_model = RainModel(
        d_model=d_model,
        num_layers=config["models"]["rain"]["backbone_layers"],
        num_heads=config["models"]["rain"]["attention_heads"],
        horizons=["1h", "6h", "24h"],
        distribution=config["models"]["rain"]["distribution"],
    )

    print("   Models initialized (untrained - for demo only)")

    # 4. Generate mock input data
    print("\nGenerating mock input data...")
    batch_size = 1
    window_steps = config["models"]["rain"]["window_steps"]
    num_cells = 100  # Use subset of cells for demo
    input_dim = 20

    # Mock features: [B, T, N, D]
    x = torch.randn(batch_size, window_steps, num_cells, input_dim)

    # Mock mask (no missing data for demo)
    mask = torch.ones_like(x)

    # Time indices
    time_idx = torch.arange(window_steps).unsqueeze(0).expand(batch_size, -1)

    # Spatial coordinates (use first 100 cells)
    import h3

    sample_cells = list(grid.cells)[:num_cells]
    lats = torch.tensor([h3.h3_to_geo(c)[0] for c in sample_cells])
    lons = torch.tensor([h3.h3_to_geo(c)[1] for c in sample_cells])

    # Seasonal embedding
    now = datetime.utcnow()
    season_sin, season_cos = get_season_embedding(now)
    season_sin_t = torch.full((batch_size, window_steps), season_sin)
    season_cos_t = torch.full((batch_size, window_steps), season_cos)

    print(f"   Input shape: {x.shape}")
    print(f"   Time steps: {window_steps}")
    print(f"   Cells: {num_cells}")

    # 5. Run readability encoder
    print("\nRunning readability encoder...")
    with torch.no_grad():
        # Expand lat/lon for batch
        lats_batch = lats.unsqueeze(0).expand(batch_size, -1)
        lons_batch = lons.unsqueeze(0).expand(batch_size, -1)

        tokens, uncertainty, instability = readability_encoder(
            x=x,
            mask=mask,
            time_idx=time_idx,
            lat=lats_batch,
            lon=lons_batch,
            season_sin=season_sin_t,
            season_cos=season_cos_t,
        )

    print(f"   Tokens shape: {tokens.shape}")
    print(f"   Uncertainty shape: {uncertainty.shape}")
    print(f"   Mean instability: {instability.mean():.3f}")

    # 6. Run rain model
    print("\nRunning rain model...")
    with torch.no_grad():
        # Mock adjacency (all cells can attend to each other for demo)
        adjacency_mask = torch.ones(batch_size, num_cells, num_cells)

        predictions = rain_model(
            tokens=tokens, adjacency_mask=adjacency_mask, instability=instability
        )

    print("\n📊 Predictions:")
    for horizon in ["1h", "6h", "24h"]:
        if config["models"]["rain"]["distribution"] == "gamma":
            shape = predictions[f"{horizon}_shape"]
            rate = predictions[f"{horizon}_rate"]
            print(f"\n   {horizon} accumulation (Gamma):")
            print(f"      Shape (k): {shape[0, :5].numpy()}")  # First 5 cells
            print(f"      Rate (θ^-1): {rate[0, :5].numpy()}")
        else:
            mu = predictions[f"{horizon}_mu"]
            sigma = predictions[f"{horizon}_sigma"]
            print(f"\n   {horizon} accumulation (LogNormal):")
            print(f"      μ: {mu[0, :5].numpy()}")
            print(f"      σ: {sigma[0, :5].numpy()}")

        exceedance_logits = predictions[f"{horizon}_exceedance_logits"]
        exceedance_probs = torch.sigmoid(exceedance_logits)
        print(f"   {horizon} extreme exceedance probability:")
        print(f"      {exceedance_probs[0, :5].numpy()}")

    # 7. Compute risk scores
    print("\n🎯 Computing combined risk scores...")

    # Simple risk fusion (in production, use calibrated weights)
    risk_scores = {}
    for horizon in ["1h", "6h", "24h"]:
        exc_prob = torch.sigmoid(predictions[f"{horizon}_exceedance_logits"])
        risk_scores[horizon] = exc_prob

    print("\n   Sample risk scores (first 5 cells):")
    for horizon in ["1h", "6h", "24h"]:
        print(f"      {horizon}: {risk_scores[horizon][0, :5].numpy()}")

    # 8. Map to risk levels
    print("\n🚦 Risk levels:")
    thresholds = config["risk"]["thresholds"]

    for i, cell in enumerate(sample_cells[:5]):
        print(f"\n   Cell {cell} (lat={lats[i]:.2f}, lon={lons[i]:.2f}):")
        for horizon in ["1h", "6h", "24h"]:
            score = risk_scores[horizon][0, i].item()
            if score > thresholds["extreme"]:
                level = "EXTREME"
            elif score > thresholds["high"]:
                level = "HIGH"
            elif score > thresholds["moderate"]:
                level = "MODERATE"
            else:
                level = "LOW"

            print(f"      {horizon}: {level} ({score:.2%})")

    print("\n✅ Inference complete!\n")
    print("Note: This used untrained models with random weights.")
    print("In production, load trained checkpoints for real predictions.")


if __name__ == "__main__":
    main()
