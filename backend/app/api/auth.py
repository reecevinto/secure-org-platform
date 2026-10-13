from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    HTTPException,
    Request,
    Response,
    status,
)
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
    PasswordRecoveryRequest,
    PasswordRecoveryResponse,
    PasswordResetRequest,
    PasswordResetResponse,
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
from app.services.password_recovery import (
    InvalidRecoveryTokenError,
    process_password_recovery_request,
)
from app.services.password_recovery import (
    reset_password as reset_password_service,
)
from app.services.password_recovery_rate_limit import (
    PasswordRecoveryRateLimiter,
    RateLimitDecision,
)
from app.services.registration import DuplicateUserError, register_user
from app.services.session import create_session, revoke_session

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["authentication"],
)


def get_password_recovery_rate_limiter(
    db: Annotated[Session, Depends(get_db)],
) -> PasswordRecoveryRateLimiter:
    """Provide a rate limiter backed by shared PostgreSQL storage."""
    try:
        return PasswordRecoveryRateLimiter(
            db=db,
            hmac_key=settings.password_recovery_rate_limit_hmac_key,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password recovery is temporarily unavailable.",
        ) from exc


def _check_rate_limit(
    limiter: PasswordRecoveryRateLimiter,
    *,
    namespace: str,
    identifier: str,
    limit: int,
    window_seconds: int,
) -> RateLimitDecision:
    """Check a rate-limit bucket and fail closed on storage errors."""
    try:
        return limiter.check(
            namespace=namespace,
            identifier=identifier,
            limit=limit,
            window_seconds=window_seconds,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password recovery is temporarily unavailable.",
        ) from exc


def _enforce_source_rate_limit(
    decision: RateLimitDecision,
) -> None:
    """Reject requests when their source has exceeded its configured limit."""
    if decision.allowed:
        return

    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Too many requests. Please try again later.",
        headers={
            "Retry-After": str(
                max(1, decision.retry_after_seconds),
            ),
        },
    )


def _get_client_address(request: Request) -> str:
    """Use the ASGI client's address without trusting forwarded headers."""
    if request.client is None or not request.client.host:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password recovery is temporarily unavailable.",
        )

    return request.client.host


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


@router.post(
    "/forgot-password",
    response_model=PasswordRecoveryResponse,
    status_code=status.HTTP_200_OK,
)
def forgot_password(
    request: PasswordRecoveryRequest,
    background_tasks: BackgroundTasks,
    client_request: Request,
    limiter: Annotated[
        PasswordRecoveryRateLimiter,
        Depends(get_password_recovery_rate_limiter),
    ],
) -> PasswordRecoveryResponse:
    client_address = _get_client_address(client_request)

    source_decision = _check_rate_limit(
        limiter,
        namespace="password-recovery-source",
        identifier=client_address,
        limit=settings.password_recovery_source_rate_limit,
        window_seconds=settings.password_recovery_source_window_seconds,
    )
    _enforce_source_rate_limit(source_decision)

    email_decision = _check_rate_limit(
        limiter,
        namespace="password-recovery-email",
        identifier=request.email.strip().lower(),
        limit=settings.password_recovery_email_rate_limit,
        window_seconds=settings.password_recovery_email_window_seconds,
    )

    # Keep the response identical whether the email is unknown or its
    # recovery-request limit has been reached.
    if email_decision.allowed:
        background_tasks.add_task(
            process_password_recovery_request,
            request.email,
        )

    return PasswordRecoveryResponse()


@router.post(
    "/reset-password",
    response_model=PasswordResetResponse,
    status_code=status.HTTP_200_OK,
)
def reset_password_endpoint(
    request: PasswordResetRequest,
    db: Annotated[Session, Depends(get_db)],
    client_request: Request,
    limiter: Annotated[
        PasswordRecoveryRateLimiter,
        Depends(get_password_recovery_rate_limiter),
    ],
) -> PasswordResetResponse:
    client_address = _get_client_address(client_request)

    source_decision = _check_rate_limit(
        limiter,
        namespace="password-reset-source",
        identifier=client_address,
        limit=settings.password_reset_source_rate_limit,
        window_seconds=settings.password_reset_source_window_seconds,
    )
    _enforce_source_rate_limit(source_decision)

    try:
        return reset_password_service(
            db=db,
            request=request,
        )
    except InvalidRecoveryTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token.",
        ) from exc
