"""Build H3 grid and basin graph for India."""

import argparse
import sys
from pathlib import Path
import pickle
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from hazard.common.geo import H3Grid, BasinGraph
from hazard.common.io import load_config, ensure_dir
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def build_h3_grid(config: dict, geojson_path: str = None) -> H3Grid:
    """
    Build H3 grid for India.

    Args:
        config: Configuration dict
        geojson_path: Optional path to India boundary GeoJSON

    Returns:
        H3Grid instance
    """
    logger.info("Building H3 grid...")

    resolution = config["grid"]["h3_resolution"]
    bounds = config["grid"]["india_bounds"]

    grid = H3Grid(resolution=resolution, bounds=bounds)

    logger.info(f"Generated {len(grid.cells)} H3 cells at resolution {resolution}")

    # If GeoJSON provided, refine to exact boundary
    if geojson_path and Path(geojson_path).exists():
        logger.info(f"Loading boundary from {geojson_path}")
        grid.load_from_geojson(geojson_path)
        logger.info(f"Refined to {len(grid.cells)} cells within boundary")

    return grid


def build_basin_graph(config: dict) -> BasinGraph:
    """
    Build river basin topology graph.

    This is a simplified example - in production, load from actual data.

    Args:
        config: Configuration dict

    Returns:
        BasinGraph instance
    """
    logger.info("Building basin graph...")

    graph = BasinGraph()

    # Major Indian river basins (simplified topology)
    # In production, load from actual hydrological data

    # Brahmaputra
    graph.add_basin(
        "brahmaputra_upper",
        "Brahmaputra Upper",
        area_km2=50000,
        mean_elevation_m=3000,
    )
    graph.add_basin(
        "brahmaputra_guwahati",
        "Brahmaputra at Guwahati",
        area_km2=80000,
        mean_elevation_m=500,
        danger_threshold_m3s=50000.0,
    )
    graph.add_flow("brahmaputra_upper", "brahmaputra_guwahati")

    # Ganga
    graph.add_basin(
        "ganga_upper",
        "Ganga Upper (Uttarakhand)",
        area_km2=30000,
        mean_elevation_m=2500,
    )
    graph.add_basin(
        "ganga_haridwar",
        "Ganga at Haridwar",
        area_km2=40000,
        mean_elevation_m=300,
    )
    graph.add_basin(
        "ganga_farakka",
        "Ganga at Farakka",
        area_km2=100000,
        mean_elevation_m=50,
        danger_threshold_m3s=60000.0,
    )
    graph.add_flow("ganga_upper", "ganga_haridwar")
    graph.add_flow("ganga_haridwar", "ganga_farakka")

    # Yamuna (tributary of Ganga)
    graph.add_basin(
        "yamuna_delhi",
        "Yamuna at Delhi",
        area_km2=25000,
        mean_elevation_m=200,
        danger_threshold_m3s=8000.0,
    )
    graph.add_flow("yamuna_delhi", "ganga_farakka")

    # Godavari
    graph.add_basin(
        "godavari_upper",
        "Godavari Upper",
        area_km2=40000,
        mean_elevation_m=600,
    )
    graph.add_basin(
        "godavari_polavaram",
        "Godavari at Polavaram",
        area_km2=70000,
        mean_elevation_m=100,
        danger_threshold_m3s=30000.0,
    )
    graph.add_flow("godavari_upper", "godavari_polavaram")

    # Mahanadi
    graph.add_basin(
        "mahanadi_hirakud",
        "Mahanadi at Hirakud",
        area_km2=50000,
        mean_elevation_m=300,
        danger_threshold_m3s=40000.0,
    )

    # Kaveri
    graph.add_basin(
        "kaveri_upper",
        "Kaveri Upper",
        area_km2=20000,
        mean_elevation_m=800,
    )

    logger.info(f"Built basin graph with {len(graph.basins)} basins")
    logger.info(f"Topological order: {graph.topological_sort()}")

    return graph


def main():
    parser = argparse.ArgumentParser(description="Build H3 grid and basin graph")
    parser.add_argument(
        "--config",
        default="configs/india_v1.yaml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--geojson",
        default=None,
        help="Path to India boundary GeoJSON (optional)",
    )
    parser.add_argument(
        "--output-dir",
        default="data/processed/grid",
        help="Output directory",
    )

    args = parser.parse_args()

    # Load config
    config = load_config(args.config)

    # Create output directory
    output_dir = ensure_dir(args.output_dir)

    # Build H3 grid
    grid = build_h3_grid(config, args.geojson)

    # Save grid
    grid_path = output_dir / "h3_grid.pkl"
    with open(grid_path, "wb") as f:
        pickle.dump(grid, f)
    logger.info(f"Saved H3 grid to {grid_path}")

    # Save as GeoJSON for visualization
    gdf = grid.to_geopandas()
    geojson_path = output_dir / "h3_grid.geojson"
    gdf.to_file(geojson_path, driver="GeoJSON")
    logger.info(f"Saved GeoJSON to {geojson_path}")

    # Build basin graph
    basin_graph = build_basin_graph(config)

    # Save basin graph
    basin_path = output_dir / "basin_graph.pkl"
    with open(basin_path, "wb") as f:
        pickle.dump(basin_graph, f)
    logger.info(f"Saved basin graph to {basin_path}")

    # Save basin info as JSON
    basin_info = {
        basin_id: info for basin_id, info in basin_graph.basins.items()
    }
    basin_json_path = output_dir / "basins.json"
    with open(basin_json_path, "w") as f:
        json.dump(basin_info, f, indent=2, default=str)
    logger.info(f"Saved basin info to {basin_json_path}")

    logger.info("\n✓ Grid and basin graph built successfully!")
    logger.info(f"  H3 cells: {len(grid.cells)}")
    logger.info(f"  Basins: {len(basin_graph.basins)}")
    logger.info(f"  Output: {output_dir}")


if __name__ == "__main__":
    main()
