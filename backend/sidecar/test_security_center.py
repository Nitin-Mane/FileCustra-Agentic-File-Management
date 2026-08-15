#!/usr/bin/env python3
"""Tests for security center, privacy lock, and integrity checks."""

import json
import os
import shutil
import tempfile

import pytest

from security_center import (
    IntegrityChecker,
    IntegrityManifest,
    PrivacyLock,
    PrivacyMode,
    SecurityCenter,
    SecurityCheck,
    ThreatLevel,
    create_security_center,
)


@pytest.fixture
def tmp_workspace():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def privacy_lock(tmp_workspace):
    config_dir = os.path.join(tmp_workspace, "security_config")
    return PrivacyLock(config_dir)


@pytest.fixture
def integrity_checker(tmp_workspace):
    manifests_dir = os.path.join(tmp_workspace, "integrity")
    return IntegrityChecker(manifests_dir)


@pytest.fixture
def security_center(tmp_workspace):
    config_dir = os.path.join(tmp_workspace, "security_config")
    manifests_dir = os.path.join(tmp_workspace, "integrity")
    return create_security_center(config_dir, manifests_dir)


class TestThreatLevel:
    def test_threat_values(self):
        assert ThreatLevel.NONE.value == "none"
        assert ThreatLevel.LOW.value == "low"
        assert ThreatLevel.MEDIUM.value == "medium"
        assert ThreatLevel.HIGH.value == "high"
        assert ThreatLevel.CRITICAL.value == "critical"


class TestSecurityCheck:
    def test_to_dict(self):
        check = SecurityCheck(
            check_id="test",
            name="Test Check",
            passed=True,
            threat_level=ThreatLevel.NONE,
            details="All good",
        )
        d = check.to_dict()
        assert d["check_id"] == "test"
        assert d["passed"] is True
        assert d["threat_level"] == "none"


class TestIntegrityManifest:
    def test_to_dict(self):
        m = IntegrityManifest(
            name="test-model",
            version="1.0",
            expected_hash="abc123",
            verified=True,
        )
        d = m.to_dict()
        assert d["name"] == "test-model"
        assert d["verified"] is True


class TestPrivacyLock:
    def test_default_mode(self, privacy_lock):
        assert privacy_lock.get_mode() == PrivacyMode.FULL_OFFLINE
    
    def test_set_mode(self, privacy_lock):
        privacy_lock.set_mode(PrivacyMode.NO_TELEMETRY)
        assert privacy_lock.get_mode() == PrivacyMode.NO_TELEMETRY
    
    def test_is_network_allowed_offline(self, privacy_lock):
        assert privacy_lock.is_network_allowed() is False
    
    def test_is_network_allowed_restricted(self, privacy_lock):
        privacy_lock.set_mode(PrivacyMode.RESTRICTED_NETWORK)
        assert privacy_lock.is_network_allowed() is True
    
    def test_is_domain_allowed_offline(self, privacy_lock):
        assert privacy_lock.is_domain_allowed("example.com") is False
    
    def test_add_allowed_domain(self, privacy_lock):
        privacy_lock.set_mode(PrivacyMode.RESTRICTED_NETWORK)
        success = privacy_lock.add_allowed_domain("example.com")
        assert success is True
        assert privacy_lock.is_domain_allowed("example.com") is True
    
    def test_remove_allowed_domain(self, privacy_lock):
        privacy_lock.set_mode(PrivacyMode.RESTRICTED_NETWORK)
        privacy_lock.add_allowed_domain("example.com")
        success = privacy_lock.remove_allowed_domain("example.com")
        assert success is True
        assert privacy_lock.is_domain_allowed("example.com") is False
    
    def test_audit_log(self, privacy_lock):
        privacy_lock.set_mode(PrivacyMode.NO_TELEMETRY)
        log = privacy_lock.get_audit_log()
        assert len(log) > 0
        assert log[0]["action"] == "set_mode"
    
    def test_clear_audit_log(self, privacy_lock):
        privacy_lock.set_mode(PrivacyMode.NO_TELEMETRY)
        privacy_lock.clear_audit_log()
        assert len(privacy_lock.get_audit_log()) == 0
    
    def test_privacy_report(self, privacy_lock):
        report = privacy_lock.get_privacy_report()
        assert "mode" in report
        assert "network_allowed" in report
        assert "data_stays_local" in report
        assert report["data_stays_local"] is True
    
    def test_persistence(self, tmp_workspace):
        config_dir = os.path.join(tmp_workspace, "security_config")
        lock1 = PrivacyLock(config_dir)
        lock1.set_mode(PrivacyMode.NO_TELEMETRY)
        lock1.add_allowed_domain("test.com")
        
        lock2 = PrivacyLock(config_dir)
        assert lock2.get_mode() == PrivacyMode.NO_TELEMETRY
        assert lock2.is_domain_allowed("test.com") is False


class TestIntegrityChecker:
    def test_register_manifest(self, integrity_checker):
        integrity_checker.register_manifest(
            name="test-model",
            version="1.0",
            expected_hash="abc123",
        )
        assert "test-model" in integrity_checker._manifests
    
    def test_compute_file_hash(self, integrity_checker, tmp_workspace):
        test_file = os.path.join(tmp_workspace, "test.bin")
        with open(test_file, "wb") as f:
            f.write(b"test content")
        
        hash_val = integrity_checker.compute_file_hash(test_file)
        assert hash_val is not None
        assert len(hash_val) == 64
    
    def test_verify_integrity_pass(self, integrity_checker, tmp_workspace):
        test_file = os.path.join(tmp_workspace, "model.bin")
        with open(test_file, "wb") as f:
            f.write(b"model data")
        
        import hashlib
        expected_hash = hashlib.sha256(b"model data").hexdigest()
        
        integrity_checker.register_manifest(
            name="model",
            version="1.0",
            expected_hash=expected_hash,
            file_path=test_file,
        )
        
        check = integrity_checker.verify_integrity("model")
        assert check.passed is True
        assert check.threat_level == ThreatLevel.NONE
    
    def test_verify_integrity_fail(self, integrity_checker, tmp_workspace):
        test_file = os.path.join(tmp_workspace, "model.bin")
        with open(test_file, "wb") as f:
            f.write(b"model data")
        
        integrity_checker.register_manifest(
            name="model",
            version="1.0",
            expected_hash="wrong_hash",
            file_path=test_file,
        )
        
        check = integrity_checker.verify_integrity("model")
        assert check.passed is False
        assert check.threat_level == ThreatLevel.HIGH
    
    def test_verify_missing_manifest(self, integrity_checker):
        check = integrity_checker.verify_integrity("nonexistent")
        assert check.passed is False
    
    def test_verify_all(self, integrity_checker, tmp_workspace):
        for name in ["model1", "model2"]:
            test_file = os.path.join(tmp_workspace, f"{name}.bin")
            with open(test_file, "wb") as f:
                f.write(b"content")
            
            integrity_checker.register_manifest(
                name=name,
                version="1.0",
                expected_hash="any_hash",
                file_path=test_file,
            )
        
        checks = integrity_checker.verify_all()
        assert len(checks) == 2


class TestSecurityCenter:
    def test_run_audit(self, security_center):
        checks = security_center.run_security_audit()
        assert len(checks) > 0
        assert all(isinstance(c, SecurityCheck) for c in checks)
    
    def test_security_summary(self, security_center):
        security_center.run_security_audit()
        summary = security_center.get_security_summary()
        assert "total_checks" in summary
        assert "passed" in summary
        assert "failed" in summary
        assert "privacy_report" in summary
    
    def test_to_dict(self, security_center):
        security_center.run_security_audit()
        d = security_center.to_dict()
        assert "privacy_report" in d
        assert "security_summary" in d
        assert "checks" in d
    
    def test_offline_mode_audit(self, security_center):
        security_center.privacy_lock.set_mode(PrivacyMode.FULL_OFFLINE)
        checks = security_center.run_security_audit()
        passed = sum(1 for c in checks if c.passed)
        assert passed > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
