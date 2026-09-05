---
name: analyze-shipment-risk
description: Use whenever creating or editing risk-scoring logic, temperature-excursion detection, RiskScore/RiskLevel thresholds, or the rule-based AI-recommendation text. Triggers on keywords: risk score, risk level, temperature excursion, threshold, TempThresholdMin, TempThresholdMax, recommendation paragraph.
---

# Pharma Shipment Risk Analysis — Editing Guidance

You are editing code that controls how shipments are classified as "high-risk" or "safe," and how the system recommends cold-chain audit actions. **All decisions made here have audit implications.** This skill ensures your changes remain correct, consistent, and verifiable.

## Canonical Thresholds & Formulas

Before making any change, review these constants from `risk_logic.py`. **If you ever see a different value in CLAUDE.md, `app.py`, or the sample-data generator, the code is wrong — update the code to match, never the other way around.**

### Risk Score Bands

| Level | Score Range | Class |
|---|---|---|
| Low | [0, 40) | Safe |
| Medium | [40, 70) | Watch |
| High | [70, 85) | Alert |
| Critical | [85, 100] | Action |

**High-risk = {High, Critical}**

### Temperature Excursion

A breach occurs when:
```
MinTemp < TempThresholdMin  OR  MaxTemp > TempThresholdMax
```

**Magnitude** (°C) = max(TempThresholdMin − MinTemp, MaxTemp − TempThresholdMax)

**Severity classification** by magnitude:
- `minor`: 0 < magnitude ≤ 2°C
- `moderate`: 2 < magnitude ≤ 5°C
- `critical`: magnitude > 5°C

### Recommendation Rules (Most-Severe-First)

1. **Critical excursion rule**: If any shipment has `magnitude > 5°C`, lead with: "N shipment(s) show critical temperature excursions… recommend immediate cold-chain audit for {top_origin} routes."

2. **Moderate excursion rule**: Else if any excursion, say: "N shipment(s) recorded temperature excursions within 5°C… continue monitoring."

3. **No-excursion rule**: Else: "No temperature excursions detected… cold-chain integrity appears intact."

4. **Risk-level assessment**: Always append a second sentence comparing `(HighRiskCount / Total) * 100` to a 25% warning threshold, and recommend action if exceeded.

## How to Make a Threshold Change

### Step 1: Locate the Constant

Find the value **only** in `risk_logic.py`. Examples:
- Risk bands: `RISK_BANDS = {"Low": (0, 40), ...}` (lines ~14–18)
- Excursion severity: `EXCURSION_SEVERITY_THRESHOLDS = {"minor": (0, 2), ...}` (lines ~21–25)
- Critical excursion magnitude: `CRITICAL_EXCURSION_THRESHOLD = 5.0` (line ~28)
- High-risk percentage warning: `HIGH_RISK_PERCENTAGE_WARNING = 25.0` (line ~29)

### Step 2: Update Only in `risk_logic.py`

Change the constant in one place. Do **not** adjust it in:
- `app.py` (it imports from `risk_logic`, do not re-define)
- `scripts/generate_sample_data.py` (it imports from `risk_logic`)
- CLAUDE.md (update CLAUDE.md *after* verifying the code works)

### Step 3: Regenerate Sample Data (if a threshold changed)

```bash
python3 scripts/generate_sample_data.py
```

This ensures the bundled demo data reflects your new thresholds. **Commit the regenerated `.xlsx`** so future users see consistent, up-to-date sample data.

### Step 4: Sanity-Check the App

```bash
streamlit run app.py --server.port 8501
```

Upload `sample_data/shipments_sample.xlsx` (or a test file) and verify:
- **KPI counts are reasonable.** If you lowered the "High" threshold from 70 to 60, the high-risk count should increase.
- **No exceptions in the Streamlit console.**
- **Recommendation text makes sense.** Sentences should be grammatically sound and logically ordered.

### Step 5: Update CLAUDE.md

Once the code is correct, mirror the changed threshold(s) into CLAUDE.md so the documentation stays authoritative.

## Hard Invariants to Preserve

✓ **Excursion formula is always `MinTemp < TempThresholdMin OR MaxTemp > TempThresholdMax`** — never > instead of >=, never mix AND with OR, never invert the logic.

✓ **Risk bands are contiguous (no gaps) and non-overlapping.** Example: `Low [0, 40)`, `Medium [40, 70)`, `High [70, 85)`, `Critical [85, 100]` — the next band always starts where the previous ends.

✓ **Recommendation rules are ordered most-severe-first** — always check critical excursions before moderate, moderate before none. Never re-sort based on data.

✓ **Recommendation rules are deterministic.** No `random.choice()`, no `np.random.shuffled()`, no network calls (`requests`, `urllib`). Every run with the same input must produce the same text.

✓ **No API keys or authentication tokens embedded anywhere.** The app is local and fully offline.

## Pre-Completion Checklist

Before you consider this change done:

- [ ] I located the constant(s) I changed **only** in `risk_logic.py`.
- [ ] I did **not** copy or re-implement the same logic in `app.py` or the sample generator.
- [ ] I ran `python3 scripts/generate_sample_data.py` and saw output confirming the new data was written.
- [ ] I ran `streamlit run app.py --server.port 8501` and loaded the sample file; no exceptions appeared.
- [ ] I eyeballed the KPI tiles to confirm counts moved in the expected direction.
- [ ] If I touched the risk-distribution chart, I reviewed it against the **`dataviz` skill's status-palette guidance** (see CLAUDE.md § Custom Claude Code Tooling → "Skill: /analyze-shipment-risk"):
  - `Low` uses status-palette `good` (#0ca30c).
  - `Medium` uses status-palette `warning` (#fab219).
  - `High` uses status-palette `serious` (#ec835a).
  - `Critical` uses status-palette `critical` (#d03b3b).
  - Bars have direct value labels as a relief channel (because warning/serious are below 3:1 contrast on the light surface).
- [ ] I updated CLAUDE.md to reflect the new threshold(s).
- [ ] **I am delegating this change to the `pharma-compliance-checker` subagent for final review before I mark it complete.**

## After You're Done

Proactively send this change to the **`pharma-compliance-checker` subagent** (see `.claude/agents/pharma-compliance-checker.md`) before considering the task finished. It will verify:
1. No threshold is duplicated outside `risk_logic.py`.
2. All 12 required columns are still handled correctly.
3. The excursion formula has not drifted.
4. The recommendation logic is deterministic.
5. Risk bands remain aligned.
6. The recommendation text is sensible and auditable.

If it flags any issues, fix them before declaring this change complete.

---

**Remember:** This system is auditable precisely because all thresholds and logic live in one place and are never re-derived. Guard that property.
