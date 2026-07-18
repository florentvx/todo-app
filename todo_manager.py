"""
Data access layer for the todo list.

All reads/writes go through here, backed by a single JSON file.
Writes are atomic (write to a temp file, then os.replace) so a
concurrent read (e.g. someone browsing the Samba share) never sees
a half-written file.

If this ever needs to become a SQLite-backed store, only this file
should need to change - app.py just calls these functions.
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path

# Path to the JSON file, overridable via env var (set in docker-compose.yml)
DATA_DIR = Path(os.environ.get("TODO_DATA_DIR", "/data"))
DATA_FILE = DATA_DIR / "todos.json"


def _ensure_store():
    """Create the data dir/file if they don't exist yet."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        _write_all([])


def _read_all():
    _ensure_store()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        # File missing or mid-write from another process - treat as empty
        # rather than crashing the app.
        return []


def _write_all(todos):
    """Atomic write: write to a temp file in the same dir, then replace."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = DATA_FILE.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(todos, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, DATA_FILE)  # atomic on same filesystem


def list_todos():
    """Return all todos, newest first."""
    todos = _read_all()
    return sorted(todos, key=lambda t: t["created_at"], reverse=True)


def add_todo(text: str, priority: str = "normal", comment: str = ""):
    todos = _read_all()
    todos.append(
        {
            "id": str(uuid.uuid4()),
            "text": text.strip(),
            "comment": comment.strip(),
            "done": False,
            "priority": priority,
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    _write_all(todos)


def set_done(todo_id: str, done: bool):
    todos = _read_all()
    for t in todos:
        if t["id"] == todo_id:
            t["done"] = done
            break
    _write_all(todos)


def update_comment(todo_id: str, comment: str):
    todos = _read_all()
    for t in todos:
        if t["id"] == todo_id:
            t["comment"] = comment.strip()
            break
    _write_all(todos)


def delete_todo(todo_id: str):
    todos = _read_all()
    todos = [t for t in todos if t["id"] != todo_id]
    _write_all(todos)
