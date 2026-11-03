from dataclasses import replace

from app.core.config import get_settings
from app.core.throttle import MAX_FAILURES
from tests.conftest import login

PASSWORD_OK = "ArcDemo123!"


def _attempt(client, email: str, password: str):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def test_login_is_blocked_after_repeated_failures(client):
    for _ in range(MAX_FAILURES):
        assert _attempt(client, "mestre@arc.local", "errada").status_code == 401
    blocked = _attempt(client, "mestre@arc.local", PASSWORD_OK)
    assert blocked.status_code == 429
    assert "Aguarde" in blocked.json()["detail"]


def test_throttle_is_per_account(client):
    for _ in range(MAX_FAILURES):
        _attempt(client, "mestre@arc.local", "errada")
    assert _attempt(client, "trabalhador@arc.local", PASSWORD_OK).status_code == 200


def test_successful_login_clears_the_failure_count(client):
    for _ in range(MAX_FAILURES - 1):
        _attempt(client, "mestre@arc.local", "errada")
    assert _attempt(client, "mestre@arc.local", PASSWORD_OK).status_code == 200
    for _ in range(MAX_FAILURES - 1):
        assert _attempt(client, "mestre@arc.local", "errada").status_code == 401


def test_demo_mode_caps_upload_size(client, monkeypatch):
    demo = replace(get_settings(), demo_mode=True)
    monkeypatch.setattr("app.api.routes.get_settings", lambda: demo)
    me = login(client, "engenheiro@arc.local")
    project_id = me["projects"][0]["id"]
    too_big = b"a" * (demo.upload_limit_mb * 1024 * 1024 + 1)
    response = client.post(
        f"/api/projects/{project_id}/documents",
        files={"file": ("grande.txt", too_big, "text/plain")},
    )
    assert response.status_code == 413
