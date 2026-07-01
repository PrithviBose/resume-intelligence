from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.controllers.user_controller import get_users
from app.lib.database import get_db
from app.schemas.user import UsersListResponse

router = APIRouter(prefix="/api", tags=["users"])


@router.get("/users", response_model=UsersListResponse)
def list_users(db: Session = Depends(get_db)) -> UsersListResponse:
    return get_users(db)
