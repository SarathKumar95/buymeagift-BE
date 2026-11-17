import hashlib, os, secrets, smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from .database import Base, engine, get_db
from .models import User, Address, Order, EmailVerificationToken
from .schemas import RegisterIn, LoginIn, UserOut, AddressIn, AddressOut, OrderCreate, OrderCreated
from .security import hash_password, verify_password, set_session_cookie, clear_session_cookie, get_current_user

Base.metadata.create_all(bind=engine)
with engine.begin() as connection:
    connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_email_confirmed BOOLEAN NOT NULL DEFAULT FALSE"))

def send_verification_email(user: User, raw_token: str):
    verification_url = f"{os.getenv('VERIFICATION_BASE_URL', 'http://localhost:8000/api/auth/verify-email')}?token={raw_token}"
    message = EmailMessage()
    message["Subject"] = "Confirm your Buy Me A Random Gift account"
    message["From"] = os.getenv("MAIL_FROM", "no-reply@randomgift.local")
    message["To"] = user.email
    message.set_content(f"Hi {user.name},\n\nConfirm your email address by opening this link:\n{verification_url}\n\nThis link expires in 24 hours.\n")
    with smtplib.SMTP(os.getenv("MAIL_HOST", "localhost"), int(os.getenv("MAIL_PORT", "1025"))) as smtp:
        smtp.send_message(message)

def create_verification_token(user: User, db: Session):
    raw_token = secrets.token_urlsafe(32)
    token = EmailVerificationToken(
        user_id=user.id,
        token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(token); db.commit()
    return raw_token
app = FastAPI(title="Buy Me A Random Gift API", version="0.2.0",
              description="Customer auth, profiles, addresses and order history. Payments/fulfilment are not enabled.")
app.add_middleware(
    CORSMiddleware, allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

oauth_config = Config(environ={
    "GOOGLE_CLIENT_ID": os.getenv("GOOGLE_CLIENT_ID", ""),
    "GOOGLE_CLIENT_SECRET": os.getenv("GOOGLE_CLIENT_SECRET", ""),
})
oauth = OAuth(oauth_config)
if os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET"):
    oauth.register(
        name="google", client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

@app.get("/health")
def health():
    return {"status": "ok", "service": "random-gift-api"}

@app.post("/api/auth/register", response_model=UserOut, status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(409, "An account with this email already exists")
    if db.query(User).filter(User.phone == payload.phone).first():
        raise HTTPException(409, "An account with this phone number already exists")
    user = User(name=payload.name, email=email, phone=payload.phone, password_hash=hash_password(payload.password))
    db.add(user); db.commit(); db.refresh(user)
    try:
        send_verification_email(user, create_verification_token(user, db))
    except OSError:
        raise HTTPException(503, "Could not send confirmation email. Please try again shortly.")
    return user

@app.post("/api/auth/login", response_model=UserOut)
def login(payload: LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    if not user.is_active:
        raise HTTPException(403, "Account disabled")
    set_session_cookie(response, user.id)
    return user

@app.post("/api/auth/logout")
def logout(response: Response):
    clear_session_cookie(response)
    return {"message": "Signed out"}

@app.get("/api/auth/verify-email")
def verify_email(token: str, response: Response, db: Session = Depends(get_db)):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    verification = db.query(EmailVerificationToken).filter(EmailVerificationToken.token_hash == token_hash).first()
    now = datetime.now(timezone.utc)
    if not verification or verification.used_at or verification.expires_at < now:
        raise HTTPException(400, "This confirmation link is invalid or has expired")
    user = db.query(User).filter(User.id == verification.user_id).first()
    if not user:
        raise HTTPException(400, "This confirmation link is invalid")
    verification.used_at = now; user.is_email_confirmed = True
    db.commit()
    redirect = RedirectResponse(url=os.getenv("FRONTEND_AFTER_LOGIN", "http://localhost:3000/dashboard"))
    set_session_cookie(redirect, user.id)
    return redirect

@app.post("/api/auth/resend-verification")
def resend_verification(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if user.is_email_confirmed:
        return {"message": "Your email is already confirmed"}
    try:
        send_verification_email(user, create_verification_token(user, db))
    except OSError:
        raise HTTPException(503, "Could not send confirmation email. Please try again shortly.")
    return {"message": "Confirmation email sent"}

@app.get("/api/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user

@app.get("/api/auth/google")
async def google_login(request: Request):
    if not os.getenv("GOOGLE_CLIENT_ID") or not os.getenv("GOOGLE_CLIENT_SECRET"):
        raise HTTPException(503, "Google login is not configured. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/api/auth/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    if not os.getenv("GOOGLE_CLIENT_ID") or not os.getenv("GOOGLE_CLIENT_SECRET"):
        raise HTTPException(503, "Google login is not configured")
    token = await oauth.google.authorize_access_token(request)
    info = token.get("userinfo")
    if not info:
        info = await oauth.google.parse_id_token(request, token)
    email = (info.get("email") or "").lower()
    if not email or not info.get("email_verified"):
        raise HTTPException(400, "Google account must have a verified email")
    user = db.query(User).filter(User.google_sub == info["sub"]).first()
    if not user:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.google_sub = info["sub"]
        else:
            # Phone is mandatory for this product. Google sign-in starts a pending profile;
            # customer completes phone number after OAuth before using protected features.
            user = User(name=info.get("name") or email.split("@")[0], email=email,
                        phone="PENDING-" + secrets.token_hex(5), google_sub=info["sub"])
            db.add(user)
    db.commit(); db.refresh(user)
    response = RedirectResponse(url=os.getenv("FRONTEND_AFTER_LOGIN", "http://localhost:3000/dashboard"))
    set_session_cookie(response, user.id)
    return response

@app.patch("/api/me/phone", response_model=UserOut)
def update_phone(payload: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    phone = str(payload.get("phone", "")).strip()
    if not phone.startswith("+91") or not phone[3:].isdigit() or len(phone) != 13:
        raise HTTPException(422, "Enter a valid 10-digit Indian mobile number")
    if db.query(User).filter(User.phone == phone, User.id != user.id).first():
        raise HTTPException(409, "Phone number already in use")
    user.phone = phone; db.commit(); db.refresh(user)
    return user

@app.get("/api/addresses", response_model=list[AddressOut])
def list_addresses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Address).filter(Address.user_id == user.id).order_by(Address.is_default.desc(), Address.id.desc()).all()

@app.post("/api/addresses", response_model=AddressOut, status_code=201)
def create_address(payload: AddressIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if payload.is_default:
        db.query(Address).filter(Address.user_id == user.id).update({"is_default": False})
    address = Address(user_id=user.id, **payload.model_dump())
    db.add(address); db.commit(); db.refresh(address)
    return address

@app.delete("/api/addresses/{address_id}")
def delete_address(address_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    address = db.query(Address).filter(Address.id == address_id, Address.user_id == user.id).first()
    if not address: raise HTTPException(404, "Address not found")
    db.delete(address); db.commit()
    return {"message": "Address deleted"}

@app.post("/api/orders", response_model=OrderCreated, status_code=201)
def create_order(payload: OrderCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not user.is_email_confirmed:
        raise HTTPException(403, "Please confirm your email address before placing an order")
    if user.phone.startswith("PENDING-"):
        raise HTTPException(403, "Please add your phone number before ordering")
    order_number = "RND-" + secrets.token_hex(4).upper()
    order = Order(
        order_number=order_number, user_id=user.id, recipient_type=payload.recipient_type,
        budget_paise=payload.budget * 100, categories=",".join(payload.categories),
        exclusions=",".join(payload.exclusions), recipient_name=payload.recipient_name,
        recipient_email=payload.recipient_email, delivery_address=payload.delivery_address,
        gift_message=payload.gift_message, status="PLACED",
    )
    db.add(order); db.commit()
    return OrderCreated(order_number=order_number, status="PLACED",
        message="Your request has been received. No payment or shipment is enabled in this demo.")

@app.get("/api/orders")
def order_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    orders = db.query(Order).filter(Order.user_id == user.id).order_by(Order.created_at.desc()).all()
    return [{"order_number": o.order_number, "status": o.status, "budget": o.budget_paise // 100,
             "created_at": o.created_at, "recipient_type": o.recipient_type} for o in orders]

@app.get("/api/orders/{order_number}")
def get_order(order_number: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    order = db.query(Order).filter(Order.order_number == order_number, Order.user_id == user.id).first()
    if not order: raise HTTPException(status_code=404, detail="Order not found")
    return {"order_number": order.order_number, "status": order.status, "budget": order.budget_paise // 100,
            "created_at": order.created_at}
