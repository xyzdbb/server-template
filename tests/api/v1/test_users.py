from fastapi.testclient import TestClient
from sqlmodel import Session

from app.modules.users.repository import user_repository


def test_read_users_returns_paginated_response_for_superuser(
    client: TestClient,
    session: Session,
):
    client.post(
        "/api/v1/auth/signup",
        json={"email": "admin@example.com", "password": "Test1234", "full_name": "Admin"},
    )
    client.post(
        "/api/v1/auth/signup",
        json={"email": "user@example.com", "password": "Test1234", "full_name": "User"},
    )

    admin = user_repository.get_by_email(session, "admin@example.com")
    assert admin is not None
    admin.is_superuser = True
    session.add(admin)
    session.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@example.com", "password": "Test1234"},
    )
    access_token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/users/?skip=0&limit=10&sort_by=email&sort_order=asc",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert response.json()["skip"] == 0
    assert response.json()["limit"] == 10
    assert len(response.json()["items"]) == 2
    assert response.json()["items"][0]["email"] == "admin@example.com"
    assert response.json()["items"][1]["email"] == "user@example.com"


def test_read_users_rejects_limit_above_max(
    client: TestClient,
    session: Session,
):
    client.post(
        "/api/v1/auth/signup",
        json={"email": "admin-limit@example.com", "password": "Test1234", "full_name": "Admin"},
    )

    admin = user_repository.get_by_email(session, "admin-limit@example.com")
    assert admin is not None
    admin.is_superuser = True
    session.add(admin)
    session.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin-limit@example.com", "password": "Test1234"},
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
        json={"email": "search-admin@example.com", "password": "Test1234", "full_name": "Search Admin"},
    )
    client.post(
        "/api/v1/auth/signup",
        json={"email": "member@example.com", "password": "Test1234", "full_name": "Regular Member"},
    )

    admin = user_repository.get_by_email(session, "search-admin@example.com")
    assert admin is not None
    admin.is_superuser = True
    session.add(admin)
    session.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "search-admin@example.com", "password": "Test1234"},
    )
    access_token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/users/?search=member",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["email"] == "member@example.com"


def test_read_users_supports_boolean_filters(
    client: TestClient,
    session: Session,
):
    client.post(
        "/api/v1/auth/signup",
        json={"email": "filter-admin@example.com", "password": "Test1234", "full_name": "Filter Admin"},
    )
    client.post(
        "/api/v1/auth/signup",
        json={"email": "inactive@example.com", "password": "Test1234", "full_name": "Inactive User"},
    )

    admin = user_repository.get_by_email(session, "filter-admin@example.com")
    inactive_user = user_repository.get_by_email(session, "inactive@example.com")
    assert admin is not None
    assert inactive_user is not None

    admin.is_superuser = True
    inactive_user.is_active = False
    session.add(admin)
    session.add(inactive_user)
    session.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "filter-admin@example.com", "password": "Test1234"},
    )
    access_token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/users/?is_active=false",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["email"] == "inactive@example.com"
