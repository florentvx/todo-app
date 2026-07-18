# Todo Streamlit App

A minimal Streamlit todo list backed by a JSON file on your Samba share,
running in Docker on the Pi.

## 1. Create the folder on your Samba share

On the Pi, find where your Samba share lives on disk (check `/etc/samba/smb.conf`
for the `path =` line of the share you want to use), then create a subfolder:

```bash
sudo mkdir -p /srv/samba/shared/todo-app
sudo chown pi:pi /srv/samba/shared/todo-app   # or whatever user runs docker
```

(Adjust the path to match your actual Samba share location.)

## 2. Copy this project onto the Pi

Copy this whole folder to the Pi, e.g. via `scp` or by cloning from git,
into somewhere like `/home/pi/todo-streamlit`.

## 3. Point docker-compose at your Samba folder

Edit `docker-compose.yml` and change the volume line's left side to the
folder you made in step 1:

```yaml
volumes:
  - /srv/samba/shared/todo-app:/data
```

## 4. Build and run

```bash
cd todo-streamlit
docker compose up -d --build
```

The app will be available at `http://<pi-ip>:8501`.

## 5. Check logs / data

```bash
docker compose logs -f          # app logs
cat /srv/samba/shared/todo-app/todos.json   # the raw data file
```

## Data format

Todos are stored as a JSON array in `todos.json`:

```json
[
  {
    "id": "a1b2c3...",
    "text": "Buy milk",
    "done": false,
    "priority": "normal",
    "created_at": "2026-07-14T10:00:00"
  }
]
```

## Growing this later

- All data access lives in `todo_manager.py`. If you outgrow JSON
  (e.g. need concurrent multi-user writes or querying), swap that module's
  internals for SQLite without touching `app.py`.
- Add auth: Streamlit supports basic auth via a reverse proxy (e.g. nginx
  in front of the container) if you expose this beyond your LAN.
- Add categories/due dates: extend the todo dict in `todo_manager.add_todo`
  and the form in `app.py`.
