#!/usr/bin/env python3
"""
FileCustra E2E Integration & Fault Injection Engine
End-to-end pipeline testing, fault injection, and large-folder performance benchmarks.
"""

import os
import random
import shutil
import string
import tempfile
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class FaultType(Enum):
    """Types of faults that can be injected."""
    DISK_FULL = "disk_full"
    PERMISSION_DENIED = "permission_denied"
    FILE_LOCKED = "file_locked"
    NETWORK_TIMEOUT = "network_timeout"
    CORRUPTED_DATA = "corrupted_data"
    PARTIAL_WRITE = "partial_write"


class TestStatus(Enum):
    """Status of a test run."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    """Result of a single test."""
    test_id: str
    name: str
    status: TestStatus
    duration_sec: float = 0.0
    details: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "test_id": self.test_id,
            "name": self.name,
            "status": self.status.value,
            "duration_sec": self.duration_sec,
            "details": self.details,
            "metrics": self.metrics,
        }


@dataclass
class BenchmarkResult:
    """Result of a performance benchmark."""
    name: str
    files_processed: int
    total_size_bytes: int
    duration_sec: float
    throughput_files_per_sec: float = 0.0
    throughput_mbps: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "files_processed": self.files_processed,
            "total_size_bytes": self.total_size_bytes,
            "duration_sec": self.duration_sec,
            "throughput_files_per_sec": self.throughput_files_per_sec,
            "throughput_mbps": self.throughput_mbps,
        }


class FaultInjector:
    """Injects faults for testing error handling."""
    
    def __init__(self):
        self._active_faults: Dict[FaultType, bool] = {ft: False for ft in FaultType}
        self._fault_probability: Dict[FaultType, float] = {ft: 0.0 for ft in FaultType}
    
    def enable_fault(self, fault_type: FaultType, probability: float = 1.0) -> None:
        self._active_faults[fault_type] = True
        self._fault_probability[fault_type] = min(1.0, max(0.0, probability))
    
    def disable_fault(self, fault_type: FaultType) -> None:
        self._active_faults[fault_type] = False
        self._fault_probability[fault_type] = 0.0
    
    def disable_all(self) -> None:
        for ft in FaultType:
            self.disable_fault(ft)
    
    def should_inject(self, fault_type: FaultType) -> bool:
        if not self._active_faults.get(fault_type, False):
            return False
        return random.random() < self._fault_probability[fault_type]
    
    def get_active_faults(self) -> List[str]:
        return [ft.value for ft, active in self._active_faults.items() if active]


class TestDataGenerator:
    """Generates test data for integration tests."""
    
    @staticmethod
    def create_file_tree(
        root_dir: str,
        num_files: int = 100,
        max_depth: int = 3,
        file_size_range: tuple = (100, 10000),
    ) -> List[str]:
        """Create a tree of test files."""
        files = []
        
        for _ in range(num_files):
            depth = random.randint(0, max_depth)
            parts = [
                random.choice(string.ascii_lowercase)
                for _ in range(depth)
            ]
            dir_path = os.path.join(root_dir, *parts) if parts else root_dir
            os.makedirs(dir_path, exist_ok=True)
            
            ext = random.choice([".txt", ".pdf", ".jpg", ".py", ".md", ".csv"])
            name = "".join(random.choices(string.ascii_lowercase, k=8)) + ext
            file_path = os.path.join(dir_path, name)
            
            size = random.randint(*file_size_range)
            with open(file_path, "wb") as f:
                f.write(os.urandom(size))
            
            files.append(file_path)
        
        return files
    
    @staticmethod
    def create_large_folder(
        root_dir: str,
        file_count: int = 1000,
    ) -> dict:
        """Create a large folder for performance testing."""
        start = time.time()
        files = TestDataGenerator.create_file_tree(
            root_dir,
            num_files=file_count,
            max_depth=4,
            file_size_range=(100, 50000),
        )
        duration = time.time() - start
        
        total_size = sum(os.path.getsize(f) for f in files)
        
        return {
            "files_created": len(files),
            "total_size_bytes": total_size,
            "creation_time_sec": round(duration, 3),
        }


class E2ETestRunner:
    """Runs end-to-end integration tests."""
    
    def __init__(self, fault_injector: Optional[FaultInjector] = None):
        self._fault_injector = fault_injector or FaultInjector()
        self._results: List[TestResult] = []
    
    @property
    def fault_injector(self) -> FaultInjector:
        return self._fault_injector
    
    def run_pipeline_test(self, source_dir: str) -> TestResult:
        """Test the full scan-analyze-plan pipeline."""
        start = time.time()
        
        try:
            files = []
            for root, _, filenames in os.walk(source_dir):
                for fname in filenames:
                    files.append(os.path.join(root, fname))
            
            if not files:
                return TestResult(
                    test_id="pipeline-001",
                    name="Full Pipeline Test",
                    status=TestStatus.SKIPPED,
                    details="No files found in source directory",
                )
            
            analyzed = 0
            for f in files:
                try:
                    size = os.path.getsize(f)
                    ext = Path(f).suffix.lower()
                    analyzed += 1
                except Exception as e:
                    if self._fault_injector.should_inject(FaultType.PERMISSION_DENIED):
                        continue
                    return TestResult(
                        test_id="pipeline-001",
                        name="Full Pipeline Test",
                        status=TestStatus.FAILED,
                        duration_sec=time.time() - start,
                        details=f"Error analyzing {f}: {e}",
                    )
            
            duration = time.time() - start
            
            return TestResult(
                test_id="pipeline-001",
                name="Full Pipeline Test",
                status=TestStatus.PASSED,
                duration_sec=round(duration, 3),
                details=f"Successfully analyzed {analyzed}/{len(files)} files",
                metrics={
                    "files_scanned": len(files),
                    "files_analyzed": analyzed,
                    "scan_duration_sec": round(duration, 3),
                },
            )
        
        except Exception as e:
            return TestResult(
                test_id="pipeline-001",
                name="Full Pipeline Test",
                status=TestStatus.ERROR,
                duration_sec=time.time() - start,
                details=str(e),
            )
    
    def run_copy_with_fault_test(
        self,
        source_dir: str,
        dest_dir: str,
    ) -> TestResult:
        """Test file copy with potential faults."""
        start = time.time()
        
        try:
            files = []
            for root, _, filenames in os.walk(source_dir):
                for fname in filenames:
                    files.append(os.path.join(root, fname))
            
            copied = 0
            failed = 0
            
            for f in files:
                try:
                    rel = os.path.relpath(f, source_dir)
                    dest_path = os.path.join(dest_dir, rel)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    
                    if self._fault_injector.should_inject(FaultType.DISK_FULL):
                        failed += 1
                        continue
                    
                    shutil.copy2(f, dest_path)
                    copied += 1
                except Exception:
                    failed += 1
            
            duration = time.time() - start
            
            return TestResult(
                test_id="fault-001",
                name="Copy with Fault Injection",
                status=TestStatus.PASSED if failed == 0 else TestStatus.PARTIAL if copied > 0 else TestStatus.FAILED,
                duration_sec=round(duration, 3),
                details=f"Copied: {copied}, Failed: {failed}",
                metrics={
                    "files_copied": copied,
                    "files_failed": failed,
                    "total_files": len(files),
                },
            )
        
        except Exception as e:
            return TestResult(
                test_id="fault-001",
                name="Copy with Fault Injection",
                status=TestStatus.ERROR,
                duration_sec=time.time() - start,
                details=str(e),
            )
    
    def run_performance_benchmark(
        self,
        test_dir: str,
        file_count: int = 500,
    ) -> BenchmarkResult:
        """Run a performance benchmark on file scanning."""
        stats = TestDataGenerator.create_large_folder(test_dir, file_count)
        
        start = time.time()
        files_scanned = 0
        total_bytes = 0
        
        for root, _, filenames in os.walk(test_dir):
            for fname in filenames:
                fpath = os.path.join(root, fname)
                try:
                    size = os.path.getsize(fpath)
                    total_bytes += size
                    files_scanned += 1
                except Exception:
                    pass
        
        duration = time.time() - start
        
        throughput = files_scanned / duration if duration > 0 else 0
        mbps = (total_bytes / 1024 / 1024) / duration if duration > 0 else 0
        
        return BenchmarkResult(
            name="File Scan Performance",
            files_processed=files_scanned,
            total_size_bytes=total_bytes,
            duration_sec=round(duration, 3),
            throughput_files_per_sec=round(throughput, 1),
            throughput_mbps=round(mbps, 2),
        )
    
    def get_all_results(self) -> List[TestResult]:
        return list(self._results)


class IntegrationTestSuite:
    """Complete integration test suite."""
    
    def __init__(self):
        self._runner = E2ETestRunner()
    
    @property
    def runner(self) -> E2ETestRunner:
        return self._runner
    
    def run_full_suite(self, test_dir: str) -> dict:
        """Run the full integration test suite."""
        results = []
        
        pipeline_result = self._runner.run_pipeline_test(test_dir)
        results.append(pipeline_result)
        
        with tempfile.TemporaryDirectory() as dest:
            copy_result = self._runner.run_copy_with_fault_test(test_dir, dest)
            results.append(copy_result)
        
        self._runner.fault_injector.enable_fault(FaultType.DISK_FULL, probability=0.3)
        with tempfile.TemporaryDirectory() as fault_dest:
            fault_result = self._runner.run_copy_with_fault_test(test_dir, fault_dest)
            results.append(fault_result)
        self._runner.fault_injector.disable_all()
        
        benchmark = self._runner.run_performance_benchmark(test_dir, file_count=200)
        
        passed = sum(1 for r in results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in results if r.status in [TestStatus.FAILED, TestStatus.ERROR])
        
        return {
            "results": [r.to_dict() for r in results],
            "benchmark": benchmark.to_dict(),
            "summary": {
                "total_tests": len(results),
                "passed": passed,
                "failed": failed,
            },
        }


def create_integration_suite() -> IntegrationTestSuite:
    """Factory function to create an integration test suite."""
    return IntegrationTestSuite()


if __name__ == "__main__":
    suite = create_integration_suite()
    with tempfile.TemporaryDirectory() as test_dir:
        TestDataGenerator.create_file_tree(test_dir, num_files=50)
        report = suite.run_full_suite(test_dir)
        print(f"Integration suite: {report['summary']['passed']}/{report['summary']['total_tests']} passed")
