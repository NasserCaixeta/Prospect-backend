def test_login_returns_access_token(client, db_session):
    from app.models.enums import UserRole
    from app.services.users import create_user

    create_user(
        db_session,
        email="admin@example.com",
        password="secret123",
        name="Admin",
        role=UserRole.ADMIN,
    )

    response = client.post(
        "/auth/login", json={"email": "admin@example.com", "password": "secret123"}
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_rejects_invalid_password(client, db_session):
    from app.models.enums import UserRole
    from app.services.users import create_user

    create_user(
        db_session,
        email="admin@example.com",
        password="secret123",
        name="Admin",
        role=UserRole.ADMIN,
    )

    response = client.post(
        "/auth/login", json={"email": "admin@example.com", "password": "wrong"}
    )

    assert response.status_code == 401


def test_me_requires_token(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_me_returns_current_user(client, db_session):
    from app.models.enums import UserRole
    from app.services.users import create_user

    create_user(
        db_session,
        email="admin@example.com",
        password="secret123",
        name="Admin",
        role=UserRole.ADMIN,
    )
    login = client.post(
        "/auth/login", json={"email": "admin@example.com", "password": "secret123"}
    )
    token = login.json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["email"] == "admin@example.com"
    assert response.json()["role"] == "admin"
