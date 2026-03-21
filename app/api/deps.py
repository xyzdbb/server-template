from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.core.config import settings
from app.core.database import get_session
from app.modules.auth.service import get_current_active_user
from app.modules.users.models import User
from app.utils.exceptions import PermissionDeniedException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

SessionDep = Annotated[Session, Depends(get_session)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    return get_current_active_user(session, token)


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise PermissionDeniedException("Not enough privileges")
    return current_user


CurrentSuperuser = Annotated[User, Depends(get_current_superuser)]
