from pydantic import BaseModel, Field


class UserProfileExtraction(BaseModel):
    user_name: str | None = None
    email: str | None = None
    current_company: str | None = None
    years_of_experience: float | None = Field(default=None, ge=0)


class UserProfileSchema(BaseModel):
    id: int
    user_name: str | None
    email: str | None
    current_company: str | None
    years_of_experience: float | None


class UserListItem(BaseModel):
    user_name: str | None
    email: str | None
    current_company: str | None
    resume_id: str


class UsersListResponse(BaseModel):
    users: list[UserListItem]
