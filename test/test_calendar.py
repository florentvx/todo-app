"""
Unit tests for calendar_cls and calendar_manager.

Run with: pytest test/test_calendar.py -v
"""

import json
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

import calendar_manager
from calendar_cls import CalendarEntry, CALENDAR_COLORS


# ============================================================
# CalendarEntry model tests
# ============================================================


def test_calendar_entry_defaults():
    entry = CalendarEntry(date="2026-08-15")
    assert entry.date == "2026-08-15"
    assert entry.title == ""
    assert entry.notes == ""
    assert entry.color == "default"
    assert uuid.UUID(entry.id)


def test_calendar_entry_all_fields():
    entry = CalendarEntry(
        date="2026-08-20",
        title="Team standup",
        notes="Daily sync at 10am",
        color="blue",
        id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    )
    assert entry.date == "2026-08-20"
    assert entry.title == "Team standup"
    assert entry.notes == "Daily sync at 10am"
    assert entry.color == "blue"
    assert entry.id == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def test_calendar_entry_to_dict():
    entry = CalendarEntry(
        date="2026-08-20",
        title="Team standup",
        notes="Daily sync at 10am",
        color="blue",
        id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    )
    d = entry.to_dict()
    assert d == {
        "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "date": "2026-08-20",
        "title": "Team standup",
        "notes": "Daily sync at 10am",
        "color": "blue",
    }


def test_calendar_entry_from_dict_all_fields():
    data = {
        "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "date": "2026-08-20",
        "title": "Team standup",
        "notes": "Daily sync at 10am",
        "color": "blue",
    }
    entry = CalendarEntry.from_dict(data)
    assert entry.id == "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    assert entry.date == "2026-08-20"
    assert entry.title == "Team standup"
    assert entry.notes == "Daily sync at 10am"
    assert entry.color == "blue"


def test_calendar_entry_from_dict_minimal():
    data = {"date": "2026-08-20"}
    entry = CalendarEntry.from_dict(data)
    assert uuid.UUID(entry.id)
    assert entry.date == "2026-08-20"
    assert entry.title == ""
    assert entry.notes == ""
    assert entry.color == "default"


def test_calendar_entry_from_dict_missing_id_generates_new():
    data = {"date": "2026-08-20", "title": "Test"}
    entry = CalendarEntry.from_dict(data)
    assert uuid.UUID(entry.id)


def test_calendar_entry_roundtrip():
    original = CalendarEntry(
        date="2026-08-20",
        title="Roundtrip",
        notes="Should survive",
        color="green",
    )
    data = original.to_dict()
    restored = CalendarEntry.from_dict(data)
    assert restored.date == original.date
    assert restored.title == original.title
    assert restored.notes == original.notes
    assert restored.color == original.color
    assert restored.id == original.id


def test_calendar_entry_id_is_valid_uuid():
    for color in CALENDAR_COLORS:
        entry = CalendarEntry(date="2026-08-01", color=color)
        parsed = uuid.UUID(entry.id)
        assert str(parsed) == entry.id


def test_calendar_colors_has_expected_keys():
    assert set(CALENDAR_COLORS.keys()) == {
        "default", "red", "blue", "green", "yellow", "orange", "purple",
    }
    for name, hex_color in CALENDAR_COLORS.items():
        assert hex_color.startswith("#"), f"{name}: {hex_color} should be a hex color"
        assert len(hex_color) == 7, f"{name}: {hex_color} should be 7 chars"


# ============================================================
# calendar_manager tests
# ============================================================

SAMPLE_ENTRIES = [
    {"id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeee01", "date": "2026-08-15", "title": "Meeting", "notes": "Room 3", "color": "blue"},
    {"id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeee02", "date": "2026-08-20", "title": "Deadline", "notes": "", "color": "red"},
    {"id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeee03", "date": "2026-08-25", "title": "Lunch", "notes": "Italian place", "color": "default"},
]


@pytest.fixture(autouse=True)
def isolated_cal_data_dir(tmp_path):
    """Redirect calendar_manager DATA_DIR and DATA_FILE to temp."""
    with patch.object(calendar_manager, "DATA_DIR", tmp_path), \
         patch.object(calendar_manager, "DATA_FILE", tmp_path / "calendar_entries.json"):
        yield tmp_path


@pytest.fixture
def seeded_store(tmp_path):
    """Pre-populate calendar_entries.json with three sample entries."""
    path = tmp_path / "calendar_entries.json"
    path.write_text(json.dumps(SAMPLE_ENTRIES, indent=2), encoding="utf-8")
    return path


def test_ensure_store_creates_empty_file(isolated_cal_data_dir):
    data_file = isolated_cal_data_dir / "calendar_entries.json"
    assert not data_file.exists()
    calendar_manager._ensure_store()
    assert data_file.is_file()
    assert json.loads(data_file.read_text(encoding="utf-8")) == []


def test_list_entries_empty(isolated_cal_data_dir):
    entries = calendar_manager.list_entries()
    assert entries == []


def test_list_entries_returns_all(seeded_store):
    entries = calendar_manager.list_entries()
    assert len(entries) == 3
    dates = {e.date for e in entries}
    assert dates == {"2026-08-15", "2026-08-20", "2026-08-25"}


def test_get_entry_found(seeded_store):
    entry = calendar_manager.get_entry("2026-08-20")
    assert entry is not None
    assert entry.title == "Deadline"
    assert entry.color == "red"


def test_get_entry_not_found(seeded_store):
    entry = calendar_manager.get_entry("2026-09-01")
    assert entry is None


def test_save_entry_creates_new(isolated_cal_data_dir):
    calendar_manager.save_entry("2026-09-01", "New event", "some notes", "green")
    entry = calendar_manager.get_entry("2026-09-01")
    assert entry is not None
    assert entry.title == "New event"
    assert entry.notes == "some notes"
    assert entry.color == "green"


def test_save_entry_updates_existing(seeded_store):
    calendar_manager.save_entry("2026-08-20", "Updated deadline", "New details", "purple")
    entry = calendar_manager.get_entry("2026-08-20")
    assert entry.title == "Updated deadline"
    assert entry.notes == "New details"
    assert entry.color == "purple"
    entries = calendar_manager.list_entries()
    assert len(entries) == 3


def test_save_entry_default_values(seeded_store):
    calendar_manager.save_entry("2026-09-05", "No extras")
    entry = calendar_manager.get_entry("2026-09-05")
    assert entry.title == "No extras"
    assert entry.notes == ""
    assert entry.color == "default"


def test_delete_entry_removes(seeded_store):
    calendar_manager.delete_entry("2026-08-20")
    assert calendar_manager.get_entry("2026-08-20") is None
    entries = calendar_manager.list_entries()
    assert len(entries) == 2


def test_delete_entry_nonexistent_is_noop(seeded_store):
    calendar_manager.delete_entry("2099-01-01")
    assert len(calendar_manager.list_entries()) == 3


def test_save_all_colors(isolated_cal_data_dir):
    for color in CALENDAR_COLORS:
        calendar_manager.save_entry(f"2026-07-{ord(color[0])%28+1:02d}", f"Color {color}", "", color)
    entries = calendar_manager.list_entries()
    assert len(entries) == len(CALENDAR_COLORS)
    saved_colors = {e.color for e in entries}
    assert saved_colors == set(CALENDAR_COLORS.keys())


def test_multiple_entries_independent(isolated_cal_data_dir):
    calendar_manager.save_entry("2026-08-01", "First", "note a", "red")
    calendar_manager.save_entry("2026-08-02", "Second", "note b", "blue")
    calendar_manager.save_entry("2026-08-03", "Third", "", "default")

    e1 = calendar_manager.get_entry("2026-08-01")
    assert e1.title == "First" and e1.color == "red"

    e2 = calendar_manager.get_entry("2026-08-02")
    assert e2.title == "Second" and e2.color == "blue"

    e3 = calendar_manager.get_entry("2026-08-03")
    assert e3.title == "Third" and e3.color == "default"

    calendar_manager.delete_entry("2026-08-02")
    assert calendar_manager.get_entry("2026-08-01") is not None
    assert calendar_manager.get_entry("2026-08-02") is None
    assert calendar_manager.get_entry("2026-08-03") is not None


def test_overwrite_same_date(isolated_cal_data_dir):
    calendar_manager.save_entry("2026-08-01", "Original", "first version", "red")
    calendar_manager.save_entry("2026-08-01", "Overwritten", "second version", "blue")
    entries = calendar_manager.list_entries()
    assert len(entries) == 1
    assert entries[0].title == "Overwritten"
    assert entries[0].notes == "second version"
    assert entries[0].color == "blue"


def test_corrupt_file_returns_empty(isolated_cal_data_dir):
    data_file = isolated_cal_data_dir / "calendar_entries.json"
    data_file.write_text("{invalid json!!!", encoding="utf-8")
    entries = calendar_manager.list_entries()
    assert entries == []


def test_data_file_created_on_first_write(isolated_cal_data_dir):
    data_file = isolated_cal_data_dir / "calendar_entries.json"
    assert not data_file.exists()
    calendar_manager.save_entry("2026-08-01", "Triggers creation")
    assert data_file.is_file()
    content = json.loads(data_file.read_text(encoding="utf-8"))
    assert len(content) == 1
