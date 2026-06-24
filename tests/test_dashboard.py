def test_dashboard_metrics_and_breakdowns(client, admin_headers):
    lead_a = client.post(
        "/leads",
        headers=admin_headers,
        json={
            "name": "A",
            "phone": "111",
            "city": "Campinas",
            "segment": "barbearia",
            "website_url": "https://a.test",
        },
    ).json()
    client.patch(
        f"/leads/{lead_a['id']}",
        headers=admin_headers,
        json={"current_status": "contatado", "digital_presence": "site_ruim"},
    )
    lead_b = client.post(
        "/leads",
        headers=admin_headers,
        json={"name": "B", "phone": "222", "city": "Santos", "segment": "restaurante"},
    ).json()
    client.patch(
        f"/leads/{lead_b['id']}",
        headers=admin_headers,
        json={"current_status": "interessado"},
    )

    metrics = client.get("/dashboard/metrics", headers=admin_headers)
    breakdown = client.get("/dashboard/breakdown", headers=admin_headers)

    assert metrics.status_code == 200
    assert metrics.json()["total_leads"] == 2
    assert metrics.json()["leads_without_site"] == 1
    assert metrics.json()["bad_site_leads"] == 1
    assert metrics.json()["leads_with_phone"] == 2
    assert metrics.json()["contacted_leads"] == 1
    assert metrics.json()["interested_leads"] == 1
    assert breakdown.json()["by_city"]["Campinas"] == 1
    assert breakdown.json()["by_segment"]["barbearia"] == 1
    assert breakdown.json()["by_status"]["interessado"] == 1


def test_admin_can_patch_and_read_settings(client, admin_headers):
    response = client.patch(
        "/settings",
        headers=admin_headers,
        json={"scraper": {"default_limit": 10, "max_limit": 20}},
    )
    read = client.get("/settings", headers=admin_headers)

    assert response.status_code == 200
    assert read.json()["scraper"]["max_limit"] == 20
