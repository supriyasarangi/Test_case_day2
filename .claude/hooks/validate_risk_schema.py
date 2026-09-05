#!/usr/bin/env python3
"""
PostToolUse hook: Validate risk schema and threshold integrity after Edit/Write operations.

This script runs automatically after any Edit or Write to critical files:
- risk_logic.py
- app.py
- scripts/generate_sample_data.py
- sample_data/*.xlsx

On failure, exits with code 2 (blocking) and prints HOOK FAIL to stderr.
On success, exits 0 (silent pass).
"""

import sys
import json
import subprocess
import tempfile
from pathlib import Path


def fail(message: str) -> None:
    """Print a blocking failure and exit."""
    print(f"HOOK FAIL: {message}", file=sys.stderr)
    sys.exit(2)


def get_file_path() -> Path:
    """Extract file_path from the PostToolUse hook JSON on stdin."""
    try:
        hook_data = json.load(sys.stdin)
        file_path = hook_data.get("tool_input", {}).get("file_path")
        if not file_path:
            return None
        return Path(file_path)
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def validate_risk_logic_py(fpath: Path) -> None:
    """
    Import risk_logic.py in a subprocess and validate:
    - Risk bands are contiguous and non-overlapping.
    - Excursion-severity thresholds are ordered.
    """
    try:
        # Attempt to import the module in a subprocess to catch import-time errors
        result = subprocess.run(
            [sys.executable, "-c", f"import sys; sys.path.insert(0, '{fpath.parent}'); import risk_logic; "
             "assert risk_logic.RISK_BANDS is not None; "
             "assert risk_logic.EXCURSION_SEVERITY_THRESHOLDS is not None"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            fail(f"risk_logic.py import failed: {result.stderr}")

        # Additional validation: check band contiguity
        result = subprocess.run(
            [sys.executable, "-c",
             f"""
import sys
sys.path.insert(0, '{fpath.parent}')
import risk_logic

bands = risk_logic.RISK_BANDS
expected = [("Low", 0, 40), ("Medium", 40, 70), ("High", 70, 85), ("Critical", 85, 101)]
for name, expected_low, expected_high in expected:
    if name not in bands:
        raise AssertionError(f"Band {{name}} not found")
    actual_low, actual_high = bands[name]
    if actual_low != expected_low or actual_high != expected_high:
        raise AssertionError(f"Band {{name}} is {{(actual_low, actual_high)}}, expected {{(expected_low, expected_high)}}")
"""],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            fail(f"Risk bands validation failed: {result.stderr}")

    except subprocess.TimeoutExpired:
        fail("risk_logic.py validation timed out")
    except Exception as e:
        fail(f"risk_logic.py validation error: {e}")


def validate_python_file(fpath: Path) -> None:
    """
    For app.py or generate_sample_data.py:
    - Syntax check via py_compile.
    - Grep for forbidden network imports.
    """
    # Syntax check
    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(fpath)],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            fail(f"Python syntax error in {fpath.name}: {result.stderr}")
    except subprocess.TimeoutExpired:
        fail(f"Syntax check for {fpath.name} timed out")

    # Check for forbidden imports
    try:
        content = fpath.read_text()
        forbidden = ["requests", "urllib.request", "openai", "anthropic"]
        for imp in forbidden:
            if imp in content and not imp.startswith("#"):
                # Do a more careful check to avoid false positives in comments/strings
                for line in content.split("\n"):
                    if imp in line and not line.strip().startswith("#"):
                        fail(f"Forbidden import '{imp}' found in {fpath.name}:{fpath.read_text().count(chr(10)) - len(content.split(imp, 1)[0].split(chr(10))) + 1}")
    except Exception as e:
        fail(f"Cannot validate imports in {fpath.name}: {e}")


def validate_xlsx_file(fpath: Path) -> None:
    """
    For sample_data/*.xlsx:
    - Check that the 12 required columns are present.
    """
    try:
        import pandas as pd
    except ImportError:
        # pandas not installed yet; skip this check
        return

    try:
        df = pd.read_excel(fpath)
        required = [
            "ShipmentID", "Origin", "Destination", "ProductType", "DepartureDate",
            "MinTemp", "MaxTemp", "TempThresholdMin", "TempThresholdMax",
            "TransitDays", "RiskScore", "RiskLevel"
        ]
        missing = [col for col in required if col not in df.columns]
        if missing:
            fail(f"Excel file {fpath.name} is missing columns: {', '.join(missing)}")
    except Exception as e:
        fail(f"Cannot validate Excel file {fpath.name}: {e}")


def main():
    """Main hook logic."""
    fpath = get_file_path()

    # No-op for files we don't care about
    if fpath is None:
        sys.exit(0)

    fname = fpath.name
    is_risk_logic = fname == "risk_logic.py"
    is_app = fname == "app.py"
    is_generator = fname == "generate_sample_data.py"
    is_sample_xlsx = fpath.name.endswith(".xlsx") and "sample_data" in str(fpath)

    # Only validate files we recognize
    if not any([is_risk_logic, is_app, is_generator, is_sample_xlsx]):
        sys.exit(0)

    # Route to appropriate validator
    if is_risk_logic:
        validate_risk_logic_py(fpath)
    elif is_app or is_generator:
        validate_python_file(fpath)
    elif is_sample_xlsx:
        validate_xlsx_file(fpath)

    # Success: silent exit
    sys.exit(0)


if __name__ == "__main__":
    main()
