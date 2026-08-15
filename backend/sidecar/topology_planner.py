#!/usr/bin/env python3
"""
FileCustra Auto AI Topology Planner
Four file-organization strategies with JSON schema validation and human-readable rationale.
"""

import json
import os
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class TopologyStrategy(Enum):
    """Four core file organization strategies."""
    DATE_CHRONOLOGICAL = "date_chronological"
    PROJECT_DOMAIN = "project_domain"
    FILE_TYPE_FORMAT = "file_type_format"
    SEMANTIC_CLUSTER = "semantic_cluster"


STRATEGY_DESCRIPTIONS = {
    TopologyStrategy.DATE_CHRONOLOGICAL: "Organizes files by creation or modification date into year/month/day hierarchies.",
    TopologyStrategy.PROJECT_DOMAIN: "Groups files by project name or domain into dedicated folders.",
    TopologyStrategy.FILE_TYPE_FORMAT: "Separates files by extension or MIME type into categorized directories.",
    TopologyStrategy.SEMANTIC_CLUSTER: "Clusters files by content similarity and semantic relationships.",
}

STRATEGY_RECOMMENDATIONS = {
    TopologyStrategy.DATE_CHRONOLOGICAL: [
        "Best for photo libraries, journal entries, and time-series data",
        "Works well when files have reliable timestamps",
        "Avoid if file timestamps are unreliable or heavily mixed",
    ],
    TopologyStrategy.PROJECT_DOMAIN: [
        "Ideal for multi-project workspaces and team collaborations",
        "Requires prior knowledge of project boundaries",
        "May struggle with ambiguous files spanning multiple projects",
    ],
    TopologyStrategy.FILE_TYPE_FORMAT: [
        "Effective for mixed-format asset libraries",
        "Simple to implement and understand",
        "Does not capture semantic relationships between files",
    ],
    TopologyStrategy.SEMANTIC_CLUSTER: [
        "Captures deep content relationships between files",
        "Requires embedding model and more compute resources",
        "Best for large, diverse document collections",
    ],
}

NODE_SCHEMA = {
    "type": "object",
    "required": ["name", "type"],
    "properties": {
        "name": {"type": "string"},
        "type": {"type": "string", "enum": ["directory", "file"]},
        "children": {"type": "array"},
        "source_path": {"type": "string"},
        "reason": {"type": "string"},
        "confidence": {"type": "number"},
    },
}

PLAN_SCHEMA = {
    "type": "object",
    "required": ["strategy", "root", "summary"],
    "properties": {
        "strategy": {"type": "string", "enum": [s.value for s in TopologyStrategy]},
        "root": NODE_SCHEMA,
        "summary": {"type": "string"},
        "rationale": {"type": "string"},
        "estimated_duration_sec": {"type": "number"},
        "node_count": {"type": "integer"},
    },
}


@dataclass
class TopologyNode:
    """A node in the proposed directory tree."""
    name: str
    node_type: str = "directory"
    children: List["TopologyNode"] = field(default_factory=list)
    source_path: Optional[str] = None
    reason: str = ""
    confidence: float = 1.0
    
    def to_dict(self) -> dict:
        d = {
            "name": self.name,
            "type": self.node_type,
            "reason": self.reason,
            "confidence": self.confidence,
        }
        if self.source_path:
            d["source_path"] = self.source_path
        if self.children:
            d["children"] = [c.to_dict() for c in self.children]
        return d
    
    def count_nodes(self) -> int:
        count = 1
        for child in self.children:
            count += child.count_nodes()
        return count


@dataclass
class TopologyPlan:
    """A complete proposed file organization plan."""
    strategy: TopologyStrategy
    root: TopologyNode
    summary: str
    rationale: str = ""
    estimated_duration_sec: float = 0.0
    
    @property
    def node_count(self) -> int:
        return self.root.count_nodes()
    
    def to_dict(self) -> dict:
        return {
            "strategy": self.strategy.value,
            "root": self.root.to_dict(),
            "summary": self.summary,
            "rationale": self.rationale,
            "estimated_duration_sec": self.estimated_duration_sec,
            "node_count": self.node_count,
        }
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class TopologyPlanValidator:
    """Validates topology plans against the JSON schema."""
    
    @staticmethod
    def validate(plan_dict: dict) -> tuple:
        errors = []
        
        if "strategy" not in plan_dict:
            errors.append("Missing required field: strategy")
        elif plan_dict["strategy"] not in [s.value for s in TopologyStrategy]:
            errors.append(f"Invalid strategy: {plan_dict['strategy']}")
        
        if "root" not in plan_dict:
            errors.append("Missing required field: root")
        else:
            root_errors = TopologyPlanValidator._validate_node(plan_dict["root"])
            errors.extend(root_errors)
        
        if "summary" not in plan_dict:
            errors.append("Missing required field: summary")
        elif not isinstance(plan_dict["summary"], str) or len(plan_dict["summary"]) == 0:
            errors.append("Summary must be a non-empty string")
        
        if "node_count" in plan_dict:
            if not isinstance(plan_dict["node_count"], int) or plan_dict["node_count"] < 1:
                errors.append("node_count must be a positive integer")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _validate_node(node: dict) -> list:
        errors = []
        
        if "name" not in node:
            errors.append("Node missing required field: name")
        elif not isinstance(node["name"], str) or len(node["name"]) == 0:
            errors.append("Node name must be a non-empty string")
        
        if "type" not in node:
            errors.append("Node missing required field: type")
        elif node["type"] not in ("directory", "file"):
            errors.append(f"Invalid node type: {node.get('type')}")
        
        if "children" in node:
            if not isinstance(node["children"], list):
                errors.append("Node children must be a list")
            else:
                for child in node["children"]:
                    child_errors = TopologyPlanValidator._validate_node(child)
                    errors.extend(child_errors)
        
        return errors


class TopologyPlanner:
    """Auto AI topology planner with four strategy variants."""
    
    def __init__(self):
        self._strategies = {
            TopologyStrategy.DATE_CHRONOLOGICAL: self._plan_date_chronological,
            TopologyStrategy.PROJECT_DOMAIN: self._plan_project_domain,
            TopologyStrategy.FILE_TYPE_FORMAT: self._plan_file_type_format,
            TopologyStrategy.SEMANTIC_CLUSTER: self._plan_semantic_cluster,
        }
    
    def plan(
        self,
        source_dir: str,
        strategy: TopologyStrategy,
        max_depth: int = 5,
    ) -> TopologyPlan:
        """Generate a topology plan using the specified strategy."""
        if strategy not in self._strategies:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        start_time = time.time()
        root = self._strategies[strategy](source_dir, max_depth)
        duration = time.time() - start_time
        
        summary = f"Organized {root.count_nodes()} items using {strategy.value} strategy"
        rationale = STRATEGY_DESCRIPTIONS.get(strategy, "")
        
        return TopologyPlan(
            strategy=strategy,
            root=root,
            summary=summary,
            rationale=rationale,
            estimated_duration_sec=round(duration, 3),
        )
    
    def plan_all_strategies(
        self,
        source_dir: str,
        max_depth: int = 5,
    ) -> Dict[TopologyStrategy, TopologyPlan]:
        """Generate plans using all four strategies."""
        plans = {}
        for strategy in TopologyStrategy:
            plans[strategy] = self.plan(source_dir, strategy, max_depth)
        return plans
    
    def compare_plans(
        self,
        plans: Dict[TopologyStrategy, TopologyPlan],
    ) -> List[dict]:
        """Compare multiple plans and return ranked results."""
        results = []
        for strategy, plan in plans.items():
            results.append({
                "strategy": strategy.value,
                "node_count": plan.node_count,
                "estimated_duration_sec": plan.estimated_duration_sec,
                "summary": plan.summary,
                "recommendations": STRATEGY_RECOMMENDATIONS.get(strategy, []),
            })
        results.sort(key=lambda x: x["node_count"])
        return results
    
    def _plan_date_chronological(
        self,
        source_dir: str,
        max_depth: int,
    ) -> TopologyNode:
        """Organize files by date into year/month/day hierarchy."""
        root = TopologyNode(name=os.path.basename(source_dir) or "organized")
        
        files = self._scan_files(source_dir, max_files=500)
        
        year_nodes: Dict[str, TopologyNode] = {}
        
        for file_path in files:
            try:
                mtime = os.path.getmtime(file_path)
                t = time.localtime(mtime)
                year = str(t.tm_year)
                month = f"{t.tm_mon:02d}"
                day = f"{t.tm_mday:02d}"
                
                if year not in year_nodes:
                    year_node = TopologyNode(
                        name=year,
                        reason=f"Files from year {year}",
                    )
                    year_nodes[year] = year_node
                    root.children.append(year_node)
                
                month_key = f"{year}-{month}"
                month_node = None
                for child in year_nodes[year].children:
                    if child.name == month:
                        month_node = child
                        break
                
                if month_node is None:
                    month_node = TopologyNode(
                        name=month,
                        reason=f"Files from month {month}",
                    )
                    year_nodes[year].children.append(month_node)
                
                file_node = TopologyNode(
                    name=os.path.basename(file_path),
                    node_type="file",
                    source_path=file_path,
                    reason=f"Last modified {year}/{month}/{day}",
                )
                month_node.children.append(file_node)
            
            except Exception:
                file_node = TopologyNode(
                    name=os.path.basename(file_path),
                    node_type="file",
                    source_path=file_path,
                    reason="Unclassified file",
                )
                root.children.append(file_node)
        
        return root
    
    def _plan_project_domain(
        self,
        source_dir: str,
        max_depth: int,
    ) -> TopologyNode:
        """Group files by project or domain."""
        root = TopologyNode(name=os.path.basename(source_dir) or "organized")
        
        files = self._scan_files(source_dir, max_files=500)
        
        project_nodes: Dict[str, TopologyNode] = {}
        
        for file_path in files:
            project = self._detect_project(file_path, source_dir)
            
            if project not in project_nodes:
                project_node = TopologyNode(
                    name=project,
                    reason=f"Project: {project}",
                )
                project_nodes[project] = project_node
                root.children.append(project_node)
            
            file_node = TopologyNode(
                name=os.path.basename(file_path),
                node_type="file",
                source_path=file_path,
                reason=f"Belongs to project {project}",
            )
            project_nodes[project].children.append(file_node)
        
        return root
    
    def _plan_file_type_format(
        self,
        source_dir: str,
        max_depth: int,
    ) -> TopologyNode:
        """Separate files by type into categorized directories."""
        root = TopologyNode(name=os.path.basename(source_dir) or "organized")
        
        files = self._scan_files(source_dir, max_files=500)
        
        TYPE_CATEGORIES = {
            "documents": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".md", ".tex"},
            "spreadsheets": {".xls", ".xlsx", ".csv", ".tsv", ".ods"},
            "images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".svg", ".webp"},
            "audio": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma"},
            "video": {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv"},
            "code": {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".rs", ".go"},
            "archives": {".zip", ".tar", ".gz", ".rar", ".7z", ".bz2"},
        }
        
        category_nodes: Dict[str, TopologyNode] = {}
        
        for file_path in files:
            ext = Path(file_path).suffix.lower()
            category = "other"
            
            for cat_name, extensions in TYPE_CATEGORIES.items():
                if ext in extensions:
                    category = cat_name
                    break
            
            if category not in category_nodes:
                cat_node = TopologyNode(
                    name=category,
                    reason=f"{category.capitalize()} files",
                )
                category_nodes[category] = cat_node
                root.children.append(cat_node)
            
            file_node = TopologyNode(
                name=os.path.basename(file_path),
                node_type="file",
                source_path=file_path,
                reason=f"File type: {ext or 'no extension'}",
            )
            category_nodes[category].children.append(file_node)
        
        return root
    
    def _plan_semantic_cluster(
        self,
        source_dir: str,
        max_depth: int,
    ) -> TopologyNode:
        """Cluster files by content similarity (simplified word-based)."""
        root = TopologyNode(name=os.path.basename(source_dir) or "organized")
        
        files = self._scan_files(source_dir, max_files=200)
        
        clusters: Dict[str, List[str]] = {}
        
        for file_path in files:
            cluster = self._detect_semantic_cluster(file_path)
            if cluster not in clusters:
                clusters[cluster] = []
            clusters[cluster].append(file_path)
        
        for cluster_name, cluster_files in clusters.items():
            cluster_node = TopologyNode(
                name=cluster_name,
                reason=f"Semantic cluster: {cluster_name}",
            )
            root.children.append(cluster_node)
            
            for file_path in cluster_files:
                file_node = TopologyNode(
                    name=os.path.basename(file_path),
                    node_type="file",
                    source_path=file_path,
                    reason=f"Semantically related to {cluster_name}",
                )
                cluster_node.children.append(file_node)
        
        return root
    
    def _scan_files(self, source_dir: str, max_files: int = 500) -> List[str]:
        """Scan directory for files."""
        files = []
        try:
            for root_dir, _, filenames in os.walk(source_dir):
                for fname in filenames:
                    if len(files) >= max_files:
                        return files
                    files.append(os.path.join(root_dir, fname))
        except Exception:
            pass
        return files
    
    def _detect_project(self, file_path: str, source_dir: str) -> str:
        """Detect project name from file path."""
        rel = os.path.relpath(file_path, source_dir)
        parts = Path(rel).parts
        
        if len(parts) > 1:
            return parts[0]
        
        stem = Path(file_path).stem
        project_patterns = [
            r"^(.+?)[-_](?:v\d+|test|src|lib|doc)",
            r"^([A-Z][a-z]+(?:[A-Z][a-z]+)+)",
        ]
        
        for pattern in project_patterns:
            match = re.match(pattern, stem)
            if match:
                return match.group(1)
        
        return "uncategorized"
    
    def _detect_semantic_cluster(self, file_path: str) -> str:
        """Detect semantic cluster from filename and content hints."""
        stem = Path(file_path).stem.lower()
        
        CLUSTER_KEYWORDS = {
            "documentation": ["readme", "doc", "guide", "manual", "help"],
            "configuration": ["config", "settings", "env", "rc", "ini", "yaml", "toml"],
            "tests": ["test", "spec", "check", "verify"],
            "data": ["data", "dataset", "csv", "json", "table"],
            "images": ["img", "photo", "pic", "icon", "logo", "banner"],
            "scripts": ["script", "run", "build", "deploy", "make"],
            "reports": ["report", "summary", "analysis", "review"],
        }
        
        for cluster, keywords in CLUSTER_KEYWORDS.items():
            if any(kw in stem for kw in keywords):
                return cluster
        
        return "miscellaneous"


def create_topology_planner() -> TopologyPlanner:
    """Factory function to create a topology planner."""
    return TopologyPlanner()


def validate_plan_json(plan_dict: dict) -> tuple:
    """Validate a plan dictionary against the schema."""
    return TopologyPlanValidator.validate(plan_dict)


if __name__ == "__main__":
    planner = create_topology_planner()
    print("Topology planner initialized with 4 strategies:")
    for s in TopologyStrategy:
        print(f"  - {s.value}: {STRATEGY_DESCRIPTIONS[s]}")
