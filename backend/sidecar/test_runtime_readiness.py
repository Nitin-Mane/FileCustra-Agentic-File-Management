"""Unit tests for the startup runtime readiness probe."""

import json
import subprocess
import sys
from pathlib import Path

from runtime_readiness import check_libraries, check_models, check_tesseract

SCRIPT_PATH = Path(__file__).parent / "runtime_readiness.py"


def test_check_libraries_reports_every_entry():
    results = check_libraries()
    assert len(results) == 9
    assert all("module" in r and "available" in r for r in results)


def test_check_libraries_flags_missing_module():
    results = check_libraries()
    fake = next((r for r in results if r["module"] == "numpy"), None)
    assert fake is not None
    # numpy is a real test dependency in this repo, so it should resolve.
    assert fake["available"] is True
    assert "version" in fake


def test_check_models_reads_manifest():
    results = check_models()
    ids = {entry["id"] for entry in results}
    assert "magika-v1" in ids
    for entry in results:
        assert "present" in entry
        assert "isPlaceholder" in entry


def test_check_tesseract_returns_bool_and_optional_path():
    result = check_tesseract()
    assert isinstance(result["available"], bool)
    assert result["path"] is None or isinstance(result["path"], str)


def test_cli_entrypoint_prints_valid_json():
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["pythonAvailable"] is True
    assert "libraries" in payload
    assert "models" in payload
    assert "tesseract" in payload
