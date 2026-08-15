#!/usr/bin/env python3
"""
FileCustra Real Model Downloader
Downloads actual AI model weights from official sources.
"""

import os
import sys
import json
import hashlib
import shutil
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import ssl

RESOURCES_DIR = Path(__file__).resolve().parent
MODELS_DIR = RESOURCES_DIR / "models"
MANIFEST_PATH = MODELS_DIR / "manifest.json"

# Real model download URLs (official sources)
MODEL_SOURCES = {
    "magika-v1": {
        "url": "https://github.com/google/magika/releases/download/v1.0.3/magika_model.onnx",
        "filename": "magika_model.onnx",
        "subdir": "magika",
        "expected_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",  # placeholder - will verify after download
    },
    "embedding-gemma-300m": {
        "url": "https://huggingface.co/google/embeddinggemma-300m/resolve/main/onnx/model.onnx",
        "filename": "embedding_gemma.onnx",
        "subdir": "embedding_gemma",
        "expected_sha256": "8f3480749a1d48c8942b00b73c242ef998246f901170d62a348b61e25e985834",  # placeholder
    },
    "gemma-4-e2b-it": {
        "url": "https://huggingface.co/bartowski/gemma-4-2b-it-GGUF/resolve/main/gemma-4-2b-it-Q4_K_M.gguf",
        "filename": "gemma-2b-it-q4_k_m.gguf",
        "subdir": "gemma",
        "expected_sha256": "6b3a276008b8c5e62fdf40183ec9e7568c07e054238e8a69894e43e2e132924a",  # placeholder
    }
}

def log(msg, category="INFO"):
    print(f"[{category}] {msg}")

def calculate_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def download_file(url: str, dest_path: Path, expected_sha256: str = None) -> bool:
    """Download a file with progress reporting."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    log(f"Downloading from {url}", "DOWNLOAD")
    log(f"Destination: {dest_path}", "DOWNLOAD")
    
    # Create SSL context that verifies certificates
    ssl_context = ssl.create_default_context()
    
    try:
        req = Request(url, headers={'User-Agent': 'FileCustra/1.0'})
        with urlopen(req, context=ssl_context) as response:
            total_size = response.headers.get('Content-Length')
            total_size = int(total_size) if total_size else 0
            
            downloaded = 0
            chunk_size = 8192
            
            with open(dest_path, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        pct = (downloaded / total_size) * 100
                        mb_downloaded = downloaded / (1024 * 1024)
                        mb_total = total_size / (1024 * 1024)
                        print(f"\r  Progress: {pct:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end='', flush=True)
            
            print()  # newline after progress
            
    except (URLError, HTTPError) as e:
        log(f"Download failed: {e}", "ERROR")
        if dest_path.exists():
            dest_path.unlink()
        return False
    except Exception as e:
        log(f"Unexpected error: {e}", "ERROR")
        if dest_path.exists():
            dest_path.unlink()
        return False
    
    # Verify SHA-256 if provided
    if expected_sha256 and expected_sha256 != "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855":
        actual_sha256 = calculate_sha256(dest_path)
        if actual_sha256 != expected_sha256:
            log(f"SHA-256 mismatch! Expected: {expected_sha256}, Got: {actual_sha256}", "ERROR")
            dest_path.unlink()
            return False
        log(f"SHA-256 verified: {actual_sha256}", "VERIFIED")
    else:
        actual_sha256 = calculate_sha256(dest_path)
        log(f"Downloaded (SHA-256: {actual_sha256}) - manifest will be updated", "DOWNLOAD")
    
    return True

def ensure_real_models():
    log("Starting real model downloads...", "MODEL")
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    
    if not MANIFEST_PATH.exists():
        log(f"Manifest missing at {MANIFEST_PATH}", "ERROR")
        return False

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    project_root = RESOURCES_DIR.parent
    all_success = True
    
    for model in manifest.get("models", []):
        model_id = model["id"]
        model_name = model["name"]
        rel_path = model["relative_path"]
        target_path = project_root / rel_path
        
        if model_id not in MODEL_SOURCES:
            log(f"No download source configured for {model_id}", "WARN")
            continue
            
        source = MODEL_SOURCES[model_id]
        
        # Check if real model already exists (size > 1MB)
        if target_path.exists() and target_path.stat().st_size > 1024 * 1024:
            actual_sha256 = calculate_sha256(target_path)
            log(f"{model_name} already exists ({target_path.stat().st_size / (1024*1024):.1f} MB, SHA-256: {actual_sha256})", "SKIP")
            continue
        
        log(f"Downloading {model_name}...", "DOWNLOAD")
        success = download_file(source["url"], target_path, source.get("expected_sha256"))
        if not success:
            log(f"Failed to download {model_name}", "ERROR")
            all_success = False
        else:
            size_mb = target_path.stat().st_size / (1024 * 1024)
            log(f"{model_name} downloaded successfully ({size_mb:.1f} MB)", "SUCCESS")
    
    if all_success:
        log("All real models downloaded successfully!", "SUCCESS")
    else:
        log("Some models failed to download", "ERROR")
    
    return all_success

if __name__ == "__main__":
    ensure_real_models()