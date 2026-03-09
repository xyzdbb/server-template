from fastapi import APIRouter, HTTPException, Depends
from app.api.deps import SessionDep, CurrentUser, get_current_superuser
from app.schemas.user import UserResponse, UserUpdate
from app.crud import user_crud
from app.services import update_user

router = APIRouter()

@router.get("/me", response_model=UserResponse)
def read_user_me(current_user: CurrentUser):
    return current_user

@router.put("/me", response_model=UserResponse)
def update_user_me(session: SessionDep, current_user: CurrentUser, user_in: UserUpdate):
    try:
        user = update_user(session, current_user, user_in)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=list[UserResponse])
def read_users(
    session: SessionDep,
    current_user: CurrentUser = Depends(get_current_superuser),
    skip: int = 0,
    limit: int = 100
):
    users = user_crud.get_multi(session, skip=skip, limit=limit)
    return users