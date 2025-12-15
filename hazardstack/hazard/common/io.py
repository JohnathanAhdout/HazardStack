"""I/O utilities for data loading and saving."""

import yaml
import json
import pickle
from pathlib import Path
from typing import Any, Optional
import numpy as np
import pandas as pd
import xarray as xr


def load_config(config_path: str) -> dict:
    """
    Load YAML configuration file.

    Args:
        config_path: Path to config file

    Returns:
        Config dictionary
    """
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config


def save_config(config: dict, config_path: str):
    """
    Save configuration to YAML file.

    Args:
        config: Config dictionary
        config_path: Path to save config
    """
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


def load_json(path: str) -> dict:
    """Load JSON file."""
    with open(path, "r") as f:
        return json.load(f)


def save_json(data: dict, path: str, indent: int = 2):
    """Save dictionary to JSON file."""
    with open(path, "w") as f:
        json.dump(data, f, indent=indent)


def load_pickle(path: str) -> Any:
    """Load pickle file."""
    with open(path, "rb") as f:
        return pickle.load(f)


def save_pickle(data: Any, path: str):
    """Save data to pickle file."""
    with open(path, "wb") as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)


def load_parquet(path: str) -> pd.DataFrame:
    """Load parquet file."""
    return pd.read_parquet(path)


def save_parquet(df: pd.DataFrame, path: str, **kwargs):
    """
    Save DataFrame to parquet.

    Args:
        df: DataFrame to save
        path: Output path
        **kwargs: Additional arguments for to_parquet
    """
    df.to_parquet(path, **kwargs)


def load_netcdf(path: str) -> xr.Dataset:
    """Load NetCDF file."""
    return xr.open_dataset(path)


def save_netcdf(ds: xr.Dataset, path: str):
    """Save xarray Dataset to NetCDF."""
    ds.to_netcdf(path)


def ensure_dir(path: str) -> Path:
    """
    Ensure directory exists, create if not.

    Args:
        path: Directory path

    Returns:
        Path object
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def list_files(directory: str, pattern: str = "*", recursive: bool = False) -> list[Path]:
    """
    List files in directory matching pattern.

    Args:
        directory: Directory path
        pattern: Glob pattern (e.g., "*.nc", "*.parquet")
        recursive: If True, search recursively

    Returns:
        List of Path objects
    """
    p = Path(directory)
    if recursive:
        return sorted(p.rglob(pattern))
    else:
        return sorted(p.glob(pattern))


def get_file_size_mb(path: str) -> float:
    """Get file size in megabytes."""
    return Path(path).stat().st_size / (1024 * 1024)


class TokenWriter:
    """Writer for token datasets (Parquet format)."""

    def __init__(self, output_dir: str, max_rows_per_file: int = 1_000_000):
        """
        Initialize token writer.

        Args:
            output_dir: Output directory
            max_rows_per_file: Maximum rows per parquet file
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_rows = max_rows_per_file
        self.buffer = []
        self.file_counter = 0

    def write(self, token: dict):
        """Add token to buffer."""
        # Flatten token for DataFrame
        row = {
            "h3_id": token["h3_id"],
            "t": token["t"],
            "lat": token["meta"].get("lat"),
            "lon": token["meta"].get("lon"),
            "basin_id": token["meta"].get("basin_id"),
            "elev_m": token["meta"].get("elev_m"),
        }

        # Add features as columns
        for i, val in enumerate(token["x"]):
            row[f"x_{i}"] = val

        # Add mask as columns
        for i, val in enumerate(token["mask"]):
            row[f"mask_{i}"] = val

        self.buffer.append(row)

        # Flush if buffer full
        if len(self.buffer) >= self.max_rows:
            self.flush()

    def flush(self):
        """Write buffer to file."""
        if not self.buffer:
            return

        df = pd.DataFrame(self.buffer)
        output_path = self.output_dir / f"tokens_{self.file_counter:04d}.parquet"
        df.to_parquet(output_path, index=False)

        self.buffer = []
        self.file_counter += 1

    def close(self):
        """Flush and close writer."""
        self.flush()


class TokenReader:
    """Reader for token datasets."""

    def __init__(self, input_dir: str):
        """
        Initialize token reader.

        Args:
            input_dir: Directory containing token parquet files
        """
        self.input_dir = Path(input_dir)
        self.files = sorted(self.input_dir.glob("tokens_*.parquet"))

        if not self.files:
            raise ValueError(f"No token files found in {input_dir}")

    def iter_tokens(self, batch_size: Optional[int] = None):
        """
        Iterate over tokens.

        Args:
            batch_size: If specified, yield batches of tokens

        Yields:
            Token dict or list of token dicts
        """
        for file_path in self.files:
            df = pd.read_parquet(file_path)

            for _, row in df.iterrows():
                # Reconstruct token
                feature_cols = [c for c in df.columns if c.startswith("x_")]
                mask_cols = [c for c in df.columns if c.startswith("mask_")]

                token = {
                    "h3_id": row["h3_id"],
                    "t": int(row["t"]),
                    "x": np.array([row[c] for c in feature_cols], dtype=np.float32),
                    "mask": np.array([row[c] for c in mask_cols], dtype=bool),
                    "meta": {
                        "lat": row.get("lat"),
                        "lon": row.get("lon"),
                        "basin_id": row.get("basin_id"),
                        "elev_m": row.get("elev_m"),
                    },
                }

                yield token

    def load_all(self) -> pd.DataFrame:
        """Load all token files into a single DataFrame."""
        dfs = [pd.read_parquet(f) for f in self.files]
        return pd.concat(dfs, ignore_index=True)
