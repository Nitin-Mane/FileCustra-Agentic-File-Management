#!/usr/bin/env python3
"""
FileCustra Transactional Dry-Run Planner
Generates operation plans with collision checks, path validation,
and tree diff payloads without modifying the filesystem.
"""

import hashlib
import json
import os
import shutil
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class OperationType(Enum):
    """Types of file operations."""
    MOVE = "move"
    COPY = "copy"
    RENAME = "rename"
    DELETE = "delete"
    CREATE_DIR = "create_dir"
    SEND_TO_RECYCLE = "send_to_recycle"


class OperationStatus(Enum):
    """Status of an operation."""
    PENDING = "pending"
    VALIDATED = "validated"
    COLLISION = "collision"
    ERROR = "error"
    BLOCKED = "blocked"


class RiskLevel(Enum):
    """Risk levels for operations."""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class FileOperation:
    """A single file operation."""
    operation_id: str
    operation_type: OperationType
    source_path: str
    target_path: Optional[str] = None
    status: OperationStatus = OperationStatus.PENDING
    risk_level: RiskLevel = RiskLevel.SAFE
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type.value,
            "source_path": self.source_path,
            "target_path": self.target_path,
            "status": self.status.value,
            "risk_level": self.risk_level.value,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


@dataclass
class CollisionInfo:
    """Information about a path collision."""
    source_path: str
    target_path: str
    collision_type: str
    existing_item_type: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "source_path": self.source_path,
            "target_path": self.target_path,
            "collision_type": self.collision_type,
            "existing_item_type": self.existing_item_type,
        }


@dataclass
class TreeDiffNode:
    """A node in the tree diff."""
    path: str
    action: str
    children: List["TreeDiffNode"] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "action": self.action,
            "children": [child.to_dict() for child in self.children],
            "metadata": self.metadata,
        }


@dataclass
class OperationPlan:
    """A complete operation plan."""
    plan_id: str
    name: str
    description: str
    operations: List[FileOperation] = field(default_factory=list)
    collisions: List[CollisionInfo] = field(default_factory=list)
    tree_diff: Optional[TreeDiffNode] = None
    status: str = "draft"
    created_at: float = field(default_factory=time.time)
    total_size_bytes: int = 0
    estimated_duration_sec: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "name": self.name,
            "description": self.description,
            "operations": [op.to_dict() for op in self.operations],
            "collisions": [c.to_dict() for c in self.collisions],
            "tree_diff": self.tree_diff.to_dict() if self.tree_diff else None,
            "status": self.status,
            "created_at": self.created_at,
            "total_size_bytes": self.total_size_bytes,
            "estimated_duration_sec": self.estimated_duration_sec,
            "metadata": self.metadata,
        }
    
    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_operations": len(self.operations),
            "move_count": sum(1 for op in self.operations if op.operation_type == OperationType.MOVE),
            "copy_count": sum(1 for op in self.operations if op.operation_type == OperationType.COPY),
            "delete_count": sum(1 for op in self.operations if op.operation_type == OperationType.DELETE),
            "collision_count": len(self.collisions),
            "has_errors": any(op.status == OperationStatus.ERROR for op in self.operations),
            "total_size_gb": round(self.total_size_bytes / (1024 ** 3), 2),
        }


class CollisionDetector:
    """Detects path collisions and conflicts."""
    
    def __init__(self):
        self._existing_paths: Set[str] = set()
        self._target_paths: Set[str] = set()
    
    def scan_directory(self, root_path: str) -> None:
        """Scan a directory to build the existing paths index."""
        self._existing_paths.clear()
        root = Path(root_path)
        
        if not root.exists():
            return
        
        for path in root.rglob("*"):
            self._existing_paths.add(str(path).lower())
    
    def check_collision(
        self,
        source_path: str,
        target_path: str,
    ) -> Optional[CollisionInfo]:
        """Check if a move/copy operation would cause a collision."""
        source = Path(source_path)
        target = Path(target_path)
        
        if not source.exists():
            return CollisionInfo(
                source_path=source_path,
                target_path=target_path,
                collision_type="source_not_found",
            )
        
        if target.exists():
            if target.is_file() and source.is_file():
                return CollisionInfo(
                    source_path=source_path,
                    target_path=target_path,
                    collision_type="file_exists",
                    existing_item_type="file",
                )
            elif target.is_dir() and source.is_dir():
                return CollisionInfo(
                    source_path=source_path,
                    target_path=target_path,
                    collision_type="directory_exists",
                    existing_item_type="directory",
                )
            elif target.is_dir() and source.is_file():
                file_in_dir = target / source.name
                if file_in_dir.exists():
                    return CollisionInfo(
                        source_path=source_path,
                        target_path=str(file_in_dir),
                        collision_type="file_exists_in_directory",
                        existing_item_type="file",
                    )
        
        if target_path.lower() in self._target_paths:
            return CollisionInfo(
                source_path=source_path,
                target_path=target_path,
                collision_type="duplicate_target",
            )
        
        self._target_paths.add(target_path.lower())
        return None
    
    def check_cyclic_move(
        self,
        source_path: str,
        target_path: str,
    ) -> bool:
        """Check if a move would create a cyclic reference."""
        source = Path(source_path)
        target = Path(target_path)
        
        try:
            source_resolved = source.resolve()
            target_resolved = target.resolve()
            
            if str(target_resolved).startswith(str(source_resolved)):
                return True
            
            return False
        except Exception:
            return False
    
    def clear(self) -> None:
        self._existing_paths.clear()
        self._target_paths.clear()


class DryRunPlanner:
    """Generates and validates operation plans without filesystem modification."""
    
    def __init__(self):
        self._collision_detector = CollisionDetector()
        self._plan_counter = 0
    
    def create_plan(
        self,
        name: str,
        description: str = "",
    ) -> OperationPlan:
        """Create a new operation plan."""
        self._plan_counter += 1
        plan_id = f"plan-{int(time.time())}-{self._plan_counter}"
        
        return OperationPlan(
            plan_id=plan_id,
            name=name,
            description=description,
        )
    
    def add_move_operation(
        self,
        plan: OperationPlan,
        source_path: str,
        target_path: str,
    ) -> FileOperation:
        """Add a move operation to the plan."""
        operation_id = f"op-{len(plan.operations) + 1}-{int(time.time())}"
        
        source = Path(source_path)
        size_bytes = source.stat().st_size if source.exists() else 0
        
        operation = FileOperation(
            operation_id=operation_id,
            operation_type=OperationType.MOVE,
            source_path=source_path,
            target_path=target_path,
            metadata={"size_bytes": size_bytes},
        )
        
        plan.operations.append(operation)
        plan.total_size_bytes += size_bytes
        
        return operation
    
    def add_copy_operation(
        self,
        plan: OperationPlan,
        source_path: str,
        target_path: str,
    ) -> FileOperation:
        """Add a copy operation to the plan."""
        operation_id = f"op-{len(plan.operations) + 1}-{int(time.time())}"
        
        source = Path(source_path)
        size_bytes = source.stat().st_size if source.exists() else 0
        
        operation = FileOperation(
            operation_id=operation_id,
            operation_type=OperationType.COPY,
            source_path=source_path,
            target_path=target_path,
            metadata={"size_bytes": size_bytes},
        )
        
        plan.operations.append(operation)
        plan.total_size_bytes += size_bytes
        
        return operation
    
    def add_delete_operation(
        self,
        plan: OperationPlan,
        source_path: str,
    ) -> FileOperation:
        """Add a delete operation to the plan."""
        operation_id = f"op-{len(plan.operations) + 1}-{int(time.time())}"
        
        source = Path(source_path)
        size_bytes = source.stat().st_size if source.exists() else 0
        
        operation = FileOperation(
            operation_id=operation_id,
            operation_type=OperationType.DELETE,
            source_path=source_path,
            metadata={"size_bytes": size_bytes},
        )
        
        plan.operations.append(operation)
        
        return operation
    
    def add_create_dir_operation(
        self,
        plan: OperationPlan,
        dir_path: str,
    ) -> FileOperation:
        """Add a create directory operation to the plan."""
        operation_id = f"op-{len(plan.operations) + 1}-{int(time.time())}"
        
        operation = FileOperation(
            operation_id=operation_id,
            operation_type=OperationType.CREATE_DIR,
            source_path=dir_path,
        )
        
        plan.operations.append(operation)
        
        return operation
    
    def validate_plan(
        self,
        plan: OperationPlan,
        root_path: Optional[str] = None,
    ) -> OperationPlan:
        """Validate all operations in the plan."""
        self._collision_detector.clear()
        
        if root_path:
            self._collision_detector.scan_directory(root_path)
        
        plan.collisions.clear()
        
        for operation in plan.operations:
            if operation.operation_type in [OperationType.MOVE, OperationType.COPY]:
                if operation.target_path:
                    if self._collision_detector.check_cyclic_move(
                        operation.source_path, operation.target_path
                    ):
                        operation.status = OperationStatus.BLOCKED
                        operation.error_message = "Cyclic move detected"
                        operation.risk_level = RiskLevel.HIGH
                        continue
                    
                    collision = self._collision_detector.check_collision(
                        operation.source_path, operation.target_path
                    )
                    
                    if collision:
                        operation.status = OperationStatus.COLLISION
                        operation.error_message = f"Collision: {collision.collision_type}"
                        operation.risk_level = RiskLevel.MEDIUM
                        plan.collisions.append(collision)
                    else:
                        operation.status = OperationStatus.VALIDATED
                        operation.risk_level = RiskLevel.SAFE
            else:
                operation.status = OperationStatus.VALIDATED
                operation.risk_level = RiskLevel.SAFE
        
        plan.status = "validated" if not plan.collisions else "has_collisions"
        plan.estimated_duration_sec = len(plan.operations) * 0.1
        
        return plan
    
    def generate_tree_diff(
        self,
        plan: OperationPlan,
    ) -> TreeDiffNode:
        """Generate a tree diff visualization of the plan."""
        root = TreeDiffNode(path="root", action="root")
        
        for operation in plan.operations:
            if operation.operation_type == OperationType.MOVE:
                source_parts = Path(operation.source_path).parts
                target_parts = Path(operation.target_path).parts if operation.target_path else []
                
                source_node = TreeDiffNode(
                    path=str(Path(*source_parts[-2:])) if len(source_parts) >= 2 else str(source_parts[-1]),
                    action="remove",
                    metadata={"original_path": operation.source_path},
                )
                root.children.append(source_node)
                
                target_node = TreeDiffNode(
                    path=str(Path(*target_parts[-2:])) if len(target_parts) >= 2 else str(target_parts[-1]),
                    action="add",
                    metadata={"target_path": operation.target_path},
                )
                root.children.append(target_node)
            
            elif operation.operation_type == OperationType.COPY:
                target_parts = Path(operation.target_path).parts if operation.target_path else []
                target_node = TreeDiffNode(
                    path=str(Path(*target_parts[-2:])) if len(target_parts) >= 2 else str(target_parts[-1]),
                    action="copy",
                    metadata={"source_path": operation.source_path},
                )
                root.children.append(target_node)
            
            elif operation.operation_type == OperationType.DELETE:
                source_parts = Path(operation.source_path).parts
                source_node = TreeDiffNode(
                    path=str(Path(*source_parts[-2:])) if len(source_parts) >= 2 else str(source_parts[-1]),
                    action="delete",
                    metadata={"original_path": operation.source_path},
                )
                root.children.append(source_node)
            
            elif operation.operation_type == OperationType.CREATE_DIR:
                dir_parts = Path(operation.source_path).parts
                dir_node = TreeDiffNode(
                    path=str(Path(*dir_parts[-2:])) if len(dir_parts) >= 2 else str(dir_parts[-1]),
                    action="create_dir",
                )
                root.children.append(dir_node)
        
        plan.tree_diff = root
        return root
    
    def estimate_duration(self, plan: OperationPlan) -> float:
        """Estimate the duration of plan execution."""
        total_bytes = sum(
            op.metadata.get("size_bytes", 0) for op in plan.operations
        )
        
        move_count = sum(1 for op in plan.operations if op.operation_type == OperationType.MOVE)
        copy_count = sum(1 for op in plan.operations if op.operation_type == OperationType.COPY)
        delete_count = sum(1 for op in plan.operations if op.operation_type == OperationType.DELETE)
        
        base_time = (move_count * 0.2) + (copy_count * 0.5) + (delete_count * 0.1)
        size_time = total_bytes / (100 * 1024 * 1024)
        
        return base_time + size_time


def create_dry_run_planner() -> DryRunPlanner:
    """Factory function to create a dry-run planner."""
    return DryRunPlanner()


if __name__ == "__main__":
    import sys
    
    planner = create_dry_run_planner()
    plan = planner.create_plan("Test Organization", "Organize files by type")
    
    print(f"Created plan: {plan.plan_id}")
    print(f"Name: {plan.name}")
    print(f"Status: {plan.status}")
