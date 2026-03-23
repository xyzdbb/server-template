import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.modules.users.repository import user_repository


@pytest.fixture
def user_auth_headers(client: TestClient) -> dict:
    client.post(
        "/api/v1/auth/signup",
        json={"username": "meuser", "password": "Test1234", "full_name": "Me"},
    )
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "meuser", "password": "Test1234"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_update_user_me_full_name(client: TestClient, user_auth_headers: dict):
    response = client.put(
        "/api/v1/users/me",
        json={"full_name": "Updated Name"},
        headers=user_auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"


def test_update_user_me_password(client: TestClient, user_auth_headers: dict):
    response = client.put(
        "/api/v1/users/me",
        json={"password": "NewPass1234"},
        headers=user_auth_headers,
    )
    assert response.status_code == 200
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "meuser", "password": "NewPass1234"},
    )
    assert login.status_code == 200


def test_update_user_me_weak_password_returns_400(client: TestClient, user_auth_headers: dict):
    response = client.put(
        "/api/v1/users/me",
        json={"password": "weak"},
        headers=user_auth_headers,
    )
    assert response.status_code == 422


def test_read_users_requires_superuser(client: TestClient, user_auth_headers: dict):
    response = client.get("/api/v1/users/", headers=user_auth_headers)
    assert response.status_code == 403


def test_read_users_returns_paginated_response_for_superuser(
    client: TestClient,
    superuser_headers: dict,
):
    client.post(
        "/api/v1/auth/signup",
        json={"username": "regularuser", "password": "Test1234", "full_name": "User"},
    )

    response = client.get(
        "/api/v1/users/?skip=0&limit=10&sort_by=username&sort_order=asc",
        headers=superuser_headers,
    )

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert response.json()["skip"] == 0
    assert response.json()["limit"] == 10
    assert len(response.json()["items"]) == 2
    assert response.json()["items"][0]["username"] == "regularuser"
    assert response.json()["items"][1]["username"] == "superadmin"


def test_read_users_rejects_limit_above_max(
    client: TestClient,
    superuser_headers: dict,
):
    response = client.get(
        "/api/v1/users/?limit=101",
        headers=superuser_headers,
    )

    assert response.status_code == 422


def test_read_users_supports_search(
    client: TestClient,
    superuser_headers: dict,
):
    client.post(
        "/api/v1/auth/signup",
        json={"username": "memberuser", "password": "Test1234", "full_name": "Regular Member"},
    )

    response = client.get(
        "/api/v1/users/?search=member",
        headers=superuser_headers,
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["username"] == "memberuser"


def test_read_users_supports_boolean_filters(
    client: TestClient,
    session: Session,
    superuser_headers: dict,
):
    client.post(
        "/api/v1/auth/signup",
        json={"username": "inactiveuser", "password": "Test1234", "full_name": "Inactive User"},
    )

    inactive_user = user_repository.get_by_username(session, "inactiveuser")
    assert inactive_user is not None
    inactive_user.is_active = False
    session.add(inactive_user)
    session.commit()

    response = client.get(
        "/api/v1/users/?is_active=false",
        headers=superuser_headers,
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["username"] == "inactiveuser"
