#!/usr/bin/env python3
"""Tests for realtime event constellation, transitions, and keyboard UX."""

import time

import pytest

from event_constellation import (
    ConstellationEngine,
    EventBus,
    Event,
    EventType,
    KeyboardManager,
    KeyboardShortcut,
    ProgressTracker,
    TransitionManager,
    EventPriority,
    create_constellation_engine,
)


@pytest.fixture
def event_bus():
    return EventBus(max_history=100)


@pytest.fixture
def engine():
    return create_constellation_engine()


class TestEventType:
    def test_all_types_exist(self):
        assert EventType.FILE_SCANNED.value == "file_scanned"
        assert EventType.FILE_MOVED.value == "file_moved"
        assert EventType.PROGRESS_UPDATE.value == "progress_update"
        assert EventType.ERROR_OCCURRED.value == "error_occurred"
        assert EventType.SECURITY_ALERT.value == "security_alert"


class TestEventPriority:
    def test_priorities(self):
        assert EventPriority.LOW.value == "low"
        assert EventPriority.NORMAL.value == "normal"
        assert EventPriority.HIGH.value == "high"
        assert EventPriority.URGENT.value == "urgent"


class TestEvent:
    def test_create_event(self):
        event = Event(
            event_id="evt-1",
            event_type=EventType.FILE_SCANNED,
            payload={"path": "/tmp/file.txt"},
        )
        assert event.event_id == "evt-1"
        assert event.event_type == EventType.FILE_SCANNED
    
    def test_to_dict(self):
        event = Event(
            event_id="evt-1",
            event_type=EventType.FILE_SCANNED,
            payload={"path": "/tmp/file.txt"},
            priority=EventPriority.HIGH,
        )
        d = event.to_dict()
        assert d["event_id"] == "evt-1"
        assert d["event_type"] == "file_scanned"
        assert d["priority"] == "high"
    
    def test_from_dict(self):
        data = {
            "event_id": "evt-1",
            "event_type": "file_scanned",
            "payload": {"path": "/tmp/file.txt"},
            "priority": "normal",
        }
        event = Event.from_dict(data)
        assert event.event_id == "evt-1"
        assert event.event_type == EventType.FILE_SCANNED


class TestEventBus:
    def test_publish_subscribe(self, event_bus):
        received = []
        event_bus.subscribe("file_scanned", lambda e: received.append(e))
        
        event = Event(
            event_id="evt-1",
            event_type=EventType.FILE_SCANNED,
            payload={},
        )
        event_bus.publish(event)
        assert len(received) == 1
    
    def test_wildcard_subscribe(self, event_bus):
        received = []
        event_bus.subscribe_all(lambda e: received.append(e))
        
        event_bus.publish(Event("e1", EventType.FILE_SCANNED, {}))
        event_bus.publish(Event("e2", EventType.FILE_MOVED, {}))
        assert len(received) == 2
    
    def test_unsubscribe(self, event_bus):
        received = []
        callback = lambda e: received.append(e)
        event_bus.subscribe("file_scanned", callback)
        
        event_bus.publish(Event("e1", EventType.FILE_SCANNED, {}))
        assert len(received) == 1
        
        event_bus.unsubscribe("file_scanned", callback)
        event_bus.publish(Event("e2", EventType.FILE_SCANNED, {}))
        assert len(received) == 1
    
    def test_get_history(self, event_bus):
        event_bus.publish(Event("e1", EventType.FILE_SCANNED, {}))
        event_bus.publish(Event("e2", EventType.FILE_MOVED, {}))
        
        history = event_bus.get_history()
        assert len(history) == 2
    
    def test_get_history_filtered(self, event_bus):
        event_bus.publish(Event("e1", EventType.FILE_SCANNED, {}))
        event_bus.publish(Event("e2", EventType.FILE_MOVED, {}))
        event_bus.publish(Event("e3", EventType.FILE_SCANNED, {}))
        
        history = event_bus.get_history(event_type=EventType.FILE_SCANNED)
        assert len(history) == 2
    
    def test_clear_history(self, event_bus):
        event_bus.publish(Event("e1", EventType.FILE_SCANNED, {}))
        event_bus.clear_history()
        assert len(event_bus.get_history()) == 0
    
    def test_history_max_size(self):
        bus = EventBus(max_history=3)
        for i in range(5):
            bus.publish(Event(f"e{i}", EventType.FILE_SCANNED, {}))
        assert len(bus.get_history()) == 3


class TestProgressTracker:
    def test_start_operation(self, engine):
        engine.progress_tracker.start_operation("op-1", 10, "Testing")
        op = engine.progress_tracker.get_operation("op-1")
        assert op is not None
        assert op["status"] == "running"
    
    def test_update_progress(self, engine):
        engine.progress_tracker.start_operation("op-1", 10)
        engine.progress_tracker.update_progress("op-1", 5)
        op = engine.progress_tracker.get_operation("op-1")
        assert op["completed_steps"] == 5
    
    def test_complete_operation(self, engine):
        engine.progress_tracker.start_operation("op-1", 10)
        engine.progress_tracker.complete_operation("op-1")
        op = engine.progress_tracker.get_operation("op-1")
        assert op["status"] == "completed"
    
    def test_fail_operation(self, engine):
        engine.progress_tracker.start_operation("op-1", 10)
        engine.progress_tracker.fail_operation("op-1", "disk full")
        op = engine.progress_tracker.get_operation("op-1")
        assert op["status"] == "failed"
        assert op["error"] == "disk full"
    
    def test_get_all_operations(self, engine):
        engine.progress_tracker.start_operation("op-1", 10)
        engine.progress_tracker.start_operation("op-2", 5)
        ops = engine.progress_tracker.get_all_operations()
        assert len(ops) == 2


class TestKeyboardShortcut:
    def test_to_dict(self):
        shortcut = KeyboardShortcut("n", "new_plan", "Create new plan", ["ctrl"])
        d = shortcut.to_dict()
        assert d["key"] == "n"
        assert d["modifiers"] == ["ctrl"]
    
    def test_matches(self):
        shortcut = KeyboardShortcut("s", "save", "Save", ["ctrl"])
        assert shortcut.matches("s", ["ctrl"]) is True
        assert shortcut.matches("s", ["ctrl", "shift"]) is False
        assert shortcut.matches("x", ["ctrl"]) is False


class TestKeyboardManager:
    def test_default_shortcuts(self):
        km = KeyboardManager()
        shortcuts = km.get_shortcuts()
        assert len(shortcuts) > 0
    
    def test_handle_keypress(self):
        km = KeyboardManager()
        called = []
        km.register_handler("save", lambda: called.append(True))
        
        action = km.handle_keypress("s", ["ctrl"])
        assert action == "save"
        assert len(called) == 1
    
    def test_unmatched_keypress(self):
        km = KeyboardManager()
        action = km.handle_keypress("z", [])
        assert action is None
    
    def test_register_custom_shortcut(self):
        km = KeyboardManager()
        custom = KeyboardShortcut("k", "custom", "Custom action")
        km.register_shortcut(custom)
        
        km.register_handler("custom", lambda: None)
        action = km.handle_keypress("k", [])
        assert action == "custom"
    
    def test_get_shortcut_for_action(self):
        km = KeyboardManager()
        shortcut = km.get_shortcut_for_action("save")
        assert shortcut is not None
        assert shortcut["key"] == "s"
    
    def test_get_nonexistent_shortcut(self):
        km = KeyboardManager()
        shortcut = km.get_shortcut_for_action("nonexistent")
        assert shortcut is None


class TestTransitionManager:
    def test_define_transition(self):
        tm = TransitionManager()
        tm.define_transition("slide", 300, "ease-out")
        transitions = tm.get_available_transitions()
        assert len(transitions) == 1
    
    def test_start_transition(self):
        tm = TransitionManager()
        tm.define_transition("fade", 200)
        result = tm.start_transition("fade", {"opacity": 0}, {"opacity": 1})
        assert "error" not in result
        assert result["status"] == "running"
    
    def test_unknown_transition(self):
        tm = TransitionManager()
        result = tm.start_transition("unknown", {}, {})
        assert "error" in result
    
    def test_get_transition_state(self):
        tm = TransitionManager()
        tm.define_transition("scale", 100)
        tm.start_transition("scale", {"scale": 0}, {"scale": 1})
        
        state = tm.get_transition_state("scale")
        assert state is not None
        assert "progress" in state
    
    def test_get_available_transitions(self):
        tm = TransitionManager()
        tm.define_transition("a", 100)
        tm.define_transition("b", 200)
        transitions = tm.get_available_transitions()
        assert len(transitions) == 2


class TestConstellationEngine:
    def test_emit_event(self, engine):
        event = engine.emit_event(
            EventType.FILE_SCANNED,
            {"path": "/tmp/file.txt"},
        )
        assert event.event_type == EventType.FILE_SCANNED
    
    def test_get_event_history(self, engine):
        engine.emit_event(EventType.FILE_SCANNED, {"path": "/tmp/a"})
        engine.emit_event(EventType.FILE_MOVED, {"path": "/tmp/b"})
        history = engine.get_event_history()
        assert len(history) == 2
    
    def test_get_status(self, engine):
        status = engine.get_status()
        assert "event_history_size" in status
        assert "active_operations" in status
        assert "registered_shortcuts" in status
        assert "available_transitions" in status
    
    def test_integration(self, engine):
        received = []
        engine.event_bus.subscribe_all(lambda e: received.append(e))
        
        engine.emit_event(EventType.FILE_SCANNED, {"path": "/tmp/a"})
        engine.emit_event(EventType.FILE_MOVED, {"path": "/tmp/b"})
        
        assert len(received) == 2
        history = engine.get_event_history()
        assert len(history) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
