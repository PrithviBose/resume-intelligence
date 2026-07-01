from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import (
    UserListItem,
    UserProfileExtraction,
    UserProfileSchema,
)


def create_user(
    db: Session,
    profile: UserProfileExtraction,
    *,
    resume_id: str,
    source_filename: str,
) -> UserProfileSchema:
    user = User(
        user_name=profile.user_name,
        email=profile.email,
        current_company=profile.current_company,
        years_of_experience=profile.years_of_experience,
        resume_id=resume_id,
        source_filename=source_filename,
    )
    db.add(user)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("A user with this email already exists") from exc

    db.refresh(user)
    return _to_schema(user)


def list_users(db: Session) -> list[UserListItem]:
    rows = (
        db.query(User)
        .filter(User.resume_id.isnot(None))
        .order_by(User.user_name)
        .all()
    )
    return [
        UserListItem(
            user_name=user.user_name,
            email=user.email,
            current_company=user.current_company,
            resume_id=user.resume_id,
        )
        for user in rows
        if user.resume_id
    ]


def _to_schema(user: User) -> UserProfileSchema:
    return UserProfileSchema(
        id=user.id,
        user_name=user.user_name,
        email=user.email,
        current_company=user.current_company,
        years_of_experience=user.years_of_experience,
    )
