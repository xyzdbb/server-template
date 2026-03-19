from sqlmodel import Session

from app.core.config import settings
from app.core.database import get_engine
from app.modules.users.repository import user_repository
from app.modules.users.schemas import UserCreate
from app.modules.users.service import create_superuser


def main() -> None:
    print("Bootstrapping database data...")

    with Session(get_engine()) as session:
        user = user_repository.get_by_username(session, settings.FIRST_SUPERUSER)
        if user:
            print("Superuser already exists")
            return

        user_in = UserCreate(
            username=settings.FIRST_SUPERUSER,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            full_name=settings.FIRST_SUPERUSER_FULL_NAME,
        )
        user = create_superuser(session, user_in)
        print(f"Superuser created: {user.username}")

    print("Database bootstrap completed!")


if __name__ == "__main__":
    main()
