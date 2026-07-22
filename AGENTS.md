# AGENTS.md

## Project Overview

A Python/Streamlit todo application designed to run in Docker on a Raspberry Pi with data persisted via a Samba share.

## Tech Stack

- **Language**: Python 3.12
- **UI Framework**: Streamlit (>=1.38.0)
- **Testing**: pytest (>=8.0.0)
- **Containerization**: Docker + Docker Compose

## Project Structure

```
app.py                 # Streamlit UI (add, list, filter, detail dialog, edit, delete)
todo_cls.py            # Todo dataclass (model with validation)
todo_manager.py        # Data access layer (CRUD operations backed by JSON file)
requirements.txt       # Python dependencies (streamlit, pytest)
Dockerfile             # Python 3.11-slim image, runs Streamlit on port 8501
docker-compose.yml     # Mounts host folder as /data for persistent todos.json
test/
  todos.json           # Sample data for retro-compatibility tests
  test_todos.py        # Schema validation tests
```

## Architecture

- **Model** (`todo_cls.py`): `Todo` dataclass with validation, serialization, and constants (`VALID_PRIORITIES`, `VALID_VERSIONS`, `LEGACY_DELIVERY_DATE`)
  - `to_dict()` — Serializes to a plain dict
  - `from_dict(data)` — Deserializes from a dict; raises `NotImplementedError` if `version` is missing
  - `get_delivery_date()` — Returns `delivery_date` or `LEGACY_DELIVERY_DATE` fallback for v1 todos
- **UI Layer** (`app.py`): Streamlit web application handling user interactions
- **Data Layer** (`todo_manager.py`): Pure data-access module with CRUD operations
  - Reads/writes single JSON file (`todos.json`)
  - Atomic writes (temp file + `os.replace`)
  - Data directory configurable via `TODO_DATA_DIR` env var (default: `/data`)
  - All reads/writes go through this module only

## Data Schema

Todo objects in `todos.json`:

| Field           | Type    | Values/Format                          |
|-----------------|---------|----------------------------------------|
| `id`            | string  | UUID v4 (`a1b2c3d4-e5f6-...`)         |
| `text`          | string  | Non-empty, stripped whitespace         |
| `comment`       | string  | Optional notes (default: `""`)         |
| `done`          | boolean | Completion status (default: `false`)   |
| `priority`      | string  | `"high"`, `"normal"`, or `"low"`       |
| `created_at`    | string  | ISO 8601 (`2026-07-14T10:00:00`)      |
| `version`       | int     | `1` or `2` (default: `1`)             |
| `delivery_date` | string  | ISO 8601 date (`2026-07-20`), v2 only |

### Version Rules

- **Version 1**: Legacy todos without delivery_date. Must NOT have a `delivery_date` field.
- **Version 2**: Todos with delivery_date. MUST have a `delivery_date` field.
- Version is hidden from the UI and cannot be modified by the user.
- Version is determined at creation and remains fixed throughout the todo's lifecycle.
- All todos created from the app are version 2 (with delivery_date).
- `update_delivery_date` auto-sets version to 2 when a non-legacy date is provided.

## Key Functions (todo_manager.py)

- `_ensure_store()` — Creates data dir/file if missing
- `_read_all()` — Reads full JSON array from disk, returns `list[Todo]`
- `_write_all(todos)` — Atomic write to disk, accepts `list[Todo]`
- `list_todos()` — Returns all todos sorted newest-first
- `add_todo(text, priority, comment, delivery_date)` — Creates new Todo; if delivery_date provided, creates version 2
- `set_done(todo_id, done)` — Marks todo as done/not done
- `update_comment(todo_id, comment)` — Updates comment field
- `update_delivery_date(todo_id, delivery_date)` — Updates delivery date, auto-sets version to 2
- `delete_todo(todo_id)` — Removes todo by ID

## Testing

Run tests:
```bash
python -m pytest test/test_todos.py -v
```

### Test Coverage

19 retro-compatibility tests covering:
- Schema structure (list type, required fields, no unknown fields)
- Field types (UUID, string, bool, priority enum, ISO 8601)
- Data integrity (unique IDs, all priorities, both done states)
- Version validation (v1/v2 constraints, crash tests)

### Adding New Features

When adding new fields to the todo schema:

1. Add the field to the `Todo` dataclass in `todo_cls.py`
2. Update `REQUIRED_FIELDS` in `test/test_todos.py`
3. Add the new field to `test/todos.json` sample data
4. Add a type validation test for the new field
5. Update `test_no_extra_unknown_fields` if needed

## Conventions

- No comments in code unless explicitly requested
- Follow existing code style and patterns
- Prefer editing existing files over creating new ones
- Atomic file writes for data integrity
- Environment variables for configuration (e.g., `TODO_DATA_DIR`)

## Commands

- **Run app**: `streamlit run app.py` (or via Docker)
- **Run tests**: `python -m pytest test/test_todos.py -v`
- **Install deps**: `pip install -r requirements.txt`
