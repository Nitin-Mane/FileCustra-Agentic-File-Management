#!/usr/bin/env python3
"""Tests for guided query mode with five questions workflow."""

import json

import pytest

from guided_query import (
    GuidedQuestion,
    GuidedQueryEngine,
    IntentAnswer,
    QueryStep,
    QuestionType,
    StructuredIntent,
    create_guided_query_engine,
    guided_query_to_json,
)


@pytest.fixture
def engine():
    return create_guided_query_engine()


class TestQuestionType:
    def test_types_exist(self):
        assert QuestionType.SINGLE_CHOICE.value == "single_choice"
        assert QuestionType.MULTI_CHOICE.value == "multi_choice"
        assert QuestionType.FREE_TEXT.value == "free_text"
        assert QuestionType.RANGE.value == "range"
        assert QuestionType.TOGGLE.value == "toggle"


class TestQueryStep:
    def test_five_steps(self):
        from guided_query import STEP_ORDER
        assert len(STEP_ORDER) == 5
    
    def test_step_values(self):
        assert QueryStep.STEP_1_PURPOSE.value == "purpose"
        assert QueryStep.STEP_2_STRUCTURE.value == "structure"
        assert QueryStep.STEP_3_DEPTH.value == "depth"
        assert QueryStep.STEP_4_EXCLUSIONS.value == "exclusions"
        assert QueryStep.STEP_5_CONFIRM.value == "confirm"


class TestGuidedQuestion:
    def test_to_dict(self):
        q = GuidedQuestion(
            step=QueryStep.STEP_1_PURPOSE,
            question_id="test",
            prompt="Test?",
            question_type=QuestionType.SINGLE_CHOICE,
            options=["A", "B"],
            default_value="A",
            description="A test question",
        )
        d = q.to_dict()
        assert d["question_id"] == "test"
        assert d["type"] == "single_choice"
        assert d["options"] == ["A", "B"]


class TestStructuredIntent:
    def test_to_dict(self):
        intent = StructuredIntent(
            purpose="clean_desktop",
            structure_type="date_chronological",
            max_depth=3,
            exclude_patterns=["*.tmp"],
            exclude_dirs=["node_modules"],
        )
        d = intent.to_dict()
        assert d["purpose"] == "clean_desktop"
        assert d["max_depth"] == 3
        assert "*.tmp" in d["exclude_patterns"]
    
    def test_to_json(self):
        intent = StructuredIntent(purpose="test")
        j = intent.to_json()
        parsed = json.loads(j)
        assert parsed["purpose"] == "test"
    
    def test_default_values(self):
        intent = StructuredIntent()
        assert intent.max_depth == 3
        assert intent.dry_run is True
        assert intent.include_hidden is False


class TestGuidedQueryEngine:
    def test_initial_state(self, engine):
        progress = engine.get_progress()
        assert progress["current_step"] == "purpose"
        assert progress["current_step_index"] == 0
        assert progress["total_steps"] == 5
        assert progress["progress_pct"] == 0.0
        assert progress["is_complete"] is False
    
    def test_get_current_questions(self, engine):
        questions = engine.get_current_questions()
        assert len(questions) == 1
        assert questions[0].question_id == "purpose"
    
    def test_submit_answer(self, engine):
        success, error = engine.submit_answer("purpose", "Clean up desktop")
        assert success is True
        assert error is None
    
    def test_submit_invalid_question(self, engine):
        success, error = engine.submit_answer("nonexistent", "value")
        assert success is False
        assert "Unknown question" in error
    
    def test_depth_validation(self, engine):
        success, error = engine.submit_answer("depth", 3)
        assert success is True
        
        success, error = engine.submit_answer("depth", 0)
        assert success is False
        assert "between 1 and 10" in error
        
        success, error = engine.submit_answer("depth", 11)
        assert success is False
        
        success, error = engine.submit_answer("depth", "abc")
        assert success is False
    
    def test_advance_step(self, engine):
        engine.submit_answer("purpose", "Sort project files")
        success, error = engine.advance_step()
        assert success is True
        assert engine.get_current_step() == QueryStep.STEP_2_STRUCTURE
    
    def test_advance_without_answer(self, engine):
        success, error = engine.advance_step()
        assert success is False
        assert "Missing answer" in error
    
    def test_full_workflow(self, engine):
        engine.submit_answer("purpose", "Sort project files")
        engine.advance_step()
        
        engine.submit_answer("structure", "By date (year/month/day)")
        engine.advance_step()
        
        engine.submit_answer("depth", 4)
        engine.advance_step()
        
        engine.submit_answer("exclude_patterns", "*.tmp,*.bak")
        engine.submit_answer("exclude_dirs", ".git,node_modules")
        engine.submit_answer("include_hidden", "No")
        engine.advance_step()
        
        engine.submit_answer("dry_run", "Yes, preview first")
        
        progress = engine.get_progress()
        assert progress["is_complete"] is True
    
    def test_compile_intent(self, engine):
        engine.submit_answer("purpose", "Sort project files")
        engine.advance_step()
        
        engine.submit_answer("structure", "By date (year/month/day)")
        engine.advance_step()
        
        engine.submit_answer("depth", 5)
        engine.advance_step()
        
        engine.submit_answer("exclude_patterns", "*.tmp")
        engine.submit_answer("exclude_dirs", "node_modules")
        engine.submit_answer("include_hidden", "Yes")
        engine.advance_step()
        
        engine.submit_answer("dry_run", "Yes, preview first")
        
        intent = engine.compile_intent()
        assert intent.max_depth == 5
        assert "*.tmp" in intent.exclude_patterns
        assert "node_modules" in intent.exclude_dirs
        assert intent.include_hidden is True
        assert intent.dry_run is True
    
    def test_go_to_step(self, engine):
        success = engine.go_to_step(QueryStep.STEP_3_DEPTH)
        assert success is True
        assert engine.get_current_step() == QueryStep.STEP_3_DEPTH
    
    def test_invalid_step(self, engine):
        success = engine.go_to_step("invalid")
        assert success is False
    
    def test_get_step_questions(self, engine):
        questions = engine.get_step_questions(QueryStep.STEP_4_EXCLUSIONS)
        assert len(questions) == 3
    
    def test_get_answers(self, engine):
        engine.submit_answer("purpose", "test purpose")
        answers = engine.get_answers()
        assert answers["purpose"] == "test purpose"
    
    def test_get_answers_list(self, engine):
        engine.submit_answer("purpose", "test")
        answers = engine.get_answers_list()
        assert len(answers) == 1
        assert "question_id" in answers[0]
    
    def test_reset(self, engine):
        engine.submit_answer("purpose", "test")
        engine.advance_step()
        engine.reset()
        
        progress = engine.get_progress()
        assert progress["current_step_index"] == 0
        assert len(engine.get_answers()) == 0
    
    def test_to_dict(self, engine):
        engine.submit_answer("purpose", "test")
        d = engine.to_dict()
        assert "progress" in d
        assert "answers" in d
        assert "intent" in d


class TestGuidedQueryIntegration:
    def test_full_workflow_to_json(self, engine):
        engine.submit_answer("purpose", "Clean up a cluttered desktop")
        engine.advance_step()
        
        engine.submit_answer("structure", "By file type or format")
        engine.advance_step()
        
        engine.submit_answer("depth", 3)
        engine.advance_step()
        
        engine.submit_answer("exclude_patterns", "*.tmp,*.log")
        engine.submit_answer("exclude_dirs", ".git")
        engine.submit_answer("include_hidden", "No")
        engine.advance_step()
        
        engine.submit_answer("dry_run", "Yes, preview first")
        
        json_str = guided_query_to_json(engine)
        parsed = json.loads(json_str)
        
        assert parsed["progress"]["is_complete"] is True
        assert "intent" in parsed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
