from sqlmodel import Session

from app.modules.users.repository import user_repository


def _make_user(session: Session, username: str) -> dict:
    data = {"username": username, "hashed_password": "hashed", "full_name": "Test"}
    return user_repository.create(session, data)


def test_create_user(session: Session):
    user = _make_user(session, "testuser")
    session.commit()
    assert user.username == "testuser"
    assert user.id is not None


def test_get_by_username(session: Session):
    _make_user(session, "testuser")
    session.commit()
    user = user_repository.get_by_username(session, "testuser")
    assert user is not None
    assert user.username == "testuser"


def test_get_multi(session: Session):
    _make_user(session, "userA")
    _make_user(session, "userB")
    session.commit()
    users = user_repository.get_multi(session, skip=0, limit=10)
    assert len(users) == 2


def test_soft_delete(session: Session):
    user = _make_user(session, "deluser")
    session.commit()

    deleted = user_repository.soft_delete(session, user.id)
    session.commit()

    assert deleted is not None
    assert deleted.deleted_at is not None

    fetched = user_repository.get(session, user.id)
    assert fetched is None


def test_soft_delete_excluded_from_get_multi(session: Session):
    _make_user(session, "activeuser")
    deleted_user = _make_user(session, "deleteduser")
    session.commit()

    user_repository.soft_delete(session, deleted_user.id)
    session.commit()

    users = user_repository.get_multi(session)
    usernames = [u.username for u in users]
    assert "activeuser" in usernames
    assert "deleteduser" not in usernames
