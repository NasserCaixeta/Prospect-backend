def test_admin_can_create_user(client, db_session):
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

    response = client.post(
        "/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": "user@example.com",
            "password": "secret123",
            "name": "User",
            "role": "user",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "user@example.com"
    assert "hashed_password" not in response.json()


def test_regular_user_cannot_create_user(client, db_session):
    from app.models.enums import UserRole
    from app.services.users import create_user

    create_user(
        db_session,
        email="user@example.com",
        password="secret123",
        name="User",
        role=UserRole.USER,
    )
    login = client.post(
        "/auth/login", json={"email": "user@example.com", "password": "secret123"}
    )
    token = login.json()["access_token"]

    response = client.post(
        "/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": "other@example.com",
            "password": "secret123",
            "name": "Other",
            "role": "user",
        },
    )

    assert response.status_code == 403


def test_admin_can_list_users(client, db_session):
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

    response = client.get("/users", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()[0]["email"] == "admin@example.com"
