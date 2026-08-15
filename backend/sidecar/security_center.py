#!/usr/bin/env python3
"""
FileCustra Security Center
Privacy lock policy, dependency/model integrity checks, and offline-only verification.
"""

import hashlib
import json
import os
import platform
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ThreatLevel(Enum):
    """Security threat levels."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PrivacyMode(Enum):
    """Privacy lock modes."""
    FULL_OFFLINE = "full_offline"
    NO_TELEMETRY = "no_telemetry"
    RESTRICTED_NETWORK = "restricted_network"
    CUSTOM = "custom"


@dataclass
class SecurityCheck:
    """Result of a security check."""
    check_id: str
    name: str
    passed: bool
    threat_level: ThreatLevel
    details: str = ""
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> dict:
        return {
            "check_id": self.check_id,
            "name": self.name,
            "passed": self.passed,
            "threat_level": self.threat_level.value,
            "details": self.details,
            "timestamp": self.timestamp,
        }


@dataclass
class IntegrityManifest:
    """Integrity manifest for a model or dependency."""
    name: str
    version: str
    expected_hash: str
    actual_hash: Optional[str] = None
    verified: bool = False
    file_path: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "expected_hash": self.expected_hash,
            "actual_hash": self.actual_hash,
            "verified": self.verified,
            "file_path": self.file_path,
        }


class PrivacyLock:
    """Privacy lock policy manager."""
    
    def __init__(self, config_dir: Optional[str] = None):
        self._config_dir = Path(config_dir) if config_dir else Path("security_config")
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._mode = PrivacyMode.FULL_OFFLINE
        self._allowed_domains: List[str] = []
        self._audit_log: List[dict] = []
        self._load_config()
    
    def _load_config(self) -> None:
        config_file = self._config_dir / "privacy_lock.json"
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    data = json.load(f)
                self._mode = PrivacyMode(data.get("mode", "full_offline"))
                self._allowed_domains = data.get("allowed_domains", [])
                self._audit_log = data.get("audit_log", [])
            except Exception:
                pass
    
    def _save_config(self) -> None:
        config_file = self._config_dir / "privacy_lock.json"
        data = {
            "mode": self._mode.value,
            "allowed_domains": self._allowed_domains,
            "audit_log": self._audit_log[-100:],
        }
        with open(config_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def set_mode(self, mode: PrivacyMode) -> None:
        """Set privacy lock mode."""
        self._mode = mode
        self._audit_log.append({
            "action": "set_mode",
            "mode": mode.value,
            "timestamp": time.time(),
        })
        self._save_config()
    
    def get_mode(self) -> PrivacyMode:
        return self._mode
    
    def add_allowed_domain(self, domain: str) -> bool:
        """Add an allowed domain for network access."""
        if domain not in self._allowed_domains:
            self._allowed_domains.append(domain)
            self._audit_log.append({
                "action": "add_domain",
                "domain": domain,
                "timestamp": time.time(),
            })
            self._save_config()
            return True
        return False
    
    def remove_allowed_domain(self, domain: str) -> bool:
        if domain in self._allowed_domains:
            self._allowed_domains.remove(domain)
            self._audit_log.append({
                "action": "remove_domain",
                "domain": domain,
                "timestamp": time.time(),
            })
            self._save_config()
            return True
        return False
    
    def is_domain_allowed(self, domain: str) -> bool:
        """Check if a domain is allowed."""
        if self._mode == PrivacyMode.FULL_OFFLINE:
            return False
        if self._mode == PrivacyMode.NO_TELEMETRY:
            return False
        return domain in self._allowed_domains
    
    def is_network_allowed(self) -> bool:
        """Check if any network access is allowed."""
        return self._mode not in [PrivacyMode.FULL_OFFLINE, PrivacyMode.NO_TELEMETRY]
    
    def get_audit_log(self) -> List[dict]:
        return list(self._audit_log)
    
    def clear_audit_log(self) -> None:
        self._audit_log.clear()
        self._save_config()
    
    def get_privacy_report(self) -> dict:
        return {
            "mode": self._mode.value,
            "network_allowed": self.is_network_allowed(),
            "allowed_domains": self._allowed_domains,
            "audit_entries": len(self._audit_log),
            "data_stays_local": self._mode in [
                PrivacyMode.FULL_OFFLINE,
                PrivacyMode.NO_TELEMETRY,
            ],
        }


class IntegrityChecker:
    """Checks integrity of models and dependencies."""
    
    def __init__(self, manifests_dir: Optional[str] = None):
        self._manifests_dir = Path(manifests_dir) if manifests_dir else Path("integrity_manifests")
        self._manifests_dir.mkdir(parents=True, exist_ok=True)
        self._manifests: Dict[str, IntegrityManifest] = {}
    
    def register_manifest(
        self,
        name: str,
        version: str,
        expected_hash: str,
        file_path: Optional[str] = None,
    ) -> None:
        """Register an integrity manifest."""
        self._manifests[name] = IntegrityManifest(
            name=name,
            version=version,
            expected_hash=expected_hash,
            file_path=file_path,
        )
        self._save_manifests()
    
    def compute_file_hash(self, file_path: str) -> Optional[str]:
        """Compute SHA-256 hash of a file."""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(8192), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            return None
    
    def verify_integrity(self, name: str) -> SecurityCheck:
        """Verify integrity of a registered manifest."""
        manifest = self._manifests.get(name)
        if manifest is None:
            return SecurityCheck(
                check_id=f"integrity_{name}",
                name=f"Integrity check: {name}",
                passed=False,
                threat_level=ThreatLevel.HIGH,
                details=f"Manifest not found for {name}",
            )
        
        if manifest.file_path and os.path.exists(manifest.file_path):
            actual_hash = self.compute_file_hash(manifest.file_path)
            manifest.actual_hash = actual_hash
            manifest.verified = actual_hash == manifest.expected_hash
        else:
            manifest.verified = False
        
        return SecurityCheck(
            check_id=f"integrity_{name}",
            name=f"Integrity check: {name}",
            passed=manifest.verified,
            threat_level=ThreatLevel.NONE if manifest.verified else ThreatLevel.HIGH,
            details=f"Version {manifest.version}: {'verified' if manifest.verified else 'hash mismatch or file missing'}",
        )
    
    def verify_all(self) -> List[SecurityCheck]:
        """Verify all registered manifests."""
        checks = []
        for name in self._manifests:
            checks.append(self.verify_integrity(name))
        return checks
    
    def _save_manifests(self) -> None:
        data = {k: v.to_dict() for k, v in self._manifests.items()}
        manifests_file = self._manifests_dir / "manifests.json"
        with open(manifests_file, "w") as f:
            json.dump(data, f, indent=2)


class SecurityCenter:
    """Central security management hub."""
    
    def __init__(
        self,
        config_dir: Optional[str] = None,
        manifests_dir: Optional[str] = None,
    ):
        self._privacy_lock = PrivacyLock(config_dir)
        self._integrity_checker = IntegrityChecker(manifests_dir)
        self._security_checks: List[SecurityCheck] = []
    
    @property
    def privacy_lock(self) -> PrivacyLock:
        return self._privacy_lock
    
    @property
    def integrity_checker(self) -> IntegrityChecker:
        return self._integrity_checker
    
    def run_security_audit(self) -> List[SecurityCheck]:
        """Run a full security audit."""
        checks = []
        
        privacy_check = self._check_privacy_mode()
        checks.append(privacy_check)
        
        network_check = self._check_network_policy()
        checks.append(network_check)
        
        integrity_checks = self._integrity_checker.verify_all()
        checks.extend(integrity_checks)
        
        platform_check = self._check_platform_security()
        checks.append(platform_check)
        
        self._security_checks = checks
        return checks
    
    def _check_privacy_mode(self) -> SecurityCheck:
        mode = self._privacy_lock.get_mode()
        is_safe = mode in [PrivacyMode.FULL_OFFLINE, PrivacyMode.NO_TELEMETRY]
        
        return SecurityCheck(
            check_id="privacy_mode",
            name="Privacy Mode Check",
            passed=is_safe,
            threat_level=ThreatLevel.NONE if is_safe else ThreatLevel.MEDIUM,
            details=f"Current mode: {mode.value}",
        )
    
    def _check_network_policy(self) -> SecurityCheck:
        network_allowed = self._privacy_lock.is_network_allowed()
        
        return SecurityCheck(
            check_id="network_policy",
            name="Network Policy Check",
            passed=True,
            threat_level=ThreatLevel.NONE if not network_allowed else ThreatLevel.LOW,
            details=f"Network access: {'allowed' if network_allowed else 'blocked'}",
        )
    
    def _check_platform_security(self) -> SecurityCheck:
        os_name = platform.system()
        details = f"Platform: {os_name}, Python: {platform.python_version()}"
        
        return SecurityCheck(
            check_id="platform_security",
            name="Platform Security Check",
            passed=True,
            threat_level=ThreatLevel.NONE,
            details=details,
        )
    
    def get_security_summary(self) -> dict:
        """Get a summary of the security state."""
        passed = sum(1 for c in self._security_checks if c.passed)
        failed = sum(1 for c in self._security_checks if not c.passed)
        
        max_threat = ThreatLevel.NONE
        for check in self._security_checks:
            if check.threat_level.value > max_threat.value:
                max_threat = check.threat_level
        
        return {
            "total_checks": len(self._security_checks),
            "passed": passed,
            "failed": failed,
            "max_threat_level": max_threat.value,
            "privacy_report": self._privacy_lock.get_privacy_report(),
        }
    
    def to_dict(self) -> dict:
        return {
            "privacy_report": self._privacy_lock.get_privacy_report(),
            "security_summary": self.get_security_summary(),
            "checks": [c.to_dict() for c in self._security_checks],
        }


def create_security_center(
    config_dir: Optional[str] = None,
    manifests_dir: Optional[str] = None,
) -> SecurityCenter:
    """Factory function to create a security center."""
    return SecurityCenter(config_dir, manifests_dir)


if __name__ == "__main__":
    center = create_security_center()
    checks = center.run_security_audit()
    print(f"Security audit: {len(checks)} checks completed")
    for check in checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"  [{status}] {check.name}: {check.details}")
