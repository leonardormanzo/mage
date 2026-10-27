from sqlalchemy import select

from app.database.models import AuditLog, ExtractedRecord, MaterialMovement
from tests.conftest import login


def test_audio_like_full_flow_updates_stock_rdo_and_query(client, db_session):
    me = login(client)
    project_id = me["projects"][0]["id"]

    received = client.post(
        f"/api/projects/{project_id}/messages",
        json={"content": "Usamos 20 sacos.", "message_type": "audio", "external_id": "audio-e2e-1"},
    )
    assert received.status_code == 200
    data = received.json()
    record_id = data["record_id"]
    assert data["record_status"] == "incomplete"
    assert "material" in data["bot"].lower()

    answer_material = client.post(
        f"/api/projects/{project_id}/records/{record_id}/answer", json={"answer": "Cimento"}
    )
    assert answer_material.status_code == 200
    assert "serviço" in answer_material.json()["bot"].lower()

    answer_service = client.post(
        f"/api/projects/{project_id}/records/{record_id}/answer",
        json={"answer": "Alvenaria do segundo pavimento"},
    )
    assert answer_service.json()["record_status"] == "awaiting_confirmation"
    assert "20" in answer_service.json()["bot"]

    confirmation = client.post(f"/api/projects/{project_id}/records/{record_id}/confirm")
    assert confirmation.status_code == 200
    assert confirmation.json()["balance"] == 80.0
    assert confirmation.json()["record_status"] == "included_in_rdo"

    report_data = client.get(f"/api/projects/{project_id}/reports/today").json()
    assert len(report_data["items"]) == 1
    report_id = report_data["report"]["id"]
    assert (
        client.post(
            f"/api/projects/{project_id}/reports/{report_id}/close?allow_incomplete=true"
        ).status_code
        == 403
    )

    login(client, "mestre@arc.local")
    closed = client.post(
        f"/api/projects/{project_id}/reports/{report_id}/close?allow_incomplete=true"
    )
    assert closed.status_code == 200
    assert closed.json()["status"] == "closed"
    pdf = client.get(f"/api/projects/{project_id}/reports/{report_id}.pdf")
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")

    query = client.post(
        f"/api/projects/{project_id}/query", json={"question": "Qual é o saldo de cimento?"}
    )
    assert query.status_code == 200
    assert "80" in query.json()["answer"]
    assert query.json()["route"] == "structured"
    assert len(query.json()["sources"]) == 2

    record = db_session.get(ExtractedRecord, record_id)
    assert record.status == "closed"
    assert db_session.scalar(
        select(MaterialMovement).where(MaterialMovement.source_record_id == record_id)
    )
    assert db_session.scalar(select(AuditLog).where(AuditLog.entity_id == record_id))


def test_message_idempotency(client):
    me = login(client)
    project_id = me["projects"][0]["id"]
    payload = {"content": "Usamos 2 sacos de cimento na alvenaria", "external_id": "same-id"}
    first = client.post(f"/api/projects/{project_id}/messages", json=payload)
    second = client.post(f"/api/projects/{project_id}/messages", json=payload)
    assert first.status_code == second.status_code == 200
    assert second.json()["duplicate"] is True
    assert first.json()["message_id"] == second.json()["message_id"]


def test_close_requires_explicit_incomplete_decision(client):
    me = login(client, "mestre@arc.local")
    project_id = me["projects"][0]["id"]
    login(client, "trabalhador@arc.local")
    response = client.post(
        f"/api/projects/{project_id}/messages",
        json={"content": "Executamos limpeza do térreo", "external_id": "service-1"},
    )
    record_id = response.json()["record_id"]
    client.post(f"/api/projects/{project_id}/records/{record_id}/confirm")
    report_id = client.get(f"/api/projects/{project_id}/reports/today").json()["report"]["id"]
    login(client, "mestre@arc.local")
    blocked = client.post(f"/api/projects/{project_id}/reports/{report_id}/close")
    assert blocked.status_code == 409
    assert "Clima" in blocked.json()["detail"]["pending"]
