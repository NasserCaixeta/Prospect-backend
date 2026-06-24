class FakeScraper:
    def __init__(self, items=None, error=None):
        self.items = items or []
        self.error = error

    def search(self, *, city, state, segment, max_results):
        if self.error:
            raise self.error
        return self.items[:max_results]


def test_create_job_defaults_to_10_and_completes_with_no_results(client, admin_headers):
    response = client.post(
        "/search-jobs",
        headers=admin_headers,
        json={"city": "Campinas", "state": "SP", "segment": "barbearia"},
    )

    assert response.status_code == 201
    assert response.json()["max_results"] == 10
    assert response.json()["status"] in {"pending", "completed"}


def test_create_job_rejects_limit_above_20(client, admin_headers):
    response = client.post(
        "/search-jobs",
        headers=admin_headers,
        json={"city": "Campinas", "state": "SP", "segment": "barbearia", "max_results": 21},
    )

    assert response.status_code == 422


def test_cancel_job_sets_cancel_requested(client, admin_headers):
    created = client.post(
        "/search-jobs",
        headers=admin_headers,
        json={"city": "Campinas", "state": "SP", "segment": "barbearia"},
    ).json()

    response = client.post(f"/search-jobs/{created['id']}/cancel", headers=admin_headers)

    assert response.status_code == 200
    assert response.json()["cancel_requested"] is True


def test_run_search_job_saves_results(db_session):
    from app.models.enums import UserRole
    from app.services.search_jobs import create_search_job, list_search_job_results, run_search_job
    from app.services.users import create_user

    user = create_user(
        db_session,
        email="admin@example.com",
        password="secret123",
        name="Admin",
        role=UserRole.ADMIN,
    )
    job = create_search_job(
        db_session,
        city="Campinas",
        state="SP",
        segment="barbearia",
        max_results=10,
        created_by_user_id=user.id,
    )

    run_search_job(
        db_session,
        job.id,
        FakeScraper(
            [
                {
                    "name": "Barbearia Central",
                    "phone": "19999999999",
                    "google_maps_url": "https://maps.google.com/?cid=1",
                }
            ]
        ),
    )
    results = list_search_job_results(db_session, job.id)

    assert results[0].lead.name == "Barbearia Central"
    assert results[0].lead.city == "Campinas"
    assert results[0].lead.state == "SP"
    assert results[0].lead.segment == "barbearia"
    assert results[0].action == "created"


def test_run_search_job_preserves_partial_results_on_scraper_error(db_session):
    from app.models.enums import SearchJobStatus, UserRole
    from app.services.search_jobs import create_search_job, get_search_job, run_search_job
    from app.services.users import create_user

    user = create_user(
        db_session,
        email="admin@example.com",
        password="secret123",
        name="Admin",
        role=UserRole.ADMIN,
    )
    job = create_search_job(
        db_session,
        city="Campinas",
        state="SP",
        segment="barbearia",
        max_results=10,
        created_by_user_id=user.id,
    )

    run_search_job(db_session, job.id, FakeScraper(error=RuntimeError("blocked")))

    failed = get_search_job(db_session, job.id)
    assert failed.status == SearchJobStatus.FAILED
    assert failed.error_message == "blocked"


def test_parse_result_card_extracts_business_fields():
    from pathlib import Path

    from app.services.scraper import parse_result_card

    html = Path("tests/fixtures/google_maps_result.html").read_text()

    result = parse_result_card(html)

    assert result.name == "Barbearia Central"
    assert result.phone == "(19) 99999-9999"
    assert result.google_maps_url == "https://maps.google.com/?cid=123"
    assert result.website_url == "https://barbearia.test"
    assert result.rating == 4.7
    assert result.review_count == 82


def test_extract_brazilian_phone_from_detail_text():
    from app.services.scraper import extract_brazilian_phone

    assert extract_brazilian_phone("Telefone: (19) 99999-9999") == "(19) 99999-9999"
    assert extract_brazilian_phone("Ligar +55 19 99999-9999") == "+55 19 99999-9999"
    assert extract_brazilian_phone("Comercial (19) 3333-4444") == "(19) 3333-4444"
    assert extract_brazilian_phone("Sem telefone") is None


def test_probable_whatsapp_for_mobile_phone():
    from app.services.scraper import is_probable_whatsapp_phone

    assert is_probable_whatsapp_phone("19999999999") is True
    assert is_probable_whatsapp_phone("5519999999999") is True
    assert is_probable_whatsapp_phone("1933334444") is False


def test_extract_detail_phone_reads_phone_from_page_text():
    from app.services.scraper import GoogleMapsScraper

    scraper = GoogleMapsScraper()

    assert scraper._extract_detail_phone("A Barbearia\nTelefone\n(19) 99999-9999") == (
        "(19) 99999-9999"
    )
