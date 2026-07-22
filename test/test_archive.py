"""
Unit tests for the daily archive feature in todo_manager.

Run with: pytest test/test_archive.py -v
"""

import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

import todo_manager


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path):
    """Run each test in an isolated temp directory."""
    with patch.object(todo_manager, "DATA_DIR", tmp_path), \
         patch.object(todo_manager, "DATA_FILE", tmp_path / "todos.json"), \
         patch.object(todo_manager, "ARCHIVE_DIR", tmp_path / "archive"):
        yield tmp_path


@pytest.fixture
def todos_json(tmp_path):
    """Create a minimal todos.json with two sample todos."""
    data = [
        {
            "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "text": "Task A",
            "comment": "",
            "done": False,
            "priority": "high",
            "created_at": "2026-07-20T10:00:00",
            "version": 2,
            "delivery_date": "2026-08-01",
        },
        {
            "id": "11111111-2222-3333-4444-555555555555",
            "text": "Task B",
            "comment": "with comment",
            "done": True,
            "priority": "low",
            "created_at": "2026-07-21T12:30:00",
            "version": 1,
        },
    ]
    path = tmp_path / "todos.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def test_ensure_archive_creates_directory(isolated_data_dir):
    archive = isolated_data_dir / "archive"
    assert not archive.exists()
    todo_manager._ensure_archive_exists()
    assert archive.is_dir()


def test_archive_today_creates_file(todos_json, isolated_data_dir):
    archive = isolated_data_dir / "archive"
    today = date.today()
    expected = archive / f"todo_{today.strftime('%Y%m%d')}.json"

    todo_manager._archive_today_if_needed()

    assert expected.is_file()
    content = json.loads(expected.read_text(encoding="utf-8"))
    assert len(content) == 2
    assert content[0]["id"] == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def test_archive_today_preserves_original_file(todos_json, isolated_data_dir):
    original = isolated_data_dir / "todos.json"
    mtime_before = original.stat().st_mtime

    todo_manager._archive_today_if_needed()

    assert original.stat().st_mtime == mtime_before
    content = json.loads(original.read_text(encoding="utf-8"))
    assert len(content) == 2


def test_archive_today_noop_when_already_exists(todos_json, isolated_data_dir):
    archive = isolated_data_dir / "archive"
    today = date.today()
    archive_file = archive / f"todo_{today.strftime('%Y%m%d')}.json"

    todo_manager._archive_today_if_needed()
    archive_file.write_text("[]", encoding="utf-8")
    mtime = archive_file.stat().st_mtime

    todo_manager._archive_today_if_needed()

    assert archive_file.read_text(encoding="utf-8") == "[]"
    assert archive_file.stat().st_mtime == mtime


def test_archive_today_handles_missing_todos_file(isolated_data_dir):
    today = date.today()
    expected = isolated_data_dir / "archive" / f"todo_{today.strftime('%Y%m%d')}.json"

    todo_manager._archive_today_if_needed()

    assert expected.is_file()
    assert json.loads(expected.read_text(encoding="utf-8")) == []


def test_archive_today_handles_corrupt_todos_file(isolated_data_dir):
    (isolated_data_dir / "todos.json").write_text("{invalid json!!!", encoding="utf-8")
    today = date.today()
    expected = isolated_data_dir / "archive" / f"todo_{today.strftime('%Y%m%d')}.json"

    todo_manager._archive_today_if_needed()

    assert expected.is_file()
    assert json.loads(expected.read_text(encoding="utf-8")) == []


def test_read_all_triggers_archive(isolated_data_dir):
    today = date.today()
    archive = isolated_data_dir / "archive"
    expected = archive / f"todo_{today.strftime('%Y%m%d')}.json"

    todo_manager._read_all()

    assert expected.is_file()


def test_read_all_returns_empty_list_when_no_file(isolated_data_dir):
    result = todo_manager._read_all()
    assert result == []
