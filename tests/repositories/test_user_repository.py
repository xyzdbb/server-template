from sqlmodel import Session

from app.modules.users.repository import user_repository


def _make_user(session: Session, email: str) -> dict:
    data = {"email": email, "hashed_password": "hashed", "full_name": "Test"}
    return user_repository.create(session, data)


def test_create_user(session: Session):
    user = _make_user(session, "test@example.com")
    session.commit()
    assert user.email == "test@example.com"
    assert user.id is not None


def test_get_by_email(session: Session):
    _make_user(session, "test@example.com")
    session.commit()
    user = user_repository.get_by_email(session, "test@example.com")
    assert user is not None
    assert user.email == "test@example.com"


def test_get_multi(session: Session):
    _make_user(session, "a@example.com")
    _make_user(session, "b@example.com")
    session.commit()
    users = user_repository.get_multi(session, skip=0, limit=10)
    assert len(users) == 2


def test_soft_delete(session: Session):
    user = _make_user(session, "del@example.com")
    session.commit()

    deleted = user_repository.soft_delete(session, user.id)
    session.commit()

    assert deleted is not None
    assert deleted.deleted_at is not None

    # 软删除后 get 应返回 None
    fetched = user_repository.get(session, user.id)
    assert fetched is None


def test_soft_delete_excluded_from_get_multi(session: Session):
    user = _make_user(session, "active@example.com")
    deleted_user = _make_user(session, "deleted@example.com")
    session.commit()

    user_repository.soft_delete(session, deleted_user.id)
    session.commit()

    users = user_repository.get_multi(session)
    emails = [u.email for u in users]
    assert "active@example.com" in emails
    assert "deleted@example.com" not in emails
