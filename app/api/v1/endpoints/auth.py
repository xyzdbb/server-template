from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from app.api.deps import SessionDep
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserResponse
from app.services import authenticate_user, create_user_token, create_user

router = APIRouter()

@router.post("/login", response_model=Token)
def login(session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    tokens = create_user_token(user.id)
    return Token(**tokens)

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(session: SessionDep, user_in: UserCreate):
    try:
        user = create_user(session, user_in)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))