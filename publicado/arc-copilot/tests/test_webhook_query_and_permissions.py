from tests.conftest import login


def test_mock_webhook_routes_phone_and_is_idempotent(client):
    payload = {
        "external_id": "wamid.demo-1",
        "origin_phone": "+5511988881111",
        "destination_phone": "+5511999990001",
        "sender_email": "trabalhador@arc.local",
        "message_type": "text",
        "content": "Recebemos 10 sacos de cimento para a alvenaria",
    }
    first = client.post("/api/webhooks/whatsapp/mock", json=payload)
    second = client.post("/api/webhooks/whatsapp/mock", json=payload)
    assert first.status_code == 200
    assert second.json()["duplicate"] is True


def test_documental_query_cites_project_document(client):
    me = login(client)
    project_id = me["projects"][0]["id"]
    result = client.post(
        f"/api/projects/{project_id}/query",
        json={"question": "O que conferir antes da concretagem?"},
    )
    assert result.status_code == 200
    body = result.json()
    assert body["route"] == "documental"
    assert "armaduras" in body["answer"]
    assert body["sources"][0]["type"] == "document"


def test_stock_adjustment_requires_engineer(client):
    me = login(client, "mestre@arc.local")
    project_id = me["projects"][0]["id"]
    material_id = client.get(f"/api/projects/{project_id}/materials").json()[0]["id"]
    payload = {
        "material_id": material_id,
        "movement_type": "adjustment_positive",
        "quantity": "3",
        "unit": "sacos",
        "reason": "Inventário físico",
    }
    assert client.post(f"/api/projects/{project_id}/movements", json=payload).status_code == 403
    login(client, "engenheiro@arc.local")
    assert client.post(f"/api/projects/{project_id}/movements", json=payload).status_code == 200


def test_no_evidence_response(client):
    me = login(client)
    project_id = me["projects"][0]["id"]
    result = client.post(
        f"/api/projects/{project_id}/query",
        json={"question": "Qual foi a ocorrência com o guindaste amarelo?"},
    ).json()
    assert result["confidence"] == 0.0
    assert result["sources"] == []
    assert "Não encontrei" in result["answer"]
