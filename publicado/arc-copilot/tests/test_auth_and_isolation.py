from sqlalchemy import select

from app.database.models import Project
from tests.conftest import login


def test_login_and_role(client):
    assert (
        client.post("/api/auth/login", json={"email": "x@x.com", "password": "x"}).status_code
        == 401
    )
    me = login(client)
    assert me["role"] == "worker"
    assert len(me["projects"]) == 1


def test_project_isolation_is_enforced_in_backend(client, db_session):
    me = login(client)
    allowed_id = me["projects"][0]["id"]
    restricted = db_session.scalar(select(Project).where(Project.code == "OR-002"))
    assert client.get(f"/api/projects/{allowed_id}/dashboard").status_code == 200
    assert client.get(f"/api/projects/{restricted.id}/dashboard").status_code == 404


def test_worker_cannot_view_audit(client):
    me = login(client)
    project_id = me["projects"][0]["id"]
    assert client.get(f"/api/projects/{project_id}/audit").status_code == 403
