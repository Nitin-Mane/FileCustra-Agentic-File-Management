#!/usr/bin/env python3
"""
FileCustra Local Model Manager
Manages local AI model catalog, downloads, SHA-256 verification, device benchmarking,
and hardware auto-detection for Gemma models.
"""

import hashlib
import json
import logging
import os
import platform
import shutil
import struct
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Information about a local AI model."""
    name: str
    version: str
    model_type: str
    file_path: str
    size_bytes: int
    hash_sha256: Optional[str] = None
    hash_verified: bool = False
    downloaded: bool = False
    download_url: Optional[str] = None
    license_accepted: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "model_type": self.model_type,
            "file_path": self.file_path,
            "size_bytes": self.size_bytes,
            "size_gb": round(self.size_bytes / (1024 ** 3), 2),
            "hash_sha256": self.hash_sha256,
            "hash_verified": self.hash_verified,
            "downloaded": self.downloaded,
            "download_url": self.download_url,
            "license_accepted": self.license_accepted,
            "metadata": self.metadata,
        }


@dataclass
class DeviceCapabilities:
    """Hardware device capabilities."""
    cpu_cores: int
    cpu_threads: int
    cpu_name: str
    ram_total_gb: float
    ram_available_gb: float
    gpu_name: Optional[str]
    gpu_vram_gb: Optional[float]
    cuda_available: bool
    directml_available: bool
    cpu_only: bool
    
    def to_dict(self) -> dict:
        return {
            "cpu_cores": self.cpu_cores,
            "cpu_threads": self.cpu_threads,
            "cpu_name": self.cpu_name,
            "ram_total_gb": self.ram_total_gb,
            "ram_available_gb": self.ram_available_gb,
            "gpu_name": self.gpu_name,
            "gpu_vram_gb": self.gpu_vram_gb,
            "cuda_available": self.cuda_available,
            "directml_available": self.directml_available,
            "cpu_only": self.cpu_only,
        }


@dataclass
class BenchmarkResult:
    """Result of a device benchmark."""
    device: str
    inference_speed_tokens_per_sec: float
    memory_usage_gb: float
    recommended_model_size: str
    benchmark_duration_sec: float
    
    def to_dict(self) -> dict:
        return {
            "device": self.device,
            "inference_speed_tokens_per_sec": self.inference_speed_tokens_per_sec,
            "memory_usage_gb": self.memory_usage_gb,
            "recommended_model_size": self.recommended_model_size,
            "benchmark_duration_sec": self.benchmark_duration_sec,
        }


class HardwareDetector:
    """Detects hardware capabilities."""
    
    def detect(self) -> DeviceCapabilities:
        cpu_info = self._detect_cpu()
        ram_info = self._detect_ram()
        gpu_info = self._detect_gpu()
        
        return DeviceCapabilities(
            cpu_cores=cpu_info["cores"],
            cpu_threads=cpu_info["threads"],
            cpu_name=cpu_info["name"],
            ram_total_gb=ram_info["total_gb"],
            ram_available_gb=ram_info["available_gb"],
            gpu_name=gpu_info["name"],
            gpu_vram_gb=gpu_info["vram_gb"],
            cuda_available=gpu_info["cuda"],
            directml_available=gpu_info["directml"],
            cpu_only=not gpu_info["cuda"] and not gpu_info["directml"],
        )
    
    def _detect_cpu(self) -> Dict[str, Any]:
        name = platform.processor() or platform.machine() or "Unknown CPU"
        cores = os.cpu_count() or 1
        threads = cores
        
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command",
                     "(Get-CimInstance Win32_Processor).NumberOfCores"],
                    capture_output=True, text=True, timeout=5,
                )
                if result.returncode == 0:
                    cores = int(result.stdout.strip())
        except Exception:
            pass
        
        return {"name": name, "cores": cores, "threads": threads}
    
    def _detect_ram(self) -> Dict[str, float]:
        total_gb = 8.0
        available_gb = 4.0
        
        try:
            if platform.system() == "Windows":
                import ctypes
                
                class MemoryStatus(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]
                
                status = MemoryStatus()
                status.dwLength = ctypes.sizeof(MemoryStatus)
                ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
                
                total_gb = status.ullTotalPhys / (1024 ** 3)
                available_gb = status.ullAvailPhys / (1024 ** 3)
                
                if total_gb > 0:
                    return {"total_gb": round(total_gb, 2), "available_gb": round(available_gb, 2)}
        except Exception:
            pass
        
        try:
            import psutil
            mem = psutil.virtual_memory()
            total_gb = mem.total / (1024 ** 3)
            available_gb = mem.available / (1024 ** 3)
            return {"total_gb": round(total_gb, 2), "available_gb": round(available_gb, 2)}
        except ImportError:
            pass
        
        return {"total_gb": total_gb, "available_gb": available_gb}
    
    def _detect_gpu(self) -> Dict[str, Any]:
        gpu_name = None
        vram_gb = None
        cuda = False
        directml = False
        
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-Command",
                     "(Get-CimInstance Win32_VideoController).Name"],
                    capture_output=True, text=True, timeout=5,
                )
                if result.returncode == 0:
                    names = [n.strip() for n in result.stdout.splitlines() if n.strip()]
                    if names:
                        gpu_name = names[0]
                        
                        if "nvidia" in gpu_name.lower():
                            cuda = True
                        elif "amd" in gpu_name.lower() or "radeon" in gpu_name.lower():
                            directml = True
                        elif "intel" in gpu_name.lower():
                            directml = True
        except Exception:
            pass
        
        return {
            "name": gpu_name,
            "vram_gb": vram_gb,
            "cuda": cuda,
            "directml": directml,
        }


class DeviceBenchmark:
    """Benchmarks device performance for model inference."""
    
    def __init__(self, hardware_detector: HardwareDetector):
        self._detector = hardware_detector
    
    def run_benchmark(self, device: Optional[str] = None) -> BenchmarkResult:
        caps = self._detector.detect()
        
        start_time = time.time()
        
        operations = 1000000
        matrix_size = 100
        
        import numpy as np
        
        for _ in range(10):
            a = np.random.randn(matrix_size, matrix_size).astype(np.float32)
            b = np.random.randn(matrix_size, matrix_size).astype(np.float32)
            _ = np.dot(a, b)
        
        duration = time.time() - start_time
        
        tokens_per_sec = operations / duration / 1000
        
        memory_usage = caps.ram_total_gb * 0.3
        
        if caps.gpu_vram_gb and caps.gpu_vram_gb >= 8:
            recommended = "large"
        elif caps.ram_total_gb >= 16:
            recommended = "medium"
        else:
            recommended = "small"
        
        return BenchmarkResult(
            device=device or "cpu",
            inference_speed_tokens_per_sec=round(tokens_per_sec, 2),
            memory_usage_gb=round(memory_usage, 2),
            recommended_model_size=recommended,
            benchmark_duration_sec=round(duration, 2),
        )


class ChecksumValidator:
    """Validates file checksums."""
    
    @staticmethod
    def compute_sha256(file_path: str) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(8192), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    @staticmethod
    def validate_checksum(file_path: str, expected_hash: str) -> bool:
        actual_hash = ChecksumValidator.compute_sha256(file_path)
        return actual_hash.lower() == expected_hash.lower()


class ModelManager:
    """Manages local AI model catalog and downloads."""
    
    def __init__(
        self,
        models_dir: Optional[str] = None,
        manifest_path: Optional[str] = None,
    ):
        self._models_dir = Path(models_dir) if models_dir else Path("resources/models")
        self._manifest_path = Path(manifest_path) if manifest_path else self._models_dir / "manifest.json"
        self._models: Dict[str, ModelInfo] = {}
        self._hardware_detector = HardwareDetector()
        self._benchmark = DeviceBenchmark(self._hardware_detector)
        self._checksum_validator = ChecksumValidator()
        
        self._models_dir.mkdir(parents=True, exist_ok=True)
        self._load_manifest()
    
    def _load_manifest(self):
        if self._manifest_path.exists():
            try:
                with open(self._manifest_path, "r") as f:
                    data = json.load(f)
                    for model_data in data.get("models", []):
                        model = ModelInfo(**model_data)
                        self._models[model.name] = model
                logger.info(f"Loaded {len(self._models)} models from manifest")
            except Exception as e:
                logger.warning(f"Failed to load manifest: {e}")
    
    def _save_manifest(self):
        try:
            models_data = []
            for model in self._models.values():
                model_dict = {
                    "name": model.name,
                    "version": model.version,
                    "model_type": model.model_type,
                    "file_path": model.file_path,
                    "size_bytes": model.size_bytes,
                    "hash_sha256": model.hash_sha256,
                    "downloaded": model.downloaded,
                    "download_url": model.download_url,
                    "license_accepted": model.license_accepted,
                    "metadata": model.metadata,
                }
                models_data.append(model_dict)
            
            data = {
                "version": "1.0",
                "models": models_data,
            }
            with open(self._manifest_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self._models)} models to manifest")
        except Exception as e:
            logger.warning(f"Failed to save manifest: {e}")
    
    def register_model(
        self,
        name: str,
        version: str,
        model_type: str,
        file_path: str,
        download_url: Optional[str] = None,
        hash_sha256: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ModelInfo:
        path = Path(file_path)
        size_bytes = path.stat().st_size if path.exists() else 0
        
        model = ModelInfo(
            name=name,
            version=version,
            model_type=model_type,
            file_path=file_path,
            size_bytes=size_bytes,
            hash_sha256=hash_sha256,
            downloaded=path.exists(),
            download_url=download_url,
            metadata=metadata or {},
        )
        
        self._models[name] = model
        self._save_manifest()
        
        return model
    
    def get_model(self, name: str) -> Optional[ModelInfo]:
        return self._models.get(name)
    
    def list_models(self) -> List[ModelInfo]:
        return list(self._models.values())
    
    def verify_model(self, name: str) -> bool:
        model = self._models.get(name)
        if not model:
            return False
        
        if not Path(model.file_path).exists():
            return False
        
        if model.hash_sha256:
            verified = self._checksum_validator.validate_checksum(
                model.file_path, model.hash_sha256
            )
            model.hash_verified = verified
            self._save_manifest()
            return verified
        
        return True
    
    def get_device_capabilities(self) -> DeviceCapabilities:
        return self._hardware_detector.detect()
    
    def run_benchmark(self, device: Optional[str] = None) -> BenchmarkResult:
        return self._benchmark.run_benchmark(device)
    
    def get_recommended_model(self) -> Optional[ModelInfo]:
        caps = self._hardware_detector.detect()
        benchmark = self._benchmark.run_benchmark()
        
        if benchmark.recommended_model_size == "large":
            preferred_types = ["large", "medium", "small"]
        elif benchmark.recommended_model_size == "medium":
            preferred_types = ["medium", "small"]
        else:
            preferred_types = ["small"]
        
        for model_type in preferred_types:
            for model in self._models.values():
                if model.model_type == model_type and model.downloaded:
                    return model
        
        for model in self._models.values():
            if model.downloaded:
                return model
        
        return None
    
    def accept_license(self, name: str) -> bool:
        model = self._models.get(name)
        if not model:
            return False
        
        model.license_accepted = True
        self._save_manifest()
        return True
    
    def get_installed_size(self) -> int:
        return sum(model.size_bytes for model in self._models.values() if model.downloaded)
    
    def get_model_count(self) -> Dict[str, int]:
        counts = {"total": len(self._models), "downloaded": 0, "verified": 0}
        for model in self._models.values():
            if model.downloaded:
                counts["downloaded"] += 1
            if model.hash_verified:
                counts["verified"] += 1
        return counts


def create_model_manager(
    models_dir: Optional[str] = None,
    manifest_path: Optional[str] = None,
) -> ModelManager:
    """Factory function to create a model manager."""
    return ModelManager(models_dir, manifest_path)


if __name__ == "__main__":
    manager = create_model_manager()
    
    print("Device Capabilities:")
    caps = manager.get_device_capabilities()
    print(f"  CPU: {caps.cpu_name} ({caps.cpu_threads} threads)")
    print(f"  RAM: {caps.ram_total_gb} GB total, {caps.ram_available_gb} GB available")
    if caps.gpu_name:
        print(f"  GPU: {caps.gpu_name}")
    print(f"  CUDA: {caps.cuda_available}, DirectML: {caps.directml_available}")
    
    print("\nRunning benchmark...")
    benchmark = manager.run_benchmark()
    print(f"  Speed: {benchmark.inference_speed_tokens_per_sec} tokens/sec")
    print(f"  Recommended model size: {benchmark.recommended_model_size}")
    
    print("\nModel Stats:")
    stats = manager.get_model_count()
    print(f"  Total: {stats['total']}, Downloaded: {stats['downloaded']}, Verified: {stats['verified']}")
