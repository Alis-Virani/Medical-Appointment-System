"""Auth router: login, register, profile, password-reset."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, HTTPException
from backend.models import LoginRequest, RegisterRequest, TokenResponse
from backend.auth_utils import create_access_token, get_current_user
from fastapi import Depends
from pydantic import BaseModel
import sqlite3

# Import existing auth functions (no modification to auth.py)
from auth import login_user, register_user, get_user_profile, lookup_by_email, _try_email_otp

router = APIRouter()

# ── In-memory OTP store (simple, stateless — good enough for dev) ──────────────
_otp_store: dict[str, str] = {}  # email → otp


class ForgotRequest(BaseModel):
    email: str

class VerifyOTPRequest(BaseModel):
    email: str
    otp: str
    new_password: str


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    ok, user = login_user(req.username, req.password)
    if not ok or not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token({
        "sub": str(user["id"]),
        "username": user["username"],
        "full_name": user["full_name"],
        "email": user["email"],
        "role": user["role"],
    })
    return TokenResponse(access_token=token, user=user)


@router.post("/register")
def register(req: RegisterRequest):
    role = req.role if req.role in ("patient", "doctor") else "patient"
    ok, msg = register_user(
        req.username, req.password, req.full_name,
        req.email, req.phone, role=role
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    profile = get_user_profile(current_user["id"])
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return profile


@router.post("/forgot-password")
def forgot_password(req: ForgotRequest):
    """Step 1 — look up the email, generate OTP and email it."""
    user = lookup_by_email(req.email)
    if not user:
        # Don't reveal whether the email exists
        return {"message": "If that email is registered, a reset code has been sent."}

    import random, string
    otp = "".join(random.choices(string.digits, k=6))
    _otp_store[req.email.strip().lower()] = otp

    sent = _try_email_otp(user, otp)
    if not sent:
        # SendGrid not configured — return OTP in response for dev environments
        return {
            "message": "Email service not configured. Use this code to reset (dev only).",
            "dev_otp": otp,
        }
    return {"message": "Reset code sent to your email."}


@router.post("/verify-otp")
def verify_otp(req: VerifyOTPRequest):
    """Step 2 — verify OTP then set new password."""
    key = req.email.strip().lower()
    stored = _otp_store.get(key)
    if not stored or stored != req.otp.strip():
        raise HTTPException(status_code=400, detail="Invalid or expired code.")

    # Reset the password using the existing update_profile helper
    from auth import update_profile
    ok, msg = update_profile(
        user_id=lookup_by_email(req.email)["id"],
        password=req.new_password,
    )
    if not ok:
        raise HTTPException(status_code=500, detail=msg)
    del _otp_store[key]          # invalidate OTP
    return {"message": "Password updated successfully. Please sign in."}
