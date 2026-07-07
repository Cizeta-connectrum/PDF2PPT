import csv
import io
import os

import requests

SHEET_CSV_URL = os.environ.get("SHEET_CSV_URL")
REQUEST_TIMEOUT = 10


class StorageError(RuntimeError):
    pass


def list_apps() -> list:
    if not SHEET_CSV_URL:
        raise StorageError(
            "SHEET_CSV_URL が設定されていません。GoogleスプレッドシートをCSVとして公開し、"
            "そのURLを環境変数に設定してください。"
        )

    resp = requests.get(SHEET_CSV_URL, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()

    reader = csv.DictReader(io.StringIO(resp.text))
    apps = []
    for row in reader:
        name = (row.get("name") or "").strip()
        url = (row.get("url") or "").strip()
        if not name or not url:
            continue
        apps.append({"name": name, "url": url})
    return apps
