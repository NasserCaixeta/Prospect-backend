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


def test_create_manual_lead_analyzes_bad_website(db_session):
    from app.models.enums import DigitalPresence, SiteAnalysisStatus
    from app.models.site_analysis import SiteAnalysis
    from app.schemas.lead import LeadCreate
    from app.services.leads import create_manual_lead
    from app.services.site_analysis import WebsiteAnalysisResult

    def fake_analyzer(url: str | None) -> WebsiteAnalysisResult:
        return WebsiteAnalysisResult(
            status=SiteAnalysisStatus.SITE_RUIM,
            score=20,
            issues=["missing_https"],
            analysis_data={"url": url},
        )

    lead = create_manual_lead(
        db_session,
        LeadCreate(name="Lead Com Site Ruim", website_url="http://example.com"),
        website_analyzer=fake_analyzer,
    )

    analyses = db_session.query(SiteAnalysis).filter_by(lead_id=lead.id).all()
    assert lead.digital_presence == DigitalPresence.SITE_RUIM
    assert lead.potential_score == 20
    assert len(analyses) == 1
    assert analyses[0].website_url == "http://example.com"
    assert analyses[0].status == SiteAnalysisStatus.SITE_RUIM
    assert analyses[0].issues == ["missing_https"]


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
    from app.models.enums import SiteAnalysisStatus
    from app.services.leads import upsert_scraped_lead
    from app.services.site_analysis import WebsiteAnalysisResult

    def fake_analyzer(url: str | None) -> WebsiteAnalysisResult:
        return WebsiteAnalysisResult(
            status=SiteAnalysisStatus.SITE_OK,
            score=90,
            issues=[],
            analysis_data={"url": url},
        )

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
        website_analyzer=fake_analyzer,
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


def test_upsert_scraped_lead_analyzes_ok_website(db_session):
    from app.models.enums import DigitalPresence, SiteAnalysisStatus
    from app.models.site_analysis import SiteAnalysis
    from app.services.leads import upsert_scraped_lead
    from app.services.site_analysis import WebsiteAnalysisResult

    def fake_analyzer(url: str | None) -> WebsiteAnalysisResult:
        return WebsiteAnalysisResult(
            status=SiteAnalysisStatus.SITE_OK,
            score=90,
            issues=[],
            analysis_data={"url": url, "title": "Empresa"},
        )

    lead, action = upsert_scraped_lead(
        db_session,
        {
            "name": "Lead Scrapeado",
            "google_maps_url": "https://maps.google.com/?cid=123",
            "website_url": "https://example.com",
            "phone": "(19) 99999-9999",
        },
        website_analyzer=fake_analyzer,
    )

    analyses = db_session.query(SiteAnalysis).filter_by(lead_id=lead.id).all()
    assert action == "created"
    assert lead.digital_presence == DigitalPresence.SITE_OK
    assert len(analyses) == 1
    assert analyses[0].status == SiteAnalysisStatus.SITE_OK


def test_lead_response_marks_probable_whatsapp(client, admin_headers):
    response = client.post(
        "/leads",
        headers=admin_headers,
        json={"name": "Lead WhatsApp", "phone": "(19) 99999-9999"},
    )

    assert response.status_code == 201
    assert response.json()["whatsapp_probable"] is True


def test_update_lead_analyzes_added_website(db_session):
    from app.models.enums import DigitalPresence, SiteAnalysisStatus, UserRole
    from app.models.site_analysis import SiteAnalysis
    from app.schemas.lead import LeadCreate, LeadUpdate
    from app.services.leads import create_manual_lead, update_lead
    from app.services.site_analysis import WebsiteAnalysisResult
    from app.services.users import create_user

    user = create_user(
        db_session,
        email="site-update@example.com",
        password="secret123",
        name="Site Update",
        role=UserRole.ADMIN,
    )
    lead = create_manual_lead(
        db_session,
        LeadCreate(name="Lead Sem Site", phone="(19) 3333-4444"),
    )

    def fake_analyzer(url: str | None) -> WebsiteAnalysisResult:
        return WebsiteAnalysisResult(
            status=SiteAnalysisStatus.SITE_OK,
            score=95,
            issues=[],
            analysis_data={"url": url},
        )

    updated = update_lead(
        db_session,
        lead.id,
        LeadUpdate(website_url="https://example.com"),
        user,
        website_analyzer=fake_analyzer,
    )

    analyses = db_session.query(SiteAnalysis).filter_by(lead_id=lead.id).all()
    assert updated.digital_presence == DigitalPresence.SITE_OK
    assert len(analyses) == 1
