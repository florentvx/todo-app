import json
import os
from datetime import date
from pathlib import Path

from todo_cls import Todo, LEGACY_DELIVERY_DATE

DATA_DIR = Path(os.environ.get("TODO_DATA_DIR", "./data"))
DATA_FILE = DATA_DIR / "todos.json"
ARCHIVE_DIR = DATA_DIR / "archive"


def _ensure_archive_exists():
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)


def _archive_today_if_needed():
    _ensure_archive_exists()
    today = date.today()
    archive_file = ARCHIVE_DIR / f"todo_{today.strftime('%Y%m%d')}.json"
    if archive_file.exists():
        return
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            todos = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        todos = []
    with open(archive_file, "w", encoding="utf-8") as f:
        json.dump(todos, f, indent=2, ensure_ascii=False)


def _ensure_store():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        _write_all([])


def _read_all():
    _ensure_store()
    _archive_today_if_needed()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return [Todo.from_dict(t) for t in json.load(f)]
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _write_all(todos: list[Todo]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = DATA_FILE.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump([t.to_dict() for t in todos], f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, DATA_FILE)


def list_todos() -> list[Todo]:
    todos = _read_all()
    return sorted(todos, key=lambda t: t.created_at, reverse=True)


def add_todo(text: str, priority: str = "normal", comment: str = "", delivery_date: str | None = None):
    todos = _read_all()
    if delivery_date:
        todos.append(Todo(text=text, priority=priority, comment=comment, version=2, delivery_date=delivery_date))
    else:
        todos.append(Todo(text=text, priority=priority, comment=comment))
    _write_all(todos)


def set_done(todo_id: str, done: bool):
    todos = _read_all()
    for t in todos:
        if t.id == todo_id:
            t.done = done
            break
    _write_all(todos)


def update_comment(todo_id: str, comment: str):
    todos = _read_all()
    for t in todos:
        if t.id == todo_id:
            t.comment = comment.strip()
            break
    _write_all(todos)


def update_delivery_date(todo_id: str, delivery_date: str):
    todos = _read_all()
    for t in todos:
        if t.id == todo_id:
            _delivery_date = delivery_date.strip()
            if _delivery_date != LEGACY_DELIVERY_DATE:
                t.delivery_date = _delivery_date
                t.version = 2
            break
    _write_all(todos)


def delete_todo(todo_id: str):
    todos = _read_all()
    todos = [t for t in todos if t.id != todo_id]
    _write_all(todos)
