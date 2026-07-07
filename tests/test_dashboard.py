import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSheet:
    """In-memory stand-in for the Google Sheet the GAS web app manages."""

    def __init__(self):
        self.apps = []

    def get(self, _url, params=None, timeout=None):
        return FakeResponse(list(self.apps))

    def post(self, _url, json=None, timeout=None):
        action = json.get("action")
        if action == "add":
            import uuid
            from datetime import datetime, timezone

            record = {
                "id": uuid.uuid4().hex,
                "name": json["name"],
                "url": json["url"],
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self.apps.append(record)
            return FakeResponse(record, 201)
        if action == "delete":
            before = len(self.apps)
            self.apps = [a for a in self.apps if a["id"] != json["id"]]
            success = len(self.apps) < before
            return FakeResponse({"success": success})
        return FakeResponse({"error": "invalid_action"})


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("GAS_WEBAPP_URL", "https://script.google.com/macros/s/fake/exec")
    monkeypatch.setenv("GAS_API_TOKEN", "test-token")

    import importlib
    import app as app_module
    import storage as storage_module
    importlib.reload(storage_module)
    importlib.reload(app_module)

    fake_sheet = FakeSheet()
    with patch.object(app_module.storage, "requests") as mock_requests:
        mock_requests.get.side_effect = fake_sheet.get
        mock_requests.post.side_effect = fake_sheet.post

        app_module.app.config["TESTING"] = True
        with app_module.app.test_client() as c:
            yield c


def test_dashboard_page_renders(client):
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "アプリ一覧".encode() in response.data


def test_list_apps_initially_empty(client):
    response = client.get("/api/apps")
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_and_list_app(client):
    response = client.post("/api/apps", json={"name": "My App", "url": "https://example.com"})
    assert response.status_code == 201
    created = response.get_json()
    assert created["name"] == "My App"
    assert created["url"] == "https://example.com"
    assert "id" in created

    response = client.get("/api/apps")
    apps = response.get_json()
    assert len(apps) == 1
    assert apps[0]["id"] == created["id"]


def test_create_app_rejects_missing_name(client):
    response = client.post("/api/apps", json={"name": "", "url": "https://example.com"})
    assert response.status_code == 400


def test_create_app_rejects_invalid_url(client):
    response = client.post("/api/apps", json={"name": "Bad", "url": "not-a-url"})
    assert response.status_code == 400


def test_delete_app(client):
    created = client.post("/api/apps", json={"name": "To Delete", "url": "https://example.com"}).get_json()

    response = client.delete(f"/api/apps/{created['id']}")
    assert response.status_code == 204

    apps = client.get("/api/apps").get_json()
    assert apps == []


def test_delete_missing_app_returns_404(client):
    response = client.delete("/api/apps/does-not-exist")
    assert response.status_code == 404


def test_list_apps_without_config_returns_error(monkeypatch):
    monkeypatch.delenv("GAS_WEBAPP_URL", raising=False)
    monkeypatch.delenv("GAS_API_TOKEN", raising=False)

    import importlib
    import app as app_module
    import storage as storage_module
    importlib.reload(storage_module)
    importlib.reload(app_module)

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        response = c.get("/api/apps")
        assert response.status_code == 502
