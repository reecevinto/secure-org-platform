from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import UserRegistrationRequest, UserRegistrationResponse
from app.services.registration import DuplicateUserError, register_user

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["authentication"],
)


@router.post(
    "/register",
    response_model=UserRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: UserRegistrationRequest,
    db: Annotated[Session, Depends(get_db)],
) -> UserRegistrationResponse:
    try:
        return register_user(db, request)
    except DuplicateUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        ) from exc
