from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.authentication import get_current_session
from app.core.database import get_db
from app.models.session import Session as AuthSession
from app.schemas.auth import (
    LogoutRequest,
    LogoutResponse,
    MFAEnrollmentResponse,
    UserLoginRequest,
    UserLoginResponse,
    UserRegistrationRequest,
    UserRegistrationResponse,
)
from app.services.login import InvalidCredentialsError, login_user
from app.services.mfa import enroll_totp_credential
from app.services.registration import DuplicateUserError, register_user
from app.services.session import revoke_session

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


@router.post(
    "/login",
    response_model=UserLoginResponse,
    status_code=status.HTTP_200_OK,
)
def login(
    request: UserLoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> UserLoginResponse:
    try:
        return login_user(db, request)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        ) from exc


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
)
def logout(
    request: LogoutRequest,
    db: Annotated[Session, Depends(get_db)],
) -> LogoutResponse:
    session = revoke_session(
        db=db,
        session_identifier=request.session_identifier,
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    return LogoutResponse(message="Logout successful.")


@router.post(
    "/mfa/enroll",
    response_model=MFAEnrollmentResponse,
    status_code=status.HTTP_200_OK,
)
def enroll_mfa(
    session: Annotated[AuthSession, Depends(get_current_session)],
    db: Annotated[Session, Depends(get_db)],
) -> MFAEnrollmentResponse:
    credential, secret = enroll_totp_credential(
        db=db,
        session=session,
    )

    return MFAEnrollmentResponse(
        type=credential.type,
        secret=secret,
    )
