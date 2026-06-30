from fastapi import APIRouter

from app.controllers.health_controller import check_health

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return check_health()
