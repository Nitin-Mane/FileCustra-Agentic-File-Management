#!/usr/bin/env python3
"""Tests for personalization engine and cold-start recommender."""

import json
import os
import shutil
import tempfile

import pytest

from personalization import (
    ColdStartRecommender,
    OSContextDetector,
    Preference,
    PreferenceRecorder,
    PersonalizationManager,
    Recommendation,
    create_personalization_manager,
)


@pytest.fixture
def tmp_workspace():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def recorder(tmp_workspace):
    prefs_dir = os.path.join(tmp_workspace, "prefs")
    return PreferenceRecorder(prefs_dir)


@pytest.fixture
def manager(tmp_workspace):
    prefs_dir = os.path.join(tmp_workspace, "prefs")
    return create_personalization_manager(prefs_dir)


class TestPreference:
    def test_to_dict(self):
        p = Preference(key="test", value="hello", source="user")
        d = p.to_dict()
        assert d["key"] == "test"
        assert d["value"] == "hello"
        assert d["source"] == "user"


class TestPreferenceRecorder:
    def test_set_and_get(self, recorder):
        success = recorder.set("preferred_strategy", "date_chronological")
        assert success is True
        assert recorder.get("preferred_strategy") == "date_chronological"
    
    def test_invalid_key(self, recorder):
        success = recorder.set("invalid_key", "value")
        assert success is False
    
    def test_type_conversion(self, recorder):
        recorder.set("max_depth", "5")
        assert recorder.get("max_depth") == 5
    
    def test_persistence(self, tmp_workspace):
        prefs_dir = os.path.join(tmp_workspace, "prefs")
        r1 = PreferenceRecorder(prefs_dir)
        r1.set("theme", "dark")
        
        r2 = PreferenceRecorder(prefs_dir)
        assert r2.get("theme") == "dark"
    
    def test_delete(self, recorder):
        recorder.set("theme", "dark")
        success = recorder.delete("theme")
        assert success is True
        assert recorder.get("theme") is None
    
    def test_delete_nonexistent(self, recorder):
        success = recorder.delete("nonexistent")
        assert success is False
    
    def test_reset(self, recorder):
        recorder.set("theme", "dark")
        recorder.reset()
        assert recorder.get("theme") is None
    
    def test_export_import(self, recorder):
        recorder.set("preferred_strategy", "date_chronological")
        recorder.set("max_depth", 4)
        
        exported = recorder.export_preferences()
        assert "date_chronological" in exported
        
        recorder.reset()
        success = recorder.import_preferences(exported)
        assert success is True
        assert recorder.get("preferred_strategy") == "date_chronological"
    
    def test_import_invalid_json(self, recorder):
        success = recorder.import_preferences("not valid json")
        assert success is False
    
    def test_get_all(self, recorder):
        recorder.set("theme", "dark")
        recorder.set("language", "en")
        all_prefs = recorder.get_all()
        assert all_prefs["theme"] == "dark"
        assert all_prefs["language"] == "en"
    
    def test_get_metadata(self, recorder):
        recorder.set("theme", "dark")
        meta = recorder.get_metadata("theme")
        assert meta is not None
        assert meta["key"] == "theme"
        assert meta["source"] == "user"
    
    def test_record_operation(self, recorder):
        recorder.record_operation("date_chronological", accepted=True)
        assert recorder.get("total_operations") == 1
        assert recorder.get("accepted_suggestions") == 1
        
        recorder.record_operation("date_chronological", accepted=False)
        assert recorder.get("total_operations") == 2
        assert recorder.get("rejected_suggestions") == 1
    
    def test_default_get(self, recorder):
        value = recorder.get("nonexistent", "default")
        assert value == "default"


class TestRecommendation:
    def test_to_dict(self):
        r = Recommendation(
            strategy="date_chronological",
            confidence=0.8,
            reason="test reason",
            source_signals=["os_detection"],
        )
        d = r.to_dict()
        assert d["strategy"] == "date_chronological"
        assert d["confidence"] == 0.8
        assert "os_detection" in d["source_signals"]


class TestOSContextDetector:
    def test_detect_os(self):
        os_name = OSContextDetector.detect_os()
        assert os_name in ["windows", "darwin", "linux"]
    
    def test_detect_common_paths(self):
        paths = OSContextDetector.detect_common_paths()
        assert isinstance(paths, list)
    
    def test_get_os_specific_recommendations(self):
        recs = OSContextDetector.get_os_specific_recommendations()
        assert "exclude_dirs" in recs
        assert "preferred_strategy" in recs


class TestColdStartRecommender:
    def test_cold_start_recommendations(self, recorder):
        recommender = ColdStartRecommender(recorder)
        recs = recommender.get_recommendations()
        assert len(recs) > 0
        assert all(isinstance(r, Recommendation) for r in recs)
    
    def test_learned_recommendations(self, recorder):
        recorder.record_operation("file_type_format", accepted=True)
        recommender = ColdStartRecommender(recorder)
        recs = recommender.get_recommendations()
        assert len(recs) > 0


class TestPersonalizationManager:
    def test_get_recommendations(self, manager):
        recs = manager.get_recommendations()
        assert isinstance(recs, list)
    
    def test_record_and_recommend(self, manager):
        recs = manager.record_and_recommend("date_chronological", accepted=True)
        assert isinstance(recs, list)
        assert manager.preferences.get("total_operations") == 1
    
    def test_export_import(self, manager):
        manager.preferences.set("theme", "dark")
        exported = manager.export_preferences()
        
        manager.reset_all()
        success = manager.import_preferences(exported)
        assert success is True
        assert manager.preferences.get("theme") == "dark"
    
    def test_privacy_summary(self, manager):
        manager.preferences.set("theme", "dark")
        summary = manager.get_privacy_summary()
        assert summary["network_transmission"] == "none"
        assert summary["external_storage"] == "none"
        assert summary["data_stays_local"] is True
        assert summary["total_preferences"] >= 1
    
    def test_reset_all(self, manager):
        manager.preferences.set("theme", "dark")
        manager.reset_all()
        assert manager.preferences.get("theme") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
