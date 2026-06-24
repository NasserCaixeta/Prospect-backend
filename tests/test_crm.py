def test_create_lead_event_adds_note(client, admin_headers):
    lead = client.post(
        "/leads",
        headers=admin_headers,
        json={"name": "Barbearia Central", "phone": "19999999999"},
    ).json()

    response = client.post(
        f"/leads/{lead['id']}/events",
        headers=admin_headers,
        json={"event_type": "note", "note": "Ligar amanhã"},
    )

    assert response.status_code == 201
    assert response.json()["note"] == "Ligar amanhã"


def test_status_update_creates_history_event(client, admin_headers):
    lead = client.post(
        "/leads",
        headers=admin_headers,
        json={"name": "Barbearia Central", "phone": "19999999999"},
    ).json()

    response = client.patch(
        f"/leads/{lead['id']}",
        headers=admin_headers,
        json={"current_status": "contatado"},
    )
    events = client.get(f"/leads/{lead['id']}/events", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["current_status"] == "contatado"
    assert events.json()[0]["old_status"] == "novo"
    assert events.json()[0]["new_status"] == "contatado"
