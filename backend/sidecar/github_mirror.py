#!/usr/bin/env python3
"""
FileCustra GitHub Mirror Hygiene
Directory parity checks, artifact exclusion, and release synchronization.
"""

import fnmatch
import hashlib
import json
import os
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


EXCLUDED_PATTERNS = [
    "*.pyc",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    ".venv",
    "venv",
    ".env",
    ".env.local",
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
    "*.egg-info",
    ".mypy_cache",
    ".tox",
    "dist",
    "build",
    ".idea",
    ".vscode",
    "*.swp",
    "*.swo",
    "*~",
    ".git",
    "*.log",
    "*.tmp",
    "*.bak",
    "*.backup.*",
    "*.journal",
    "journals",
    "backups",
    "preferences",
    "security_config",
    "integrity_manifests",
    ".cache",
]

EXCLUDED_DIRS = [
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    ".git",
    ".idea",
    ".vscode",
    "dist",
    "build",
    ".cache",
    "journals",
    "backups",
    "preferences",
    "security_config",
    "integrity_manifests",
]


@dataclass
class MirrorResult:
    """Result of a mirror operation."""
    source_path: str
    dest_path: str
    files_copied: int = 0
    files_skipped: int = 0
    files_failed: int = 0
    excluded_count: int = 0
    duration_sec: float = 0.0
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "source_path": self.source_path,
            "dest_path": self.dest_path,
            "files_copied": self.files_copied,
            "files_skipped": self.files_skipped,
            "files_failed": self.files_failed,
            "excluded_count": self.excluded_count,
            "duration_sec": self.duration_sec,
            "errors": self.errors,
        }


@dataclass
class ParityCheck:
    """Result of a directory parity check."""
    source_count: int
    dest_count: int
    matched: int
    missing_in_dest: List[str] = field(default_factory=list)
    extra_in_dest: List[str] = field(default_factory=list)
    mismatched: List[str] = field(default_factory=list)
    
    @property
    def is_parity(self) -> bool:
        return (
            self.source_count == self.dest_count
            and self.matched == self.source_count
            and len(self.missing_in_dest) == 0
            and len(self.extra_in_dest) == 0
        )
    
    def to_dict(self) -> dict:
        return {
            "source_count": self.source_count,
            "dest_count": self.dest_count,
            "matched": self.matched,
            "missing_in_dest": self.missing_in_dest,
            "extra_in_dest": self.extra_in_dest,
            "mismatched": self.mismatched,
            "is_parity": self.is_parity,
        }


@dataclass
class ArtifactEntry:
    """An artifact entry in the release manifest."""
    name: str
    version: str
    files: List[str] = field(default_factory=list)
    checksum: str = ""
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "files": self.files,
            "checksum": self.checksum,
            "created_at": self.created_at,
        }


class ExclusionFilter:
    """Filters files based on exclusion patterns."""
    
    def __init__(self, patterns: Optional[List[str]] = None, dirs: Optional[List[str]] = None):
        self._patterns = patterns or EXCLUDED_PATTERNS
        self._dirs = dirs or EXCLUDED_DIRS
    
    def should_exclude(self, path: str) -> bool:
        """Check if a path should be excluded."""
        name = os.path.basename(path)
        
        for pattern in self._patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
            if fnmatch.fnmatch(path, pattern):
                return True
        
        parts = Path(path).parts
        for part in parts:
            if part in self._dirs:
                return True
        
        return False
    
    def should_exclude_dir(self, dir_name: str) -> bool:
        """Check if a directory should be excluded."""
        return dir_name in self._dirs


class MirrorSync:
    """Synchronizes source to destination with exclusion filtering."""
    
    def __init__(self, exclusion_filter: Optional[ExclusionFilter] = None):
        self._filter = exclusion_filter or ExclusionFilter()
    
    def sync(
        self,
        source_dir: str,
        dest_dir: str,
        delete_extras: bool = False,
    ) -> MirrorResult:
        """Sync source directory to destination."""
        start = time.time()
        result = MirrorResult(source_path=source_dir, dest_path=dest_dir)
        
        source_files = self._scan_directory(source_dir)
        dest_files = self._scan_directory(dest_dir) if os.path.exists(dest_dir) else set()
        
        for rel_path in source_files:
            if self._filter.should_exclude(rel_path):
                result.excluded_count += 1
                continue
            
            src_path = os.path.join(source_dir, rel_path)
            dst_path = os.path.join(dest_dir, rel_path)
            
            try:
                if rel_path in dest_files:
                    src_hash = self._compute_hash(src_path)
                    dst_hash = self._compute_hash(dst_path)
                    if src_hash == dst_hash:
                        result.files_skipped += 1
                        continue
                
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                shutil.copy2(src_path, dst_path)
                result.files_copied += 1
            except Exception as e:
                result.files_failed += 1
                result.errors.append(f"Failed to copy {rel_path}: {e}")
        
        if delete_extras:
            for rel_path in dest_files:
                if rel_path not in source_files:
                    if not self._filter.should_exclude(rel_path):
                        try:
                            os.remove(os.path.join(dest_dir, rel_path))
                        except Exception:
                            pass
        
        result.duration_sec = round(time.time() - start, 3)
        return result
    
    def _scan_directory(self, directory: str) -> set:
        """Scan directory and return set of relative paths."""
        files = set()
        for root, dirs, filenames in os.walk(directory):
            dirs[:] = [d for d in dirs if not self._filter.should_exclude_dir(d)]
            for fname in filenames:
                full_path = os.path.join(root, fname)
                rel_path = os.path.relpath(full_path, directory)
                if not self._filter.should_exclude(rel_path):
                    files.add(rel_path)
        return files
    
    def _compute_hash(self, file_path: str) -> str:
        """Compute SHA-256 hash of a file."""
        try:
            sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception:
            return ""


class ParityChecker:
    """Checks directory parity between source and destination."""
    
    def __init__(self, exclusion_filter: Optional[ExclusionFilter] = None):
        self._filter = exclusion_filter or ExclusionFilter()
    
    def check_parity(
        self,
        source_dir: str,
        dest_dir: str,
    ) -> ParityCheck:
        """Check parity between two directories."""
        source_files = self._get_relative_files(source_dir)
        dest_files = self._get_relative_files(dest_dir) if os.path.exists(dest_dir) else set()
        
        missing_in_dest = sorted(source_files - dest_files)
        extra_in_dest = sorted(dest_files - source_files)
        matched_files = source_files & dest_files
        
        mismatched = []
        for rel_path in matched_files:
            src = os.path.join(source_dir, rel_path)
            dst = os.path.join(dest_dir, rel_path)
            if self._compute_hash(src) != self._compute_hash(dst):
                mismatched.append(rel_path)
        
        return ParityCheck(
            source_count=len(source_files),
            dest_count=len(dest_files),
            matched=len(matched_files) - len(mismatched),
            missing_in_dest=missing_in_dest,
            extra_in_dest=extra_in_dest,
            mismatched=mismatched,
        )
    
    def _get_relative_files(self, directory: str) -> set:
        files = set()
        for root, dirs, filenames in os.walk(directory):
            dirs[:] = [d for d in dirs if not self._filter.should_exclude_dir(d)]
            for fname in filenames:
                full_path = os.path.join(root, fname)
                rel_path = os.path.relpath(full_path, directory)
                if not self._filter.should_exclude(rel_path):
                    files.add(rel_path)
        return files
    
    def _compute_hash(self, file_path: str) -> str:
        try:
            sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception:
            return ""


class ReleaseManifest:
    """Manages release artifacts."""
    
    def __init__(self, manifest_dir: Optional[str] = None):
        self._dir = Path(manifest_dir) if manifest_dir else Path("release_manifests")
        self._dir.mkdir(parents=True, exist_ok=True)
        self._artifacts: Dict[str, ArtifactEntry] = {}
        self._load_manifests()
    
    def _load_manifests(self) -> None:
        manifest_file = self._dir / "manifest.json"
        if manifest_file.exists():
            try:
                with open(manifest_file, "r") as f:
                    data = json.load(f)
                for key, entry_data in data.items():
                    self._artifacts[key] = ArtifactEntry(
                        name=entry_data["name"],
                        version=entry_data["version"],
                        files=entry_data.get("files", []),
                        checksum=entry_data.get("checksum", ""),
                        created_at=entry_data.get("created_at", time.time()),
                    )
            except Exception:
                pass
    
    def _save_manifests(self) -> None:
        manifest_file = self._dir / "manifest.json"
        data = {k: v.to_dict() for k, v in self._artifacts.items()}
        with open(manifest_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def register_artifact(
        self,
        name: str,
        version: str,
        files: List[str],
    ) -> None:
        """Register a release artifact."""
        checksum = self._compute_files_checksum(files)
        self._artifacts[f"{name}:{version}"] = ArtifactEntry(
            name=name,
            version=version,
            files=files,
            checksum=checksum,
        )
        self._save_manifests()
    
    def get_artifact(self, name: str, version: str) -> Optional[ArtifactEntry]:
        return self._artifacts.get(f"{name}:{version}")
    
    def list_artifacts(self) -> List[ArtifactEntry]:
        return list(self._artifacts.values())
    
    def verify_integrity(self, name: str, version: str) -> bool:
        """Verify artifact file integrity."""
        entry = self.get_artifact(name, version)
        if not entry:
            return False
        
        for file_path in entry.files:
            if not os.path.exists(file_path):
                return False
        
        current_checksum = self._compute_files_checksum(entry.files)
        return current_checksum == entry.checksum
    
    def _compute_files_checksum(self, files: List[str]) -> str:
        sha256 = hashlib.sha256()
        for f in sorted(files):
            try:
                with open(f, "rb") as fh:
                    for chunk in iter(lambda: fh.read(8192), b""):
                        sha256.update(chunk)
            except Exception:
                pass
        return sha256.hexdigest()


def create_mirror_sync() -> MirrorSync:
    """Factory function to create a mirror sync."""
    return MirrorSync()


def create_parity_checker() -> ParityChecker:
    """Factory function to create a parity checker."""
    return ParityChecker()


if __name__ == "__main__":
    print("GitHub Mirror Hygiene initialized")
    print(f"Excluded patterns: {len(EXCLUDED_PATTERNS)}")
    print(f"Excluded directories: {len(EXCLUDED_DIRS)}")
