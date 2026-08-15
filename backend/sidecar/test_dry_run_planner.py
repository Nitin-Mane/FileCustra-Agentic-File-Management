#!/usr/bin/env python3
"""
Test suite for FileCustra Transactional Dry-Run Planner.
"""

import tempfile
import unittest
from pathlib import Path

from dry_run_planner import (
    DryRunPlanner,
    CollisionDetector,
    OperationPlan,
    FileOperation,
    CollisionInfo,
    TreeDiffNode,
    OperationType,
    OperationStatus,
    RiskLevel,
    create_dry_run_planner,
)


class TestOperationType(unittest.TestCase):
    """Test OperationType enum."""
    
    def test_operation_types(self):
        self.assertEqual(OperationType.MOVE.value, "move")
        self.assertEqual(OperationType.COPY.value, "copy")
        self.assertEqual(OperationType.DELETE.value, "delete")
        self.assertEqual(OperationType.CREATE_DIR.value, "create_dir")


class TestCollisionDetector(unittest.TestCase):
    """Test collision detection."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.detector = CollisionDetector()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_no_collision(self):
        source = Path(self.temp_dir) / "source.txt"
        source.write_text("content")
        target = Path(self.temp_dir) / "target.txt"
        
        collision = self.detector.check_collision(str(source), str(target))
        self.assertIsNone(collision)
    
    def test_file_exists_collision(self):
        source = Path(self.temp_dir) / "source.txt"
        source.write_text("content")
        target = Path(self.temp_dir) / "target.txt"
        target.write_text("existing")
        
        collision = self.detector.check_collision(str(source), str(target))
        self.assertIsNotNone(collision)
        self.assertEqual(collision.collision_type, "file_exists")
    
    def test_cyclic_move(self):
        source = Path(self.temp_dir) / "folder"
        source.mkdir()
        target = source / "subfolder"
        
        is_cyclic = self.detector.check_cyclic_move(str(source), str(target))
        self.assertTrue(is_cyclic)


class TestOperationPlan(unittest.TestCase):
    """Test OperationPlan dataclass."""
    
    def test_to_dict(self):
        plan = OperationPlan(
            plan_id="plan-1",
            name="Test Plan",
            description="Test description",
        )
        
        d = plan.to_dict()
        
        self.assertEqual(d["plan_id"], "plan-1")
        self.assertEqual(d["name"], "Test Plan")
        self.assertEqual(d["status"], "draft")
    
    def test_get_summary(self):
        plan = OperationPlan(
            plan_id="plan-1",
            name="Test Plan",
            description="Test",
        )
        
        plan.operations.append(FileOperation(
            operation_id="op-1",
            operation_type=OperationType.MOVE,
            source_path="/a.txt",
            target_path="/b.txt",
        ))
        plan.operations.append(FileOperation(
            operation_id="op-2",
            operation_type=OperationType.DELETE,
            source_path="/c.txt",
        ))
        
        summary = plan.get_summary()
        
        self.assertEqual(summary["total_operations"], 2)
        self.assertEqual(summary["move_count"], 1)
        self.assertEqual(summary["delete_count"], 1)


class TestDryRunPlanner(unittest.TestCase):
    """Test dry-run planner."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.planner = create_dry_run_planner()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_plan(self):
        plan = self.planner.create_plan("Test Plan", "Description")
        
        self.assertIsInstance(plan, OperationPlan)
        self.assertEqual(plan.name, "Test Plan")
        self.assertEqual(plan.status, "draft")
    
    def test_add_move_operation(self):
        plan = self.planner.create_plan("Test")
        
        source = Path(self.temp_dir) / "source.txt"
        source.write_text("content")
        target = Path(self.temp_dir) / "target.txt"
        
        operation = self.planner.add_move_operation(plan, str(source), str(target))
        
        self.assertEqual(operation.operation_type, OperationType.MOVE)
        self.assertEqual(len(plan.operations), 1)
        self.assertEqual(plan.total_size_bytes, 7)
    
    def test_add_copy_operation(self):
        plan = self.planner.create_plan("Test")
        
        source = Path(self.temp_dir) / "source.txt"
        source.write_text("content")
        target = Path(self.temp_dir) / "target.txt"
        
        operation = self.planner.add_copy_operation(plan, str(source), str(target))
        
        self.assertEqual(operation.operation_type, OperationType.COPY)
        self.assertEqual(len(plan.operations), 1)
    
    def test_add_delete_operation(self):
        plan = self.planner.create_plan("Test")
        
        source = Path(self.temp_dir) / "source.txt"
        source.write_text("content")
        
        operation = self.planner.add_delete_operation(plan, str(source))
        
        self.assertEqual(operation.operation_type, OperationType.DELETE)
        self.assertEqual(len(plan.operations), 1)
    
    def test_add_create_dir_operation(self):
        plan = self.planner.create_plan("Test")
        
        dir_path = str(Path(self.temp_dir) / "new_dir")
        
        operation = self.planner.add_create_dir_operation(plan, dir_path)
        
        self.assertEqual(operation.operation_type, OperationType.CREATE_DIR)
        self.assertEqual(len(plan.operations), 1)
    
    def test_validate_plan_no_collisions(self):
        plan = self.planner.create_plan("Test")
        
        source = Path(self.temp_dir) / "source.txt"
        source.write_text("content")
        target = Path(self.temp_dir) / "target.txt"
        
        self.planner.add_move_operation(plan, str(source), str(target))
        
        validated_plan = self.planner.validate_plan(plan)
        
        self.assertEqual(validated_plan.status, "validated")
        self.assertEqual(len(validated_plan.collisions), 0)
    
    def test_validate_plan_with_collisions(self):
        plan = self.planner.create_plan("Test")
        
        source = Path(self.temp_dir) / "source.txt"
        source.write_text("content")
        target = Path(self.temp_dir) / "target.txt"
        target.write_text("existing")
        
        self.planner.add_move_operation(plan, str(source), str(target))
        
        validated_plan = self.planner.validate_plan(plan)
        
        self.assertEqual(validated_plan.status, "has_collisions")
        self.assertEqual(len(validated_plan.collisions), 1)
    
    def test_generate_tree_diff(self):
        plan = self.planner.create_plan("Test")
        
        source = Path(self.temp_dir) / "source.txt"
        source.write_text("content")
        target = Path(self.temp_dir) / "target.txt"
        
        self.planner.add_move_operation(plan, str(source), str(target))
        
        tree_diff = self.planner.generate_tree_diff(plan)
        
        self.assertIsInstance(tree_diff, TreeDiffNode)
        self.assertEqual(tree_diff.action, "root")
        self.assertEqual(len(tree_diff.children), 2)
    
    def test_estimate_duration(self):
        plan = self.planner.create_plan("Test")
        
        for i in range(5):
            source = Path(self.temp_dir) / f"source{i}.txt"
            source.write_text("content")
            target = Path(self.temp_dir) / f"target{i}.txt"
            self.planner.add_move_operation(plan, str(source), str(target))
        
        duration = self.planner.estimate_duration(plan)
        
        self.assertGreater(duration, 0)


class TestDryRunPlannerIntegration(unittest.TestCase):
    """Integration tests for dry-run planner."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.planner = create_dry_run_planner()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_workflow(self):
        source_dir = Path(self.temp_dir) / "source"
        source_dir.mkdir()
        
        for i in range(3):
            (source_dir / f"file{i}.txt").write_text(f"content {i}")
        
        plan = self.planner.create_plan("Organize Files", "Move files to organized structure")
        
        for i in range(3):
            source = source_dir / f"file{i}.txt"
            target = Path(self.temp_dir) / "organized" / f"file{i}.txt"
            self.planner.add_move_operation(plan, str(source), str(target))
        
        validated_plan = self.planner.validate_plan(plan)
        tree_diff = self.planner.generate_tree_diff(validated_plan)
        duration = self.planner.estimate_duration(validated_plan)
        
        self.assertEqual(validated_plan.status, "validated")
        self.assertEqual(len(validated_plan.operations), 3)
        self.assertGreater(duration, 0)
        self.assertIsInstance(tree_diff, TreeDiffNode)


if __name__ == "__main__":
    unittest.main()
