#!/usr/bin/env python3
"""Tests for write-ahead operation journal and rollback engine."""

import os
import shutil
import tempfile
import time
from pathlib import Path

import pytest

from operation_journal import (
    BackupManager,
    JournalEntry,
    JournalEntryStatus,
    OperationJournal,
    RollbackEngine,
    RollbackResult,
    RollbackStatus,
    create_operation_journal,
    create_rollback_engine,
)


@pytest.fixture
def tmp_workspace():
    """Create a temporary workspace."""
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def journal(tmp_workspace):
    """Create a journal in a temp directory."""
    journal_dir = os.path.join(tmp_workspace, "journals")
    return create_operation_journal(journal_dir)


@pytest.fixture
def backup_mgr(tmp_workspace):
    """Create a backup manager."""
    backup_dir = os.path.join(tmp_workspace, "backups")
    return BackupManager(backup_dir)


@pytest.fixture
def engine(journal, backup_mgr, tmp_workspace):
    """Create a rollback engine with a temp backup dir."""
    backup_dir = os.path.join(tmp_workspace, "backups")
    return create_rollback_engine(journal, backup_dir)


class TestJournalEntryStatus:
    def test_status_values(self):
        assert JournalEntryStatus.PENDING.value == "pending"
        assert JournalEntryStatus.IN_PROGRESS.value == "in_progress"
        assert JournalEntryStatus.COMPLETED.value == "completed"
        assert JournalEntryStatus.FAILED.value == "failed"
        assert JournalEntryStatus.ROLLED_BACK.value == "rolled_back"


class TestOperationJournal:
    def test_record_operation(self, journal):
        entry = journal.record_operation(
            operation_id="op-1",
            operation_type="move",
            source_path="/tmp/a.txt",
            target_path="/tmp/b.txt",
        )
        assert entry.operation_id == "op-1"
        assert entry.operation_type == "move"
        assert entry.status == JournalEntryStatus.PENDING

    def test_entry_id_unique(self, journal):
        e1 = journal.record_operation("op-1", "move", "/tmp/a")
        e2 = journal.record_operation("op-2", "move", "/tmp/b")
        assert e1.entry_id != e2.entry_id

    def test_update_status(self, journal):
        entry = journal.record_operation("op-1", "copy", "/tmp/a")
        journal.update_entry_status(
            entry.entry_id,
            JournalEntryStatus.COMPLETED,
            backup_path="/tmp/a.bak",
        )
        updated = journal.get_entry(entry.entry_id)
        assert updated.status == JournalEntryStatus.COMPLETED
        assert updated.backup_path == "/tmp/a.bak"
        assert updated.completed_at is not None

    def test_get_entries_by_status(self, journal):
        journal.record_operation("op-1", "move", "/tmp/a")
        journal.record_operation("op-2", "copy", "/tmp/b")
        entry = journal.record_operation("op-3", "delete", "/tmp/c")
        journal.update_entry_status(entry.entry_id, JournalEntryStatus.FAILED)

        pending = journal.get_entries_by_status(JournalEntryStatus.PENDING)
        failed = journal.get_entries_by_status(JournalEntryStatus.FAILED)
        assert len(pending) == 2
        assert len(failed) == 1

    def test_record_file_hash(self, journal, tmp_workspace):
        test_file = os.path.join(tmp_workspace, "test.txt")
        with open(test_file, "w") as f:
            f.write("hello world")

        entry = journal.record_operation("op-1", "move", test_file)
        assert entry.original_hash is not None
        assert entry.original_size == 11

    def test_record_nonexistent_file(self, journal):
        entry = journal.record_operation("op-1", "move", "/nonexistent/file")
        assert entry.original_hash is None
        assert entry.original_size == 0

    def test_entry_to_dict(self, journal):
        entry = journal.record_operation(
            "op-1", "move", "/tmp/a", target_path="/tmp/b"
        )
        d = entry.to_dict()
        assert d["operation_id"] == "op-1"
        assert d["status"] == "pending"
        assert d["target_path"] == "/tmp/b"

    def test_save_and_load_journal(self, journal, tmp_workspace):
        journal.record_operation("op-1", "move", "/tmp/a")
        journal.record_operation("op-2", "copy", "/tmp/b")
        path = journal.save_journal("session-1")
        assert Path(path).exists()

        journal_dir = os.path.join(tmp_workspace, "journals")
        journal2 = create_operation_journal(journal_dir)
        loaded = journal2.load_journal("session-1")
        assert loaded is True
        assert len(journal2.get_all_entries()) == 2

    def test_load_nonexistent_journal(self, journal):
        loaded = journal.load_journal("nonexistent-session")
        assert loaded is False

    def test_clear(self, journal):
        journal.record_operation("op-1", "move", "/tmp/a")
        assert len(journal.get_all_entries()) == 1
        journal.clear()
        assert len(journal.get_all_entries()) == 0


class TestRollbackStatus:
    def test_status_values(self):
        assert RollbackStatus.SUCCESS.value == "success"
        assert RollbackStatus.PARTIAL.value == "partial"
        assert RollbackStatus.FAILED.value == "failed"


class TestRollbackResult:
    def test_to_dict(self):
        result = RollbackResult(
            session_id="s1",
            status=RollbackStatus.SUCCESS,
            entries_rolled_back=3,
            entries_failed=0,
        )
        d = result.to_dict()
        assert d["session_id"] == "s1"
        assert d["status"] == "success"
        assert d["entries_rolled_back"] == 3


class TestRollbackEngine:
    def test_rollback_copy_operation(self, engine, journal, tmp_workspace):
        src = os.path.join(tmp_workspace, "original.txt")
        dst = os.path.join(tmp_workspace, "copy.txt")
        with open(src, "w") as f:
            f.write("original content")
        shutil.copy2(src, dst)

        entry = journal.record_operation(
            "op-1", "copy", src, target_path=dst
        )
        journal.update_entry_status(entry.entry_id, JournalEntryStatus.COMPLETED)

        result = engine.rollback_session("session-1")
        assert not Path(dst).exists()

    def test_rollback_delete_operation(self, engine, journal, tmp_workspace):
        test_file = os.path.join(tmp_workspace, "to_delete.txt")
        with open(test_file, "w") as f:
            f.write("will be deleted")

        backup_mgr = BackupManager(os.path.join(tmp_workspace, "backups"))
        backup_path = backup_mgr.create_backup(test_file)

        entry = journal.record_operation("op-1", "delete", test_file)
        entry.backup_path = backup_path
        journal.update_entry_status(
            entry.entry_id,
            JournalEntryStatus.COMPLETED,
            backup_path=backup_path,
        )

        result = engine.rollback_session("session-1")
        assert Path(test_file).exists()
        assert result.status == RollbackStatus.SUCCESS

    def test_can_rollback(self, engine, journal):
        assert engine.can_rollback() is False
        entry = journal.record_operation("op-1", "move", "/tmp/a")
        journal.update_entry_status(entry.entry_id, JournalEntryStatus.COMPLETED)
        assert engine.can_rollback() is True

    def test_rollback_result_saves_journal(self, engine, journal, tmp_workspace):
        entry = journal.record_operation("op-1", "move", "/tmp/a")
        journal.update_entry_status(entry.entry_id, JournalEntryStatus.COMPLETED)

        engine.rollback_session("session-2")

        journal_dir = os.path.join(tmp_workspace, "journals")
        journal2 = create_operation_journal(journal_dir)
        loaded = journal2.load_journal("session-2-rollback")
        assert loaded is True


class TestBackupManager:
    def test_create_backup(self, backup_mgr, tmp_workspace):
        test_file = os.path.join(tmp_workspace, "file.txt")
        with open(test_file, "w") as f:
            f.write("test")

        backup_path = backup_mgr.create_backup(test_file)
        assert backup_path is not None
        assert Path(backup_path).exists()

    def test_restore_backup(self, backup_mgr, tmp_workspace):
        test_file = os.path.join(tmp_workspace, "file.txt")
        with open(test_file, "w") as f:
            f.write("original")

        backup_path = backup_mgr.create_backup(test_file)

        with open(test_file, "w") as f:
            f.write("modified")

        success = backup_mgr.restore_backup(backup_path, test_file)
        assert success is True
        with open(test_file) as f:
            assert f.read() == "original"

    def test_cleanup_backup(self, backup_mgr, tmp_workspace):
        test_file = os.path.join(tmp_workspace, "file.txt")
        with open(test_file, "w") as f:
            f.write("test")

        backup_path = backup_mgr.create_backup(test_file)
        success = backup_mgr.cleanup_backup(backup_path)
        assert success is True
        assert not Path(backup_path).exists()

    def test_create_backup_nonexistent(self, backup_mgr):
        result = backup_mgr.create_backup("/nonexistent/file")
        assert result is None

    def test_restore_nonexistent_backup(self, backup_mgr):
        success = backup_mgr.restore_backup("/nonexistent/backup", "/tmp/target")
        assert success is False
