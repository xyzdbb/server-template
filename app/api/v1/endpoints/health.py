from fastapi import APIRouter
from app.schemas.common import Message
from app.core.database import check_database_health

router = APIRouter()

@router.get("/", response_model=Message)
def health_check():
    try:
        check_database_health()
        return Message(message="OK")
    except Exception:
        return Message(message="Database unhealthy")