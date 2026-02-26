from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.google_oauth import (
    build_google_start_url,
    generate_oauth_state,
    upsert_user_from_google_callback,
)
from app.services.password_auth import login_with_password, signup_with_password
from app.services.password_reset import consume_reset_token, create_reset_token
from app.services.session_service import (
    clear_session_cookie,
    create_session,
    revoke_session,
    set_session_cookie,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupBody(BaseModel):
    email: str
    password: str
    displayName: str | None = None


class LoginBody(BaseModel):
    email: str
    password: str


class ForgotPasswordBody(BaseModel):
    email: str


class ResetPasswordBody(BaseModel):
    token: str
    newPassword: str


def _user_payload(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "displayName": user.display_name,
        "role": user.role,
    }


@router.post("/signup")
async def signup(
    body: SignupBody,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        user = await signup_with_password(
            db,
            email=body.email,
            password=body.password,
            display_name=body.displayName,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    token = await create_session(db, user.id, request)
    set_session_cookie(response, token)
    return {"authenticated": True, "user": _user_payload(user)}


@router.post("/login")
async def login(
    body: LoginBody,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        user = await login_with_password(db, email=body.email, password=body.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    token = await create_session(db, user.id, request)
    set_session_cookie(response, token)
    return {"authenticated": True, "user": _user_payload(user)}


@router.post("/password/forgot")
async def forgot_password(
    body: ForgotPasswordBody,
    db: AsyncSession = Depends(get_db),
) -> dict:
    token = await create_reset_token(db, body.email)
    # For local/dev Phase 1 flow we return token directly.
    return {"status": "ok", "resetToken": token}


@router.post("/password/reset")
async def reset_password(
    body: ResetPasswordBody,
    db: AsyncSession = Depends(get_db),
) -> dict:
    try:
        is_ok = await consume_reset_token(db, body.token, body.newPassword)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not is_ok:
        raise HTTPException(status_code=400, detail="invalid or expired reset token")
    return {"status": "ok"}


@router.get("/oauth/google/start")
async def auth_oauth_google_start() -> RedirectResponse:
    if not settings.google_oauth_client_id or not settings.google_oauth_client_secret:
        raise HTTPException(status_code=500, detail="google oauth is not configured")

    state = generate_oauth_state()
    redirect = RedirectResponse(url=build_google_start_url(state), status_code=307)
    redirect.set_cookie(
        key="cfai_oauth_state",
        value=state,
        max_age=600,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )
    return redirect


@router.get("/oauth/google/callback")
async def auth_oauth_google_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    cookie_state = request.cookies.get("cfai_oauth_state")
    if not cookie_state or cookie_state != state:
        raise HTTPException(status_code=400, detail="invalid oauth state")

    try:
        user = await upsert_user_from_google_callback(db, code)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"google oauth failed: {exc}") from exc

    token = await create_session(db, user.id, request)
    redirect = RedirectResponse(url=settings.frontend_url, status_code=307)
    set_session_cookie(redirect, token)
    redirect.delete_cookie("cfai_oauth_state", path="/")
    return redirect


@router.get("/me")
async def auth_me(current_user: User | None = Depends(get_current_user)) -> dict:
    if current_user is None:
        return {"authenticated": False, "user": None, "canTriggerAnalysis": False}
    return {
        "authenticated": True,
        "user": _user_payload(current_user),
        "canTriggerAnalysis": True,
    }


@router.post("/logout")
async def auth_logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    raw_token = request.cookies.get(settings.session_cookie_name)
    await revoke_session(db, raw_token)
    clear_session_cookie(response)
    return {"status": "ok"}
