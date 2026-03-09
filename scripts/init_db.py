from sqlmodel import Session

from app.core.config import settings
from app.core.database import engine, init_db
from app.modules.users.repository import user_repository
from app.modules.users.schemas import UserCreate
from app.modules.users.service import create_user

def main():
    print("Creating tables...")
    init_db()
    
    print("Creating superuser...")
    with Session(engine) as session:
        user = user_repository.get_by_email(session, settings.FIRST_SUPERUSER)
        if not user:
            user_in = UserCreate(
                email=settings.FIRST_SUPERUSER,
                password=settings.FIRST_SUPERUSER_PASSWORD,
                full_name=settings.FIRST_SUPERUSER_FULL_NAME,
            )
            user = create_user(session, user_in)
            user.is_superuser = True
            session.add(user)
            session.commit()
            print(f"Superuser created: {user.email}")
        else:
            print("Superuser already exists")
    
    print("Database initialized!")

if __name__ == "__main__":
    main()