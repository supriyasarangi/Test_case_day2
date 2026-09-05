"""Pharma Shipment Risk Analyzer - Core logic module.

Single source of truth for all thresholds, formulas, and business rules.
Do not duplicate or re-derive these constants elsewhere in the codebase.
"""

import pandas as pd
from typing import Tuple, List


# Data schema - required columns
REQUIRED_COLUMNS = [
    "ShipmentID", "Origin", "Destination", "ProductType", "DepartureDate",
    "MinTemp", "MaxTemp", "TempThresholdMin", "TempThresholdMax",
    "TransitDays", "RiskScore", "RiskLevel"
]

# Risk score bands (upper bound exclusive except for the top)
RISK_BANDS = {
    "Low": (0, 40),
    "Medium": (40, 70),
    "High": (70, 85),
    "Critical": (85, 101)
}

HIGH_RISK_LEVELS = {"High", "Critical"}

# Excursion severity thresholds (°C)
EXCURSION_SEVERITY_THRESHOLDS = {
    "minor": (0, 2),
    "moderate": (2, 5),
    "critical": (5, float('inf'))
}

# Recommendation rules configuration
CRITICAL_EXCURSION_THRESHOLD = 5.0  # °C
HIGH_RISK_PERCENTAGE_WARNING = 25.0  # %


def classify_risk_level(score: float) -> str:
    """Classify a RiskScore into a risk level."""
    score = max(0, min(100, score))
    for level, (low, high) in RISK_BANDS.items():
        if low <= score < high:
            return level
    return "Critical"


def validate_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate that df contains all required columns.

    Returns (is_valid, missing_columns).
    """
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    return (len(missing) == 0, missing)


def calculate_excursion_magnitude(min_temp: float, max_temp: float,
                                   threshold_min: float, threshold_max: float) -> float:
    """Calculate how far the temperatures breach the thresholds (°C)."""
    breach_low = max(0, threshold_min - min_temp)
    breach_high = max(0, max_temp - threshold_max)
    return max(breach_low, breach_high)


def classify_excursion_severity(magnitude: float) -> str:
    """Classify excursion severity by magnitude."""
    if magnitude <= 0:
        return "none"
    for severity, (low, high) in EXCURSION_SEVERITY_THRESHOLDS.items():
        if low < magnitude <= high:
            return severity
    return "critical"


def add_risk_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived IsExcursion, ExcursionMagnitude, ExcursionSeverity, HighRisk columns."""
    df = df.copy()

    df["IsExcursion"] = (df["MinTemp"] < df["TempThresholdMin"]) | \
                        (df["MaxTemp"] > df["TempThresholdMax"])

    df["ExcursionMagnitude"] = df.apply(
        lambda row: calculate_excursion_magnitude(
            row["MinTemp"], row["MaxTemp"],
            row["TempThresholdMin"], row["TempThresholdMax"]
        ),
        axis=1
    )

    df["ExcursionSeverity"] = df["ExcursionMagnitude"].apply(classify_excursion_severity)

    df["HighRisk"] = df["RiskLevel"].isin(HIGH_RISK_LEVELS)

    return df


def generate_recommendation(df: pd.DataFrame) -> str:
    """Generate a rule-based, AI-style recommendation paragraph."""

    # Compute aggregate metrics
    critical_excursion_count = (df["ExcursionMagnitude"] > CRITICAL_EXCURSION_THRESHOLD).sum()
    excursion_count = df["IsExcursion"].sum()
    high_risk_count = df["HighRisk"].sum()
    total = len(df)
    high_risk_pct = (high_risk_count / total * 100) if total > 0 else 0

    # Find the origin with the most excursions
    excursion_df = df[df["IsExcursion"]]
    top_origin = excursion_df["Origin"].value_counts().index[0] if len(excursion_df) > 0 else "N/A"

    # Build recommendation using severity-ordered rules
    lines = []

    if critical_excursion_count > 0:
        lines.append(
            f"{critical_excursion_count} shipment(s) show critical temperature excursions "
            f"exceeding the allowable threshold by more than 5°C — "
            f"recommend an immediate cold-chain audit for {top_origin} routes."
        )
    elif excursion_count > 0:
        lines.append(
            f"{excursion_count} shipment(s) recorded temperature excursions within 5°C of threshold — "
            f"continue monitoring but no immediate audit required."
        )
    else:
        lines.append(
            "No temperature excursions were detected in this shipment batch — "
            "cold-chain integrity appears intact."
        )

    # Append risk-level assessment
    risk_status = (
        f"which exceeds the recommended 25% threshold — review carrier performance for {top_origin}."
        if high_risk_pct > HIGH_RISK_PERCENTAGE_WARNING
        else "which is within normal operating range."
    )
    lines.append(
        f"{high_risk_count} of {total} shipments ({high_risk_pct:.1f}%) are classified High or Critical risk, {risk_status}"
    )

    return " ".join(lines)
