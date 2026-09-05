# Pharma Shipment Risk Analyzer

A local Streamlit web application for analyzing cold-chain pharmaceutical shipment risks. The app reads an uploaded Excel file and displays KPIs, risk distribution, top-risk shipments, and deterministic risk recommendations.

## Features

- **Risk Scoring**: Automated risk assessment based on temperature excursions and transit conditions
- **KPI Dashboard**: High-level metrics including high-risk shipment count, critical excursion count, and average risk score
- **Risk Distribution**: Visual breakdown of shipments by risk level (Low, Medium, High, Critical)
- **Top-Risk Shipments**: Detailed table of the highest-risk shipments
- **Deterministic Recommendations**: Rule-based insights (no external API calls — fully offline)

## Quick Start

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/supriyasarangi/Test_case_day2.git
   cd Test_case_day2
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Generate sample data (optional):**
   ```bash
   python3 scripts/generate_sample_data.py
   ```

### Running the App

```bash
streamlit run app.py --server.port 8501
```

Then open your browser to `http://localhost:8501`

## Usage

1. **Upload an Excel file** with your shipment data, or use the bundled sample dataset
2. **View the dashboard:**
   - KPI tiles show key metrics
   - Risk distribution chart visualizes shipment breakdown
   - Top-risk table lists high-priority shipments
   - Recommendations section provides actionable insights
3. **Hover over KPI tiles** for calculation details

## Data Schema

Your Excel file should contain the following columns:

| Column | Type | Description |
|---|---|---|
| `ShipmentID` | string | Unique shipment identifier |
| `Origin` | string | Shipping origin city |
| `Destination` | string | Shipping destination city |
| `ProductType` | string | Pharmaceutical product type (e.g., Vaccine, Insulin) |
| `DepartureDate` | date | ISO format (YYYY-MM-DD) |
| `MinTemp` | float | Minimum temperature during transit (°C) |
| `MaxTemp` | float | Maximum temperature during transit (°C) |
| `TempThresholdMin` | float | Lower temperature limit (°C) |
| `TempThresholdMax` | float | Upper temperature limit (°C) |
| `TransitDays` | int | Days in transit |
| `RiskScore` | int | Risk score (0–100) |
| `RiskLevel` | string | `Low`, `Medium`, `High`, or `Critical` |

### Risk Levels

- **Low**: Risk score 0–39
- **Medium**: Risk score 40–69
- **High**: Risk score 70–84
- **Critical**: Risk score 85–100

### Temperature Excursion

A temperature excursion occurs when:
```
MinTemp < TempThresholdMin  OR  MaxTemp > TempThresholdMax
```

Excursion severity:
- **Minor**: 0–2°C out of range
- **Moderate**: 2–5°C out of range
- **Critical**: > 5°C out of range

## Repository Structure

```
Test_case_day2/
├── app.py                          # Streamlit UI and dashboard
├── risk_logic.py                   # Risk scoring and excursion logic
├── requirements.txt                # Python dependencies
├── sample_data/
│   └── shipments_sample.xlsx       # Sample dataset (80 rows)
├── scripts/
│   └── generate_sample_data.py     # Script to generate sample data
└── README.md                       # This file
```

## Design Philosophy

- **Offline-First**: No network calls or external APIs — fully deterministic and reproducible
- **Single Source of Truth**: All business logic centralized in `risk_logic.py`
- **Audit-Ready**: Rule-based recommendations are fully traceable and explainable
- **No Persistence**: Data analyzed in-memory only; no database required

## Troubleshooting

### Streamlit won't start
- Ensure dependencies are installed: `pip install -r requirements.txt`
- Check port 8501 is not in use, or use a different port: `streamlit run app.py --server.port 8502`

### Sample data missing
- Regenerate it: `python3 scripts/generate_sample_data.py`
- This creates `sample_data/shipments_sample.xlsx` with 80 synthetic rows

### Upload errors
- Verify your Excel file contains all required columns (see Data Schema above)
- Check that date columns are in ISO format (YYYY-MM-DD)
- Ensure numeric columns contain valid numbers

## Requirements

- Python 3.8+
- See `requirements.txt` for full dependencies

## License

This project is part of the Pharma Shipment Risk Analyzer suite.

## Support

For issues or questions, check the troubleshooting section above or review the sample dataset for reference.
