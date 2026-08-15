"""Unit tests for the Gemma-voiced structural report composer."""

import json
import subprocess
import sys
from pathlib import Path

from scan_report import build_report, format_size

SCRIPT_PATH = Path(__file__).parent / "scan_report.py"


def test_format_size_units():
    assert format_size(512) == "512.0 B"
    assert format_size(2048) == "2.0 KB"
    assert format_size(5 * 1024 * 1024) == "5.0 MB"


def test_build_report_empty_workspace():
    report = build_report({"root": "D:\\Empty", "totalFiles": 0, "totalDirectories": 0, "totalSizeBytes": 0})
    assert "D:\\Empty" in report
    assert "No files were detected" in report


def test_build_report_with_subfolders_and_extensions():
    summary = {
        "root": "D:\\Workspace",
        "totalFiles": 12,
        "totalDirectories": 4,
        "totalSizeBytes": 4_500_000,
        "subfolders": [
            {"name": "Docs", "fileCount": 6},
            {"name": "Images", "fileCount": 4},
            {"name": "Code", "fileCount": 2},
        ],
        "topExtensions": [{"extension": "pdf", "count": 5}, {"extension": "png", "count": 4}],
    }
    report = build_report(summary)
    assert "Docs (6 files)" in report
    assert "pdf x5" in report
    assert "No files have been moved" in report


def test_build_report_high_folder_count_calls_out_automation():
    summary = {
        "root": "E:\\Big",
        "totalFiles": 500,
        "totalDirectories": 40,
        "totalSizeBytes": 900_000_000,
        "subfolders": [{"name": f"Folder{i}", "fileCount": 10} for i in range(40)],
    }
    report = build_report(summary)
    assert "strong candidate for an automated structure plan" in report


def test_cli_entrypoint_prints_report_to_stdout():
    payload = json.dumps({"root": "D:\\CLI", "totalFiles": 3, "totalDirectories": 1, "totalSizeBytes": 1024})
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), payload],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "D:\\CLI" in result.stdout
    assert result.stderr == ""


def test_cli_entrypoint_rejects_invalid_json():
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "not-json"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "invalid scan summary JSON" in result.stderr
