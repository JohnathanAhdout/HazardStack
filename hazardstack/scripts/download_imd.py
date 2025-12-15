"""Download IMD gridded rainfall data."""

import argparse
from pathlib import Path
import sys
import logging
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from hazard.common.io import ensure_dir

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_imd_data(years: range, output_dir: Path):
    """
    Download IMD gridded rainfall data.

    Note: This is a placeholder. Actual IMD data requires:
    1. Registration at imdpune.gov.in
    2. Following their data access protocols
    3. Potentially manual download or FTP access

    Args:
        years: Range of years to download
        output_dir: Output directory
    """
    logger.info(f"Downloading IMD data for years {years.start}-{years.stop-1}")
    logger.info(f"Output directory: {output_dir}")

    ensure_dir(output_dir)

    # IMD data URL (example - actual URLs require authentication)
    base_url = "https://imdpune.gov.in/cmpg/Griddata/Rainfall_25_Bin.html"

    logger.warning(
        "\nNOTE: IMD gridded rainfall data requires manual download.\n"
        f"Please visit: {base_url}\n"
        "Steps:\n"
        "1. Register at imdpune.gov.in\n"
        "2. Download daily gridded rainfall data (0.25° resolution)\n"
        f"3. Place files in: {output_dir}/\n"
        "4. Expected format: YYYY.grd (binary gridded data)\n"
    )

    # In production, implement actual download logic
    # This might involve:
    # - FTP access
    # - HTTP requests with authentication
    # - Parsing specific data formats

    logger.info("\n✓ Instructions provided. Please download manually.")


def main():
    parser = argparse.ArgumentParser(description="Download IMD gridded rainfall data")
    parser.add_argument(
        "--years",
        default="2010-2024",
        help="Year range to download (e.g., 2010-2024)",
    )
    parser.add_argument(
        "--output",
        default="data/raw/imd",
        help="Output directory",
    )

    args = parser.parse_args()

    # Parse year range
    start_year, end_year = map(int, args.years.split("-"))
    years = range(start_year, end_year + 1)

    output_dir = Path(args.output)

    download_imd_data(years, output_dir)


if __name__ == "__main__":
    main()
