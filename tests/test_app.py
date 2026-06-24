def test_create_app_exposes_title():
    from app.main import create_app

    app = create_app()

    assert app.title == "Prospect Backend"
