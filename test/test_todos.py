"""
Retro-compatibility tests for todos.json schema.

These tests ensure that the data format remains valid across code changes.
Run with: pytest test/test_todos.py -v
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path

import pytest

SAMPLE_FILE = Path(__file__).parent / "todos.json"

VALID_PRIORITIES = {"high", "normal", "low"}
REQUIRED_FIELDS = {"id", "text", "comment", "done", "priority", "created_at", "version"}


@pytest.fixture
def todos():
    with open(SAMPLE_FILE, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_todo():
    """Return a single valid todo dict for unit checks (version 1)."""
    return {
        "id": str(uuid.uuid4()),
        "text": "Sample task",
        "comment": "",
        "done": False,
        "priority": "normal",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "version": 1,
    }


# --- Schema structure tests ---


def test_todos_is_a_list(todos):
    assert isinstance(todos, list)


def test_todos_is_non_empty(todos):
    assert len(todos) > 0, "Sample file should contain at least one todo"


def test_all_required_fields_present(todos):
    for i, todo in enumerate(todos):
        missing = REQUIRED_FIELDS - set(todo.keys())
        assert not missing, f"Todo at index {i} is missing fields: {missing}"


def test_no_extra_unknown_fields(todos):
    """Future fields should be added to this set or this test updated."""
    known = REQUIRED_FIELDS.copy()
    v2_known = known | {"delivery_date"}
    for i, todo in enumerate(todos):
        expected = v2_known if todo.get("version") == 2 else known
        extra = set(todo.keys()) - expected
        assert not extra, f"Todo at index {i} has unexpected fields: {extra}"


# --- Field type tests ---


def test_id_is_valid_uuid(todos):
    for todo in todos:
        parsed = uuid.UUID(todo["id"])
        assert str(parsed) == todo["id"], f"ID '{todo['id']}' is not a canonical UUID string"


def test_text_is_non_empty_string(todos):
    for todo in todos:
        assert isinstance(todo["text"], str), f"text must be str, got {type(todo['text']).__name__}"
        assert len(todo["text"].strip()) > 0, f"text must not be blank: {todo['text']!r}"


def test_comment_is_string(todos):
    for todo in todos:
        assert isinstance(todo["comment"], str), f"comment must be str, got {type(todo['comment']).__name__}"


def test_done_is_bool(todos):
    for todo in todos:
        assert isinstance(todo["done"], bool), f"done must be bool, got {type(todo['done']).__name__}"


def test_priority_is_valid(todos):
    for todo in todos:
        assert todo["priority"] in VALID_PRIORITIES, (
            f"priority must be one of {VALID_PRIORITIES}, got '{todo['priority']}'"
        )


def test_created_at_is_iso8601(todos):
    for todo in todos:
        assert isinstance(todo["created_at"], str)
        # Should parse without error (basic check)
        datetime.fromisoformat(todo["created_at"])


def test_version_is_valid(todos):
    for todo in todos:
        assert todo["version"] in {1, 2}, f"version must be 1 or 2, got {todo['version']}"


def test_v1_todos_have_no_delivery_date(todos):
    for todo in todos:
        if todo["version"] == 1:
            assert "delivery_date" not in todo, (
                f"version 1 todo '{todo['text']}' must not have delivery_date"
            )


def test_v2_todos_have_delivery_date(todos):
    for todo in todos:
        if todo["version"] == 2:
            assert "delivery_date" in todo, (
                f"version 2 todo '{todo['text']}' must have delivery_date"
            )


def test_v1_with_delivery_date_crashes():
    """Version 1 todo with delivery_date should raise ValueError."""
    from todo_cls import Todo
    with pytest.raises(ValueError, match="version 1 todos must not have a delivery_date"):
        Todo(
            text="Bad v1",
            version=1,
            delivery_date="2026-08-01",
        )


def test_v2_without_delivery_date_crashes():
    """Version 2 todo without delivery_date should raise ValueError."""
    from todo_cls import Todo
    with pytest.raises(ValueError, match="version 2 todos must have a delivery_date"):
        Todo(
            text="Bad v2",
            version=2,
        )


def test_both_versions_in_sample(todos):
    versions = {t["version"] for t in todos}
    assert 1 in versions and 2 in versions, "Sample should include both version 1 and version 2 todos"


# --- Data integrity tests ---


def test_all_ids_unique(todos):
    ids = [t["id"] for t in todos]
    assert len(ids) == len(set(ids)), "Duplicate IDs found"


def test_priorities_in_sample_cover_all_values(todos):
    priorities = {t["priority"] for t in todos}
    assert priorities == VALID_PRIORITIES, f"Sample should cover all priorities, got {priorities}"


def test_both_done_states_present(todos):
    done_states = {t["done"] for t in todos}
    assert True in done_states and False in done_states, "Sample should include both done and not-done todos"


def test_comments_cover_empty_and_nonempty(todos):
    comments = [t["comment"] for t in todos]
    assert "" in comments, "Sample should include at least one empty comment"
    assert any(c for c in comments), "Sample should include at least one non-empty comment"
