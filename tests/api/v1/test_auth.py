from fastapi.testclient import TestClient


def test_signup(client: TestClient):
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": "test@example.com", "password": "Test1234", "full_name": "Test"}
    )
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"

def test_login(client: TestClient):
    client.post("/api/v1/auth/signup", json={"email": "test@example.com", "password": "Test1234"})
    response = client.post("/api/v1/auth/login", data={"username": "test@example.com", "password": "Test1234"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()


def test_signup_duplicate_email_returns_conflict(client: TestClient):
    payload = {"email": "test@example.com", "password": "Test1234", "full_name": "Test"}
    client.post("/api/v1/auth/signup", json=payload)
    response = client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 409


def test_refresh_token(client: TestClient):
    client.post("/api/v1/auth/signup", json={"email": "test@example.com", "password": "Test1234"})
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "Test1234"},
    )

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": login_response.json()["refresh_token"]},
    )

    assert refresh_response.status_code == 200
    assert "access_token" in refresh_response.json()
    assert "refresh_token" in refresh_response.json()


def test_invalid_refresh_token_returns_unauthorized(client: TestClient):
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid-token"},
    )
    assert response.status_code == 401


def test_refresh_token_cannot_access_protected_route(client: TestClient):
    client.post("/api/v1/auth/signup", json={"email": "test@example.com", "password": "Test1234"})
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "Test1234"},
    )

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {login_response.json()['refresh_token']}"},
    )

    assert response.status_code == 401