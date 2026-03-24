"""
Authentication Module
=====================
Handles user registration, login, password recovery & session management.
Uses PBKDF2-SHA256 hashing (stdlib only – no extra deps).
"""

import hashlib
import secrets
import datetime
import sqlite3
import random
import streamlit as st
from database import DB_NAME


# ============================================================================
# PASSWORD UTILITIES
# ============================================================================

def _hash_password(password: str) -> tuple[str, str]:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return key.hex(), salt


def _verify_password(password: str, stored_hash: str, salt: str) -> bool:
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return secrets.compare_digest(key.hex(), stored_hash)


# ============================================================================
# CORE AUTH FUNCTIONS
# ============================================================================

def register_user(username: str, password: str, full_name: str,
                  email: str = "", phone: str = "",
                  role: str = "patient") -> tuple[bool, str]:
    username = username.strip().lower()
    full_name = full_name.strip()
    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters."
    if not full_name:
        return False, "Full name is required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    pw_hash, salt = _hash_password(password)
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        conn.execute(
            "INSERT INTO users (username, password_hash, salt, full_name, email, phone, role) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, pw_hash, salt, full_name, email.strip(), phone.strip(), role)
        )
        conn.commit()
        conn.close()
        return True, "Account created successfully! Please log in."
    except sqlite3.IntegrityError:
        return False, "Username already taken. Please choose another."
    except Exception as e:
        return False, f"Registration failed: {e}"


def login_user(username: str, password: str) -> tuple[bool, dict | None]:
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        row = conn.execute(
            "SELECT id, username, password_hash, salt, full_name, email, phone, role "
            "FROM users WHERE username = ?",
            (username.strip().lower(),)
        ).fetchone()
        conn.close()
    except Exception:
        return False, None

    if not row:
        return False, None

    uid, uname, pw_hash, salt, full_name, email, phone, role = row
    if not _verify_password(password, pw_hash, salt):
        return False, None

    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        conn.execute("UPDATE users SET last_login = ? WHERE id = ?",
                     (datetime.datetime.now().isoformat(), uid))
        conn.commit()
        conn.close()
    except Exception:
        pass

    return True, {
        "id": uid, "username": uname,
        "full_name": full_name or uname,
        "email": email or "", "phone": phone or "",
        "role": role or "patient",
    }


def get_user_profile(user_id: int) -> dict | None:
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        row = conn.execute(
            "SELECT id, username, full_name, email, phone, role, created_at, last_login "
            "FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        conn.close()
        if not row:
            return None
        return {"id": row[0], "username": row[1], "full_name": row[2],
                "email": row[3], "phone": row[4], "role": row[5],
                "created_at": row[6], "last_login": row[7]}
    except Exception:
        return None


def update_user_profile(user_id: int, full_name: str = None,
                        email: str = None, phone: str = None) -> tuple[bool, str]:
    updates, params = [], []
    if full_name is not None:
        updates.append("full_name = ?"); params.append(full_name.strip())
    if email is not None:
        updates.append("email = ?"); params.append(email.strip())
    if phone is not None:
        updates.append("phone = ?"); params.append(phone.strip())
    if not updates:
        return False, "Nothing to update."
    params.append(user_id)
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        conn.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit(); conn.close()
        return True, "Profile updated successfully."
    except Exception as e:
        return False, str(e)


def change_password(user_id: int, old_password: str, new_password: str) -> tuple[bool, str]:
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        row = conn.execute("SELECT password_hash, salt FROM users WHERE id = ?",
                           (user_id,)).fetchone()
        conn.close()
    except Exception:
        return False, "Database error."
    if not row:
        return False, "User not found."
    if not _verify_password(old_password, row[0], row[1]):
        return False, "Current password is incorrect."
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters."
    new_hash, new_salt = _hash_password(new_password)
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        conn.execute("UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
                     (new_hash, new_salt, user_id))
        conn.commit(); conn.close()
        return True, "Password changed successfully."
    except Exception as e:
        return False, str(e)


# ============================================================================
# ACCOUNT RECOVERY
# ============================================================================

def lookup_by_email(email: str) -> dict | None:
    """Find user record by registered email."""
    email = email.strip().lower()
    if not email:
        return None
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        row = conn.execute(
            "SELECT id, username, full_name, email FROM users "
            "WHERE LOWER(email) = ?", (email,)
        ).fetchone()
        conn.close()
        if not row:
            return None
        return {"id": row[0], "username": row[1], "full_name": row[2], "email": row[3]}
    except Exception:
        return None


def generate_reset_otp(user_id: int) -> str:
    """Generate a 6-digit OTP valid for 15 minutes and persist a hashed copy."""
    otp = str(random.randint(100000, 999999))
    otp_hash, salt = _hash_password(otp)
    expires = (datetime.datetime.now() +
               datetime.timedelta(minutes=15)).isoformat()
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        conn.execute("UPDATE reset_tokens SET used = 1 WHERE user_id = ? AND used = 0",
                     (user_id,))
        conn.execute(
            "INSERT INTO reset_tokens (user_id, token, expires_at) VALUES (?, ?, ?)",
            (user_id, otp_hash + ":" + salt, expires)
        )
        conn.commit(); conn.close()
    except Exception:
        pass
    return otp


def verify_and_reset_password(user_id: int, otp: str, new_password: str) -> tuple[bool, str]:
    """Verify OTP and reset password atomically."""
    if len(new_password) < 6:
        return False, "Password must be at least 6 characters."
    now = datetime.datetime.now().isoformat()
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        rows = conn.execute(
            "SELECT id, token, expires_at FROM reset_tokens "
            "WHERE user_id = ? AND used = 0 AND expires_at > ? "
            "ORDER BY id DESC LIMIT 5",
            (user_id, now)
        ).fetchall()
        conn.close()
    except Exception:
        return False, "Database error."

    if not rows:
        return False, "No valid reset code found. Please request a new one."

    matched_id = None
    for row_id, token_field, _ in rows:
        parts = token_field.split(":", 1)
        if len(parts) != 2:
            continue
        stored_hash, salt = parts
        if _verify_password(otp.strip(), stored_hash, salt):
            matched_id = row_id
            break

    if not matched_id:
        return False, "Incorrect code. Please try again."

    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        conn.execute("UPDATE reset_tokens SET used = 1 WHERE id = ?", (matched_id,))
        new_hash, new_salt = _hash_password(new_password)
        conn.execute("UPDATE users SET password_hash = ?, salt = ? WHERE id = ?",
                     (new_hash, new_salt, user_id))
        conn.commit(); conn.close()
    except Exception as e:
        return False, str(e)

    return True, "Password reset successfully! You can now log in."


def _try_email_otp(user: dict, otp: str) -> bool:
    """Attempt to email the OTP. Returns True if sent successfully."""
    try:
        from notification_service import send_email, is_email_configured
        if not is_email_configured():
            return False
        subject = "Your MediCare AI reset code"
        # Clean plain-text version (important for spam filters)
        plain = (
            f"Hi {user['full_name']},\n\n"
            f"You requested a password reset for your MediCare AI account.\n\n"
            f"Your reset code is: {otp}\n\n"
            f"This code is valid for 15 minutes.\n"
            f"If you did not make this request, you can ignore this message.\n\n"
            f"MediCare AI"
        )
        # Minimal HTML — avoids spam triggers (no heavy styling, no images)
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0;padding:0;background:#f8fafc;font-family:Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr><td align="center" style="padding:32px 16px;">
            <table width="480" cellpadding="0" cellspacing="0"
                   style="background:#ffffff;border-radius:12px;
                          border:1px solid #e2e8f0;padding:32px;">
              <tr><td>
                <p style="font-size:1.1rem;font-weight:700;color:#0f172a;margin:0 0 4px;">
                  &#128274; Password Reset Code
                </p>
                <p style="color:#64748b;font-size:0.88rem;margin:0 0 24px;">
                  MediCare AI
                </p>
                <p style="color:#334155;font-size:0.92rem;">
                  Hi {user['full_name']},
                </p>
                <p style="color:#334155;font-size:0.92rem;">
                  Use the code below to reset your password.
                </p>
                <div style="background:#f1f5f9;border-radius:10px;
                            padding:20px;text-align:center;margin:24px 0;
                            border:1px solid #cbd5e1;">
                  <div style="font-size:2rem;font-weight:800;
                              letter-spacing:10px;color:#0096c7;
                              font-family:'Courier New',monospace;">
                    {otp}
                  </div>
                  <div style="color:#94a3b8;font-size:0.78rem;margin-top:8px;">
                    Valid for 15 minutes
                  </div>
                </div>
                <p style="color:#94a3b8;font-size:0.78rem;">
                  If you did not request this, ignore this email.
                  Your password will not change.
                </p>
              </td></tr>
            </table>
          </td></tr>
        </table>
        </body></html>
        """
        return send_email(user["email"], subject, plain, html_body)
    except Exception:
        return False


# ============================================================================
# SHARED CSS
# ============================================================================

_AUTH_CSS = """
<style>
/* Hide sidebar on auth page */
section[data-testid="stSidebar"] { display: none !important; }

/* Vibrant animated gradient background */
.stApp {
    background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab) !important;
    background-size: 400% 400% !important;
    animation: gradient 15s ease infinite;
    min-height: 100vh;
}

@keyframes gradient {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* Logo block - Glowing effect */
.auth-logo {
    text-align: center;
    margin-bottom: 2rem;
    animation: fadeInDown 0.8s ease-out;
}
.auth-logo-icon {
    font-size: 4.5rem;
    line-height: 1;
    filter: drop-shadow(0 8px 16px rgba(0,0,0,0.2));
    animation: bounce 2s infinite;
}
.auth-logo-title {
    font-size: 2.8rem;
    font-weight: 900;
    color: #ffffff;
    letter-spacing: -1px;
    margin: 0.8rem 0 0.2rem;
    text-shadow: 0 4px 20px rgba(0,0,0,0.3), 0 0 40px rgba(255,255,255,0.1);
}
.auth-logo-sub {
    font-size: 0.95rem;
    color: rgba(255,255,255,0.95);
    font-weight: 500;
    letter-spacing: 0.5px;
}
.auth-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: linear-gradient(135deg, #ff6b6b, #ee5a6f, #c92a2a);
    color: #fff;
    padding: 6px 16px;
    border-radius: 30px;
    font-size: 0.78rem;
    font-weight: 700;
    margin-top: 0.8rem;
    box-shadow: 0 6px 20px rgba(255,107,107,0.4);
    letter-spacing: 0.5px;
}

/* Form container */
.stForm {
    background: rgba(255, 255, 255, 0.95) !important;
    border-radius: 20px !important;
    padding: 2.5rem !important;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3) !important;
    backdrop-filter: blur(10px);
    animation: slideUp 0.6s ease-out;
}

@keyframes fadeInDown {
    from { opacity: 0; transform: translateY(-30px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes slideUp {
    from { opacity: 0; transform: translateY(50px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}

/* Tabs - Modern style */
div[data-testid="stTabs"] button {
    font-size: 0.9rem !important;
    font-weight: 700 !important;
    color: #64748b !important;
    padding: 0.7rem 1.2rem !important;
    border-radius: 12px 12px 0 0 !important;
    transition: all 0.3s;
    background: transparent !important;
}
div[data-testid="stTabs"] button[aria-selected="true"] {
    color: #fff !important;
    background: linear-gradient(135deg, #ff6b6b, #ee5a6f) !important;
    border-bottom: 3px solid #ff6b6b !important;
    box-shadow: 0 4px 12px rgba(255,107,107,0.3);
}

/* Inputs - Modern design */
.stTextInput input {
    background: linear-gradient(135deg, #f8f9fa, #ffffff) !important;
    border: 2px solid #e9ecef !important;
    border-radius: 12px !important;
    color: #2d3748 !important;
    font-size: 0.95rem !important;
    padding: 0.75rem 1rem !important;
    transition: all 0.3s !important;
}

/* PASSWORD FIELD SPECIFIC - MASK CHARACTERS */
input[type="password"] {
    font-size: 1.5rem !important;
    letter-spacing: 0.4em !important;
    font-family: 'Arial', sans-serif !important;
    -webkit-text-security: disc !important;
    text-security: disc !important;
}

/* Ensure password field also has proper styling */
.stTextInput input[type="password"] {
    background: linear-gradient(135deg, #f8f9fa, #ffffff) !important;
    border: 2px solid #e9ecef !important;
    border-radius: 12px !important;
    color: #2d3748 !important;
    font-size: 1.5rem !important;
    padding: 0.75rem 1rem !important;
    letter-spacing: 0.4em !important;
    -webkit-text-security: disc !important;
    text-security: disc !important;
}

.stTextInput input:focus {
    border-color: #ee5a6f !important;
    box-shadow: 0 0 0 4px rgba(238,90,111,0.15) !important;
    background: #ffffff !important;
    transform: translateY(-2px);
}

.stTextInput input[type="password"]:focus {
    border-color: #ee5a6f !important;
    box-shadow: 0 0 0 4px rgba(238,90,111,0.15) !important;
    background: #ffffff !important;
    transform: translateY(-2px);
}

/* Labels - Make them visible */
.stTextInput label,
label {
    color: #2d3748 !important;
    font-size: 0.9rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.3px;
    display: block !important;
    margin-bottom: 8px !important;
}

/* Placeholder text */
.stTextInput input::placeholder {
    color: #a0aec0 !important;
}

/* Primary submit button - Vibrant gradient */
div[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #ff6b6b, #ee5a6f, #c92a2a) !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 800 !important;
    font-size: 0.95rem !important;
    color: #fff !important;
    padding: 0.75rem 0 !important;
    box-shadow: 0 8px 25px rgba(238,90,111,0.4);
    transition: all 0.3s !important;
    letter-spacing: 0.5px;
}
div[data-testid="stFormSubmitButton"] > button:hover {
    opacity: 1 !important;
    transform: translateY(-3px) !important;
    box-shadow: 0 12px 35px rgba(238,90,111,0.5) !important;
}

/* Back button */
div[data-testid="stButton"] > button {
    background: rgba(255,255,255,0.2) !important;
    border: 2px solid rgba(255,255,255,0.5) !important;
    border-radius: 10px !important;
    color: #fff !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    transition: all 0.3s;
}
div[data-testid="stButton"] > button:hover {
    background: rgba(255,255,255,0.35) !important;
    border-color: #fff !important;
}

/* Alert boxes - Color coded */
.stAlert {
    border-radius: 12px !important;
    font-size: 0.9rem !important;
    border-left: 4px solid !important;
    padding: 1rem !important;
}

/* OTP display card */
.otp-card {
    background: linear-gradient(135deg, rgba(255,107,107,0.1), rgba(238,90,111,0.1));
    border: 2px solid rgba(238,90,111,0.3);
    border-radius: 16px;
    padding: 1.5rem 1.8rem;
    margin: 1rem 0 1.2rem;
    text-align: center;
    box-shadow: 0 8px 20px rgba(238,90,111,0.15);
}
.otp-digits {
    font-size: 2.8rem;
    font-weight: 900;
    letter-spacing: 12px;
    color: #ee5a6f;
    font-family: 'Courier New', monospace;
    text-shadow: 0 4px 12px rgba(238,90,111,0.3);
}
.otp-hint {
    font-size: 0.8rem;
    color: #718096;
    margin-top: 8px;
    font-weight: 500;
}

/* Username reveal card */
.uname-card {
    background: linear-gradient(135deg, rgba(35,214,171,0.1), rgba(35,181,213,0.1));
    border: 2px solid rgba(35,214,171,0.3);
    border-radius: 14px;
    padding: 1rem 1.3rem;
    margin: 0.6rem 0 1.2rem;
    text-align: center;
    box-shadow: 0 6px 16px rgba(35,214,171,0.12);
}
.uname-label {
    font-size: 0.8rem;
    color: #718096;
    margin-bottom: 6px;
    font-weight: 600;
}
.uname-value {
    font-size: 1.35rem;
    font-weight: 800;
    color: #00a3a3;
    letter-spacing: 1px;
}

/* Radio buttons */
div[data-testid="stRadio"] label {
    font-weight: 600 !important;
    color: #2d3748 !important;
}

/* Selectbox styling */
.stSelectbox label {
    color: #2d3748 !important;
    font-size: 0.9rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.3px;
    display: block !important;
    margin-bottom: 8px !important;
}

/* Footer */
.auth-footer {
    text-align: center;
    color: rgba(255,255,255,0.8);
    font-size: 0.75rem;
    margin-top: 2rem;
    letter-spacing: 0.3px;
}
.auth-footer span {
    margin: 0 6px;
    opacity: 0.9;
}

/* Spinner enhancement */
.stSpinner > div {
    border-color: #ee5a6f !important;
}
</style>
"""


# ============================================================================
# STREAMLIT AUTH UI
# ============================================================================

def show_auth_page():
    """
    Full-page Login / Sign-Up / Forgot-Password UI.
    Sets st.session_state.authenticated & current_user on success.
    """
    st.markdown(_AUTH_CSS, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.5, 1])
    with col:

        # ── Brand header ────────────────────────────────────────────────────
        st.markdown("""
        <div class="auth-logo">
            <div class="auth-logo-icon">🩺</div>
            <div class="auth-logo-title">MediCare AI</div>
            <div class="auth-logo-sub">Intelligent Medical Appointment System</div>
            <div>
                <span class="auth-badge">
                    ✦ AI-Powered &nbsp;·&nbsp; Graph RAG &nbsp;·&nbsp; Emergency Smart
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        tab_login, tab_register, tab_recover = st.tabs(
            ["🔐  Login", "📝  Sign Up", "🔑  Forgot Password"]
        )

        # ════════════════════════════════════════════════════════════════════
        #  TAB 1 — LOGIN
        # ════════════════════════════════════════════════════════════════════
        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.form("login_form"):
                login_user_input = st.text_input(
                    "Username", placeholder="your_username")
                login_pw_input = st.text_input(
                    "Password", type="password", placeholder="••••••••")
                st.markdown("<br>", unsafe_allow_html=True)
                login_btn = st.form_submit_button(
                    "Login  →", use_container_width=True, type="primary")

            if login_btn:
                if not login_user_input.strip() or not login_pw_input:
                    st.error("Please enter both username and password.")
                else:
                    with st.spinner("Verifying..."):
                        ok, user = login_user(login_user_input, login_pw_input)
                    if ok:
                        st.session_state.authenticated = True
                        st.session_state.current_user = user
                        # Queue cookie write — app.py shell picks this up and sets it
                        from database import create_auth_token as _create_token
                        st.session_state["_pending_cookie_token"] = _create_token(user["id"])
                        st.success(f"Welcome back, **{user['full_name']}**! 🎉")
                        st.rerun()
                    else:
                        st.error("❌ Incorrect username or password.")
                        st.caption("💡 Forgot your details? Use the **Forgot Password** tab.")

        # ════════════════════════════════════════════════════════════════════
        #  TAB 2 — SIGN UP
        # ════════════════════════════════════════════════════════════════════
        with tab_register:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.form("register_form"):
                c1, c2 = st.columns(2)
                r_name     = c1.text_input("Full Name *",  placeholder="John Doe")
                r_username = c2.text_input("Username *",   placeholder="john_doe")

                c3, c4 = st.columns(2)
                r_email = c3.text_input("Email *",
                                        placeholder="john@email.com",
                                        help="Used for password recovery")
                r_phone = c4.text_input("Phone",  placeholder="+91XXXXXXXXXX")

                c5, c6 = st.columns(2)
                r_pw1 = c5.text_input("Password *",
                                      type="password", placeholder="Min. 6 chars")
                r_pw2 = c6.text_input("Confirm Password *",
                                      type="password", placeholder="Repeat")

                r_role = st.selectbox(
                    "I am registering as",
                    options=["Patient", "Doctor"],
                    help="Doctors get access to the Doctor Dashboard to manage appointments.",
                    index=0
                )

                st.markdown("<br>", unsafe_allow_html=True)
                reg_btn = st.form_submit_button(
                    "Create Account  →", use_container_width=True, type="primary")

            if reg_btn:
                if not all([r_name.strip(), r_username.strip(),
                            r_email.strip(), r_pw1, r_pw2]):
                    st.error("Please fill in all required (*) fields.")
                elif r_pw1 != r_pw2:
                    st.error("❌ Passwords do not match.")
                else:
                    _role_val = "doctor" if "Doctor" in r_role else "patient"
                    with st.spinner("Creating your account..."):
                        ok, msg = register_user(r_username, r_pw1, r_name,
                                                r_email, r_phone, role=_role_val)
                    if ok:
                        st.success(f"✅ {msg}")
                        if _role_val == "doctor":
                            st.info("Doctor account created! After login, go to **Doctor Dashboard** in the sidebar.")
                        else:
                            st.info("Switch to the **Login** tab to sign in.")
                    else:
                        st.error(f"❌ {msg}")

        # ════════════════════════════════════════════════════════════════════
        #  TAB 3 — FORGOT PASSWORD  (2-step flow)
        # ════════════════════════════════════════════════════════════════════
        with tab_recover:
            st.markdown("<br>", unsafe_allow_html=True)

            if "rec_step" not in st.session_state:
                st.session_state.rec_step = 1
                st.session_state.rec_user = None

            # ── Step 1: enter email ──────────────────────────────────────
            if st.session_state.rec_step == 1:
                st.markdown(
                    "<p style='color:#7a8fa6;font-size:0.86rem;margin-bottom:1rem;'>"
                    "Enter the email address you registered with. We will reveal "
                    "your username and give you a 6-digit reset code.</p>",
                    unsafe_allow_html=True
                )
                with st.form("rec_form1"):
                    rec_email_in = st.text_input(
                        "Registered Email", placeholder="john@email.com")
                    st.markdown("<br>", unsafe_allow_html=True)
                    send_btn = st.form_submit_button(
                        "Send Reset Code  →", use_container_width=True, type="primary")

                if send_btn:
                    if not rec_email_in.strip():
                        st.error("Please enter your email address.")
                    else:
                        with st.spinner("Looking up your account..."):
                            found = lookup_by_email(rec_email_in)
                        if not found:
                            st.error("❌ No account found with that email.")
                            st.caption("Check spelling, or use the email you registered with.")
                        else:
                            otp = generate_reset_otp(found["id"])
                            email_sent = _try_email_otp(found, otp)
                            st.session_state.rec_user        = found
                            st.session_state.rec_otp         = otp
                            st.session_state.rec_email_sent  = email_sent
                            st.session_state.rec_step        = 2
                            st.rerun()

            # ── Step 2: show username + OTP, enter new password ──────────
            else:
                found      = st.session_state.rec_user
                otp_plain  = st.session_state.get("rec_otp", "------")
                email_sent = st.session_state.get("rec_email_sent", False)

                # Username reveal
                st.markdown(f"""
                <div class="uname-card">
                    <div class="uname-label">Your Username</div>
                    <div class="uname-value">@{found['username']}</div>
                </div>
                """, unsafe_allow_html=True)

                # OTP display
                try:
                    from notification_service import is_email_configured
                    _email_ready = is_email_configured()
                except Exception:
                    _email_ready = False

                if email_sent:
                    email_note = f'&#9993;&#65039; Code sent to <b>{found["email"]}</b>'
                elif _email_ready:
                    email_note = f'&#9888;&#65039; Failed to send to {found["email"]} &mdash; check your From-email is verified in SendGrid'
                else:
                    email_note = '&#9888;&#65039; Email not configured &mdash; use the code below'
                if email_sent:
                    st.markdown(f"""
                <div class="otp-card">
                    <div style="color:#64748b;font-size:0.78rem;margin-bottom:8px;">
                        {email_note}
                    </div>
                    <div style="font-size:2.2rem;margin:8px 0;">📬</div>
                    <div style="color:#38bdf8;font-size:1rem;font-weight:600;">Check your inbox</div>
                    <div class="otp-hint" style="margin-top:6px;">⏱ Expires in 15 minutes &nbsp;·&nbsp; Check Spam if not seen</div>
                </div>
                """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                <div class="otp-card">
                    <div style="color:#64748b;font-size:0.78rem;margin-bottom:8px;">
                        {email_note}
                    </div>
                    <div class="otp-digits">{otp_plain}</div>
                    <div class="otp-hint">⏱ Expires in 15 minutes</div>
                </div>
                """, unsafe_allow_html=True)

                with st.form("rec_form2"):
                    otp_entered = st.text_input(
                        "Enter 6-Digit Code", placeholder="e.g. 483920", max_chars=6)
                    c7, c8 = st.columns(2)
                    new_pw1 = c7.text_input("New Password",     type="password",
                                            placeholder="Min. 6 chars")
                    new_pw2 = c8.text_input("Confirm Password", type="password",
                                            placeholder="Repeat")
                    st.markdown("<br>", unsafe_allow_html=True)
                    reset_btn = st.form_submit_button(
                        "Reset Password  →", use_container_width=True, type="primary")

                if reset_btn:
                    if not all([otp_entered.strip(), new_pw1, new_pw2]):
                        st.error("Please fill in all fields.")
                    elif new_pw1 != new_pw2:
                        st.error("\u274c Passwords do not match.")
                    else:
                        with st.spinner("Resetting your password..."):
                            ok, msg = verify_and_reset_password(
                                found["id"], otp_entered, new_pw1)
                        if ok:
                            st.success(f"\u2705 {msg}")
                            for k in ["rec_step", "rec_user", "rec_otp",
                                      "rec_email_sent"]:
                                st.session_state.pop(k, None)
                            st.info("Switch to the **Login** tab to sign in.")
                        else:
                            st.error(f"\u274c {msg}")

                # ── SendGrid setup guide (shown when email not configured) ──
                if not email_sent:
                    st.markdown("<br>", unsafe_allow_html=True)
                    with st.expander("\u2709\ufe0f Configure email so OTPs are sent automatically"):
                        st.markdown("""
**Step 1 — Create a free SendGrid account**
- Go to [sendgrid.com/free](https://sendgrid.com/free/) and sign up (100 emails/day free)

**Step 2 — Create an API Key**
- Dashboard → Settings → API Keys → **Create API Key**
- Permission: **Restricted Access → Mail Send → Full Access**
- Copy the key (shown only once)

**Step 3 — Verify a Sender Email**
- Dashboard → Settings → **Sender Authentication → Single Sender Verification**
- Add and verify the email you want to send *from*

**Step 4 — Add to your `.env` file**
```
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxx
SENDGRID_FROM_EMAIL=your-verified@email.com
```

**Step 5** — Restart the app. Emails will work automatically.
                        """)

                        st.markdown("**Test your current configuration:**")
                        test_col1, test_col2 = st.columns([2, 1])
                        test_addr = test_col1.text_input(
                            "Send test email to", placeholder="you@email.com",
                            key="sg_test_addr", label_visibility="collapsed")
                        if test_col2.button("Send Test", key="sg_test_btn",
                                            use_container_width=True):
                            if not test_addr.strip():
                                st.warning("Enter a recipient email first.")
                            else:
                                try:
                                    from notification_service import send_email, is_email_configured
                                    if not is_email_configured():
                                        st.error(
                                            "SENDGRID_API_KEY is still empty in `.env`. "
                                            "Add it and save the file, then click Send Test again."
                                        )
                                    else:
                                        sent = send_email(
                                            test_addr.strip(),
                                            "MediCare AI \u2014 Email Test",
                                            "If you received this, SendGrid is working correctly!"
                                        )
                                        if sent:
                                            st.success("\u2705 Test email sent! Check your inbox.")
                                        else:
                                            st.error(
                                                "\u274c Send failed. Common reasons:\n"
                                                "- API key is wrong or expired\n"
                                                "- Sender email not verified in SendGrid\n"
                                                "- Free plan daily limit reached"
                                            )
                                except Exception as ex:
                                    st.error(f"Error: {ex}")

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("← Use a different email"):
                    for k in ["rec_step", "rec_user", "rec_otp", "rec_email_sent"]:
                        st.session_state.pop(k, None)
                    st.rerun()

        # ── Footer ──────────────────────────────────────────────────────────
        st.markdown("""
        <div class="auth-footer">
            🔒 Passwords encrypted with PBKDF2
            <span>·</span> Data is private
            <span>·</span> Powered by NVIDIA AI &amp; Graph RAG
        </div>
        """, unsafe_allow_html=True)


# ============================================================================
# SIDEBAR USER WIDGET
# ============================================================================

def show_user_sidebar_widget():
    """Render user card + logout at the top of the sidebar."""
    user       = st.session_state.get("current_user", {})
    full_name  = user.get("full_name", "User")
    username   = user.get("username", "")
    role       = user.get("role", "patient")
    is_doctor  = role == "doctor"
    is_admin   = role == "admin"
    role_icon  = "👨‍⚕️" if is_doctor else ("🔑" if is_admin else "🧑‍💼")
    role_label = "Doctor" if is_doctor else ("Admin" if is_admin else "Patient")

    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg,#0f2027 0%,#203a43 100%);
        border: 1px solid rgba(0,180,216,0.22);
        border-radius: 14px; padding: 13px 15px 11px; margin-bottom: 4px;">
        <div style="display:flex;align-items:center;gap:10px;">
            <div style="
                width:36px;height:36px;border-radius:50%;flex-shrink:0;
                background:linear-gradient(135deg,#00b4d8,#0077b6);
                display:flex;align-items:center;justify-content:center;
                font-size:1rem;">{role_icon}</div>
            <div>
                <div style="font-weight:700;font-size:0.92rem;color:#e2e8f0;
                            white-space:nowrap;overflow:hidden;
                            max-width:140px;text-overflow:ellipsis;">
                    {full_name}
                </div>
                <div style="font-size:0.71rem;color:#64748b;margin-top:2px;">
                    {role_label} &nbsp;·&nbsp; @{username}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if is_doctor:
        st.page_link("pages/doctor_dashboard.py", label="👨‍⚕️ Doctor Dashboard")

    if st.button("🚪 Logout", use_container_width=True, key="logout_btn"):
        # Signal app.py shell to delete the browser cookie on next rerun
        st.session_state["_clear_cookie"] = True
        for key in [k for k in list(st.session_state.keys()) if k != "_clear_cookie"]:
            del st.session_state[key]
        st.rerun()
