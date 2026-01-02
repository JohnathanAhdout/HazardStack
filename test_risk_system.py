#!/usr/bin/env python3
"""Test the risk calculation system"""

import asyncio
import httpx
from datetime import datetime, timedelta
import math

async def fetch_usgs_earthquakes(hours=168, min_magnitude=2.5):
    """Fetch earthquakes from USGS"""
    BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

    start_time = datetime.utcnow() - timedelta(hours=hours)

    params = {
        "format": "geojson",
        "starttime": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "endtime": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
        "minmagnitude": min_magnitude,
        "orderby": "time",
    }

    print(f"Fetching earthquakes from USGS (last {hours}h, M{min_magnitude}+)...")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            earthquakes = []
            for feature in data.get("features", []):
                props = feature.get("properties", {})
                coords = feature.get("geometry", {}).get("coordinates", [])

                if len(coords) >= 3:
                    eq = {
                        "event_id": feature.get("id", "unknown"),
                        "time": datetime.fromtimestamp(props.get("time", 0) / 1000),
                        "latitude": coords[1],
                        "longitude": coords[0],
                        "depth_km": coords[2],
                        "magnitude": props.get("mag", 0.0),
                        "magnitude_type": props.get("magType", "unknown"),
                        "location": props.get("place", "Unknown location"),
                    }
                    earthquakes.append(eq)

            return earthquakes

    except Exception as e:
        print(f"Error fetching USGS data: {e}")
        return []


def calculate_distance_km(lat1, lon1, lat2, lon2):
    """Calculate distance using Haversine formula"""
    R = 6371  # Earth's radius in km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))

    return R * c


def calculate_mmi(magnitude, distance_km, depth_km):
    """Calculate Modified Mercalli Intensity"""
    if distance_km < 1:
        distance_km = 1

    hypocentral_dist = math.sqrt(distance_km**2 + depth_km**2)

    # Simplified attenuation model
    a = 2.0
    b = 1.7
    c = 3.5
    d = 0.01

    mmi = a + b * magnitude - c * math.log10(hypocentral_dist) - d * hypocentral_dist

    return max(1.0, min(10.0, mmi))


def calculate_risk_for_location(lat, lon, earthquakes):
    """Calculate risk scores for a location"""
    max_mmi = 1.0
    max_aftershock_prob = 0.0
    closest_eq = None
    closest_distance = float('inf')

    for eq in earthquakes:
        distance = calculate_distance_km(lat, lon, eq["latitude"], eq["longitude"])

        if distance < closest_distance:
            closest_distance = distance
            closest_eq = eq

        # Only consider earthquakes within 500km
        if distance > 500:
            continue

        # Calculate MMI
        mmi = calculate_mmi(eq["magnitude"], distance, eq["depth_km"])
        max_mmi = max(max_mmi, mmi)

        # Simplified aftershock probability
        hours_since = (datetime.utcnow() - eq["time"]).total_seconds() / 3600
        if hours_since < 0.1:
            hours_since = 0.1

        K = 10 ** (eq["magnitude"] - 4.5)
        c = 0.1 * 24
        t1 = hours_since
        t2 = hours_since + 24

        expected_count = K * math.log((t2 + c) / (t1 + c))
        aftershock_prob = 1 - math.exp(-expected_count / 10)
        aftershock_prob = max(0.0, min(1.0, aftershock_prob))

        distance_weight = max(0, 1 - distance / 500)
        weighted_aftershock = aftershock_prob * distance_weight

        max_aftershock_prob = max(max_aftershock_prob, weighted_aftershock)

    # Normalize MMI to 0-1 scale
    mmi_normalized = (max_mmi - 1.0) / 9.0

    # Calculate risk scores for different horizons
    risk_scores = {
        "1h": mmi_normalized * 0.9 + 0.05 * 0.1,
        "6h": mmi_normalized * 0.5 + 0.05 * 0.4 + 0.02 * 0.1,
        "24h": max_aftershock_prob * 0.5 + 0.02 * 0.3 + 0.05 * 0.2,
    }

    return {
        "max_mmi": max_mmi,
        "mmi_normalized": mmi_normalized,
        "aftershock_prob": max_aftershock_prob,
        "risk_scores": risk_scores,
        "closest_earthquake": closest_eq,
        "closest_distance_km": closest_distance if closest_eq else None,
    }


async def main():
    print("=" * 80)
    print("SPIRAL RISK SYSTEM TEST")
    print("=" * 80)
    print()

    # Fetch earthquake data
    earthquakes = await fetch_usgs_earthquakes(hours=168, min_magnitude=2.5)

    print(f"\n✓ Found {len(earthquakes)} earthquakes globally\n")

    if earthquakes:
        print("Recent earthquakes (top 10):")
        print("-" * 80)
        for i, eq in enumerate(earthquakes[:10], 1):
            print(f"{i:2}. M{eq['magnitude']:.1f} - {eq['location'][:55]:55} - {eq['depth_km']:.1f}km")
        print()
    else:
        print("⚠️  No earthquakes found! This might be why everything shows 0%\n")
        return

    # Test risk calculation for various locations
    test_locations = [
        ("New Delhi, India", 28.6139, 77.2090),
        ("Tokyo, Japan", 35.6762, 139.6503),
        ("San Francisco, USA", 37.7749, -122.4194),
        ("Central India", 20.5, 78.9),
    ]

    print("\n" + "=" * 80)
    print("RISK CALCULATIONS FOR TEST LOCATIONS")
    print("=" * 80)

    for name, lat, lon in test_locations:
        print(f"\n📍 {name} ({lat:.4f}°, {lon:.4f}°)")
        print("-" * 80)

        risk = calculate_risk_for_location(lat, lon, earthquakes)

        if risk["closest_earthquake"]:
            eq = risk["closest_earthquake"]
            print(f"Closest earthquake: M{eq['magnitude']:.1f} at {risk['closest_distance_km']:.1f}km")
            print(f"Location: {eq['location']}")
            print(f"Time: {eq['time']}")

        print(f"\nRisk Components:")
        print(f"  MMI (shaking intensity): {risk['max_mmi']:.2f} (normalized: {risk['mmi_normalized']:.3f})")
        print(f"  Aftershock probability: {risk['aftershock_prob']:.3f}")

        print(f"\nRisk Scores by Horizon:")
        for horizon, score in risk["risk_scores"].items():
            percentage = score * 100
            level = "EXTREME" if score >= 0.70 else "HIGH" if score >= 0.45 else "MODERATE" if score >= 0.20 else "LOW"
            print(f"  {horizon:4} → {score:.3f} ({percentage:.1f}%) - {level}")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
