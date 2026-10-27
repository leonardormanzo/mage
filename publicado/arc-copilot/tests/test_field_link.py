import hashlib
import hmac

from sqlalchemy import select

from app.database.models import FieldLink, Project, ProjectUser, User
from app.field import hash_token

TOKEN = "token-de-teste-bem-longo-0123456789"


def make_link(db, active=True):
    project = db.scalar(select(Project))
    user = User(
        company_id=project.company_id, name="Campo", email="campo-x@link.invalid",
        password_hash="x", role="worker",
    )
    db.add(user)
    db.flush()
    db.add(ProjectUser(company_id=project.company_id, project_id=project.id, user_id=user.id))
    link = FieldLink(
        company_id=project.company_id, project_id=project.id, user_id=user.id,
        token_hash=hash_token(TOKEN), label="t", active=active,
    )
    db.add(link)
    db.commit()
    return link


def test_page_requires_valid_active_link(client, db_session):
    assert client.get("/e/invalido").status_code == 404
    make_link(db_session, active=False)
    assert client.get(f"/e/{TOKEN}").status_code == 404


def test_full_flow_via_link_without_login(client, db_session):
    make_link(db_session)
    page = client.get(f"/e/{TOKEN}")
    assert page.status_code == 200 and "no-store" in page.headers["cache-control"]
    sent = client.post(f"/e/{TOKEN}/send", json={"content": "Usamos 20 sacos.", "sender": "Zé"}).json()
    rid = sent["record_id"]
    assert sent["record_status"] == "incomplete"
    client.post(f"/e/{TOKEN}/answer", json={"record_id": rid, "answer": "Cimento"})
    last = client.post(f"/e/{TOKEN}/answer", json={"record_id": rid, "answer": "Alvenaria"}).json()
    assert last["record_status"] == "awaiting_confirmation"
    done = client.post(f"/e/{TOKEN}/confirm", json={"record_id": rid}).json()
    assert done["record_status"] == "included_in_rdo"


def test_cancel_and_foreign_record_blocked(client, db_session):
    make_link(db_session)
    rid = client.post(f"/e/{TOKEN}/send", json={"content": "Usamos 5 sacos.", "sender": "Zé"}).json()["record_id"]
    assert client.post(f"/e/{TOKEN}/cancel", json={"record_id": rid}).json()["record_status"] == "cancelled"
    assert client.post(f"/e/{TOKEN}/confirm", json={"record_id": "nao-existe"}).status_code == 404


def test_link_gives_no_access_to_api(client, db_session):
    make_link(db_session)
    project = db_session.scalar(select(Project))
    assert client.get(f"/api/projects/{project.id}/materials").status_code == 401


def test_whatsapp_webhook_requires_signature(client):
    from app.core import config
    body = b'{"object":"whatsapp_business_account"}'
    assert client.post("/api/webhooks/whatsapp", content=body).status_code == 503
    object.__setattr__(config.get_settings(), "webhook_app_secret", "segredo")
    try:
        assert client.post("/api/webhooks/whatsapp", content=body).status_code == 403
        sig = "sha256=" + hmac.new(b"segredo", body, hashlib.sha256).hexdigest()
        ok = client.post("/api/webhooks/whatsapp", content=body, headers={"X-Hub-Signature-256": sig})
        assert ok.status_code == 200
    finally:
        object.__setattr__(config.get_settings(), "webhook_app_secret", None)
