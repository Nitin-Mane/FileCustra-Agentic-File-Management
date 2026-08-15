#!/usr/bin/env python3
"""
FileCustra Guided Query Mode
Interactive 5-question workflow for capturing user file organization intent.
"""

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class QuestionType(Enum):
    """Types of questions in the guided query workflow."""
    SINGLE_CHOICE = "single_choice"
    MULTI_CHOICE = "multi_choice"
    FREE_TEXT = "free_text"
    RANGE = "range"
    TOGGLE = "toggle"


class QueryStep(Enum):
    """The five guided query steps."""
    STEP_1_PURPOSE = "purpose"
    STEP_2_STRUCTURE = "structure"
    STEP_3_DEPTH = "depth"
    STEP_4_EXCLUSIONS = "exclusions"
    STEP_5_CONFIRM = "confirm"


STEP_ORDER = [
    QueryStep.STEP_1_PURPOSE,
    QueryStep.STEP_2_STRUCTURE,
    QueryStep.STEP_3_DEPTH,
    QueryStep.STEP_4_EXCLUSIONS,
    QueryStep.STEP_5_CONFIRM,
]


@dataclass
class GuidedQuestion:
    """A single guided question."""
    step: QueryStep
    question_id: str
    prompt: str
    question_type: QuestionType
    options: List[str] = field(default_factory=list)
    default_value: Any = None
    description: str = ""
    
    def to_dict(self) -> dict:
        return {
            "step": self.step.value,
            "question_id": self.question_id,
            "prompt": self.prompt,
            "type": self.question_type.value,
            "options": self.options,
            "default": self.default_value,
            "description": self.description,
        }


@dataclass
class IntentAnswer:
    """An answer to a guided question."""
    question_id: str
    value: Any
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> dict:
        return {
            "question_id": self.question_id,
            "value": self.value,
            "timestamp": self.timestamp,
        }


@dataclass
class StructuredIntent:
    """Compiled structured intent from user answers."""
    purpose: str = ""
    structure_type: str = ""
    max_depth: int = 3
    exclude_patterns: List[str] = field(default_factory=list)
    exclude_dirs: List[str] = field(default_factory=list)
    include_hidden: bool = False
    dry_run: bool = True
    custom_rules: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "purpose": self.purpose,
            "structure_type": self.structure_type,
            "max_depth": self.max_depth,
            "exclude_patterns": self.exclude_patterns,
            "exclude_dirs": self.exclude_dirs,
            "include_hidden": self.include_hidden,
            "dry_run": self.dry_run,
            "custom_rules": self.custom_rules,
        }
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


PURPOSE_QUESTIONS = {
    "clean_desktop": "Clean up a cluttered desktop or downloads folder",
    "project_sort": "Sort project files into organized directories",
    "photo_archive": "Archive and organize photos by date or event",
    "document_library": "Create a searchable document library",
    "code_workspace": "Organize a multi-language code workspace",
    "media_collection": "Sort media files (audio, video, images)",
    "mixed_files": "Organize a general mixed file collection",
}

STRUCTURE_OPTIONS = {
    "date_chronological": "By date (year/month/day)",
    "project_domain": "By project or topic",
    "file_type_format": "By file type or format",
    "semantic_cluster": "By content similarity",
    "hybrid": "Combination of strategies",
}


class GuidedQueryEngine:
    """Interactive 5-question guided query engine."""
    
    def __init__(self):
        self._questions = self._build_questions()
        self._answers: Dict[str, IntentAnswer] = {}
        self._current_step_idx = 0
        self._step_validators: Dict[QueryStep, Callable] = {
            QueryStep.STEP_1_PURPOSE: self._validate_purpose,
            QueryStep.STEP_2_STRUCTURE: self._validate_structure,
            QueryStep.STEP_3_DEPTH: self._validate_depth,
            QueryStep.STEP_4_EXCLUSIONS: self._validate_exclusions,
            QueryStep.STEP_5_CONFIRM: self._validate_confirm,
        }
    
    def _build_questions(self) -> Dict[QueryStep, List[GuidedQuestion]]:
        return {
            QueryStep.STEP_1_PURPOSE: [
                GuidedQuestion(
                    step=QueryStep.STEP_1_PURPOSE,
                    question_id="purpose",
                    prompt="What is the main purpose of this organization?",
                    question_type=QuestionType.SINGLE_CHOICE,
                    options=list(PURPOSE_QUESTIONS.values()),
                    description="Select the primary goal for file organization",
                ),
            ],
            QueryStep.STEP_2_STRUCTURE: [
                GuidedQuestion(
                    step=QueryStep.STEP_2_STRUCTURE,
                    question_id="structure",
                    prompt="How would you like files organized?",
                    question_type=QuestionType.SINGLE_CHOICE,
                    options=list(STRUCTURE_OPTIONS.values()),
                    description="Choose an organizational structure",
                ),
            ],
            QueryStep.STEP_3_DEPTH: [
                GuidedQuestion(
                    step=QueryStep.STEP_3_DEPTH,
                    question_id="depth",
                    prompt="Maximum folder depth (1-10)?",
                    question_type=QuestionType.RANGE,
                    options=[],
                    default_value=3,
                    description="Deeper nesting captures more detail but may be harder to navigate",
                ),
            ],
            QueryStep.STEP_4_EXCLUSIONS: [
                GuidedQuestion(
                    step=QueryStep.STEP_4_EXCLUSIONS,
                    question_id="exclude_patterns",
                    prompt="Any file patterns to exclude? (comma-separated)",
                    question_type=QuestionType.FREE_TEXT,
                    options=[],
                    default_value="*.tmp,*.bak,.DS_Store,Thumbs.db",
                    description="Files matching these patterns will not be moved",
                ),
                GuidedQuestion(
                    step=QueryStep.STEP_4_EXCLUSIONS,
                    question_id="exclude_dirs",
                    prompt="Any directories to skip? (comma-separated)",
                    question_type=QuestionType.FREE_TEXT,
                    options=[],
                    default_value=".git,node_modules,.venv,__pycache__",
                    description="These directories and their contents will be ignored",
                ),
                GuidedQuestion(
                    step=QueryStep.STEP_4_EXCLUSIONS,
                    question_id="include_hidden",
                    prompt="Include hidden files and folders?",
                    question_type=QuestionType.TOGGLE,
                    options=["Yes", "No"],
                    default_value=False,
                    description="Hidden files start with a dot (Unix) or have hidden attribute (Windows)",
                ),
            ],
            QueryStep.STEP_5_CONFIRM: [
                GuidedQuestion(
                    step=QueryStep.STEP_5_CONFIRM,
                    question_id="dry_run",
                    prompt="Run in preview-only mode first?",
                    question_type=QuestionType.TOGGLE,
                    options=["Yes, preview first", "No, execute immediately"],
                    default_value=True,
                    description="Preview mode shows planned changes without modifying files",
                ),
            ],
        }
    
    def get_current_step(self) -> QueryStep:
        return STEP_ORDER[self._current_step_idx]
    
    def get_current_questions(self) -> List[GuidedQuestion]:
        step = self.get_current_step()
        return self._questions.get(step, [])
    
    def get_step_questions(self, step: QueryStep) -> List[GuidedQuestion]:
        return self._questions.get(step, [])
    
    def submit_answer(self, question_id: str, value: Any) -> tuple:
        """Submit an answer and validate it."""
        question = self._find_question(question_id)
        if question is None:
            return False, f"Unknown question: {question_id}"
        
        step = question.step
        validator = self._step_validators.get(step)
        if validator:
            is_valid, error = validator(question_id, value)
            if not is_valid:
                return False, error
        
        self._answers[question_id] = IntentAnswer(
            question_id=question_id,
            value=value,
        )
        return True, None
    
    def advance_step(self) -> tuple:
        """Move to the next step after validating current answers."""
        step = self.get_current_step()
        questions = self._questions.get(step, [])
        
        for q in questions:
            if q.question_id not in self._answers:
                return False, f"Missing answer for: {q.prompt}"
        
        if self._current_step_idx < len(STEP_ORDER) - 1:
            self._current_step_idx += 1
            return True, None
        
        return False, "Already at the final step"
    
    def go_to_step(self, step: QueryStep) -> bool:
        """Jump to a specific step."""
        if step in STEP_ORDER:
            self._current_step_idx = STEP_ORDER.index(step)
            return True
        return False
    
    def compile_intent(self) -> StructuredIntent:
        """Compile answers into a structured intent."""
        intent = StructuredIntent()
        
        purpose_answer = self._answers.get("purpose")
        if purpose_answer:
            purpose_key = self._reverse_lookup(PURPOSE_QUESTIONS, purpose_answer.value)
            intent.purpose = purpose_key or purpose_answer.value
        
        structure_answer = self._answers.get("structure")
        if structure_answer:
            structure_key = self._reverse_lookup(STRUCTURE_OPTIONS, structure_answer.value)
            intent.structure_type = structure_key or structure_answer.value
        
        depth_answer = self._answers.get("depth")
        if depth_answer:
            try:
                intent.max_depth = int(depth_answer.value)
            except (ValueError, TypeError):
                intent.max_depth = 3
        
        patterns_answer = self._answers.get("exclude_patterns")
        if patterns_answer and patterns_answer.value:
            intent.exclude_patterns = [
                p.strip() for p in str(patterns_answer.value).split(",") if p.strip()
            ]
        
        dirs_answer = self._answers.get("exclude_dirs")
        if dirs_answer and dirs_answer.value:
            intent.exclude_dirs = [
                d.strip() for d in str(dirs_answer.value).split(",") if d.strip()
            ]
        
        hidden_answer = self._answers.get("include_hidden")
        if hidden_answer:
            intent.include_hidden = str(hidden_answer.value).lower() in ("yes", "true", "1")
        
        dry_run_answer = self._answers.get("dry_run")
        if dry_run_answer:
            intent.dry_run = str(dry_run_answer.value).lower() in ("yes", "true", "1", "yes, preview first")
        
        return intent
    
    def get_progress(self) -> dict:
        """Get current progress information."""
        total_steps = len(STEP_ORDER)
        answered_steps = 0
        
        for step in STEP_ORDER:
            questions = self._questions.get(step, [])
            if all(q.question_id in self._answers for q in questions):
                answered_steps += 1
        
        return {
            "current_step": self.get_current_step().value,
            "current_step_index": self._current_step_idx,
            "total_steps": total_steps,
            "answered_steps": answered_steps,
            "progress_pct": round(answered_steps / total_steps * 100, 1),
            "is_complete": answered_steps == total_steps,
        }
    
    def _find_question(self, question_id: str) -> Optional[GuidedQuestion]:
        for step_questions in self._questions.values():
            for q in step_questions:
                if q.question_id == question_id:
                    return q
        return None
    
    def _reverse_lookup(self, d: dict, value: str) -> Optional[str]:
        for k, v in d.items():
            if v == value:
                return k
        return None
    
    def _validate_purpose(self, question_id: str, value: Any) -> tuple:
        if not value:
            return False, "Purpose cannot be empty"
        return True, None
    
    def _validate_structure(self, question_id: str, value: Any) -> tuple:
        if not value:
            return False, "Structure type cannot be empty"
        return True, None
    
    def _validate_depth(self, question_id: str, value: Any) -> tuple:
        try:
            depth = int(value)
            if depth < 1 or depth > 10:
                return False, "Depth must be between 1 and 10"
        except (ValueError, TypeError):
            return False, "Depth must be a valid integer"
        return True, None
    
    def _validate_exclusions(self, question_id: str, value: Any) -> tuple:
        return True, None
    
    def _validate_confirm(self, question_id: str, value: Any) -> tuple:
        return True, None
    
    def get_answers(self) -> Dict[str, Any]:
        """Get all collected answers."""
        return {k: v.value for k, v in self._answers.items()}
    
    def get_answers_list(self) -> List[dict]:
        """Get answers as a list of dictionaries."""
        return [a.to_dict() for a in self._answers.values()]
    
    def reset(self) -> None:
        """Reset all answers and progress."""
        self._answers.clear()
        self._current_step_idx = 0
    
    def to_dict(self) -> dict:
        """Export full guided query state."""
        return {
            "progress": self.get_progress(),
            "answers": self.get_answers(),
            "intent": self.compile_intent().to_dict(),
        }


def create_guided_query_engine() -> GuidedQueryEngine:
    """Factory function to create a guided query engine."""
    return GuidedQueryEngine()


def guided_query_to_json(engine: GuidedQueryEngine) -> str:
    """Export guided query state as JSON."""
    return json.dumps(engine.to_dict(), indent=2)


if __name__ == "__main__":
    engine = create_guided_query_engine()
    progress = engine.get_progress()
    print(f"Guided Query Engine initialized: {progress['total_steps']} steps")
    for step in STEP_ORDER:
        questions = engine.get_step_questions(step)
        print(f"  {step.value}: {len(questions)} question(s)")
