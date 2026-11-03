from sqlalchemy import select

from app.database.models import AuditLog, ExtractedRecord, MaterialMovement
from tests.conftest import login

CONSUMPTION = "Usamos 20 sacos de cimento na alvenaria"
RECEIPT = "Recebemos 10 sacos de cimento para a alvenaria"


def _confirmed_record(client, project_id: str, content: str, external_id: str) -> str:
    sent = client.post(
        f"/api/projects/{project_id}/messages",
        json={"content": content, "external_id": external_id},
    ).json()
    assert sent["record_status"] == "awaiting_confirmation"
    confirmed = client.post(f"/api/projects/{project_id}/records/{sent['record_id']}/confirm")
    assert confirmed.status_code == 200
    return sent["record_id"]


def _cement_balance(client, project_id: str) -> float:
    materials = client.get(f"/api/projects/{project_id}/materials").json()
    return next(item["balance"] for item in materials if item["name"] == "Cimento")


def _setup(client) -> tuple[str, str]:
    me = login(client)
    project_id = me["projects"][0]["id"]
    return project_id, _confirmed_record(client, project_id, CONSUMPTION, "corr-1")


def test_worker_cancels_pending_record(client, db_session):
    me = login(client)
    project_id = me["projects"][0]["id"]
    sent = client.post(
        f"/api/projects/{project_id}/messages", json={"content": "Usamos 20 sacos."}
    ).json()
    url = f"/api/projects/{project_id}/records/{sent['record_id']}/cancel"

    cancelled = client.post(url)
    assert cancelled.status_code == 200
    assert cancelled.json()["record_status"] == "cancelled"
    assert client.post(url).status_code == 409
    assert db_session.scalar(
        select(AuditLog).where(
            AuditLog.entity_id == sent["record_id"], AuditLog.operation == "cancelled"
        )
    )


def test_cancel_refuses_confirmed_record(client):
    project_id, record_id = _setup(client)
    response = client.post(f"/api/projects/{project_id}/records/{record_id}/cancel")
    assert response.status_code == 409


def test_reverse_restores_balance_and_hides_record_from_rdo(client):
    project_id, record_id = _setup(client)
    assert _cement_balance(client, project_id) == 80.0
    url = f"/api/projects/{project_id}/records/{record_id}/reverse"

    assert client.post(url, json={"reason": "Lançado na obra errada"}).status_code == 403

    login(client, "mestre@arc.local")
    assert client.post(url, json={"reason": "x"}).status_code == 422
    reversed_ = client.post(url, json={"reason": "Lançado na obra errada"})
    assert reversed_.status_code == 200
    assert reversed_.json()["record_status"] == "reversed"
    assert reversed_.json()["balance"] == 100.0
    assert _cement_balance(client, project_id) == 100.0
    assert client.post(url, json={"reason": "Lançado na obra errada"}).status_code == 409

    report = client.get(f"/api/projects/{project_id}/reports/today").json()
    assert report["items"] == []


def test_reverse_of_receipt_removes_stock(client):
    me = login(client)
    project_id = me["projects"][0]["id"]
    record_id = _confirmed_record(client, project_id, RECEIPT, "corr-receipt")
    assert _cement_balance(client, project_id) == 110.0

    login(client, "mestre@arc.local")
    client.post(
        f"/api/projects/{project_id}/records/{record_id}/reverse",
        json={"reason": "Entrega recusada"},
    )
    assert _cement_balance(client, project_id) == 100.0


def test_totals_ignore_reversed_movements(client):
    project_id, record_id = _setup(client)
    login(client, "mestre@arc.local")
    client.post(
        f"/api/projects/{project_id}/records/{record_id}/reverse",
        json={"reason": "Lançado na obra errada"},
    )
    answer = client.post(
        f"/api/projects/{project_id}/query",
        json={"question": "Quanto cimento foi consumido?"},
    ).json()
    assert "0 sacos" in answer["answer"]


def test_correct_replaces_record_and_keeps_history(client, db_session):
    project_id, record_id = _setup(client)
    url = f"/api/projects/{project_id}/records/{record_id}/correct"
    assert client.post(url, json={"reason": "Quantidade errada", "quantity": "15"}).status_code == 403

    login(client, "mestre@arc.local")
    assert client.post(url, json={"reason": "Quantidade errada", "quantity": "0"}).status_code == 422
    corrected = client.post(url, json={"reason": "Quantidade errada", "quantity": "15"})
    assert corrected.status_code == 200
    body = corrected.json()
    assert body["record_status"] == "included_in_rdo"
    assert body["balance"] == 85.0

    old = db_session.get(ExtractedRecord, record_id)
    new = db_session.get(ExtractedRecord, body["record_id"])
    assert old.status == "corrected"
    assert new.corrected_from_id == record_id
    assert new.quantity == 15
    assert new.material_name == old.material_name

    items = client.get(f"/api/projects/{project_id}/reports/today").json()["items"]
    assert [item["id"] for item in items] == [new.id]
    assert items[0]["quantity"] == 15
    movements = db_session.scalars(
        select(MaterialMovement).where(MaterialMovement.source_record_id == record_id)
    ).all()
    assert sorted(m.movement_type for m in movements) == ["consumption", "reversal"]
    assert db_session.scalar(
        select(AuditLog).where(AuditLog.entity_id == record_id, AuditLog.operation == "corrected")
    )


def test_correct_requires_a_change(client):
    project_id, record_id = _setup(client)
    login(client, "mestre@arc.local")
    response = client.post(
        f"/api/projects/{project_id}/records/{record_id}/correct",
        json={"reason": "Sem alteração nenhuma"},
    )
    assert response.status_code == 422


def test_closed_report_blocks_reverse_until_reopened(client):
    project_id, record_id = _setup(client)
    report_id = client.get(f"/api/projects/{project_id}/reports/today").json()["report"]["id"]
    login(client, "mestre@arc.local")
    client.post(f"/api/projects/{project_id}/reports/{report_id}/close?allow_incomplete=true")
    url = f"/api/projects/{project_id}/records/{record_id}/reverse"
    blocked = client.post(url, json={"reason": "Lançado na obra errada"})
    assert blocked.status_code == 409
    assert "RDO" in blocked.json()["detail"]

    login(client, "engenheiro@arc.local")
    client.post(
        f"/api/projects/{project_id}/reports/{report_id}/reopen",
        json={"reason": "Correção de lançamento"},
    )
    assert client.post(url, json={"reason": "Lançado na obra errada"}).status_code == 200


def test_service_record_can_be_corrected_without_stock(client):
    me = login(client)
    project_id = me["projects"][0]["id"]
    record_id = _confirmed_record(client, project_id, "Executamos limpeza do térreo", "corr-svc")
    login(client, "mestre@arc.local")
    response = client.post(
        f"/api/projects/{project_id}/records/{record_id}/correct",
        json={"reason": "Local incorreto", "service": "Limpeza do primeiro pavimento"},
    )
    assert response.status_code == 200
    assert response.json()["balance"] is None
    items = client.get(f"/api/projects/{project_id}/reports/today").json()["items"]
    assert [item["service"] for item in items] == ["Limpeza do primeiro pavimento"]
