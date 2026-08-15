#!/usr/bin/env python3
"""Runtime readiness probe.

Checks the real Python interpreter, required third-party libraries, local
model catalog files, and Tesseract OCR availability, then prints a single
JSON object to stdout. Invoked as a one-shot subprocess by the Tauri
`check_runtime_readiness` command at app startup, so failures are surfaced on
the loading screen instead of showing up later as an unexplained scan error.
"""

import contextlib
import io
import json
import shutil
import sys
from pathlib import Path

SIDECAR_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SIDECAR_DIR.parent.parent
MANIFEST_PATH = PROJECT_ROOT / "resources" / "models" / "manifest.json"

LIBRARIES = [
    ("magika", "Google Magika File Classifier"),
    ("onnxruntime", "ONNX Runtime Engine"),
    ("pymupdf", "PyMuPDF PDF Engine"),
    ("pytesseract", "Tesseract OCR Interface"),
    ("docx", "python-docx Parser"),
    ("openpyxl", "openpyxl Excel Engine"),
    ("numpy", "NumPy Array Engine"),
    ("requests", "Requests HTTP Client"),
    ("pydantic", "Pydantic Schema Validator"),
]


def check_libraries():
    results = []
    for module_name, label in LIBRARIES:
        try:
            # Some libraries print notices on import (e.g. PyMuPDF's legacy
            # `fitz` alias). Swallow any such stdout noise so it can never
            # land ahead of the JSON payload this script writes to stdout.
            with contextlib.redirect_stdout(io.StringIO()):
                module = __import__(module_name)
            version = str(getattr(module, "__version__", "available"))
            results.append({"module": module_name, "label": label, "available": True, "version": version})
        except Exception as exc:
            results.append({"module": module_name, "label": label, "available": False, "error": str(exc)})
    return results


def check_models():
    if not MANIFEST_PATH.exists():
        return []

    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []

    results = []
    for entry in manifest.get("models", []):
        relative_path = entry.get("relative_path", "")
        model_path = (PROJECT_ROOT / relative_path) if relative_path else None
        present = bool(model_path and model_path.exists())
        actual_size = model_path.stat().st_size if present else 0
        expected_size = entry.get("size_bytes", 0)
        is_placeholder = present and expected_size and actual_size < expected_size * 0.05
        results.append(
            {
                "id": entry.get("id"),
                "name": entry.get("name"),
                "category": entry.get("category"),
                "quantization": entry.get("quantization"),
                "present": present,
                "actualSizeBytes": actual_size,
                "expectedSizeBytes": expected_size,
                "isPlaceholder": bool(is_placeholder),
            }
        )
    return results


def check_tesseract():
    path = shutil.which("tesseract")
    return {"available": path is not None, "path": path}


def main() -> None:
    payload = {
        "pythonAvailable": True,
        "pythonVersion": sys.version.split()[0],
        "pythonExecutable": sys.executable,
        "libraries": check_libraries(),
        "models": check_models(),
        "tesseract": check_tesseract(),
    }
    sys.stdout.write(json.dumps(payload))


if __name__ == "__main__":
    main()
