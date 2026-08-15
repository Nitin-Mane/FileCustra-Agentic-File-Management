#!/usr/bin/env python3
"""
Test suite for FileCustra Local Model Manager.
"""

import json
import tempfile
import unittest
from pathlib import Path

from model_manager import (
    ModelManager,
    ModelInfo,
    DeviceCapabilities,
    BenchmarkResult,
    HardwareDetector,
    DeviceBenchmark,
    ChecksumValidator,
    create_model_manager,
)


class TestModelInfo(unittest.TestCase):
    """Test ModelInfo dataclass."""
    
    def test_to_dict(self):
        model = ModelInfo(
            name="Gemma-4-E2B",
            version="1.0.0",
            model_type="llm",
            file_path="/models/gemma.gguf",
            size_bytes=2_000_000_000,
            hash_sha256="abc123",
            downloaded=True,
            license_accepted=True,
        )
        
        d = model.to_dict()
        
        self.assertEqual(d["name"], "Gemma-4-E2B")
        self.assertEqual(d["version"], "1.0.0")
        self.assertEqual(d["model_type"], "llm")
        self.assertEqual(d["size_gb"], 1.86)
        self.assertTrue(d["downloaded"])
        self.assertTrue(d["license_accepted"])


class TestDeviceCapabilities(unittest.TestCase):
    """Test DeviceCapabilities dataclass."""
    
    def test_to_dict(self):
        caps = DeviceCapabilities(
            cpu_cores=8,
            cpu_threads=16,
            cpu_name="Intel Core i7",
            ram_total_gb=32.0,
            ram_available_gb=16.0,
            gpu_name="NVIDIA RTX 3080",
            gpu_vram_gb=10.0,
            cuda_available=True,
            directml_available=False,
            cpu_only=False,
        )
        
        d = caps.to_dict()
        
        self.assertEqual(d["cpu_cores"], 8)
        self.assertEqual(d["cpu_threads"], 16)
        self.assertEqual(d["ram_total_gb"], 32.0)
        self.assertTrue(d["cuda_available"])


class TestBenchmarkResult(unittest.TestCase):
    """Test BenchmarkResult dataclass."""
    
    def test_to_dict(self):
        result = BenchmarkResult(
            device="cpu",
            inference_speed_tokens_per_sec=150.5,
            memory_usage_gb=4.0,
            recommended_model_size="medium",
            benchmark_duration_sec=10.5,
        )
        
        d = result.to_dict()
        
        self.assertEqual(d["device"], "cpu")
        self.assertEqual(d["inference_speed_tokens_per_sec"], 150.5)
        self.assertEqual(d["recommended_model_size"], "medium")


class TestChecksumValidator(unittest.TestCase):
    """Test checksum validation."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_compute_sha256(self):
        test_file = Path(self.temp_dir) / "test.txt"
        test_file.write_text("Hello world")
        
        hash_value = ChecksumValidator.compute_sha256(str(test_file))
        
        self.assertEqual(len(hash_value), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in hash_value))
    
    def test_validate_checksum(self):
        test_file = Path(self.temp_dir) / "test.txt"
        test_file.write_text("Hello world")
        
        hash_value = ChecksumValidator.compute_sha256(str(test_file))
        
        self.assertTrue(ChecksumValidator.validate_checksum(str(test_file), hash_value))
        self.assertFalse(ChecksumValidator.validate_checksum(str(test_file), "wrong_hash"))


class TestHardwareDetector(unittest.TestCase):
    """Test hardware detection."""
    
    def test_detect(self):
        detector = HardwareDetector()
        caps = detector.detect()
        
        self.assertIsInstance(caps, DeviceCapabilities)
        self.assertGreater(caps.cpu_cores, 0)
        self.assertGreater(caps.cpu_threads, 0)
        self.assertGreater(caps.ram_total_gb, 0)


class TestModelManager(unittest.TestCase):
    """Test model manager."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.models_dir = Path(self.temp_dir) / "models"
        self.models_dir.mkdir()
        self.manifest_path = self.models_dir / "manifest.json"
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_manager(self):
        manager = create_model_manager(str(self.models_dir), str(self.manifest_path))
        self.assertIsInstance(manager, ModelManager)
    
    def test_register_model(self):
        manager = create_model_manager(str(self.models_dir), str(self.manifest_path))
        
        test_file = self.models_dir / "model.bin"
        test_file.write_bytes(b"model data")
        
        model = manager.register_model(
            name="test-model",
            version="1.0.0",
            model_type="llm",
            file_path=str(test_file),
            hash_sha256="abc123",
        )
        
        self.assertEqual(model.name, "test-model")
        self.assertTrue(model.downloaded)
    
    def test_list_models(self):
        manager = create_model_manager(str(self.models_dir), str(self.manifest_path))
        
        manager.register_model("model1", "1.0", "llm", "/fake/path")
        manager.register_model("model2", "1.0", "embedding", "/fake/path")
        
        models = manager.list_models()
        self.assertEqual(len(models), 2)
    
    def test_get_model(self):
        manager = create_model_manager(str(self.models_dir), str(self.manifest_path))
        
        manager.register_model("test-model", "1.0", "llm", "/fake/path")
        
        model = manager.get_model("test-model")
        self.assertIsNotNone(model)
        self.assertEqual(model.name, "test-model")
        
        self.assertIsNone(manager.get_model("nonexistent"))
    
    def test_verify_model(self):
        manager = create_model_manager(str(self.models_dir), str(self.manifest_path))
        
        test_file = self.models_dir / "model.bin"
        test_file.write_text("test content")
        
        expected_hash = ChecksumValidator.compute_sha256(str(test_file))
        
        manager.register_model(
            "test-model",
            "1.0",
            "llm",
            str(test_file),
            hash_sha256=expected_hash,
        )
        
        self.assertTrue(manager.verify_model("test-model"))
    
    def test_accept_license(self):
        manager = create_model_manager(str(self.models_dir), str(self.manifest_path))
        
        manager.register_model("test-model", "1.0", "llm", "/fake/path")
        
        result = manager.accept_license("test-model")
        self.assertTrue(result)
        
        model = manager.get_model("test-model")
        self.assertTrue(model.license_accepted)
    
    def test_get_device_capabilities(self):
        manager = create_model_manager(str(self.models_dir), str(self.manifest_path))
        
        caps = manager.get_device_capabilities()
        
        self.assertIsInstance(caps, DeviceCapabilities)
        self.assertGreater(caps.cpu_threads, 0)
    
    def test_run_benchmark(self):
        manager = create_model_manager(str(self.models_dir), str(self.manifest_path))
        
        benchmark = manager.run_benchmark()
        
        self.assertIsInstance(benchmark, BenchmarkResult)
        self.assertGreater(benchmark.inference_speed_tokens_per_sec, 0)
    
    def test_get_installed_size(self):
        manager = create_model_manager(str(self.models_dir), str(self.manifest_path))
        
        test_file = self.models_dir / "model.bin"
        test_file.write_bytes(b"test content" * 1000)
        
        manager.register_model("test-model", "1.0", "llm", str(test_file))
        
        size = manager.get_installed_size()
        self.assertGreater(size, 0)
    
    def test_get_model_count(self):
        manager = create_model_manager(str(self.models_dir), str(self.manifest_path))
        
        manager.register_model("model1", "1.0", "llm", "/fake/path")
        manager.register_model("model2", "1.0", "embedding", "/fake/path")
        
        counts = manager.get_model_count()
        
        self.assertEqual(counts["total"], 2)
        self.assertEqual(counts["downloaded"], 0)


class TestModelManagerIntegration(unittest.TestCase):
    """Integration tests for model manager."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.models_dir = Path(self.temp_dir) / "models"
        self.models_dir.mkdir()
        self.manifest_path = self.models_dir / "manifest.json"
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_manifest_persistence(self):
        manager1 = create_model_manager(str(self.models_dir), str(self.manifest_path))
        manager1.register_model("test-model", "1.0", "llm", "/fake/path")
        
        manager2 = create_model_manager(str(self.models_dir), str(self.manifest_path))
        models = manager2.list_models()
        
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0].name, "test-model")


if __name__ == "__main__":
    unittest.main()
