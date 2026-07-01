from sqlalchemy.orm import Session

from app.lib.logger import get_logger, log_event
from app.schemas.user import UsersListResponse
from app.services.user_service import list_users

logger = get_logger(__name__)


def get_users(db: Session) -> UsersListResponse:
    users = list_users(db)
    log_event(logger, "users.listed", count=len(users))
    return UsersListResponse(users=users)
