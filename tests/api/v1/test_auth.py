from fastapi.testclient import TestClient


def test_signup(client: TestClient):
    response = client.post(
        "/api/v1/auth/signup",
        json={"username": "testuser", "password": "Test1234", "full_name": "Test"}
    )
    assert response.status_code == 201
    assert response.json()["username"] == "testuser"

def test_login(client: TestClient):
    client.post("/api/v1/auth/signup", json={"username": "testuser", "password": "Test1234"})
    response = client.post("/api/v1/auth/login", data={"username": "testuser", "password": "Test1234"})
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()


def test_signup_duplicate_username_returns_conflict(client: TestClient):
    payload = {"username": "testuser", "password": "Test1234", "full_name": "Test"}
    client.post("/api/v1/auth/signup", json=payload)
    response = client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 409


def test_refresh_token(client: TestClient):
    client.post("/api/v1/auth/signup", json={"username": "testuser", "password": "Test1234"})
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "Test1234"},
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
    client.post("/api/v1/auth/signup", json={"username": "testuser", "password": "Test1234"})
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "Test1234"},
    )

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {login_response.json()['refresh_token']}"},
    )

    assert response.status_code == 401


def test_refresh_token_rotation_invalidates_old_token(client: TestClient):
    """轮换后旧 refresh token 应被撤销，不可重复使用。"""
    client.post("/api/v1/auth/signup", json={"username": "testuser", "password": "Test1234"})
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "Test1234"},
    )
    old_refresh = login_resp.json()["refresh_token"]

    first = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert first.status_code == 200

    replay = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert replay.status_code == 401


def test_logout_revokes_refresh_token(client: TestClient):
    """logout 后 refresh token 不可再用于刷新。"""
    client.post("/api/v1/auth/signup", json={"username": "testuser", "password": "Test1234"})
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser", "password": "Test1234"},
    )
    tokens = login_resp.json()

    logout_resp = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert logout_resp.status_code == 204

    refresh_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_resp.status_code == 401


def test_logout_rejects_other_users_token(client: TestClient):
    """不允许用他人的 refresh token 执行 logout。"""
    client.post("/api/v1/auth/signup", json={"username": "user_a", "password": "Test1234"})
    client.post("/api/v1/auth/signup", json={"username": "user_b", "password": "Test1234"})

    login_a = client.post("/api/v1/auth/login", data={"username": "user_a", "password": "Test1234"})
    login_b = client.post("/api/v1/auth/login", data={"username": "user_b", "password": "Test1234"})

    resp = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": login_b.json()["refresh_token"]},
        headers={"Authorization": f"Bearer {login_a.json()['access_token']}"},
    )
    assert resp.status_code == 401


def test_logout_without_auth_returns_unauthorized(client: TestClient):
    """未携带认证信息的 logout 请求应返回 401。"""
    resp = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": "some-token"},
    )
    assert resp.status_code == 401
