#!/usr/bin/env python3
"""
FileCustra Write-Ahead Operation Journal & One-Click Rollback Engine
Records all filesystem operations before execution and provides atomic rollback capabilities.
"""

import hashlib
import json
import os
import shutil
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class JournalEntryStatus(Enum):
    """Status of a journal entry."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class RollbackStatus(Enum):
    """Status of a rollback operation."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass
class JournalEntry:
    """A single journal entry recording an operation."""
    entry_id: str
    operation_id: str
    operation_type: str
    source_path: str
    target_path: Optional[str] = None
    status: JournalEntryStatus = JournalEntryStatus.PENDING
    original_hash: Optional[str] = None
    original_size: int = 0
    backup_path: Optional[str] = None
    error_message: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "operation_id": self.operation_id,
            "operation_type": self.operation_type,
            "source_path": self.source_path,
            "target_path": self.target_path,
            "status": self.status.value,
            "original_hash": self.original_hash,
            "original_size": self.original_size,
            "backup_path": self.backup_path,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata,
        }


@dataclass
class RollbackResult:
    """Result of a rollback operation."""
    session_id: str
    status: RollbackStatus
    entries_rolled_back: int
    entries_failed: int
    errors: List[str] = field(default_factory=list)
    duration_sec: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "status": self.status.value,
            "entries_rolled_back": self.entries_rolled_back,
            "entries_failed": self.entries_failed,
            "errors": self.errors,
            "duration_sec": self.duration_sec,
        }


class OperationJournal:
    """Write-ahead journal for filesystem operations."""
    
    def __init__(self, journal_dir: Optional[str] = None):
        self._journal_dir = Path(journal_dir) if journal_dir else Path("journals")
        self._journal_dir.mkdir(parents=True, exist_ok=True)
        self._entries: Dict[str, JournalEntry] = {}
        self._session_counter = 0
    
    def _generate_entry_id(self) -> str:
        self._session_counter += 1
        return f"journal-{int(time.time())}-{self._session_counter}"
    
    def _compute_file_hash(self, file_path: str) -> Optional[str]:
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(8192), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            return None
    
    def record_operation(
        self,
        operation_id: str,
        operation_type: str,
        source_path: str,
        target_path: Optional[str] = None,
    ) -> JournalEntry:
        """Record an operation before execution."""
        entry_id = self._generate_entry_id()
        
        source = Path(source_path)
        original_hash = None
        original_size = 0
        
        if source.exists() and source.is_file():
            original_hash = self._compute_file_hash(source_path)
            original_size = source.stat().st_size
        
        entry = JournalEntry(
            entry_id=entry_id,
            operation_id=operation_id,
            operation_type=operation_type,
            source_path=source_path,
            target_path=target_path,
            original_hash=original_hash,
            original_size=original_size,
        )
        
        self._entries[entry_id] = entry
        return entry
    
    def update_entry_status(
        self,
        entry_id: str,
        status: JournalEntryStatus,
        backup_path: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Update the status of a journal entry."""
        entry = self._entries.get(entry_id)
        if entry:
            entry.status = status
            if backup_path:
                entry.backup_path = backup_path
            if error_message:
                entry.error_message = error_message
            if status in [JournalEntryStatus.COMPLETED, JournalEntryStatus.FAILED]:
                entry.completed_at = time.time()
    
    def get_entry(self, entry_id: str) -> Optional[JournalEntry]:
        return self._entries.get(entry_id)
    
    def get_entries_by_status(
        self,
        status: JournalEntryStatus,
    ) -> List[JournalEntry]:
        return [e for e in self._entries.values() if e.status == status]
    
    def get_all_entries(self) -> List[JournalEntry]:
        return list(self._entries.values())
    
    def save_journal(self, session_id: str) -> str:
        """Save journal entries to disk."""
        journal_path = self._journal_dir / f"{session_id}.json"
        
        data = {
            "session_id": session_id,
            "entries": [entry.to_dict() for entry in self._entries.values()],
        }
        
        with open(journal_path, "w") as f:
            json.dump(data, f, indent=2)
        
        return str(journal_path)
    
    def load_journal(self, session_id: str) -> bool:
        """Load journal entries from disk."""
        journal_path = self._journal_dir / f"{session_id}.json"
        
        if not journal_path.exists():
            return False
        
        try:
            with open(journal_path, "r") as f:
                data = json.load(f)
            
            self._entries.clear()
            for entry_data in data.get("entries", []):
                entry = JournalEntry(
                    entry_id=entry_data["entry_id"],
                    operation_id=entry_data["operation_id"],
                    operation_type=entry_data["operation_type"],
                    source_path=entry_data["source_path"],
                    target_path=entry_data.get("target_path"),
                    status=JournalEntryStatus(entry_data["status"]),
                    original_hash=entry_data.get("original_hash"),
                    original_size=entry_data.get("original_size", 0),
                    backup_path=entry_data.get("backup_path"),
                    error_message=entry_data.get("error_message"),
                    created_at=entry_data.get("created_at", time.time()),
                    completed_at=entry_data.get("completed_at"),
                    metadata=entry_data.get("metadata", {}),
                )
                self._entries[entry.entry_id] = entry
            
            return True
        except Exception:
            return False
    
    def clear(self) -> None:
        self._entries.clear()


class BackupManager:
    """Manages file backups for rollback."""
    
    def __init__(self, backup_dir: Optional[str] = None):
        self._backup_dir = Path(backup_dir) if backup_dir else Path("backups")
        self._backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, file_path: str) -> Optional[str]:
        """Create a backup of a file before modification."""
        source = Path(file_path)
        
        if not source.exists():
            return None
        
        backup_name = f"{source.name}.backup.{int(time.time())}"
        backup_path = self._backup_dir / backup_name
        
        try:
            shutil.copy2(str(source), str(backup_path))
            return str(backup_path)
        except Exception:
            return None
    
    def restore_backup(self, backup_path: str, target_path: str) -> bool:
        """Restore a file from backup."""
        backup = Path(backup_path)
        target = Path(target_path)
        
        if not backup.exists():
            return False
        
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(backup), str(target))
            return True
        except Exception:
            return False
    
    def cleanup_backup(self, backup_path: str) -> bool:
        """Remove a backup file."""
        try:
            Path(backup_path).unlink(missing_ok=True)
            return True
        except Exception:
            return False


class RollbackEngine:
    """One-click rollback engine."""
    
    def __init__(
        self,
        journal: OperationJournal,
        backup_manager: Optional[BackupManager] = None,
    ):
        self._journal = journal
        self._backup_manager = backup_manager or BackupManager()
    
    def rollback_entry(self, entry: JournalEntry) -> bool:
        """Rollback a single journal entry."""
        if entry.operation_type == "move":
            if entry.backup_path:
                return self._backup_manager.restore_backup(
                    entry.backup_path, entry.source_path
                )
            elif entry.target_path and Path(entry.target_path).exists():
                try:
                    shutil.move(entry.target_path, entry.source_path)
                    return True
                except Exception:
                    return False
        
        elif entry.operation_type == "copy":
            if Path(entry.target_path).exists():
                try:
                    Path(entry.target_path).unlink()
                    return True
                except Exception:
                    return False
        
        elif entry.operation_type == "delete":
            if entry.backup_path:
                return self._backup_manager.restore_backup(
                    entry.backup_path, entry.source_path
                )
        
        elif entry.operation_type == "create_dir":
            if Path(entry.source_path).exists():
                try:
                    shutil.rmtree(entry.source_path)
                    return True
                except Exception:
                    return False
        
        return False
    
    def rollback_session(
        self,
        session_id: str,
    ) -> RollbackResult:
        """Rollback all operations in a session."""
        start_time = time.time()
        
        entries = self._journal.get_all_entries()
        entries_to_rollback = [
            e for e in entries
            if e.status == JournalEntryStatus.COMPLETED
        ]
        
        entries_rolled_back = 0
        entries_failed = 0
        errors = []
        
        for entry in reversed(entries_to_rollback):
            try:
                success = self.rollback_entry(entry)
                if success:
                    self._journal.update_entry_status(
                        entry.entry_id, JournalEntryStatus.ROLLED_BACK
                    )
                    entries_rolled_back += 1
                else:
                    self._journal.update_entry_status(
                        entry.entry_id,
                        JournalEntryStatus.FAILED,
                        error_message="Rollback failed",
                    )
                    entries_failed += 1
                    errors.append(f"Failed to rollback {entry.entry_id}")
            except Exception as e:
                entries_failed += 1
                errors.append(f"Error rolling back {entry.entry_id}: {str(e)}")
        
        duration = time.time() - start_time
        
        status = RollbackStatus.SUCCESS
        if entries_failed > 0:
            status = RollbackStatus.PARTIAL if entries_rolled_back > 0 else RollbackStatus.FAILED
        
        result = RollbackResult(
            session_id=session_id,
            status=status,
            entries_rolled_back=entries_rolled_back,
            entries_failed=entries_failed,
            errors=errors,
            duration_sec=round(duration, 3),
        )
        
        self._journal.save_journal(f"{session_id}-rollback")
        
        return result
    
    def can_rollback(self) -> bool:
        """Check if there are entries that can be rolled back."""
        entries = self._journal.get_entries_by_status(JournalEntryStatus.COMPLETED)
        return len(entries) > 0


def create_operation_journal(journal_dir: Optional[str] = None) -> OperationJournal:
    """Factory function to create an operation journal."""
    return OperationJournal(journal_dir)


def create_rollback_engine(
    journal: OperationJournal,
    backup_dir: Optional[str] = None,
) -> RollbackEngine:
    """Factory function to create a rollback engine."""
    backup_manager = BackupManager(backup_dir)
    return RollbackEngine(journal, backup_manager)


if __name__ == "__main__":
    journal = create_operation_journal()
    print(f"Journal initialized at: {journal._journal_dir}")
