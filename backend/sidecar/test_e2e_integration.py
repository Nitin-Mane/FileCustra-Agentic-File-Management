#!/usr/bin/env python3
"""Tests for E2E integration, fault injection, and performance benchmarks."""

import os
import shutil
import tempfile

import pytest

from e2e_integration import (
    BenchmarkResult,
    E2ETestRunner,
    FaultInjector,
    FaultType,
    IntegrationTestSuite,
    TestDataGenerator,
    TestResult,
    TestStatus,
    create_integration_suite,
)


@pytest.fixture
def tmp_workspace():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def populated_dir(tmp_workspace):
    src = os.path.join(tmp_workspace, "source")
    os.makedirs(src)
    TestDataGenerator.create_file_tree(src, num_files=30)
    return src


@pytest.fixture
def fault_injector():
    return FaultInjector()


@pytest.fixture
def runner(fault_injector):
    return E2ETestRunner(fault_injector)


class TestFaultType:
    def test_all_types(self):
        assert FaultType.DISK_FULL.value == "disk_full"
        assert FaultType.PERMISSION_DENIED.value == "permission_denied"
        assert FaultType.FILE_LOCKED.value == "file_locked"


class TestTestStatus:
    def test_all_statuses(self):
        assert TestStatus.PASSED.value == "passed"
        assert TestStatus.FAILED.value == "failed"
        assert TestStatus.SKIPPED.value == "skipped"
        assert TestStatus.ERROR.value == "error"


class TestTestResult:
    def test_to_dict(self):
        result = TestResult(
            test_id="t-1",
            name="Test A",
            status=TestStatus.PASSED,
            duration_sec=1.5,
        )
        d = result.to_dict()
        assert d["test_id"] == "t-1"
        assert d["status"] == "passed"


class TestBenchmarkResult:
    def test_to_dict(self):
        b = BenchmarkResult(
            name="bench-1",
            files_processed=100,
            total_size_bytes=1024,
            duration_sec=2.0,
            throughput_files_per_sec=50.0,
        )
        d = b.to_dict()
        assert d["files_processed"] == 100
        assert d["throughput_files_per_sec"] == 50.0


class TestFaultInjector:
    def test_enable_disable(self, fault_injector):
        fault_injector.enable_fault(FaultType.DISK_FULL)
        assert fault_injector.should_inject(FaultType.DISK_FULL) is True
        
        fault_injector.disable_fault(FaultType.DISK_FULL)
        assert fault_injector.should_inject(FaultType.DISK_FULL) is False
    
    def test_disable_all(self, fault_injector):
        fault_injector.enable_fault(FaultType.DISK_FULL)
        fault_injector.enable_fault(FaultType.PERMISSION_DENIED)
        fault_injector.disable_all()
        assert fault_injector.should_inject(FaultType.DISK_FULL) is False
    
    def test_get_active_faults(self, fault_injector):
        fault_injector.enable_fault(FaultType.DISK_FULL)
        fault_injector.enable_fault(FaultType.FILE_LOCKED)
        active = fault_injector.get_active_faults()
        assert "disk_full" in active
        assert "file_locked" in active
    
    def test_probability_zero(self, fault_injector):
        fault_injector.enable_fault(FaultType.DISK_FULL, probability=0.0)
        results = [fault_injector.should_inject(FaultType.DISK_FULL) for _ in range(100)]
        assert all(r is False for r in results)


class TestDataGen:
    def test_create_file_tree(self, tmp_workspace):
        src = os.path.join(tmp_workspace, "tree")
        os.makedirs(src)
        files = TestDataGenerator.create_file_tree(src, num_files=20)
        assert len(files) == 20
        for f in files:
            assert os.path.exists(f)
    
    def test_create_large_folder(self, tmp_workspace):
        src = os.path.join(tmp_workspace, "large")
        os.makedirs(src)
        stats = TestDataGenerator.create_large_folder(src, file_count=50)
        assert stats["files_created"] == 50
        assert stats["total_size_bytes"] > 0


class TestE2ETestRunner:
    def test_pipeline_test(self, runner, populated_dir):
        result = runner.run_pipeline_test(populated_dir)
        assert result.status == TestStatus.PASSED
        assert result.metrics["files_analyzed"] > 0
    
    def test_pipeline_test_empty(self, runner, tmp_workspace):
        empty_dir = os.path.join(tmp_workspace, "empty")
        os.makedirs(empty_dir)
        result = runner.run_pipeline_test(empty_dir)
        assert result.status == TestStatus.SKIPPED
    
    def test_copy_with_faults(self, runner, populated_dir, tmp_workspace):
        dest = os.path.join(tmp_workspace, "dest")
        os.makedirs(dest)
        result = runner.run_copy_with_fault_test(populated_dir, dest)
        assert result.status == TestStatus.PASSED
    
    def test_copy_with_disk_full(self, runner, populated_dir, tmp_workspace):
        runner.fault_injector.enable_fault(FaultType.DISK_FULL, probability=1.0)
        dest = os.path.join(tmp_workspace, "dest")
        os.makedirs(dest)
        result = runner.run_copy_with_fault_test(populated_dir, dest)
        assert result.metrics["files_failed"] > 0
        runner.fault_injector.disable_all()
    
    def test_performance_benchmark(self, runner, tmp_workspace):
        bench_dir = os.path.join(tmp_workspace, "bench")
        os.makedirs(bench_dir)
        result = runner.run_performance_benchmark(bench_dir, file_count=100)
        assert result.files_processed > 0
        assert result.duration_sec > 0
        assert result.throughput_files_per_sec > 0


class TestIntegrationTestSuite:
    def test_full_suite(self, tmp_workspace):
        suite = create_integration_suite()
        TestDataGenerator.create_file_tree(tmp_workspace, num_files=20)
        report = suite.run_full_suite(tmp_workspace)
        
        assert "results" in report
        assert "benchmark" in report
        assert "summary" in report
        assert report["summary"]["total_tests"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
