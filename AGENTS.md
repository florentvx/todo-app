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
app.py                 # Streamlit UI (todo + calendar pages, dialogs, navigation)
todo_cls.py            # Todo dataclass (model with validation)
todo_manager.py        # Data access layer (CRUD operations backed by JSON file)
calendar_cls.py        # CalendarEntry dataclass (model with validation, CALENDAR_COLORS)
calendar_manager.py    # Calendar data access layer (CRUD operations backed by JSON file)
requirements.txt       # Python dependencies (streamlit, pytest)
.streamlit/config.toml # Disables Streamlit fast reruns (prevents stale widgets on slow hosts)
Dockerfile             # Python 3.11-slim image, runs Streamlit on port 8501
docker-compose.yml     # Mounts host folder as /data for persistent todos.json
test/
  todos.json           # Sample data for retro-compatibility tests
  test_todos.py        # Schema validation tests (19 tests)
  test_archive.py      # Archive feature unit tests (8 tests)
  test_calendar.py     # Calendar model + manager unit tests (24 tests)
```

## Architecture

- **Model** (`todo_cls.py`): `Todo` dataclass with validation, serialization, and constants (`VALID_PRIORITIES`, `VALID_VERSIONS`, `LEGACY_DELIVERY_DATE`)
  - `to_dict()` — Serializes to a plain dict
  - `from_dict(data)` — Deserializes from a dict; raises `NotImplementedError` if `version` is missing
  - `get_delivery_date()` — Returns `delivery_date` or `LEGACY_DELIVERY_DATE` fallback for v1 todos
- **UI Layer** (`app.py`): Streamlit web application handling user interactions
  - **Todo page**: Add, list, filter, sort, detail dialog (with notes + delivery date), delete
  - **Calendar page**: Month grid with navigation, click any day to add/edit entry via dialog
    - Day cells are hand-built raw HTML via `st.markdown(..., unsafe_allow_html=True)`
    - Title/notes are `html.escape()`d and newlines encoded as `&#10;` (tooltip) / `<br>` (cell) before insertion — otherwise CommonMark terminates the raw HTML block at a blank line and the rest of the markup leaks into the grid as visible text
    - Cells with notes but no title show a small black circle (`#212529`, 8px) at the bottom-right as an indicator; the tooltip still shows the notes
  - Manual tab navigation via a `st.sidebar.radio` (no `st.navigation`/`st.Page`)
  - All page content renders inside a single module-level `st.empty()` root container that is explicitly cleared (`root.empty()`) at the start of every rerun, then rebuilt — this forces stale widgets/elements to be deleted manually instead of relying on the frontend's (unreliable on slow hosts like the Pi) cleanup deltas
  - Dialog invocations live at module level, after the root container block
  - Uses `@st.dialog` for edit modals
- **Data Layer — Todos** (`todo_manager.py`): Pure data-access module with CRUD operations
  - Reads/writes single JSON file (`todos.json`)
  - Atomic writes (temp file + `os.replace`)
  - Data directory configurable via `TODO_DATA_DIR` env var (default: `/data`)
  - All reads/writes go through this module only
  - **Daily archive**: Automatically creates a backup of `todos.json` in `archive/todo_yyyymmdd.json` before each read (one per day)
- **Data Layer — Calendar** (`calendar_manager.py`): Pure data-access module for calendar entries
  - Reads/writes single JSON file (`calendar_entries.json`)
  - Same data directory as todos

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

## Calendar Schema

CalendarEntry objects in `calendar_entries.json`:

| Field   | Type   | Values/Format                          |
|---------|--------|----------------------------------------|
| `date`  | string | ISO 8601 date (`2026-07-20`)          |
| `title` | string | Entry title                            |
| `notes` | string | Optional notes (default: `""`)         |
| `color` | string | One of `CALENDAR_COLORS` keys          |
| `id`    | string | UUID v4                                |

`CALENDAR_COLORS`: `default` (#ffffff), `blue` (#228be6), `green` (#40c057), `red` (#fa5252), `yellow` (#fcc419), `purple` (#7950f2), `orange` (#fd7e14)

## Key Functions (todo_manager.py)

- `_ensure_store()` — Creates data dir/file if missing
- `_ensure_archive_exists()` — Creates archive directory if missing
- `_archive_today_if_needed()` — Creates today's archive file if not already present
- `_read_all()` — Reads full JSON array from disk, returns `list[Todo]` (triggers daily archive)
- `_write_all(todos)` — Atomic write to disk, accepts `list[Todo]`
- `list_todos()` — Returns all todos sorted newest-first
- `add_todo(text, priority, comment, delivery_date)` — Creates new Todo; if delivery_date provided, creates version 2
- `set_done(todo_id, done)` — Marks todo as done/not done
- `update_comment(todo_id, comment)` — Updates comment field
- `update_delivery_date(todo_id, delivery_date)` — Updates delivery date, auto-sets version to 2
- `delete_todo(todo_id)` — Removes todo by ID

## Key Functions (calendar_manager.py)

- `_ensure_store()` — Creates data dir/file if missing
- `_read_all()` — Reads full JSON array from disk, returns `list[CalendarEntry]`
- `_write_all(entries)` — Atomic write to disk
- `list_entries()` — Returns all entries
- `get_entry(date_str)` — Returns entry for a given date or None
- `save_entry(date_str, title, notes, color)` — Creates or updates entry for a date
- `delete_entry(date_str)` — Removes entry by date

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

8 archive tests covering:
- Archive directory creation
- Archive file creation with correct content
- Original file preservation
- No-op when archive already exists
- Missing/corrupt `todos.json` handling
- `_read_all` triggering archive

24 calendar tests covering:
- CalendarEntry model defaults, to_dict, from_dict, roundtrip, valid UUID
- CALENDAR_COLORS key/hex validation
- calendar_manager: store creation, list, get, save (create/update), delete, all colors, independence, overwrite, corrupt file handling, auto-creation on write

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

- **Virtual env**: `C:/workspace/repos/todo-app/.venv/Scripts/python.exe`
- **Run app**: `streamlit run app.py` (or via Docker)
- **Run tests**: `python -m pytest test/test_todos.py -v` (uses .venv)
- **Run archive tests**: `python -m pytest test/test_archive.py -v`
- **Run all tests**: `python -m pytest test/ -v`
- **Install deps**: `pip install -r requirements.txt`

### Using .venv

Always use the venv Python at `C:/workspace/repos/todo-app/.venv/Scripts/python.exe` or activate via `source .venv/Scripts/activate`. Tests and `streamlit run` commands use the venv automatically when run from the project root.
