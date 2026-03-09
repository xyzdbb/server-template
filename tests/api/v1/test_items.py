from fastapi.testclient import TestClient


def test_read_items_returns_paginated_response(client: TestClient):
    client.post(
        "/api/v1/auth/signup",
        json={"email": "items@example.com", "password": "Test1234", "full_name": "Items"},
    )
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "items@example.com", "password": "Test1234"},
    )
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    client.post("/api/v1/items/", json={"title": "Item 1"}, headers=headers)
    client.post("/api/v1/items/", json={"title": "Item 2"}, headers=headers)

    response = client.get(
        "/api/v1/items/?skip=0&limit=10&sort_by=title&sort_order=asc",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert response.json()["skip"] == 0
    assert response.json()["limit"] == 10
    assert len(response.json()["items"]) == 2
    assert response.json()["items"][0]["title"] == "Item 1"
    assert response.json()["items"][1]["title"] == "Item 2"


def test_read_items_rejects_limit_above_max(client: TestClient):
    client.post(
        "/api/v1/auth/signup",
        json={"email": "items-max@example.com", "password": "Test1234", "full_name": "Items"},
    )
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "items-max@example.com", "password": "Test1234"},
    )
    access_token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/items/?limit=101",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 422


def test_read_items_supports_search(client: TestClient):
    client.post(
        "/api/v1/auth/signup",
        json={"email": "items-search@example.com", "password": "Test1234", "full_name": "Items"},
    )
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "items-search@example.com", "password": "Test1234"},
    )
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    client.post("/api/v1/items/", json={"title": "Alpha task"}, headers=headers)
    client.post("/api/v1/items/", json={"title": "Beta task"}, headers=headers)

    response = client.get("/api/v1/items/?search=Alpha", headers=headers)

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["title"] == "Alpha task"
