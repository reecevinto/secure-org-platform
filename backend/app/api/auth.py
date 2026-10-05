from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.authentication import get_current_session
from app.core.config import settings
from app.core.database import get_db
from app.core.mfa_challenge import MFAChallengeError, verify_mfa_challenge
from app.models.session import Session as AuthSession
from app.schemas.auth import (
    LogoutRequest,
    LogoutResponse,
    MFAEnrollmentResponse,
    MFAVerificationRequest,
    MFAVerificationResponse,
    UserLoginRequest,
    UserLoginResponse,
    UserRegistrationRequest,
    UserRegistrationResponse,
)
from app.services.login import InvalidCredentialsError, login_user
from app.services.mfa import (
    MFAVerificationError,
    enroll_totp_credential,
    verify_enabled_totp_credential,
    verify_totp_credential,
)
from app.services.registration import DuplicateUserError, register_user
from app.services.session import create_session, revoke_session

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
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
def login(
    request: UserLoginRequest,
    db: Annotated[Session, Depends(get_db)],
    response: Response,
) -> UserLoginResponse:
    try:
        result = login_user(db, request)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        ) from exc

    if result.session_identifier is not None:
        response.headers["session-identifier"] = result.session_identifier

    return result


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


@router.post(
    "/mfa/verify",
    response_model=MFAVerificationResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
)
def verify_mfa(
    request: MFAVerificationRequest,
    db: Annotated[Session, Depends(get_db)],
    response: Response,
    session_identifier: Annotated[
        str | None,
        Header(),
    ] = None,
) -> MFAVerificationResponse:
    if session_identifier and request.challenge:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="MFA verification failed.",
        )

    if session_identifier:
        session = get_current_session(
            db=db,
            session_identifier=session_identifier,
        )

        try:
            verify_totp_credential(
                db=db,
                session=session,
                code=request.code,
            )
        except MFAVerificationError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="MFA verification failed.",
            ) from exc

        return MFAVerificationResponse(
            message="MFA verification successful.",
        )

    if not request.challenge:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    try:
        user_id = verify_mfa_challenge(
            request.challenge,
        )

        verify_enabled_totp_credential(
            db=db,
            user_id=user_id,
            code=request.code,
        )

        expires_at = datetime.now(UTC) + timedelta(
            seconds=settings.session_lifetime_seconds,
        )

        session = create_session(
            db=db,
            user_id=user_id,
            expires_at=expires_at,
        )

    except (
        MFAChallengeError,
        MFAVerificationError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="MFA verification failed.",
        ) from exc

    response.headers["session-identifier"] = session.session_identifier

    return MFAVerificationResponse(
        message="MFA verification successful.",
    )
