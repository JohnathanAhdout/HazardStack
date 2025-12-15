"""Time utilities for the HazardStack system."""

from datetime import datetime, timedelta
from typing import List
import numpy as np


def parse_horizon(horizon_str: str) -> timedelta:
    """
    Parse horizon string to timedelta.

    Args:
        horizon_str: Horizon string like "1h", "6h", "24h", "72h"

    Returns:
        timedelta object
    """
    if horizon_str.endswith("h"):
        hours = int(horizon_str[:-1])
        return timedelta(hours=hours)
    elif horizon_str.endswith("d"):
        days = int(horizon_str[:-1])
        return timedelta(days=days)
    elif horizon_str.endswith("m"):
        minutes = int(horizon_str[:-1])
        return timedelta(minutes=minutes)
    else:
        raise ValueError(f"Unknown horizon format: {horizon_str}")


def horizon_to_steps(horizon_str: str, step_minutes: int) -> int:
    """
    Convert horizon string to number of time steps.

    Args:
        horizon_str: Horizon string like "1h", "6h"
        step_minutes: Minutes per time step

    Returns:
        Number of steps
    """
    td = parse_horizon(horizon_str)
    total_minutes = td.total_seconds() / 60
    return int(total_minutes / step_minutes)


def get_season_embedding(dt: datetime) -> tuple[float, float]:
    """
    Get seasonal embedding (sin, cos) from datetime.

    Args:
        dt: Datetime object

    Returns:
        Tuple of (season_sin, season_cos)
    """
    day_of_year = dt.timetuple().tm_yday
    # Normalize to [0, 2π]
    angle = 2 * np.pi * day_of_year / 365.25
    return np.sin(angle), np.cos(angle)


def get_time_of_day_embedding(dt: datetime) -> tuple[float, float]:
    """
    Get time-of-day embedding (sin, cos) from datetime.

    Args:
        dt: Datetime object

    Returns:
        Tuple of (tod_sin, tod_cos)
    """
    hour_fraction = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
    angle = 2 * np.pi * hour_fraction / 24.0
    return np.sin(angle), np.cos(angle)


def get_monsoon_phase(dt: datetime) -> str:
    """
    Get monsoon phase for India.

    Phases:
    - pre_monsoon: Mar-May
    - southwest_monsoon: Jun-Sep (main rainy season)
    - post_monsoon: Oct-Nov
    - winter: Dec-Feb

    Args:
        dt: Datetime object

    Returns:
        Monsoon phase string
    """
    month = dt.month

    if month in [3, 4, 5]:
        return "pre_monsoon"
    elif month in [6, 7, 8, 9]:
        return "southwest_monsoon"
    elif month in [10, 11]:
        return "post_monsoon"
    else:  # [12, 1, 2]
        return "winter"


def is_cyclone_season(dt: datetime, region: str = "bay_of_bengal") -> bool:
    """
    Check if datetime is in cyclone season for a region.

    Args:
        dt: Datetime object
        region: "bay_of_bengal" or "arabian_sea"

    Returns:
        True if in cyclone season
    """
    month = dt.month

    if region == "bay_of_bengal":
        # Two peaks: Apr-Jun and Oct-Dec
        return month in [4, 5, 6, 10, 11, 12]
    elif region == "arabian_sea":
        # Peak: May-Jun and Oct-Nov
        return month in [5, 6, 10, 11]
    else:
        raise ValueError(f"Unknown region: {region}")


def generate_forecast_times(
    start_time: datetime, horizons: List[str], step_minutes: int = 60
) -> dict[str, List[datetime]]:
    """
    Generate forecast valid times for each horizon.

    Args:
        start_time: Forecast issue time
        horizons: List of horizon strings
        step_minutes: Time step in minutes

    Returns:
        Dict mapping horizon to list of valid times
    """
    result = {}

    for horizon_str in horizons:
        horizon_td = parse_horizon(horizon_str)
        valid_time = start_time + horizon_td
        result[horizon_str] = valid_time

    return result


def align_to_interval(dt: datetime, interval_minutes: int) -> datetime:
    """
    Align datetime to nearest interval.

    Args:
        dt: Datetime to align
        interval_minutes: Interval in minutes (e.g., 15, 60)

    Returns:
        Aligned datetime
    """
    # Round down to nearest interval
    total_minutes = dt.hour * 60 + dt.minute
    aligned_minutes = (total_minutes // interval_minutes) * interval_minutes

    return dt.replace(
        hour=aligned_minutes // 60,
        minute=aligned_minutes % 60,
        second=0,
        microsecond=0,
    )


def get_lookback_window(
    current_time: datetime, window_steps: int, step_minutes: int
) -> List[datetime]:
    """
    Get list of datetimes for lookback window.

    Args:
        current_time: Current time
        window_steps: Number of steps to look back
        step_minutes: Minutes per step

    Returns:
        List of datetimes in ascending order
    """
    times = []
    for i in range(window_steps):
        dt = current_time - timedelta(minutes=step_minutes * (window_steps - 1 - i))
        times.append(dt)
    return times


def datetime_to_unix(dt: datetime) -> int:
    """Convert datetime to Unix timestamp (seconds since epoch)."""
    return int(dt.timestamp())


def unix_to_datetime(timestamp: int) -> datetime:
    """Convert Unix timestamp to datetime."""
    return datetime.fromtimestamp(timestamp)
