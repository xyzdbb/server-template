from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.database import check_database_health
from app.schemas.common import HealthStatus

router = APIRouter()


@router.get("/", response_model=HealthStatus)
def health_check():
    try:
        check_database_health()
        return HealthStatus(status="ok", database="up")
    except Exception:
        return JSONResponse(
            status_code=503,
            content=HealthStatus(status="error", database="down").model_dump(),
        )
