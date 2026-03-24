"""
doctor_dashboard.py — Doctor Admin Dashboard
Streamlit page accessible to users with role='doctor'
"""
import streamlit as st

# ── Auth guard ────────────────────────────────────────────────────────────────
if not st.session_state.get("authenticated", False):
    st.warning("Please log in first.")
    st.page_link("pages/chat.py", label="🔒 Go to Login")
    st.stop()

_user = st.session_state.get("current_user", {})
_role = _user.get("role", "patient")

if _role != "doctor":
    st.error("🚫 This page is only accessible to doctors.")
    st.page_link("pages/chat.py", label="💬 Back to Chat")
    st.stop()

import sqlite3, datetime, re
from database import DB_NAME, cancel_booking, reschedule_booking
from auth import show_user_sidebar_widget

_doc_name = _user.get("full_name", "Doctor")

# ── Enhanced CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); }

/* Stats Cards */
.stat-card {
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    border-radius: 16px; padding: 24px;
    text-align: center; border: 1px solid #475569;
    box-shadow: 0 4px 20px rgba(0, 150, 199, 0.1);
    transition: all 0.3s ease;
}
.stat-card:hover { 
    border-color: #0096c7;
    box-shadow: 0 6px 30px rgba(0, 150, 199, 0.2);
    transform: translateY(-2px);
}
.stat-num  { 
    font-size: 2.8rem; font-weight: 900; color: #00d9ff;
    text-shadow: 0 0 10px rgba(0, 217, 255, 0.3);
}
.stat-lbl  { font-size: 0.9rem; color: #cbd5e1; margin-top: 8px; font-weight: 600; }

/* Appointment Cards */
.appt-card {
    background: linear-gradient(135deg, #1e293b 0%, #263549 100%);
    border-radius: 12px; padding: 16px 20px;
    margin-bottom: 12px; border-left: 5px solid #0096c7;
    border: 1px solid #334155;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    transition: all 0.2s ease;
}
.appt-card:hover { 
    border-color: #00d9ff;
    box-shadow: 0 4px 16px rgba(0, 150, 199, 0.2);
}

/* Status Badges */
.badge-confirmed { 
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: white; padding: 4px 10px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 600; display: inline-block;
}
.badge-pending { 
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    color: white; padding: 4px 10px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 600; display: inline-block;
}
.badge-completed { 
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    color: white; padding: 4px 10px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 600; display: inline-block;
}
.badge-cancelled { 
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    color: white; padding: 4px 10px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 600; display: inline-block;
}
.badge-no-show { 
    background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
    color: white; padding: 4px 10px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 600; display: inline-block;
}

/* Today Agenda */
.today-card {
    background: linear-gradient(135deg, #065f46 0%, #047857 100%);
    border: 1px solid #10b981;
    border-radius: 14px; padding: 20px;
    color: #d1fae5; margin-bottom: 20px;
    box-shadow: 0 4px 20px rgba(16, 185, 129, 0.1);
}

/* Section Headers */
.section-header {
    color: #00d9ff;
    font-size: 1.3rem;
    font-weight: 700;
    margin: 20px 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 2px solid #0096c7;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    show_user_sidebar_widget()
    st.divider()
    st.page_link("pages/chat.py", label="💬 Back to Chat")

# ── Helper Functions ──────────────────────────────────────────────────────────
def get_doctor_profile(doc_name: str):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    cur.execute("SELECT id, name, specialty, availability, city FROM doctors_v2 WHERE name LIKE ? LIMIT 1",
                (f"%{doc_name}%",))
    row = cur.fetchone()
    conn.close()
    return row

def get_appointments_for_doctor(doc_name: str):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, user_id, doctor_name, specialty, city,
               appointment_date, appointment_time, status, notes, created_at
        FROM bookings
        WHERE doctor_name LIKE ?
        ORDER BY appointment_date ASC, appointment_time ASC
    """, (f"%{doc_name}%",))
    rows = cur.fetchall()
    conn.close()
    return rows

def update_doctor_profile(doc_id: int, availability: str, city: str, specialty: str):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    cur.execute("""
        UPDATE doctors_v2 SET availability=?, city=?, specialty=?
        WHERE id=?
    """, (availability, city, specialty, doc_id))
    conn.commit()
    conn.close()

def get_patient_name(user_id):
    """Try to look up patient full_name from users table."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        cur = conn.cursor()
        cur.execute("SELECT full_name FROM users WHERE id=?", (user_id,))
        row = cur.fetchone()
        conn.close()
        return row[0] if row else f"Patient #{user_id}"
    except Exception:
        return f"Patient #{user_id}"

def get_status_badge(status: str) -> str:
    """Return HTML badge for appointment status"""
    status_lower = status.lower() if status else "pending"
    badge_map = {
        "confirmed": "<span class='badge-confirmed'>✓ Confirmed</span>",
        "pending": "<span class='badge-pending'>⏳ Pending</span>",
        "completed": "<span class='badge-completed'>✓ Completed</span>",
        "cancelled": "<span class='badge-cancelled'>✗ Cancelled</span>",
        "no-show": "<span class='badge-no-show'>✗ No-Show</span>",
    }
    return badge_map.get(status_lower, f"<span class='badge-pending'>{status}</span>")

# ── Profile ───────────────────────────────────────────────────────────────────
profile = get_doctor_profile(_doc_name)
all_appts = get_appointments_for_doctor(_doc_name)

today_str = datetime.date.today().strftime("%Y-%m-%d")
upcoming_appts = [a for a in all_appts if a[5] >= today_str and a[7] != "cancelled"]
past_appts     = [a for a in all_appts if a[5] < today_str]
cancelled_appts = [a for a in all_appts if a[7] == "cancelled"]

# ── Header ────────────────────────────────────────────────────────────────────
st.title(f"👨‍⚕️ Dr. Dashboard")
if profile:
    st.caption(f"**{profile[1]}** · {profile[2]} · {profile[4]}")
st.divider()

# ── Stats ─────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
for col, num, label in [
    (c1, len(upcoming_appts),  "Upcoming"),
    (c2, len(past_appts),      "Past Visits"),
    (c3, len(cancelled_appts), "Cancelled"),
    (c4, len(all_appts),       "Total Booked"),
]:
    col.markdown(f"""
<div class="stat-card">
  <div class="stat-num">{num}</div>
  <div class="stat-lbl">{label}</div>
</div>""", unsafe_allow_html=True)

st.divider()

# ── Main Tabs ─────────────────────────────────────────────────────────────────
tab_upcoming, tab_past, tab_profile = st.tabs(
    ["🗓 Upcoming Appointments", "🕐 Past Appointments", "⚙️ My Profile"]
)

# ─────────────── UPCOMING ────────────────
with tab_upcoming:
    if not upcoming_appts:
        st.info("No upcoming appointments.")
    else:
        for appt in upcoming_appts:
            appt_id, uid, doc_name, specialty, city, appt_date, appt_time, status, notes, created_at = appt
            patient = get_patient_name(uid)
            st.markdown(f"""
<div class="appt-card">
  <b style="color:#e2e8f0;font-size:1rem;">👤 {patient}</b>
  <span style="float:right;color:#94a3b8;font-size:0.8rem;">#{appt_id}</span><br>
  <span style="color:#94a3b8;font-size:0.83rem;">{specialty} · {city}</span><br>
  <span style="color:#cbd5e1;font-size:0.88rem;">📅 {appt_date} &nbsp; 🕐 {appt_time}</span>
  {"<br><span style='color:#64748b;font-size:0.8rem;'>📝 " + notes + "</span>" if notes else ""}
</div>""", unsafe_allow_html=True)

            col_cancel, col_reschedule, _ = st.columns([1, 1.4, 3])
            if col_cancel.button("Mark Cancelled", key=f"dc_{appt_id}"):
                cancel_booking(appt_id)
                st.toast("Appointment cancelled.")
                st.rerun()
            with col_reschedule:
                with st.popover("Reschedule"):
                    new_date = st.date_input("New date", min_value=datetime.date.today(),
                                             key=f"dnd_{appt_id}")
                    new_time = st.time_input("New time", key=f"dnt_{appt_id}")
                    if st.button("Confirm", key=f"drs_{appt_id}"):
                        reschedule_booking(appt_id,
                                           new_date.strftime("%Y-%m-%d"),
                                           new_time.strftime("%H:%M"))
                        st.toast("Rescheduled! ✅")
                        st.rerun()

# ─────────────── PAST ────────────────────
with tab_past:
    if not past_appts:
        st.info("No past appointments.")
    else:
        # frequency chart by month
        try:
            import plotly.express as px, pandas as pd
            from collections import Counter
            month_counts = Counter(a[5][:7] for a in past_appts)  # YYYY-MM
            df_m = pd.DataFrame(sorted(month_counts.items()), columns=["Month", "Patients"])
            fig = px.line(df_m, x="Month", y="Patients", markers=True,
                          title="Monthly Patient Volume", template="plotly_dark")
            fig.update_layout(paper_bgcolor="#131314", plot_bgcolor="#1e2130",
                              margin=dict(t=40, b=20))
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            pass

        for appt in past_appts[:20]:  # show last 20
            appt_id, uid, doc_name, specialty, city, appt_date, appt_time, status, notes, created_at = appt
            patient = get_patient_name(uid)
            st.markdown(f"""
<div class="appt-card" style="border-left-color:#475569;">
  <b style="color:#e2e8f0;font-size:1rem;">👤 {patient}</b>
  <span style="float:right;color:#94a3b8;font-size:0.8rem;">{status}</span><br>
  <span style="color:#94a3b8;font-size:0.83rem;">{specialty} · {city}</span><br>
  <span style="color:#cbd5e1;font-size:0.88rem;">📅 {appt_date} &nbsp; 🕐 {appt_time}</span>
</div>""", unsafe_allow_html=True)

# ─────────────── PROFILE ─────────────────
with tab_profile:
    st.subheader("Update Profile")
    if not profile:
        st.warning("Your name doesn't match any doctor record yet. "
                   "Ask admin to add you to the doctors table with your exact full name.")
    else:
        doc_id, db_name, db_specialty, db_avail, db_city = profile
        with st.form("doctor_profile_form"):
            new_specialty = st.text_input("Specialty", value=db_specialty)
            new_avail = st.text_input("Availability (e.g. Mon-Fri 9am-5pm)", value=db_avail)
            new_city = st.text_input("City", value=db_city)
            saved = st.form_submit_button("💾 Save Changes", type="primary")
            if saved:
                update_doctor_profile(doc_id, new_avail, new_city, new_specialty)
                st.success("✅ Profile updated! Patients will see the new info.")

    st.divider()
    st.subheader("Account")
    st.info(f"Username: **{_user.get('username')}** · Role: **{_role}** · "
            f"Email: **{_user.get('email','—')}**")
    st.caption("To change your password, use Forgot Password from the login screen.")
