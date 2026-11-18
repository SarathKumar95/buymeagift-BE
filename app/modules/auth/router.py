from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.infrastructure.auth import clear_session_cookie, get_current_user, set_session_cookie
from app.infrastructure.config import settings
from app.infrastructure.database import get_db
from app.infrastructure.email import EmailDeliveryError
from app.infrastructure.google_oauth import is_configured, oauth
from app.modules.user.models import User
from app.modules.user.schemas import UserOut
from .schemas import LoginIn, RegisterIn
from .service import AccountDisabledError, AuthService, DuplicateEmailError, DuplicatePhoneError, GoogleEmailNotVerifiedError, InvalidCredentialsError, InvalidVerificationTokenError

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    try: return AuthService(db).register(payload.name, str(payload.email), payload.phone, payload.password)
    except DuplicateEmailError: raise HTTPException(409, "An account with this email already exists")
    except DuplicatePhoneError: raise HTTPException(409, "An account with this phone number already exists")
    except EmailDeliveryError: raise HTTPException(503, "Could not send confirmation email. Please try again shortly.")

@router.post("/login", response_model=UserOut)
def login(payload: LoginIn, response: Response, db: Session = Depends(get_db)):
    try: user = AuthService(db).authenticate(str(payload.email), payload.password)
    except InvalidCredentialsError: raise HTTPException(401, "Incorrect email or password")
    except AccountDisabledError: raise HTTPException(403, "Account disabled")
    set_session_cookie(response, user.id)
    return user

@router.post("/logout")
def logout(response: Response): clear_session_cookie(response); return {"message": "Signed out"}

@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    try: user = AuthService(db).verify_email(token)
    except InvalidVerificationTokenError: raise HTTPException(400, "This confirmation link is invalid or has expired")
    response = RedirectResponse(url=settings.frontend_after_login)
    set_session_cookie(response, user.id)
    return response

@router.post("/resend-verification")
def resend_verification(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.is_email_confirmed: return {"message": "Your email is already confirmed"}
    try: AuthService(db).send_verification(user)
    except EmailDeliveryError: raise HTTPException(503, "Could not send confirmation email. Please try again shortly.")
    return {"message": "Confirmation email sent"}

@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)): return user

@router.get("/google")
async def google_login(request: Request):
    if not is_configured(): raise HTTPException(503, "Google login is not configured. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.")
    return await oauth.google.authorize_redirect(request, settings.google_redirect_uri)

@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    if not is_configured(): raise HTTPException(503, "Google login is not configured")
    token = await oauth.google.authorize_access_token(request)
    info = token.get("userinfo") or await oauth.google.parse_id_token(request, token)
    try: user = AuthService(db).resolve_google_user(info)
    except GoogleEmailNotVerifiedError: raise HTTPException(400, "Google account must have a verified email")
    response = RedirectResponse(url=settings.frontend_after_login)
    set_session_cookie(response, user.id)
    return response
