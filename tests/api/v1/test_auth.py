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