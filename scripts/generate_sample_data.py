#!/usr/bin/env python3
"""Generate synthetic pharma shipment data for testing/demo."""

import sys
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# Import risk_logic to ensure generator and app use identical thresholds
sys.path.insert(0, str(Path(__file__).parent.parent))
import risk_logic


# Reproducibility
random.seed(42)
np.random.seed(42)

N_ROWS = 80

# Product types with their temperature thresholds
PRODUCTS = {
    "Vaccine": (2, 8),
    "Insulin": (2, 8),
    "Monoclonal Antibody": (2, 8),
    "Biologic Reagent": (2, 8),
    "Blood Plasma Product": (-25, -15),
}

CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
    "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose"
]

def generate_data():
    """Generate synthetic shipment data."""
    data = []

    for i in range(N_ROWS):
        shipment_id = f"SHP{10001 + i}"

        # Origin/Destination: ensure they differ
        origin = random.choice(CITIES)
        destination = random.choice([c for c in CITIES if c != origin])

        product = random.choice(list(PRODUCTS.keys()))
        temp_min_threshold, temp_max_threshold = PRODUCTS[product]

        # Departure date: random date in the last 30 days
        departure_date = datetime.now() - timedelta(days=random.randint(0, 30))

        # Temperature excursion pattern (weighted): 60% normal, 25% mild, 15% severe
        excursion_type = np.random.choice(
            ["normal", "mild", "severe"],
            p=[0.60, 0.25, 0.15]
        )

        transit_days = random.randint(1, 10)

        if excursion_type == "normal":
            min_temp = random.uniform(temp_min_threshold, temp_min_threshold + 0.5)
            max_temp = random.uniform(temp_max_threshold - 0.5, temp_max_threshold)
        elif excursion_type == "mild":
            if random.choice([True, False]):
                min_temp = temp_min_threshold - random.uniform(0.5, 4.0)
                max_temp = random.uniform(temp_max_threshold - 0.5, temp_max_threshold)
            else:
                min_temp = random.uniform(temp_min_threshold, temp_min_threshold + 0.5)
                max_temp = temp_max_threshold + random.uniform(0.5, 4.0)
        else:  # severe
            if random.choice([True, False]):
                min_temp = temp_min_threshold - random.uniform(5.0, 12.0)
                max_temp = random.uniform(temp_max_threshold - 1.0, temp_max_threshold)
            else:
                min_temp = random.uniform(temp_min_threshold, temp_min_threshold + 0.5)
                max_temp = temp_max_threshold + random.uniform(5.0, 12.0)

        # Risk score: base + excursion impact + transit delay impact + noise
        excursion_mag = risk_logic.calculate_excursion_magnitude(
            min_temp, max_temp, temp_min_threshold, temp_max_threshold
        )
        risk_score = 15 + excursion_mag * 6 + max(transit_days - 3, 0) * 3 + random.uniform(-5, 5)
        risk_score = max(0, min(100, round(risk_score)))

        # Risk level (uses risk_logic to ensure consistency)
        risk_level = risk_logic.classify_risk_level(risk_score)

        data.append({
            "ShipmentID": shipment_id,
            "Origin": origin,
            "Destination": destination,
            "ProductType": product,
            "DepartureDate": departure_date.strftime("%Y-%m-%d"),
            "MinTemp": round(min_temp, 2),
            "MaxTemp": round(max_temp, 2),
            "TempThresholdMin": temp_min_threshold,
            "TempThresholdMax": temp_max_threshold,
            "TransitDays": transit_days,
            "RiskScore": risk_score,
            "RiskLevel": risk_level,
        })

    return pd.DataFrame(data)


if __name__ == "__main__":
    print("Generating synthetic pharma shipment data...")
    df = generate_data()

    output_path = Path(__file__).parent.parent / "sample_data" / "shipments_sample.xlsx"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df.to_excel(output_path, index=False, engine="openpyxl")

    print(f"✓ Generated {len(df)} shipments")
    print(f"✓ Saved to {output_path}")
    print(f"  High-risk count: {(df['RiskLevel'].isin(risk_logic.HIGH_RISK_LEVELS)).sum()}")
    print(f"  Excursion count: {((df['MinTemp'] < df['TempThresholdMin']) | (df['MaxTemp'] > df['TempThresholdMax'])).sum()}")
