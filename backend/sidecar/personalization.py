#!/usr/bin/env python3
"""
FileCustra Personalization Engine
Local user preference recorder, cold-start recommendation engine, and privacy-safe preference management.
"""

import json
import os
import platform
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Preference:
    """A single user preference."""
    key: str
    value: Any
    source: str = "user"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "source": self.source,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class Recommendation:
    """A recommendation based on learned preferences."""
    strategy: str
    confidence: float
    reason: str
    source_signals: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "strategy": self.strategy,
            "confidence": self.confidence,
            "reason": self.reason,
            "source_signals": self.source_signals,
        }


class PreferenceRecorder:
    """Records and manages local user preferences."""
    
    PREFERENCE_KEYS = {
        "preferred_strategy": str,
        "max_depth": int,
        "exclude_patterns": list,
        "exclude_dirs": list,
        "include_hidden": bool,
        "auto_preview": bool,
        "theme": str,
        "language": str,
        "last_used_strategy": str,
        "total_operations": int,
        "accepted_suggestions": int,
        "rejected_suggestions": int,
    }
    
    def __init__(self, preferences_dir: Optional[str] = None):
        self._dir = Path(preferences_dir) if preferences_dir else Path("preferences")
        self._dir.mkdir(parents=True, exist_ok=True)
        self._preferences: Dict[str, Preference] = {}
        self._load_preferences()
    
    def _load_preferences(self) -> None:
        prefs_file = self._dir / "user_preferences.json"
        if prefs_file.exists():
            try:
                with open(prefs_file, "r") as f:
                    data = json.load(f)
                for key, val_data in data.items():
                    self._preferences[key] = Preference(
                        key=key,
                        value=val_data.get("value"),
                        source=val_data.get("source", "user"),
                        created_at=val_data.get("created_at", time.time()),
                        updated_at=val_data.get("updated_at", time.time()),
                    )
            except Exception:
                pass
    
    def _save_preferences(self) -> None:
        prefs_file = self._dir / "user_preferences.json"
        data = {k: v.to_dict() for k, v in self._preferences.items()}
        with open(prefs_file, "w") as f:
            json.dump(data, f, indent=2)
    
    def set(self, key: str, value: Any, source: str = "user") -> bool:
        """Set a preference value."""
        if key not in self.PREFERENCE_KEYS:
            return False
        
        expected_type = self.PREFERENCE_KEYS[key]
        if not isinstance(value, expected_type):
            try:
                value = expected_type(value)
            except (ValueError, TypeError):
                return False
        
        if key in self._preferences:
            self._preferences[key].value = value
            self._preferences[key].updated_at = time.time()
            self._preferences[key].source = source
        else:
            self._preferences[key] = Preference(
                key=key,
                value=value,
                source=source,
            )
        
        self._save_preferences()
        return True
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a preference value."""
        pref = self._preferences.get(key)
        return pref.value if pref else default
    
    def get_all(self) -> Dict[str, Any]:
        """Get all preferences."""
        return {k: v.value for k, v in self._preferences.items()}
    
    def get_metadata(self, key: str) -> Optional[dict]:
        """Get preference metadata."""
        pref = self._preferences.get(key)
        return pref.to_dict() if pref else None
    
    def delete(self, key: str) -> bool:
        """Delete a preference."""
        if key in self._preferences:
            del self._preferences[key]
            self._save_preferences()
            return True
        return False
    
    def reset(self) -> None:
        """Reset all preferences."""
        self._preferences.clear()
        prefs_file = self._dir / "user_preferences.json"
        if prefs_file.exists():
            prefs_file.unlink()
    
    def export_preferences(self) -> str:
        """Export all preferences as JSON."""
        data = {k: v.to_dict() for k, v in self._preferences.items()}
        return json.dumps(data, indent=2)
    
    def import_preferences(self, json_str: str) -> bool:
        """Import preferences from JSON."""
        try:
            data = json.loads(json_str)
            for key, val_data in data.items():
                self._preferences[key] = Preference(
                    key=key,
                    value=val_data.get("value"),
                    source=val_data.get("source", "import"),
                    created_at=val_data.get("created_at", time.time()),
                    updated_at=val_data.get("updated_at", time.time()),
                )
            self._save_preferences()
            return True
        except Exception:
            return False
    
    def record_operation(self, strategy: str, accepted: bool) -> None:
        """Record an operation for learning purposes."""
        total = self.get("total_operations", 0) or 0
        self.set("total_operations", total + 1, source="system")
        
        if accepted:
            accepted_count = self.get("accepted_suggestions", 0) or 0
            self.set("accepted_suggestions", accepted_count + 1, source="system")
        else:
            rejected_count = self.get("rejected_suggestions", 0) or 0
            self.set("rejected_suggestions", rejected_count + 1, source="system")
        
        self.set("last_used_strategy", strategy, source="system")


class OSContextDetector:
    """Detects OS context for cold-start recommendations."""
    
    @staticmethod
    def detect_os() -> str:
        return platform.system().lower()
    
    @staticmethod
    def detect_common_paths() -> List[str]:
        os_name = platform.system().lower()
        paths = []
        
        home = Path.home()
        
        if os_name == "windows":
            for name in ["Desktop", "Documents", "Downloads", "Pictures", "Music", "Videos"]:
                p = home / name
                if p.exists():
                    paths.append(str(p))
        elif os_name == "darwin":
            for name in ["Desktop", "Documents", "Downloads", "Pictures", "Music", "Movies"]:
                p = home / name
                if p.exists():
                    paths.append(str(p))
        else:
            for name in ["Desktop", "Documents", "Downloads", "Pictures", "Music", "Videos"]:
                p = home / name
                if p.exists():
                    paths.append(str(p))
        
        return paths
    
    @staticmethod
    def get_os_specific_recommendations() -> Dict[str, str]:
        os_name = platform.system().lower()
        
        if os_name == "windows":
            return {
                "exclude_dirs": ".git,node_modules,.venv,__pycache__,Thumbs.db",
                "exclude_patterns": "*.tmp,*.bak,desktop.ini",
                "preferred_strategy": "file_type_format",
            }
        elif os_name == "darwin":
            return {
                "exclude_dirs": ".git,node_modules,.venv,__pycache__,.DS_Store",
                "exclude_patterns": "*.tmp,*.bak,.DS_Store",
                "preferred_strategy": "date_chronological",
            }
        else:
            return {
                "exclude_dirs": ".git,node_modules,.venv,__pycache__",
                "exclude_patterns": "*.tmp,*.bak,*~",
                "preferred_strategy": "project_domain",
            }


class ColdStartRecommender:
    """Cold-start recommendation engine using OS context."""
    
    def __init__(self, preference_recorder: PreferenceRecorder):
        self._recorder = preference_recorder
        self._os_detector = OSContextDetector()
    
    def get_recommendations(self) -> List[Recommendation]:
        """Generate recommendations based on available signals."""
        recommendations = []
        
        total_ops = self._recorder.get("total_operations", 0) or 0
        
        if total_ops == 0:
            recommendations.extend(self._get_cold_start_recommendations())
        else:
            recommendations.extend(self._get_learned_recommendations())
        
        recommendations.sort(key=lambda r: r.confidence, reverse=True)
        return recommendations
    
    def _get_cold_start_recommendations(self) -> List[Recommendation]:
        recommendations = []
        
        os_recs = self._os_detector.get_os_specific_recommendations()
        
        recommendations.append(Recommendation(
            strategy=os_recs["preferred_strategy"],
            confidence=0.6,
            reason=f"Recommended for {self._os_detector.detect_os()} users",
            source_signals=["os_detection"],
        ))
        
        common_paths = self._os_detector.detect_common_paths()
        if common_paths:
            recommendations.append(Recommendation(
                strategy="date_chronological",
                confidence=0.5,
                reason="Commonly used for Downloads and Desktop cleanup",
                source_signals=["common_paths"],
            ))
        
        return recommendations
    
    def _get_learned_recommendations(self) -> List[Recommendation]:
        recommendations = []
        
        last_strategy = self._recorder.get("last_used_strategy")
        if last_strategy:
            recommendations.append(Recommendation(
                strategy=last_strategy,
                confidence=0.7,
                reason="Based on your most recent organization",
                source_signals=["usage_history"],
            ))
        
        accepted = self._recorder.get("accepted_suggestions", 0) or 0
        rejected = self._recorder.get("rejected_suggestions", 0) or 0
        
        if accepted > rejected and accepted > 0:
            recommendations.append(Recommendation(
                strategy=last_strategy or "date_chronological",
                confidence=0.8,
                reason="You tend to accept suggestions with this approach",
                source_signals=["acceptance_rate"],
            ))
        
        return recommendations


class PersonalizationManager:
    """Manages the full personalization lifecycle."""
    
    def __init__(self, preferences_dir: Optional[str] = None):
        self._recorder = PreferenceRecorder(preferences_dir)
        self._recommender = ColdStartRecommender(self._recorder)
    
    @property
    def preferences(self) -> PreferenceRecorder:
        return self._recorder
    
    @property
    def recommender(self) -> ColdStartRecommender:
        return self._recommender
    
    def get_recommendations(self) -> List[Recommendation]:
        return self._recommender.get_recommendations()
    
    def record_and_recommend(self, strategy: str, accepted: bool) -> List[Recommendation]:
        """Record an operation and return updated recommendations."""
        self._recorder.record_operation(strategy, accepted)
        return self.get_recommendations()
    
    def export_preferences(self) -> str:
        return self._recorder.export_preferences()
    
    def import_preferences(self, json_str: str) -> bool:
        return self._recorder.import_preferences(json_str)
    
    def reset_all(self) -> None:
        self._recorder.reset()
    
    def get_privacy_summary(self) -> dict:
        """Return a summary of data stored for privacy verification."""
        prefs = self._recorder.get_all()
        return {
            "total_preferences": len(prefs),
            "stored_keys": list(prefs.keys()),
            "network_transmission": "none",
            "external_storage": "none",
            "data_stays_local": True,
            "last_updated": max(
                (self._recorder.get_metadata(k)["updated_at"]
                 for k in prefs
                 if self._recorder.get_metadata(k)),
                default=0,
            ),
        }


def create_personalization_manager(
    preferences_dir: Optional[str] = None,
) -> PersonalizationManager:
    """Factory function to create a personalization manager."""
    return PersonalizationManager(preferences_dir)


if __name__ == "__main__":
    mgr = create_personalization_manager()
    recs = mgr.get_recommendations()
    print(f"Personalization manager initialized with {len(recs)} recommendations")
    for r in recs:
        print(f"  - {r.strategy}: {r.reason} (confidence: {r.confidence})")
