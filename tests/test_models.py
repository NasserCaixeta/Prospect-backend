def test_all_expected_tables_are_registered():
    import app.models  # noqa: F401
    from app.db.base import Base

    assert set(Base.metadata.tables) == {
        "lead_events",
        "leads",
        "search_job_results",
        "search_jobs",
        "settings",
        "site_analyses",
        "users",
    }
