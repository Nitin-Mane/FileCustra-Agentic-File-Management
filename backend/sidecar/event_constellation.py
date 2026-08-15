#!/usr/bin/env python3
"""
FileCustra Realtime Event Constellation
Event streaming, transition management, and keyboard UX support.
"""

import json
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class EventType(Enum):
    """Types of events in the constellation."""
    FILE_SCANNED = "file_scanned"
    FILE_MOVED = "file_moved"
    FILE_COPIED = "file_copied"
    FILE_DELETED = "file_deleted"
    PLAN_CREATED = "plan_created"
    PLAN_EXECUTED = "plan_executed"
    PLAN_ROLLED_BACK = "plan_rolled_back"
    PROGRESS_UPDATE = "progress_update"
    ERROR_OCCURRED = "error_occurred"
    SECURITY_ALERT = "security_alert"
    USER_ACTION = "user_action"
    SYSTEM_STATUS = "system_status"


class EventPriority(Enum):
    """Event priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Event:
    """A single event in the constellation."""
    event_id: str
    event_type: EventType
    payload: Dict[str, Any]
    priority: EventPriority = EventPriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    source: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "payload": self.payload,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "source": self.source,
            "metadata": self.metadata,
        }
    
    @staticmethod
    def from_dict(data: dict) -> "Event":
        return Event(
            event_id=data.get("event_id", str(uuid.uuid4())),
            event_type=EventType(data["event_type"]),
            payload=data.get("payload", {}),
            priority=EventPriority(data.get("priority", "normal")),
            timestamp=data.get("timestamp", time.time()),
            source=data.get("source", "system"),
            metadata=data.get("metadata", {}),
        )


class EventBus:
    """Event bus for pub/sub event distribution."""
    
    def __init__(self, max_history: int = 1000):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._history: deque = deque(maxlen=max_history)
        self._wildcard_subscribers: List[Callable] = []
    
    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to a specific event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    def subscribe_all(self, callback: Callable) -> None:
        """Subscribe to all events."""
        self._wildcard_subscribers.append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable) -> bool:
        """Unsubscribe from an event type."""
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
                return True
        return False
    
    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        self._history.append(event)
        
        type_key = event.event_type.value
        for callback in self._subscribers.get(type_key, []):
            try:
                callback(event)
            except Exception:
                pass
        
        for callback in self._wildcard_subscribers:
            try:
                callback(event)
            except Exception:
                pass
    
    def get_history(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 100,
    ) -> List[Event]:
        """Get event history."""
        events = list(self._history)
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]
    
    def clear_history(self) -> None:
        self._history.clear()


class ProgressTracker:
    """Tracks progress of multi-step operations."""
    
    def __init__(self, event_bus: EventBus):
        self._bus = event_bus
        self._operations: Dict[str, dict] = {}
    
    def start_operation(
        self,
        operation_id: str,
        total_steps: int,
        description: str = "",
    ) -> None:
        """Start tracking a new operation."""
        self._operations[operation_id] = {
            "total_steps": total_steps,
            "completed_steps": 0,
            "description": description,
            "started_at": time.time(),
            "status": "running",
        }
        
        self._bus.publish(Event(
            event_id=str(uuid.uuid4()),
            event_type=EventType.PROGRESS_UPDATE,
            payload={
                "operation_id": operation_id,
                "progress_pct": 0,
                "status": "started",
                "description": description,
            },
        ))
    
    def update_progress(
        self,
        operation_id: str,
        completed_steps: int,
    ) -> None:
        """Update progress for an operation."""
        op = self._operations.get(operation_id)
        if op:
            op["completed_steps"] = min(completed_steps, op["total_steps"])
            pct = round(op["completed_steps"] / op["total_steps"] * 100, 1)
            
            self._bus.publish(Event(
                event_id=str(uuid.uuid4()),
                event_type=EventType.PROGRESS_UPDATE,
                payload={
                    "operation_id": operation_id,
                    "progress_pct": pct,
                    "completed_steps": op["completed_steps"],
                    "total_steps": op["total_steps"],
                    "status": "running",
                },
            ))
    
    def complete_operation(self, operation_id: str) -> None:
        """Mark an operation as complete."""
        op = self._operations.get(operation_id)
        if op:
            op["status"] = "completed"
            op["completed_at"] = time.time()
            
            self._bus.publish(Event(
                event_id=str(uuid.uuid4()),
                event_type=EventType.PROGRESS_UPDATE,
                payload={
                    "operation_id": operation_id,
                    "progress_pct": 100,
                    "status": "completed",
                    "duration_sec": round(op["completed_at"] - op["started_at"], 3),
                },
            ))
    
    def fail_operation(self, operation_id: str, error: str = "") -> None:
        """Mark an operation as failed."""
        op = self._operations.get(operation_id)
        if op:
            op["status"] = "failed"
            op["error"] = error
            
            self._bus.publish(Event(
                event_id=str(uuid.uuid4()),
                event_type=EventType.ERROR_OCCURRED,
                payload={
                    "operation_id": operation_id,
                    "error": error,
                    "status": "failed",
                },
            ))
    
    def get_operation(self, operation_id: str) -> Optional[dict]:
        return self._operations.get(operation_id)
    
    def get_all_operations(self) -> Dict[str, dict]:
        return dict(self._operations)


class KeyboardShortcut:
    """Defines a keyboard shortcut."""
    
    def __init__(
        self,
        key: str,
        action: str,
        description: str,
        modifiers: List[str] = None,
    ):
        self.key = key
        self.action = action
        self.description = description
        self.modifiers = modifiers or []
    
    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "modifiers": self.modifiers,
            "action": self.action,
            "description": self.description,
        }
    
    def matches(self, pressed_key: str, pressed_modifiers: List[str]) -> bool:
        """Check if a key combination matches this shortcut."""
        if pressed_key.lower() != self.key.lower():
            return False
        return sorted(m.lower() for m in pressed_modifiers) == sorted(m.lower() for m in self.modifiers)


class KeyboardManager:
    """Manages keyboard shortcuts and UX."""
    
    DEFAULT_SHORTCUTS = [
        KeyboardShortcut("n", "new_plan", "Create new plan", ["ctrl"]),
        KeyboardShortcut("o", "open_folder", "Open folder", ["ctrl"]),
        KeyboardShortcut("s", "save", "Save current plan", ["ctrl"]),
        KeyboardShortcut("z", "undo", "Undo last action", ["ctrl"]),
        KeyboardShortcut("y", "redo", "Redo last action", ["ctrl"]),
        KeyboardShortcut("Delete", "delete_selected", "Delete selected items"),
        KeyboardShortcut("Escape", "cancel", "Cancel current operation"),
        KeyboardShortcut("Enter", "confirm", "Confirm selection"),
        KeyboardShortcut("F1", "help", "Show help"),
        KeyboardShortcut("F5", "refresh", "Refresh view"),
    ]
    
    def __init__(self):
        self._shortcuts: Dict[str, KeyboardShortcut] = {}
        self._action_handlers: Dict[str, Callable] = {}
        self._load_defaults()
    
    def _load_defaults(self) -> None:
        for shortcut in self.DEFAULT_SHORTCUTS:
            self._shortcuts[shortcut.action] = shortcut
    
    def register_shortcut(self, shortcut: KeyboardShortcut) -> None:
        """Register a keyboard shortcut."""
        self._shortcuts[shortcut.action] = shortcut
    
    def register_handler(self, action: str, handler: Callable) -> None:
        """Register an action handler."""
        self._action_handlers[action] = handler
    
    def handle_keypress(self, key: str, modifiers: List[str]) -> Optional[str]:
        """Handle a keypress and return the matched action."""
        for action, shortcut in self._shortcuts.items():
            if shortcut.matches(key, modifiers):
                handler = self._action_handlers.get(action)
                if handler:
                    try:
                        handler()
                    except Exception:
                        pass
                return action
        return None
    
    def get_shortcuts(self) -> List[dict]:
        """Get all registered shortcuts."""
        return [s.to_dict() for s in self._shortcuts.values()]
    
    def get_shortcut_for_action(self, action: str) -> Optional[dict]:
        shortcut = self._shortcuts.get(action)
        return shortcut.to_dict() if shortcut else None


class TransitionManager:
    """Manages animated transitions between states."""
    
    def __init__(self):
        self._transitions: Dict[str, dict] = {}
        self._active_transitions: List[dict] = []
    
    def define_transition(
        self,
        name: str,
        duration_ms: int = 300,
        easing: str = "ease-in-out",
        properties: List[str] = None,
    ) -> None:
        """Define a named transition."""
        self._transitions[name] = {
            "name": name,
            "duration_ms": duration_ms,
            "easing": easing,
            "properties": properties or ["opacity", "transform"],
        }
    
    def start_transition(self, name: str, from_state: dict, to_state: dict) -> dict:
        """Start a transition between states."""
        transition = self._transitions.get(name)
        if not transition:
            return {"error": f"Unknown transition: {name}"}
        
        active = {
            "name": name,
            "from": from_state,
            "to": to_state,
            "started_at": time.time(),
            "duration_ms": transition["duration_ms"],
            "easing": transition["easing"],
            "status": "running",
        }
        
        self._active_transitions.append(active)
        return active
    
    def get_transition_state(self, name: str) -> Optional[dict]:
        for t in self._active_transitions:
            if t["name"] == name and t["status"] == "running":
                elapsed = (time.time() - t["started_at"]) * 1000
                progress = min(1.0, elapsed / t["duration_ms"])
                if progress >= 1.0:
                    t["status"] = "completed"
                return {**t, "progress": round(progress, 3)}
        return None
    
    def get_available_transitions(self) -> List[dict]:
        return list(self._transitions.values())


class ConstellationEngine:
    """Main engine combining event bus, progress tracking, keyboard, and transitions."""
    
    def __init__(self):
        self._event_bus = EventBus()
        self._progress_tracker = ProgressTracker(self._event_bus)
        self._keyboard_manager = KeyboardManager()
        self._transition_manager = TransitionManager()
        self._setup_default_transitions()
    
    def _setup_default_transitions(self) -> None:
        self._transition_manager.define_transition("slide_in", 300, "ease-out", ["transform", "opacity"])
        self._transition_manager.define_transition("fade", 200, "ease-in-out", ["opacity"])
        self._transition_manager.define_transition("scale", 250, "cubic-bezier(0.34, 1.56, 0.64, 1)", ["transform"])
    
    @property
    def event_bus(self) -> EventBus:
        return self._event_bus
    
    @property
    def progress_tracker(self) -> ProgressTracker:
        return self._progress_tracker
    
    @property
    def keyboard_manager(self) -> KeyboardManager:
        return self._keyboard_manager
    
    @property
    def transition_manager(self) -> TransitionManager:
        return self._transition_manager
    
    def emit_event(
        self,
        event_type: EventType,
        payload: Dict[str, Any],
        priority: EventPriority = EventPriority.NORMAL,
    ) -> Event:
        """Emit an event."""
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            payload=payload,
            priority=priority,
        )
        self._event_bus.publish(event)
        return event
    
    def get_event_history(self, limit: int = 50) -> List[dict]:
        return [e.to_dict() for e in self._event_bus.get_history(limit=limit)]
    
    def get_status(self) -> dict:
        return {
            "event_history_size": len(self._event_bus._history),
            "active_operations": len(self._progress_tracker.get_all_operations()),
            "registered_shortcuts": len(self._keyboard_manager.get_shortcuts()),
            "available_transitions": len(self._transition_manager.get_available_transitions()),
        }


def create_constellation_engine() -> ConstellationEngine:
    """Factory function to create a constellation engine."""
    return ConstellationEngine()


if __name__ == "__main__":
    engine = create_constellation_engine()
    status = engine.get_status()
    print(f"Constellation engine initialized: {status}")
