#!/usr/bin/env python3
"""Tests for auto AI topology planner."""

import json
import os
import shutil
import tempfile

import pytest

from topology_planner import (
    TopologyNode,
    TopologyPlan,
    TopologyPlanValidator,
    TopologyPlanner,
    TopologyStrategy,
    STRATEGY_DESCRIPTIONS,
    STRATEGY_RECOMMENDATIONS,
    create_topology_planner,
    validate_plan_json,
)


@pytest.fixture
def tmp_workspace():
    """Create a temporary workspace with sample files."""
    d = tempfile.mkdtemp()
    
    os.makedirs(os.path.join(d, "src"))
    os.makedirs(os.path.join(d, "docs"))
    os.makedirs(os.path.join(d, "images"))
    
    for name in ["main.py", "utils.py", "config.yaml"]:
        with open(os.path.join(d, "src", name), "w") as f:
            f.write(f"# {name}\nprint('hello')")
    
    for name in ["readme.md", "guide.txt"]:
        with open(os.path.join(d, "docs", name), "w") as f:
            f.write(f"# {name}\nDocumentation content")
    
    for name in ["logo.png", "banner.jpg"]:
        with open(os.path.join(d, "images", name), "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)
    
    with open(os.path.join(d, "data.csv"), "w") as f:
        f.write("col1,col2\n1,2\n3,4")
    
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def planner():
    return create_topology_planner()


class TestTopologyStrategy:
    def test_all_strategies_exist(self):
        assert len(TopologyStrategy) == 4
    
    def test_strategy_values(self):
        assert TopologyStrategy.DATE_CHRONOLOGICAL.value == "date_chronological"
        assert TopologyStrategy.PROJECT_DOMAIN.value == "project_domain"
        assert TopologyStrategy.FILE_TYPE_FORMAT.value == "file_type_format"
        assert TopologyStrategy.SEMANTIC_CLUSTER.value == "semantic_cluster"
    
    def test_descriptions_match(self):
        for s in TopologyStrategy:
            assert s in STRATEGY_DESCRIPTIONS
    
    def test_recommendations_match(self):
        for s in TopologyStrategy:
            assert s in STRATEGY_RECOMMENDATIONS
            assert len(STRATEGY_RECOMMENDATIONS[s]) > 0


class TestTopologyNode:
    def test_create_node(self):
        node = TopologyNode(name="test", node_type="directory")
        assert node.name == "test"
        assert node.node_type == "directory"
        assert node.children == []
    
    def test_to_dict(self):
        node = TopologyNode(
            name="folder",
            node_type="directory",
            reason="test reason",
            confidence=0.9,
        )
        d = node.to_dict()
        assert d["name"] == "folder"
        assert d["type"] == "directory"
        assert d["reason"] == "test reason"
        assert d["confidence"] == 0.9
    
    def test_to_dict_with_source(self):
        node = TopologyNode(
            name="file.txt",
            node_type="file",
            source_path="/tmp/file.txt",
        )
        d = node.to_dict()
        assert d["source_path"] == "/tmp/file.txt"
    
    def test_count_nodes(self):
        root = TopologyNode(name="root")
        child1 = TopologyNode(name="child1")
        child2 = TopologyNode(name="child2")
        grandchild = TopologyNode(name="grandchild")
        child1.children.append(grandchild)
        root.children.extend([child1, child2])
        assert root.count_nodes() == 4


class TestTopologyPlanValidator:
    def test_valid_plan(self):
        plan_dict = {
            "strategy": "date_chronological",
            "root": {"name": "test", "type": "directory"},
            "summary": "A test plan",
            "node_count": 1,
        }
        valid, errors = validate_plan_json(plan_dict)
        assert valid is True
        assert errors == []
    
    def test_missing_strategy(self):
        plan_dict = {
            "root": {"name": "test", "type": "directory"},
            "summary": "A test plan",
        }
        valid, errors = validate_plan_json(plan_dict)
        assert valid is False
        assert any("strategy" in e for e in errors)
    
    def test_invalid_strategy(self):
        plan_dict = {
            "strategy": "nonexistent",
            "root": {"name": "test", "type": "directory"},
            "summary": "A test plan",
        }
        valid, errors = validate_plan_json(plan_dict)
        assert valid is False
    
    def test_missing_root(self):
        plan_dict = {
            "strategy": "file_type_format",
            "summary": "A test plan",
        }
        valid, errors = validate_plan_json(plan_dict)
        assert valid is False
    
    def test_missing_summary(self):
        plan_dict = {
            "strategy": "project_domain",
            "root": {"name": "test", "type": "directory"},
        }
        valid, errors = validate_plan_json(plan_dict)
        assert valid is False
    
    def test_empty_summary(self):
        plan_dict = {
            "strategy": "project_domain",
            "root": {"name": "test", "type": "directory"},
            "summary": "",
        }
        valid, errors = validate_plan_json(plan_dict)
        assert valid is False


class TestTopologyPlanner:
    def test_plan_date_chronological(self, planner, tmp_workspace):
        plan = planner.plan(tmp_workspace, TopologyStrategy.DATE_CHRONOLOGICAL)
        assert plan.strategy == TopologyStrategy.DATE_CHRONOLOGICAL
        assert plan.node_count >= 1
        assert len(plan.summary) > 0
    
    def test_plan_project_domain(self, planner, tmp_workspace):
        plan = planner.plan(tmp_workspace, TopologyStrategy.PROJECT_DOMAIN)
        assert plan.strategy == TopologyStrategy.PROJECT_DOMAIN
        assert plan.node_count >= 1
    
    def test_plan_file_type_format(self, planner, tmp_workspace):
        plan = planner.plan(tmp_workspace, TopologyStrategy.FILE_TYPE_FORMAT)
        assert plan.strategy == TopologyStrategy.FILE_TYPE_FORMAT
        assert plan.node_count >= 1
        assert len(plan.root.children) > 0
    
    def test_plan_semantic_cluster(self, planner, tmp_workspace):
        plan = planner.plan(tmp_workspace, TopologyStrategy.SEMANTIC_CLUSTER)
        assert plan.strategy == TopologyStrategy.SEMANTIC_CLUSTER
        assert plan.node_count >= 1
    
    def test_plan_all_strategies(self, planner, tmp_workspace):
        plans = planner.plan_all_strategies(tmp_workspace)
        assert len(plans) == 4
        for strategy in TopologyStrategy:
            assert strategy in plans
    
    def test_compare_plans(self, planner, tmp_workspace):
        plans = planner.plan_all_strategies(tmp_workspace)
        results = planner.compare_plans(plans)
        assert len(results) == 4
        assert isinstance(results[0]["node_count"], int)
        assert "recommendations" in results[0]
    
    def test_plan_to_json(self, planner, tmp_workspace):
        plan = planner.plan(tmp_workspace, TopologyStrategy.FILE_TYPE_FORMAT)
        json_str = plan.to_json()
        parsed = json.loads(json_str)
        assert parsed["strategy"] == "file_type_format"
        assert "root" in parsed
    
    def test_plan_json_is_valid(self, planner, tmp_workspace):
        plan = planner.plan(tmp_workspace, TopologyStrategy.PROJECT_DOMAIN)
        plan_dict = plan.to_dict()
        valid, errors = validate_plan_json(plan_dict)
        assert valid is True, f"Validation errors: {errors}"
    
    def test_plan_with_max_depth(self, planner, tmp_workspace):
        plan = planner.plan(tmp_workspace, TopologyStrategy.DATE_CHRONOLOGICAL, max_depth=2)
        assert plan.node_count >= 1


class TestTopologyPlannerEdgeCases:
    def test_empty_directory(self, planner):
        with tempfile.TemporaryDirectory() as d:
            plan = planner.plan(d, TopologyStrategy.FILE_TYPE_FORMAT)
            assert plan.node_count == 1
            assert plan.root.name == os.path.basename(d)
    
    def test_nonexistent_directory(self, planner):
        plan = planner.plan("/nonexistent/path/that/does/not/exist", TopologyStrategy.DATE_CHRONOLOGICAL)
        assert plan.node_count == 1
        assert plan.root.name == "exist"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
