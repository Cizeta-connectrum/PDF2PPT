import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("APPS_DATA_FILE", str(tmp_path / "apps.json"))

    import importlib
    import app as app_module
    import storage as storage_module
    importlib.reload(storage_module)
    importlib.reload(app_module)

    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c


def test_dashboard_page_renders(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "アプリ一覧".encode() in response.data


def test_converter_page_renders(client):
    response = client.get("/convert-tool")
    assert response.status_code == 200
    assert "PDF".encode() in response.data


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
