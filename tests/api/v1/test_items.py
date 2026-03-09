import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def auth_headers(client: TestClient) -> dict:
    client.post(
        "/api/v1/auth/signup",
        json={"email": "owner@example.com", "password": "Test1234", "full_name": "Owner"},
    )
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "owner@example.com", "password": "Test1234"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture
def other_auth_headers(client: TestClient) -> dict:
    client.post(
        "/api/v1/auth/signup",
        json={"email": "other@example.com", "password": "Test1234", "full_name": "Other"},
    )
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "other@example.com", "password": "Test1234"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_create_item(client: TestClient, auth_headers: dict):
    response = client.post(
        "/api/v1/items/",
        json={"title": "My Item", "description": "A description"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My Item"
    assert data["description"] == "A description"
    assert "id" in data
    assert "owner_id" in data


def test_get_item(client: TestClient, auth_headers: dict):
    create = client.post("/api/v1/items/", json={"title": "Get Me"}, headers=auth_headers)
    item_id = create.json()["id"]

    response = client.get(f"/api/v1/items/{item_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Get Me"


def test_get_item_not_found(client: TestClient, auth_headers: dict):
    response = client.get("/api/v1/items/99999", headers=auth_headers)
    assert response.status_code == 404


def test_update_item(client: TestClient, auth_headers: dict):
    create = client.post("/api/v1/items/", json={"title": "Old Title"}, headers=auth_headers)
    item_id = create.json()["id"]

    response = client.put(
        f"/api/v1/items/{item_id}",
        json={"title": "New Title"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"


def test_delete_item(client: TestClient, auth_headers: dict):
    create = client.post("/api/v1/items/", json={"title": "To Delete"}, headers=auth_headers)
    item_id = create.json()["id"]

    response = client.delete(f"/api/v1/items/{item_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Item deleted successfully"

    # 软删除后再查询应返回 404
    get_response = client.get(f"/api/v1/items/{item_id}", headers=auth_headers)
    assert get_response.status_code == 404


def test_get_item_from_other_user_returns_403(
    client: TestClient, auth_headers: dict, other_auth_headers: dict
):
    create = client.post("/api/v1/items/", json={"title": "Private"}, headers=auth_headers)
    item_id = create.json()["id"]

    response = client.get(f"/api/v1/items/{item_id}", headers=other_auth_headers)
    assert response.status_code == 403


def test_update_item_from_other_user_returns_403(
    client: TestClient, auth_headers: dict, other_auth_headers: dict
):
    create = client.post("/api/v1/items/", json={"title": "Private"}, headers=auth_headers)
    item_id = create.json()["id"]

    response = client.put(
        f"/api/v1/items/{item_id}",
        json={"title": "Hacked"},
        headers=other_auth_headers,
    )
    assert response.status_code == 403


def test_delete_item_from_other_user_returns_403(
    client: TestClient, auth_headers: dict, other_auth_headers: dict
):
    create = client.post("/api/v1/items/", json={"title": "Private"}, headers=auth_headers)
    item_id = create.json()["id"]

    response = client.delete(f"/api/v1/items/{item_id}", headers=other_auth_headers)
    assert response.status_code == 403


def test_read_items_returns_paginated_response(client: TestClient, auth_headers: dict):
    client.post("/api/v1/items/", json={"title": "Item 1"}, headers=auth_headers)
    client.post("/api/v1/items/", json={"title": "Item 2"}, headers=auth_headers)

    response = client.get(
        "/api/v1/items/?skip=0&limit=10&sort_by=title&sort_order=asc",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert response.json()["items"][0]["title"] == "Item 1"
    assert response.json()["items"][1]["title"] == "Item 2"


def test_read_items_rejects_limit_above_max(client: TestClient, auth_headers: dict):
    response = client.get("/api/v1/items/?limit=101", headers=auth_headers)
    assert response.status_code == 422


def test_read_items_supports_search(client: TestClient, auth_headers: dict):
    client.post("/api/v1/items/", json={"title": "Alpha task"}, headers=auth_headers)
    client.post("/api/v1/items/", json={"title": "Beta task"}, headers=auth_headers)

    response = client.get("/api/v1/items/?search=Alpha", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["title"] == "Alpha task"
