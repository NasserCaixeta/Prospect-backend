def test_create_manual_lead_with_name_and_phone(client, admin_headers):
    response = client.post(
        "/leads",
        headers=admin_headers,
        json={"name": "Barbearia Central", "phone": "(19) 99999-9999", "city": "Campinas"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Barbearia Central"
    assert body["normalized_phone"] == "19999999999"
    assert body["current_status"] == "novo"


def test_create_manual_lead_rejects_name_without_contact_or_source(client, admin_headers):
    response = client.post("/leads", headers=admin_headers, json={"name": "Sem Contato"})

    assert response.status_code == 422


def test_list_leads_filters_by_city_status_and_phone(client, admin_headers):
    client.post(
        "/leads",
        headers=admin_headers,
        json={"name": "A", "phone": "111", "city": "Campinas"},
    )
    created = client.post(
        "/leads",
        headers=admin_headers,
        json={"name": "B", "phone": "222", "city": "Santos"},
    ).json()
    client.patch(
        f"/leads/{created['id']}",
        headers=admin_headers,
        json={"current_status": "interessado"},
    )

    response = client.get(
        "/leads?city=Santos&status=interessado&with_phone=true",
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["name"] == "B"


def test_upsert_scraped_lead_deduplicates_by_google_maps_url(db_session):
    from app.services.leads import upsert_scraped_lead

    first, action = upsert_scraped_lead(
        db_session,
        {
            "name": "Oficina Boa",
            "city": "Campinas",
            "phone": "19999999999",
            "google_maps_url": "https://maps.google.com/?cid=1",
        },
    )
    second, second_action = upsert_scraped_lead(
        db_session,
        {
            "name": "Oficina Boa Atualizada",
            "city": "Campinas",
            "phone": "19999999999",
            "google_maps_url": "https://maps.google.com/?cid=1",
            "website_url": "https://oficina.test",
        },
    )

    assert action == "created"
    assert second_action == "updated"
    assert second.id == first.id
    assert second.website_url == "https://oficina.test"


def test_upsert_scraped_lead_deduplicates_by_normalized_identity(db_session):
    from app.services.leads import upsert_scraped_lead

    first, _ = upsert_scraped_lead(
        db_session,
        {
            "name": "Clínica Estética Bela",
            "city": "Campinas",
            "phone": "(19) 99999-9999",
            "google_maps_url": "https://maps.google.com/?cid=1",
        },
    )
    second, action = upsert_scraped_lead(
        db_session,
        {
            "name": "Clinica Estetica Bela",
            "city": "Campinas",
            "phone": "19 99999-9999",
            "google_maps_url": "https://maps.google.com/?cid=2",
        },
    )

    assert action == "updated"
    assert second.id == first.id


def test_lead_response_marks_probable_whatsapp(client, admin_headers):
    response = client.post(
        "/leads",
        headers=admin_headers,
        json={"name": "Lead WhatsApp", "phone": "(19) 99999-9999"},
    )

    assert response.status_code == 201
    assert response.json()["whatsapp_probable"] is True
