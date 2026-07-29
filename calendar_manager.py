import json
import os
from pathlib import Path

from calendar_cls import CalendarEntry

DATA_DIR = Path(os.environ.get("TODO_DATA_DIR", "./data"))
DATA_FILE = DATA_DIR / "calendar_entries.json"


def _ensure_store():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def _read_all() -> list[CalendarEntry]:
    _ensure_store()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return [CalendarEntry.from_dict(d) for d in json.load(f)]
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _write_all(entries: list[CalendarEntry]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = DATA_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump([e.to_dict() for e in entries], f, indent=2, ensure_ascii=False)
    os.replace(tmp, DATA_FILE)


def list_entries() -> list[CalendarEntry]:
    return _read_all()


def get_entry(date_str: str) -> CalendarEntry | None:
    for e in _read_all():
        if e.date == date_str:
            return e
    return None


def save_entry(date_str: str, title: str, notes: str = "", color: str = "default"):
    entries = _read_all()
    for e in entries:
        if e.date == date_str:
            e.title = title
            e.notes = notes
            e.color = color
            _write_all(entries)
            return
    entries.append(CalendarEntry(date=date_str, title=title, notes=notes, color=color))
    _write_all(entries)


def delete_entry(date_str: str):
    entries = _read_all()
    entries = [e for e in entries if e.date != date_str]
    _write_all(entries)
