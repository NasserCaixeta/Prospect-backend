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
                    "city": "Campinas",
                    "state": "SP",
                    "segment": "barbearia",
                    "google_maps_url": "https://maps.google.com/?cid=1",
                }
            ]
        ),
    )
    results = list_search_job_results(db_session, job.id)

    assert results[0].lead.name == "Barbearia Central"
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
