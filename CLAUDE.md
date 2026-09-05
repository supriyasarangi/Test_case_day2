# Pharma Shipment Risk Analyzer

## Project Overview

A local Streamlit web application for analyzing cold-chain pharmaceutical shipment risks. The app is **entirely offline and deterministic** — it reads an uploaded Excel file (or a bundled sample dataset) and displays KPIs, risk distribution, top-risk shipments, and an AI-style recommendation section.

**Important:** The "AI recommendation" is generated using **deterministic rule-based logic**, not a live LLM call or external API. The prose is styled to read naturally, but every sentence is the output of a hardcoded rule applied to the data. This guarantees offline operation, reproducibility, and no API key requirements. Do not "improve" this by wiring in an API call — the whole point is to keep it local and unambiguous.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Generate (or regenerate) the sample data
python3 scripts/generate_sample_data.py

# Run the app
streamlit run app.py --server.port 8501
```

Then open `http://localhost:8501` in your browser.

## Repository Layout

| File / Directory | Purpose |
|---|---|
| `app.py` | Streamlit UI layer — file upload, schema validation, KPI tiles, chart, recommendation display. **Contains no business logic.** |
| `risk_logic.py` | **Single source of truth** for all thresholds, risk-band definitions, excursion detection formulas, and recommendation-text rules. Both the app and the sample-data generator import this module to ensure they never diverge. |
| `requirements.txt` | Python dependencies. |
| `scripts/generate_sample_data.py` | Generates synthetic pharma shipment data (80 rows, realistic variety) as a `.xlsx` file. Imports `risk_logic` to ensure generated data uses the same thresholds as the app. |
| `sample_data/shipments_sample.xlsx` | Pre-generated synthetic dataset for demo/testing. Regenerate it by running `python3 scripts/generate_sample_data.py`. |
| `.claude/settings.json` | Hook configuration for automated schema/threshold validation. |
| `.claude/skills/analyze-shipment-risk/SKILL.md` | Guidance for editing risk logic. |
| `.claude/agents/pharma-compliance-checker.md` | Read-only subagent for compliance review. |
| `.claude/hooks/validate_risk_schema.py` | Automated script that runs after file edits to enforce schema/threshold integrity. |

## Data Schema (Source of Truth)

This table is **authoritative and copy-identical** to `risk_logic.REQUIRED_COLUMNS` and the constants in `risk_logic.py`. If you see a discrepancy, update CLAUDE.md, not the code — the code is what runs.

| Column | Type | Purpose |
|---|---|---|
| `ShipmentID` | string | Unique shipment identifier |
| `Origin` | string | Shipping origin city |
| `Destination` | string | Shipping destination city |
| `ProductType` | string | Pharmaceutical product type (e.g., Vaccine, Insulin, Blood Plasma Product) |
| `DepartureDate` | date | ISO format (YYYY-MM-DD) |
| `MinTemp` | float | Minimum temperature recorded during transit (°C) |
| `MaxTemp` | float | Maximum temperature recorded during transit (°C) |
| `TempThresholdMin` | float | Lower allowable temperature boundary (°C, product-specific) |
| `TempThresholdMax` | float | Upper allowable temperature boundary (°C, product-specific) |
| `TransitDays` | int | Days in transit |
| `RiskScore` | int | Numeric risk score (0–100) |
| `RiskLevel` | string | Categorical risk level: `Low`, `Medium`, `High`, or `Critical` |

### Risk-Level Classification

| Risk Level | Score Range |
|---|---|
| `Low` | 0–39 |
| `Medium` | 40–69 |
| `High` | 70–84 |
| `Critical` | 85–100 |

**High-risk shipments** are those with `RiskLevel in {High, Critical}`.

### Temperature Excursion

A shipment has a temperature excursion if:
```
MinTemp < TempThresholdMin  OR  MaxTemp > TempThresholdMax
```

**Excursion magnitude** (°C) = maximum of:
- `TempThresholdMin - MinTemp` (if < 0, use 0)
- `MaxTemp - TempThresholdMax` (if < 0, use 0)

**Excursion severity** by magnitude:
- `minor`: (0, 2] °C
- `moderate`: (2, 5] °C
- `critical`: > 5 °C

## Coding Conventions

1. **All thresholds and business logic constants live exclusively in `risk_logic.py`**. Never duplicate a risk band, excursion formula, or recommendation rule elsewhere. Both `app.py` and the sample-data generator import `risk_logic` to ensure they stay in sync.

2. **`app.py` is the UI layer only.** It imports functions and constants from `risk_logic` but contains no business logic — no risk-score calculations, no band definitions, no recommendation generation outside of `risk_logic`.

3. **No network calls or API keys anywhere.** Grepping the entire codebase for `requests`, `urllib`, or `openai` should return nothing (there is a hook that enforces this automatically after every edit).

4. **Recommendation text is deterministic and ordered most-severe-first.** It follows a fixed rule sequence based on excursion counts and risk percentages, never random or generative.

5. **Public functions in `risk_logic` are type-hinted.**

## Custom Claude Code Tooling

This project uses three custom Claude Code components to keep thresholds, formulas, and schemas from drifting:

### Skill: `/analyze-shipment-risk`

Triggers when editing any risk-related code (risk thresholds, excursion detection, or recommendation logic). Loaded automatically when you open `risk_logic.py`, the KPI/recommendation sections of `app.py`, or `scripts/generate_sample_data.py`. See `.claude/skills/analyze-shipment-risk/SKILL.md` for a detailed checklist and guidance on how to make threshold changes safely.

### Subagent: `pharma-compliance-checker`

A read-only reviewer that you should **delegate to proactively** after finishing any change to `risk_logic.py`, `app.py`'s risk/KPI sections, or the sample-data generator. It checks six critical invariants: no threshold duplication, schema completeness, excursion formula correctness, offline guarantee (no network imports), risk-band alignment, and recommendation-text sanity. See `.claude/agents/pharma-compliance-checker.md` for its exact checklist.

### Hook: PostToolUse schema validator

A `.claude/settings.json` hook runs automatically after every `Edit` or `Write` to the critical files (`risk_logic.py`, `app.py`, `generate_sample_data.py`, or `sample_data/*.xlsx`). It validates that:
- Risk bands remain contiguous and non-overlapping.
- No network imports are present.
- Required Excel columns are present if a `.xlsx` was written.

On failure, it exits with code 2 (blocking) and prints `HOOK FAIL: <reason>` so you know immediately to fix the issue. See `.claude/hooks/validate_risk_schema.py` for the implementation.

## Known Limitations / Non-Goals

- **No data persistence.** Data is analyzed in-memory only; there is no database or session storage.
- **Single-file upload.** The app accepts one Excel file at a time.
- **Templated (not generative) recommendation text.** The "AI recommendation" is not LLM-generated; it follows a deterministic rule set. This is intentional — it keeps the system offline, auditable, and unambiguous.
- **No authentication.** This is a local demo tool; there is no user login or access control.
- **No real-time updates.** Re-upload or reload to refresh.

## Troubleshooting

**Streamlit won't start:**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check that port 8501 is not in use, or specify a different port: `streamlit run app.py --server.port 8502`

**Sample data is missing or outdated:**
- Regenerate it: `python3 scripts/generate_sample_data.py`
- This will create `sample_data/shipments_sample.xlsx` with 80 rows of synthetic data.

**KPI counts don't match what you expected:**
- Check that `risk_logic.py` is the source of truth. Never re-implement risk-band logic or excursion detection in `app.py`.
- Run the compliance-checker subagent to flag inconsistencies.

**Hover over the KPI tiles** for a quick summary of how each metric is calculated.
