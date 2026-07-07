import os

import requests

GAS_WEBAPP_URL = os.environ.get("GAS_WEBAPP_URL")
GAS_API_TOKEN = os.environ.get("GAS_API_TOKEN")

REQUEST_TIMEOUT = 10


class StorageError(RuntimeError):
    pass


def _require_config() -> str:
    if not GAS_WEBAPP_URL:
        raise StorageError(
            "GAS_WEBAPP_URL が設定されていません。GoogleスプレッドシートのGAS Webアプリを"
            "デプロイし、環境変数を設定してください。"
        )
    return GAS_WEBAPP_URL


def _unwrap(data):
    if isinstance(data, dict) and data.get("error"):
        raise StorageError(str(data["error"]))
    return data


def list_apps() -> list:
    url = _require_config()
    resp = requests.get(url, params={"token": GAS_API_TOKEN}, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    apps = _unwrap(resp.json())
    return sorted(apps, key=lambda a: a["created_at"])


def add_app(name: str, url: str) -> dict:
    endpoint = _require_config()
    resp = requests.post(
        endpoint,
        json={"action": "add", "name": name, "url": url, "token": GAS_API_TOKEN},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return _unwrap(resp.json())


def delete_app(app_id: str) -> bool:
    endpoint = _require_config()
    resp = requests.post(
        endpoint,
        json={"action": "delete", "id": app_id, "token": GAS_API_TOKEN},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    data = _unwrap(resp.json())
    return bool(data.get("success"))
