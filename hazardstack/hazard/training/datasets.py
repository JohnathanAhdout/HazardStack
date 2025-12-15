"""PyTorch datasets for hazard prediction."""

import torch
from torch.utils.data import Dataset
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import pickle


class RainDataset(Dataset):
    """
    Dataset for rain nowcast/forecast training.

    Loads tokenized spatiotemporal data.
    """

    def __init__(
        self,
        data_dir: str,
        window_steps: int = 12,
        horizons: List[str] = ["1h", "6h", "24h"],
        split: str = "train",
    ):
        """
        Initialize dataset.

        Args:
            data_dir: Directory with processed tokens
            window_steps: Number of past timesteps for input
            horizons: Forecast horizons to include as targets
            split: "train", "val", or "test"
        """
        self.data_dir = Path(data_dir)
        self.window_steps = window_steps
        self.horizons = horizons
        self.split = split

        # Load metadata
        meta_path = self.data_dir / f"{split}_metadata.pkl"
        if meta_path.exists():
            with open(meta_path, "rb") as f:
                self.metadata = pickle.load(f)
        else:
            raise FileNotFoundError(f"Metadata not found: {meta_path}")

        self.samples = self.metadata["samples"]
        self.cell_list = self.metadata["cell_list"]

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """
        Get a single sample.

        Returns:
            Dict with keys:
                - features: [T, N, D] input features
                - mask: [T, N, D] missing data mask
                - targets: Dict of target arrays per horizon
                - metadata: Sample metadata
        """
        sample_info = self.samples[idx]

        # Load features from disk
        feature_path = self.data_dir / f"{self.split}/features/{sample_info['sample_id']}.npz"
        data = np.load(feature_path)

        features = torch.from_numpy(data["features"]).float()  # [T, N, D]
        mask = torch.from_numpy(data["mask"]).float()  # [T, N, D]

        # Load targets
        targets = {}
        for horizon in self.horizons:
            target_key = f"target_{horizon}"
            if target_key in data:
                targets[horizon] = {
                    "accumulation": torch.from_numpy(data[f"{target_key}_accum"]).float(),
                    "exceedance": torch.from_numpy(data[f"{target_key}_exceed"]).float(),
                }

        # Metadata
        metadata = {
            "sample_id": sample_info["sample_id"],
            "timestamp": sample_info["timestamp"],
            "cells": self.cell_list,
        }

        return {
            "features": features,
            "mask": mask,
            "targets": targets,
            "metadata": metadata,
        }


class FloodDataset(Dataset):
    """Dataset for flood exceedance prediction."""

    def __init__(
        self,
        data_dir: str,
        window_steps: int = 72,
        horizons: List[str] = ["12h", "24h"],
        split: str = "train",
    ):
        """Initialize flood dataset."""
        self.data_dir = Path(data_dir)
        self.window_steps = window_steps
        self.horizons = horizons
        self.split = split

        # Load metadata
        meta_path = self.data_dir / f"{split}_metadata.pkl"
        with open(meta_path, "rb") as f:
            self.metadata = pickle.load(f)

        self.samples = self.metadata["samples"]
        self.basin_list = self.metadata["basin_list"]

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """Get flood sample."""
        sample_info = self.samples[idx]

        feature_path = self.data_dir / f"{self.split}/features/{sample_info['sample_id']}.npz"
        data = np.load(feature_path)

        features = torch.from_numpy(data["features"]).float()  # [T, N_basins, D]
        mask = torch.from_numpy(data["mask"]).float()

        # Load basin adjacency
        adjacency = torch.from_numpy(data["adjacency"]).float()  # [N_basins, N_basins]

        # Targets
        targets = {}
        for horizon in self.horizons:
            targets[horizon] = torch.from_numpy(data[f"target_{horizon}"]).float()

        return {
            "features": features,
            "mask": mask,
            "adjacency": adjacency,
            "targets": targets,
            "metadata": {"sample_id": sample_info["sample_id"]},
        }


class EarthquakeDataset(Dataset):
    """Dataset for earthquake shaking and aftershock prediction."""

    def __init__(
        self,
        data_dir: str,
        mode: str = "shaking",  # or "aftershock"
        split: str = "train",
    ):
        """Initialize earthquake dataset."""
        self.data_dir = Path(data_dir)
        self.mode = mode
        self.split = split

        # Load event catalog
        meta_path = self.data_dir / f"{split}_events.pkl"
        with open(meta_path, "rb") as f:
            self.events = pickle.load(f)

    def __len__(self) -> int:
        return len(self.events)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        """Get earthquake sample."""
        event = self.events[idx]

        if self.mode == "shaking":
            # Load shaking features for all cells
            feature_path = self.data_dir / f"{self.split}/shaking/{event['event_id']}.npz"
            data = np.load(feature_path)

            features = torch.from_numpy(data["features"]).float()  # [N_cells, F]
            target_mmi = torch.from_numpy(data["mmi"]).float()  # [N_cells]

            return {
                "features": features,
                "target_mmi": target_mmi,
                "metadata": {"event_id": event["event_id"]},
            }

        else:  # aftershock mode
            # Load event sequence
            seq_path = self.data_dir / f"{self.split}/aftershock/{event['event_id']}.npz"
            data = np.load(seq_path)

            event_sequence = torch.from_numpy(data["sequence"]).float()  # [N_events, 5]
            target_prob = torch.from_numpy(data["aftershock_occurred"]).float()  # Binary

            return {
                "event_sequence": event_sequence,
                "target_aftershock": target_prob,
                "metadata": {"event_id": event["event_id"]},
            }


def collate_rain_batch(batch: List[Dict]) -> Dict[str, torch.Tensor]:
    """Custom collate for rain dataset with variable-size spatial dims."""
    # Assume all samples have same T, N (if not, need padding)

    features = torch.stack([b["features"] for b in batch])  # [B, T, N, D]
    masks = torch.stack([b["mask"] for b in batch])

    # Collate targets
    targets_collated = {}
    for horizon in batch[0]["targets"].keys():
        targets_collated[horizon] = {
            "accumulation": torch.stack([b["targets"][horizon]["accumulation"] for b in batch]),
            "exceedance": torch.stack([b["targets"][horizon]["exceedance"] for b in batch]),
        }

    return {
        "features": features,
        "mask": masks,
        "targets": targets_collated,
    }
