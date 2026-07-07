import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))


class FakeResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


SAMPLE_CSV = "name,url\nKakeibo,https://kakeibo.example.com\nTodo,https://todo.example.com\n"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("SHEET_CSV_URL", "https://docs.google.com/spreadsheets/d/e/fake/pub?output=csv")

    import importlib
    import app as app_module
    import storage as storage_module
    importlib.reload(storage_module)
    importlib.reload(app_module)

    with patch.object(app_module.storage, "requests") as mock_requests:
        mock_requests.get.return_value = FakeResponse(SAMPLE_CSV)

        app_module.app.config["TESTING"] = True
        with app_module.app.test_client() as c:
            yield c


def test_dashboard_page_renders(client):
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "アプリ一覧".encode() in response.data


def test_list_apps_returns_rows_from_csv(client):
    response = client.get("/api/apps")
    assert response.status_code == 200
    assert response.get_json() == [
        {"name": "Kakeibo", "url": "https://kakeibo.example.com"},
        {"name": "Todo", "url": "https://todo.example.com"},
    ]


def test_list_apps_skips_incomplete_rows(monkeypatch):
    monkeypatch.setenv("SHEET_CSV_URL", "https://docs.google.com/spreadsheets/d/e/fake/pub?output=csv")

    import importlib
    import app as app_module
    import storage as storage_module
    importlib.reload(storage_module)
    importlib.reload(app_module)

    csv_with_gap = "name,url\nGood,https://good.example.com\n,https://missing-name.example.com\nNoUrl,\n"
    with patch.object(app_module.storage, "requests") as mock_requests:
        mock_requests.get.return_value = FakeResponse(csv_with_gap)
        app_module.app.config["TESTING"] = True
        with app_module.app.test_client() as c:
            response = c.get("/api/apps")
            assert response.get_json() == [{"name": "Good", "url": "https://good.example.com"}]


def test_list_apps_without_config_returns_error(monkeypatch):
    monkeypatch.delenv("SHEET_CSV_URL", raising=False)

    import importlib
    import app as app_module
    import storage as storage_module
    importlib.reload(storage_module)
    importlib.reload(app_module)

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        response = c.get("/api/apps")
        assert response.status_code == 502
