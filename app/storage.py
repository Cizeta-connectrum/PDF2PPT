import json
import os
import threading
import uuid
from datetime import datetime, timezone

_DEFAULT_DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "apps.json")
_lock = threading.Lock()


def _data_file() -> str:
    return os.environ.get("APPS_DATA_FILE", _DEFAULT_DATA_FILE)


def _load() -> list:
    path = _data_file()
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _save(apps: list) -> None:
    path = _data_file()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(apps, f, ensure_ascii=False, indent=2)


def list_apps() -> list:
    with _lock:
        return sorted(_load(), key=lambda a: a["created_at"])


def add_app(name: str, url: str) -> dict:
    app_record = {
        "id": uuid.uuid4().hex,
        "name": name,
        "url": url,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with _lock:
        apps = _load()
        apps.append(app_record)
        _save(apps)
    return app_record


def delete_app(app_id: str) -> bool:
    with _lock:
        apps = _load()
        remaining = [a for a in apps if a["id"] != app_id]
        if len(remaining) == len(apps):
            return False
        _save(remaining)
        return True
