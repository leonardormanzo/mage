from dataclasses import replace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.database.models import AuditLog, FieldLink, Project, ProjectUser, User
from app.field import hash_token
from app.main import app
from tests.conftest import login

NEW_USER = {
    "name": "Ana Souza",
    "email": "Ana.Souza@arc.local",
    "password": "SenhaForte123",
    "role": "master",
}


def _project_ids(db_session) -> dict[str, str]:
    return {p.code: p.id for p in db_session.scalars(select(Project)).all()}


def _create(client, db_session, **overrides):
    ids = _project_ids(db_session)
    payload = {**NEW_USER, "project_ids": [ids["RA-001"]], **overrides}
    return client.post("/api/users", json=payload)


@pytest.mark.parametrize("email", ["mestre@arc.local", "trabalhador@arc.local"])
def test_only_engineer_can_manage_users(client, email):
    login(client, email)
    assert client.get("/api/users").status_code == 403
    assert client.post("/api/users", json=NEW_USER).status_code == 403


def test_anonymous_cannot_list_users(client):
    assert client.get("/api/users").status_code == 401


def test_list_users_hides_password_hash(client):
    login(client, "engenheiro@arc.local")
    rows = client.get("/api/users").json()
    assert {row["email"] for row in rows} >= {"engenheiro@arc.local", "mestre@arc.local"}
    assert all("password" not in key for row in rows for key in row)


def test_engineer_creates_user_who_can_log_in(client, db_session):
    login(client, "engenheiro@arc.local")
    created = _create(client, db_session)
    assert created.status_code == 201
    body = created.json()
    assert body["email"] == "ana.souza@arc.local"
    assert body["role"] == "master"
    assert len(body["project_ids"]) == 1
    assert "password" not in str(body)

    with TestClient(app) as other:
        response = other.post(
            "/api/auth/login", json={"email": "ana.souza@arc.local", "password": "SenhaForte123"}
        )
        assert response.status_code == 200
        me = other.get("/api/me").json()
    assert me["role"] == "master"
    assert [p["code"] for p in me["projects"]] == ["RA-001"]


def test_create_rejects_duplicates_and_weak_input(client, db_session):
    login(client, "engenheiro@arc.local")
    assert _create(client, db_session).status_code == 201
    assert _create(client, db_session, email="ANA.SOUZA@arc.local").status_code == 409
    assert _create(client, db_session, email="outro@arc.local", password="curta").status_code == 422
    assert _create(client, db_session, email="semarroba", password="SenhaForte123").status_code == 422
    assert _create(client, db_session, email="x@arc.local", role="admin").status_code == 422
    assert _create(client, db_session, email="y@arc.local", project_ids=["nao-existe"]).status_code == 422


def test_deactivated_user_loses_access_immediately(client, db_session):
    login(client, "engenheiro@arc.local")
    user_id = _create(client, db_session).json()["id"]

    with TestClient(app) as other:
        other.post(
            "/api/auth/login", json={"email": "ana.souza@arc.local", "password": "SenhaForte123"}
        )
        assert other.get("/api/me").status_code == 200
        assert client.patch(f"/api/users/{user_id}", json={"active": False}).status_code == 200
        assert other.get("/api/me").status_code == 401
        denied = other.post(
            "/api/auth/login", json={"email": "ana.souza@arc.local", "password": "SenhaForte123"}
        )
        assert denied.status_code == 401


def test_engineer_cannot_lock_themselves_out(client):
    me = login(client, "engenheiro@arc.local")
    url = f"/api/users/{me['id']}"
    assert client.patch(url, json={"active": False}).status_code == 409
    assert client.patch(url, json={"role": "worker"}).status_code == 409
    assert client.patch(url, json={"name": "Marina C."}).status_code == 200


def test_update_role_and_project_assignment(client, db_session):
    login(client, "engenheiro@arc.local")
    ids = _project_ids(db_session)
    user_id = _create(client, db_session).json()["id"]
    updated = client.patch(
        f"/api/users/{user_id}",
        json={"role": "worker", "project_ids": [ids["RA-001"], ids["OR-002"]]},
    ).json()
    assert updated["role"] == "worker"
    assert sorted(updated["project_ids"]) == sorted(ids.values())

    narrowed = client.patch(f"/api/users/{user_id}", json={"project_ids": [ids["OR-002"]]}).json()
    assert narrowed["project_ids"] == [ids["OR-002"]]
    rows = db_session.scalars(select(ProjectUser).where(ProjectUser.user_id == user_id)).all()
    assert [row.project_id for row in rows] == [ids["OR-002"]]


def test_update_unknown_user_is_404(client):
    login(client, "engenheiro@arc.local")
    assert client.patch("/api/users/nao-existe", json={"name": "Fulano"}).status_code == 404


def test_password_reset_replaces_credentials_and_audits_without_secret(client, db_session):
    login(client, "engenheiro@arc.local")
    user_id = _create(client, db_session).json()["id"]
    reset = client.post(f"/api/users/{user_id}/password", json={"password": "NovaSenha4567"})
    assert reset.status_code == 204

    with TestClient(app) as other:
        old = other.post(
            "/api/auth/login", json={"email": "ana.souza@arc.local", "password": "SenhaForte123"}
        )
        new = other.post(
            "/api/auth/login", json={"email": "ana.souza@arc.local", "password": "NovaSenha4567"}
        )
        assert (old.status_code, new.status_code) == (401, 200)

    entries = db_session.scalars(select(AuditLog).where(AuditLog.entity_id == user_id)).all()
    assert {entry.operation for entry in entries} >= {"user_created", "password_reset"}
    assert "NovaSenha4567" not in str([(e.old_value, e.new_value, e.reason) for e in entries])


def test_password_reset_enforces_minimum_length(client, db_session):
    login(client, "engenheiro@arc.local")
    user_id = _create(client, db_session).json()["id"]
    assert client.post(f"/api/users/{user_id}/password", json={"password": "curta"}).status_code == 422


def test_field_link_stops_working_when_its_user_is_deactivated(client, db_session):
    login(client, "engenheiro@arc.local")
    project = db_session.scalar(select(Project))
    user = User(
        company_id=project.company_id,
        name="Campo",
        email="campo@link.invalid",
        password_hash="x",
        role="worker",
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(
        FieldLink(
            company_id=project.company_id,
            project_id=project.id,
            user_id=user.id,
            token_hash=hash_token("token-de-campo-0123456789-abcdef"),
            label="t",
        )
    )
    db_session.commit()
    with TestClient(app) as anonymous:
        assert anonymous.get("/e/token-de-campo-0123456789-abcdef").status_code == 200
        client.patch(f"/api/users/{user.id}", json={"active": False})
        assert anonymous.get("/e/token-de-campo-0123456789-abcdef").status_code == 404


def test_demo_mode_protects_seeded_accounts(client, monkeypatch, db_session):
    monkeypatch.setattr(
        "app.services.users.get_settings", lambda: replace(get_settings(), demo_mode=True)
    )
    login(client, "engenheiro@arc.local")
    master = db_session.scalar(select(User).where(User.email == "mestre@arc.local"))
    assert client.patch(f"/api/users/{master.id}", json={"active": False}).status_code == 403
    assert client.post(f"/api/users/{master.id}/password", json={"password": "OutraSenha123"}).status_code == 403
    assert client.patch(f"/api/users/{master.id}", json={"name": "Carlos M."}).status_code == 200
