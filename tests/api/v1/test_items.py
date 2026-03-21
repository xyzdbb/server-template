import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.modules.users.repository import user_repository


@pytest.fixture
def auth_headers(client: TestClient) -> dict:
    client.post(
        "/api/v1/auth/signup",
        json={"username": "itemowner", "password": "Test1234", "full_name": "Owner"},
    )
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "itemowner", "password": "Test1234"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture
def other_auth_headers(client: TestClient) -> dict:
    client.post(
        "/api/v1/auth/signup",
        json={"username": "otheruser", "password": "Test1234", "full_name": "Other"},
    )
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "otheruser", "password": "Test1234"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture
def superuser_headers(client: TestClient, session: Session) -> dict:
    client.post(
        "/api/v1/auth/signup",
        json={"username": "superadmin", "password": "Test1234", "full_name": "Super"},
    )
    admin = user_repository.get_by_username(session, "superadmin")
    assert admin is not None
    admin.is_superuser = True
    session.add(admin)
    session.commit()

    login = client.post(
        "/api/v1/auth/login",
        data={"username": "superadmin", "password": "Test1234"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


# ── Create ───────────────────────────────────────────────────


def test_create_item(client: TestClient, auth_headers: dict):
    response = client.post(
        "/api/v1/items/",
        json={"title": "Test Item", "description": "A test item"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Item"
    assert data["description"] == "A test item"
    assert "id" in data
    assert "owner_id" in data


def test_create_item_without_description(client: TestClient, auth_headers: dict):
    response = client.post(
        "/api/v1/items/",
        json={"title": "No Desc"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["description"] is None


def test_create_item_requires_auth(client: TestClient):
    response = client.post("/api/v1/items/", json={"title": "No Auth"})
    assert response.status_code == 401


def test_create_item_empty_title_returns_422(client: TestClient, auth_headers: dict):
    response = client.post(
        "/api/v1/items/",
        json={"title": ""},
        headers=auth_headers,
    )
    assert response.status_code == 422


# ── Read single ──────────────────────────────────────────────


def test_read_own_item(client: TestClient, auth_headers: dict):
    create = client.post(
        "/api/v1/items/",
        json={"title": "My Item"},
        headers=auth_headers,
    )
    item_id = create.json()["id"]

    response = client.get(f"/api/v1/items/{item_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "My Item"


def test_read_other_user_item_returns_403(
    client: TestClient, auth_headers: dict, other_auth_headers: dict
):
    create = client.post(
        "/api/v1/items/",
        json={"title": "Private"},
        headers=auth_headers,
    )
    item_id = create.json()["id"]

    response = client.get(f"/api/v1/items/{item_id}", headers=other_auth_headers)
    assert response.status_code == 403


def test_superuser_can_read_any_item(
    client: TestClient, auth_headers: dict, superuser_headers: dict
):
    create = client.post(
        "/api/v1/items/",
        json={"title": "Anyone"},
        headers=auth_headers,
    )
    item_id = create.json()["id"]

    response = client.get(f"/api/v1/items/{item_id}", headers=superuser_headers)
    assert response.status_code == 200


def test_read_nonexistent_item_returns_404(client: TestClient, auth_headers: dict):
    response = client.get("/api/v1/items/99999", headers=auth_headers)
    assert response.status_code == 404


# ── Update ───────────────────────────────────────────────────


def test_update_own_item(client: TestClient, auth_headers: dict):
    create = client.post(
        "/api/v1/items/",
        json={"title": "Original", "description": "Old"},
        headers=auth_headers,
    )
    item_id = create.json()["id"]

    response = client.put(
        f"/api/v1/items/{item_id}",
        json={"title": "Updated", "description": "New"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated"
    assert response.json()["description"] == "New"


def test_update_other_user_item_returns_403(
    client: TestClient, auth_headers: dict, other_auth_headers: dict
):
    create = client.post(
        "/api/v1/items/",
        json={"title": "Owned"},
        headers=auth_headers,
    )
    item_id = create.json()["id"]

    response = client.put(
        f"/api/v1/items/{item_id}",
        json={"title": "Hijack"},
        headers=other_auth_headers,
    )
    assert response.status_code == 403


def test_partial_update_item(client: TestClient, auth_headers: dict):
    create = client.post(
        "/api/v1/items/",
        json={"title": "Partial", "description": "Keep me"},
        headers=auth_headers,
    )
    item_id = create.json()["id"]

    response = client.put(
        f"/api/v1/items/{item_id}",
        json={"title": "Changed"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Changed"
    assert response.json()["description"] == "Keep me"


# ── Delete ───────────────────────────────────────────────────


def test_delete_own_item(client: TestClient, auth_headers: dict):
    create = client.post(
        "/api/v1/items/",
        json={"title": "Delete Me"},
        headers=auth_headers,
    )
    item_id = create.json()["id"]

    response = client.delete(f"/api/v1/items/{item_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Item deleted"

    get_response = client.get(f"/api/v1/items/{item_id}", headers=auth_headers)
    assert get_response.status_code == 404


def test_delete_other_user_item_returns_403(
    client: TestClient, auth_headers: dict, other_auth_headers: dict
):
    create = client.post(
        "/api/v1/items/",
        json={"title": "Not Yours"},
        headers=auth_headers,
    )
    item_id = create.json()["id"]

    response = client.delete(f"/api/v1/items/{item_id}", headers=other_auth_headers)
    assert response.status_code == 403


# ── List my items ────────────────────────────────────────────


def test_list_my_items(client: TestClient, auth_headers: dict):
    for i in range(3):
        client.post(
            "/api/v1/items/",
            json={"title": f"Item {i}"},
            headers=auth_headers,
        )

    response = client.get("/api/v1/items/my", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


def test_list_my_items_excludes_others(
    client: TestClient, auth_headers: dict, other_auth_headers: dict
):
    client.post("/api/v1/items/", json={"title": "Mine"}, headers=auth_headers)
    client.post("/api/v1/items/", json={"title": "Theirs"}, headers=other_auth_headers)

    response = client.get("/api/v1/items/my", headers=auth_headers)
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["title"] == "Mine"


def test_list_my_items_with_search(client: TestClient, auth_headers: dict):
    client.post("/api/v1/items/", json={"title": "Apple"}, headers=auth_headers)
    client.post("/api/v1/items/", json={"title": "Banana"}, headers=auth_headers)

    response = client.get("/api/v1/items/my?search=apple", headers=auth_headers)
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["title"] == "Apple"


def test_list_my_items_pagination(client: TestClient, auth_headers: dict):
    for i in range(5):
        client.post(
            "/api/v1/items/",
            json={"title": f"Page {i}"},
            headers=auth_headers,
        )

    response = client.get("/api/v1/items/my?skip=0&limit=2", headers=auth_headers)
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["has_next"] is True


# ── List all items (superuser) ───────────────────────────────


def test_list_all_items_requires_superuser(client: TestClient, auth_headers: dict):
    response = client.get("/api/v1/items/", headers=auth_headers)
    assert response.status_code == 403


def test_list_all_items_as_superuser(
    client: TestClient, auth_headers: dict, superuser_headers: dict
):
    client.post("/api/v1/items/", json={"title": "A"}, headers=auth_headers)
    client.post("/api/v1/items/", json={"title": "B"}, headers=auth_headers)

    response = client.get("/api/v1/items/", headers=superuser_headers)
    assert response.status_code == 200
    assert response.json()["total"] >= 2
