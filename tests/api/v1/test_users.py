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
    session: Session,
):
    client.post(
        "/api/v1/auth/signup",
        json={"username": "adminuser", "password": "Test1234", "full_name": "Admin"},
    )
    client.post(
        "/api/v1/auth/signup",
        json={"username": "regularuser", "password": "Test1234", "full_name": "User"},
    )

    admin = user_repository.get_by_username(session, "adminuser")
    assert admin is not None
    admin.is_superuser = True
    session.add(admin)
    session.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "adminuser", "password": "Test1234"},
    )
    access_token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/users/?skip=0&limit=10&sort_by=username&sort_order=asc",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert response.json()["skip"] == 0
    assert response.json()["limit"] == 10
    assert len(response.json()["items"]) == 2
    assert response.json()["items"][0]["username"] == "adminuser"
    assert response.json()["items"][1]["username"] == "regularuser"


def test_read_users_rejects_limit_above_max(
    client: TestClient,
    session: Session,
):
    client.post(
        "/api/v1/auth/signup",
        json={"username": "adminlimit", "password": "Test1234", "full_name": "Admin"},
    )

    admin = user_repository.get_by_username(session, "adminlimit")
    assert admin is not None
    admin.is_superuser = True
    session.add(admin)
    session.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "adminlimit", "password": "Test1234"},
    )
    access_token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/users/?limit=101",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 422


def test_read_users_supports_search(
    client: TestClient,
    session: Session,
):
    client.post(
        "/api/v1/auth/signup",
        json={"username": "searchadmin", "password": "Test1234", "full_name": "Search Admin"},
    )
    client.post(
        "/api/v1/auth/signup",
        json={"username": "memberuser", "password": "Test1234", "full_name": "Regular Member"},
    )

    admin = user_repository.get_by_username(session, "searchadmin")
    assert admin is not None
    admin.is_superuser = True
    session.add(admin)
    session.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "searchadmin", "password": "Test1234"},
    )
    access_token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/users/?search=member",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["username"] == "memberuser"


def test_read_users_supports_boolean_filters(
    client: TestClient,
    session: Session,
):
    client.post(
        "/api/v1/auth/signup",
        json={"username": "filteradmin", "password": "Test1234", "full_name": "Filter Admin"},
    )
    client.post(
        "/api/v1/auth/signup",
        json={"username": "inactiveuser", "password": "Test1234", "full_name": "Inactive User"},
    )

    admin = user_repository.get_by_username(session, "filteradmin")
    inactive_user = user_repository.get_by_username(session, "inactiveuser")
    assert admin is not None
    assert inactive_user is not None

    admin.is_superuser = True
    inactive_user.is_active = False
    session.add(admin)
    session.add(inactive_user)
    session.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "filteradmin", "password": "Test1234"},
    )
    access_token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/users/?is_active=false",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["username"] == "inactiveuser"
