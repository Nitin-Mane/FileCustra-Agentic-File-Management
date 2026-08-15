#!/usr/bin/env python3
"""Tests for GitHub mirror hygiene, parity checks, and release manifests."""

import os
import shutil
import tempfile

import pytest

from github_mirror import (
    ArtifactEntry,
    ExclusionFilter,
    MirrorResult,
    MirrorSync,
    ParityCheck,
    ParityChecker,
    ReleaseManifest,
    create_mirror_sync,
    create_parity_checker,
)


@pytest.fixture
def tmp_workspace():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def mirror_sync():
    return create_mirror_sync()


@pytest.fixture
def parity_checker():
    return create_parity_checker()


@pytest.fixture
def exclusion_filter():
    return ExclusionFilter()


class TestExclusionFilter:
    def test_exclude_pyc(self, exclusion_filter):
        assert exclusion_filter.should_exclude("file.pyc") is True
    
    def test_exclude_pycache(self, exclusion_filter):
        assert exclusion_filter.should_exclude("__pycache__") is True
    
    def test_exclude_node_modules(self, exclusion_filter):
        assert exclusion_filter.should_exclude("node_modules") is True
    
    def test_exclude_dot_git(self, exclusion_filter):
        assert exclusion_filter.should_exclude(".git") is True
    
    def test_not_exclude_python(self, exclusion_filter):
        assert exclusion_filter.should_exclude("main.py") is False
    
    def test_not_exclude_markdown(self, exclusion_filter):
        assert exclusion_filter.should_exclude("README.md") is False
    
    def test_should_exclude_dir(self, exclusion_filter):
        assert exclusion_filter.should_exclude_dir("__pycache__") is True
        assert exclusion_filter.should_exclude_dir("src") is False


class TestMirrorSync:
    def test_sync_copies_files(self, mirror_sync, tmp_workspace):
        src = os.path.join(tmp_workspace, "src")
        dst = os.path.join(tmp_workspace, "dst")
        os.makedirs(src)
        os.makedirs(dst)
        
        with open(os.path.join(src, "file.txt"), "w") as f:
            f.write("hello")
        
        result = mirror_sync.sync(src, dst)
        assert result.files_copied == 1
        assert os.path.exists(os.path.join(dst, "file.txt"))
    
    def test_sync_skips_identical(self, mirror_sync, tmp_workspace):
        src = os.path.join(tmp_workspace, "src")
        dst = os.path.join(tmp_workspace, "dst")
        os.makedirs(src)
        os.makedirs(dst)
        
        with open(os.path.join(src, "file.txt"), "w") as f:
            f.write("hello")
        shutil.copy2(os.path.join(src, "file.txt"), os.path.join(dst, "file.txt"))
        
        result = mirror_sync.sync(src, dst)
        assert result.files_copied == 0
        assert result.files_skipped == 1
    
    def test_sync_excludes_pyc(self, mirror_sync, tmp_workspace):
        src = os.path.join(tmp_workspace, "src")
        dst = os.path.join(tmp_workspace, "dst")
        os.makedirs(src)
        os.makedirs(dst)
        
        with open(os.path.join(src, "main.py"), "w") as f:
            f.write("print('hello')")
        
        pycache = os.path.join(src, "__pycache__")
        os.makedirs(pycache)
        with open(os.path.join(pycache, "main.pyc"), "wb") as f:
            f.write(b"\x00")
        
        result = mirror_sync.sync(src, dst)
        assert result.files_copied == 1
        assert not os.path.exists(os.path.join(dst, "__pycache__", "main.pyc"))
    
    def test_sync_empty_source(self, mirror_sync, tmp_workspace):
        src = os.path.join(tmp_workspace, "src")
        dst = os.path.join(tmp_workspace, "dst")
        os.makedirs(src)
        os.makedirs(dst)
        
        result = mirror_sync.sync(src, dst)
        assert result.files_copied == 0


class TestMirrorResult:
    def test_to_dict(self):
        result = MirrorResult(
            source_path="/src",
            dest_path="/dst",
            files_copied=5,
            files_skipped=2,
        )
        d = result.to_dict()
        assert d["files_copied"] == 5
        assert d["files_skipped"] == 2


class TestParityCheck:
    def test_is_parity(self):
        check = ParityCheck(source_count=10, dest_count=10, matched=10)
        assert check.is_parity is True
    
    def test_not_parity(self):
        check = ParityCheck(
            source_count=10,
            dest_count=10,
            matched=8,
            missing_in_dest=["file1.txt"],
            extra_in_dest=["extra.txt"],
        )
        assert check.is_parity is False
    
    def test_to_dict(self):
        check = ParityCheck(source_count=5, dest_count=5, matched=5)
        d = check.to_dict()
        assert d["source_count"] == 5
        assert d["is_parity"] is True


class TestParityChecker:
    def test_parity_match(self, parity_checker, tmp_workspace):
        src = os.path.join(tmp_workspace, "src")
        dst = os.path.join(tmp_workspace, "dst")
        os.makedirs(src)
        os.makedirs(dst)
        
        with open(os.path.join(src, "file.txt"), "w") as f:
            f.write("hello")
        shutil.copy2(os.path.join(src, "file.txt"), os.path.join(dst, "file.txt"))
        
        result = parity_checker.check_parity(src, dst)
        assert result.is_parity is True
    
    def test_parity_missing(self, parity_checker, tmp_workspace):
        src = os.path.join(tmp_workspace, "src")
        dst = os.path.join(tmp_workspace, "dst")
        os.makedirs(src)
        os.makedirs(dst)
        
        with open(os.path.join(src, "file.txt"), "w") as f:
            f.write("hello")
        
        result = parity_checker.check_parity(src, dst)
        assert result.is_parity is False
        assert len(result.missing_in_dest) == 1
    
    def test_parity_mismatched(self, parity_checker, tmp_workspace):
        src = os.path.join(tmp_workspace, "src")
        dst = os.path.join(tmp_workspace, "dst")
        os.makedirs(src)
        os.makedirs(dst)
        
        with open(os.path.join(src, "file.txt"), "w") as f:
            f.write("hello")
        with open(os.path.join(dst, "file.txt"), "w") as f:
            f.write("different")
        
        result = parity_checker.check_parity(src, dst)
        assert result.is_parity is False
        assert len(result.mismatched) == 1


class TestArtifactEntry:
    def test_to_dict(self):
        entry = ArtifactEntry(
            name="filecustra",
            version="1.0.0",
            files=["file1.txt", "file2.txt"],
            checksum="abc123",
        )
        d = entry.to_dict()
        assert d["name"] == "filecustra"
        assert d["version"] == "1.0.0"


class TestReleaseManifest:
    def test_register_artifact(self, tmp_workspace):
        manifest_dir = os.path.join(tmp_workspace, "manifests")
        manifest = ReleaseManifest(manifest_dir)
        
        test_file = os.path.join(tmp_workspace, "test.txt")
        with open(test_file, "w") as f:
            f.write("test content")
        
        manifest.register_artifact("app", "1.0", [test_file])
        artifact = manifest.get_artifact("app", "1.0")
        assert artifact is not None
        assert artifact.name == "app"
    
    def test_list_artifacts(self, tmp_workspace):
        manifest_dir = os.path.join(tmp_workspace, "manifests")
        manifest = ReleaseManifest(manifest_dir)
        
        test_file = os.path.join(tmp_workspace, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")
        
        manifest.register_artifact("app", "1.0", [test_file])
        artifacts = manifest.list_artifacts()
        assert len(artifacts) == 1
    
    def test_verify_integrity(self, tmp_workspace):
        manifest_dir = os.path.join(tmp_workspace, "manifests")
        manifest = ReleaseManifest(manifest_dir)
        
        test_file = os.path.join(tmp_workspace, "test.txt")
        with open(test_file, "w") as f:
            f.write("test content")
        
        manifest.register_artifact("app", "1.0", [test_file])
        assert manifest.verify_integrity("app", "1.0") is True
    
    def test_verify_nonexistent(self, tmp_workspace):
        manifest_dir = os.path.join(tmp_workspace, "manifests")
        manifest = ReleaseManifest(manifest_dir)
        assert manifest.verify_integrity("nonexistent", "1.0") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
