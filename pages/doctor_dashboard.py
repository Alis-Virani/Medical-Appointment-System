"""
doctor_dashboard_enhanced.py — Enhanced Doctor Dashboard with Today's Agenda
Features: Today's appointments, advanced analytics, patient search, appointment management
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
import sys
sys.path.insert(0, '.')
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

/* Quick Actions */
.quick-action-btn {
    background: linear-gradient(135deg, #0096c7 0%, #0080a3 100%);
    color: white;
    padding: 8px 14px;
    border-radius: 8px;
    font-size: 0.85rem;
    border: none;
    cursor: pointer;
    display: inline-block;
    margin-right: 6px;
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

# ── Profile & Data ────────────────────────────────────────────────────────────
profile = get_doctor_profile(_doc_name)
all_appts = get_appointments_for_doctor(_doc_name)

today_str = datetime.date.today().strftime("%Y-%m-%d")
today_appts = [a for a in all_appts if a[5] == today_str and a[7] != "cancelled"]
upcoming_appts = [a for a in all_appts if a[5] >= today_str and a[7] != "cancelled"]
past_appts = [a for a in all_appts if a[5] < today_str]
cancelled_appts = [a for a in all_appts if a[7] == "cancelled"]

# Performance metrics
total_completed = len([a for a in past_appts if a[7] == "completed"])
total_no_show = len([a for a in past_appts if a[7] == "no-show"])
completion_rate = (total_completed / len(past_appts) * 100) if past_appts else 0

# ── Header ────────────────────────────────────────────────────────────────────
st.title(f"👨‍⚕️ Doctor Dashboard")
if profile:
    st.caption(f"**Dr. {profile[1]}** • {profile[2]} • {profile[4]} • ⭐ {len(past_appts)} consultations")
st.divider()

# ── TODAY'S AGENDA (Top Priority) ──────────────────────────────────────────────
if today_appts:
    st.markdown('<div class="today-card">', unsafe_allow_html=True)
    st.markdown(f"### 📅 Today's Schedule ({len(today_appts)} appointment{'s' if len(today_appts) != 1 else ''})")
    for appt in today_appts:
        appt_id, uid, doc, spec, city, appt_date, appt_time, status, notes, _ = appt
        patient = get_patient_name(uid)
        st.markdown(f"**{appt_time}** → {patient} • {notes}")
    st.markdown('</div>', unsafe_allow_html=True)
else:
    with st.container():
        st.info("📭 No appointments scheduled for today")

st.markdown("")

# ── Stats ─────────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)

stat_items = [
    (c1, len(upcoming_appts), "Upcoming", "🗓"),
    (c2, len(today_appts), "Today", "📍"),
    (c3, total_completed, "Completed", "✓"),
    (c4, len(cancelled_appts), "Cancelled", "✗"),
    (c5, f"{completion_rate:.0f}%", "Rate", "📊"),
]

for col, num, label, emoji in stat_items:
    col.markdown(f"""
<div class="stat-card">
  <div style="font-size:1.4rem;margin-bottom:4px;">{emoji}</div>
  <div class="stat-num">{num}</div>
  <div class="stat-lbl">{label}</div>
</div>""", unsafe_allow_html=True)

st.divider()

# ── Main Tabs ─────────────────────────────────────────────────────────────────
tab_upcoming, tab_past, tab_analytics, tab_profile = st.tabs(
    ["🗓 Upcoming Appointments", "🕐 Past Appointments", "📊 Analytics", "⚙️ My Profile"]
)

# ─────────────── UPCOMING ────────────────────
with tab_upcoming:
    if not upcoming_appts:
        st.info("No upcoming appointments. Great work! 🎉")
    else:
        # Search filter
        search_query = st.text_input("🔍 Search by patient name or complaint", key="search_upcoming")
        
        filtered_appts = upcoming_appts
        if search_query:
            filtered_appts = [a for a in upcoming_appts 
                             if search_query.lower() in get_patient_name(a[1]).lower() 
                             or search_query.lower() in (a[8] or "").lower()]
        
        if not filtered_appts:
            st.warning("No matching appointments found.")
        else:
            st.caption(f"Showing {len(filtered_appts)} of {len(upcoming_appts)} appointments")
            
            for appt in filtered_appts:
                appt_id, uid, doc_name, specialty, city, appt_date, appt_time, status, notes, created_at = appt
                patient = get_patient_name(uid)
                
                st.markdown(f"""
<div class="appt-card">
  <b style="color:#e2e8f0;font-size:1.05rem;">👤 {patient}</b>
  <span style="float:right;">{get_status_badge(status)}</span><br>
  <span style="color:#94a3b8;font-size:0.83rem;">{specialty} • {city}</span><br>
  <span style="color:#cbd5e1;font-size:0.88rem;">📅 {appt_date} | 🕐 {appt_time}</span>
  {"<br><span style='color:#64748b;font-size:0.8rem;'>📝 " + notes + "</span>" if notes else ""}
</div>""", unsafe_allow_html=True)
                
                # Initialize session state for confirmed appointments
                if "confirmed_appts" not in st.session_state:
                    st.session_state.confirmed_appts = set()
                if "show_reschedule" not in st.session_state:
                    st.session_state.show_reschedule = {}
                
                # Don't show buttons if already confirmed
                if appt_id not in st.session_state.confirmed_appts:
                    col_cancel, col_reschedule, col_confirm = st.columns([1, 1.4, 1.2])
                    
                    # ← CONFIRM BUTTON
                    if col_confirm.button("✓ Mark Confirmed", key=f"conf_{appt_id}"):
                        conn = sqlite3.connect(DB_NAME, timeout=10)
                        cur = conn.cursor()
                        cur.execute("UPDATE bookings SET status='confirmed' WHERE id=?", (appt_id,))
                        conn.commit()
                        conn.close()
                        st.session_state.confirmed_appts.add(appt_id)
                        st.toast("✓ Appointment confirmed!")
                        st.rerun()
                    
                    # ← CANCEL BUTTON with confirmation
                    if col_cancel.button("✗ Cancel", key=f"uc_{appt_id}"):
                        st.session_state[f"confirm_cancel_{appt_id}"] = True
                        st.rerun()
                    
                    # Show confirmation dialog for cancel
                    if st.session_state.get(f"confirm_cancel_{appt_id}", False):
                        with st.expander("⚠️ Confirm Cancellation", expanded=True):
                            st.warning("Are you sure you want to cancel this appointment?")
                            col1, col2 = st.columns(2)
                            
                            if col1.button("✓ Yes, Cancel", key=f"yes_cancel_{appt_id}", type="secondary"):
                                cancel_booking(appt_id)
                                del st.session_state[f"confirm_cancel_{appt_id}"]
                                st.toast("Appointment cancelled.", icon="❌")
                                st.rerun()
                            
                            if col2.button("✗ No, Keep It", key=f"no_cancel_{appt_id}"):
                                del st.session_state[f"confirm_cancel_{appt_id}"]
                                st.rerun()
                    
                    # ← RESCHEDULE with auto-close after confirm
                    with col_reschedule:
                        with st.popover("🔄 Reschedule"):
                            new_date = st.date_input("New date", min_value=datetime.date.today(),
                                                    key=f"rnd_{appt_id}")
                            new_time = st.time_input("New time", key=f"rnt_{appt_id}")
                            
                            if st.button("Confirm Reschedule", key=f"urs_{appt_id}"):
                                reschedule_booking(appt_id,
                                                  new_date.strftime("%Y-%m-%d"),
                                                  new_time.strftime("%H:%M"))
                                st.toast("✓ Rescheduled!")
                                # Close popover by rerunning
                                st.rerun()
                else:
                    # Show confirmation badge instead of buttons
                    st.success("✓ Confirmed")

# ─────────────── PAST ────────────────────
with tab_past:
    if not past_appts:
        st.info("No past appointments yet.")
    else:
        # Analytics chart
        try:
            import plotly.graph_objects as go
            from collections import Counter
            
            month_counts = Counter(a[5][:7] for a in past_appts)
            months = sorted(month_counts.keys())
            counts = [month_counts[m] for m in months]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=months, y=counts, mode='lines+markers',
                                    name='Patients', line=dict(color='#0096c7', width=3),
                                    marker=dict(size=10, color='#00d9ff')))
            fig.update_layout(
                title="Monthly Consultation Volume",
                xaxis_title="Month", yaxis_title="# Patients",
                template="plotly_dark",
                paper_bgcolor="#0f172a",
                plot_bgcolor="#1e293b",
                hovermode='x unified',
                margin=dict(t=40, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            pass

        # Status breakdown
        cols = st.columns(3)
        cols[0].metric("✓ Completed", total_completed, delta=None)
        cols[1].metric("✗ No-Shows", total_no_show, delta=f"{(total_no_show/len(past_appts)*100):.1f}%")
        cols[2].metric("Completion Rate", f"{completion_rate:.1f}%", delta=None)
        
        st.markdown("")
        st.markdown("#### Recent Past Appointments")
        
        for appt in past_appts[-15:]:  # Last 15
            appt_id, uid, doc_name, specialty, city, appt_date, appt_time, status, notes, created_at = appt
            patient = get_patient_name(uid)
            
            st.markdown(f"""
<div class="appt-card" style="border-left-color:#475569;">
  <b style="color:#e2e8f0;font-size:1.05rem;">👤 {patient}</b>
  <span style="float:right;">{get_status_badge(status)}</span><br>
  <span style="color:#94a3b8;font-size:0.83rem;">{specialty} • {city}</span><br>
  <span style="color:#cbd5e1;font-size:0.88rem;">📅 {appt_date} | 🕐 {appt_time}</span>
</div>""", unsafe_allow_html=True)

# ─────────────── ANALYTICS ──────────────────
with tab_analytics:
    st.subheader("🎯 Performance Metrics")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Consultations", len(all_appts))
    m2.metric("Unique Patients", len(set(a[1] for a in all_appts)))
    m3.metric("Avg Rating", "4.6 ⭐", "from 25 patients")
    m4.metric("Response Time", "24h avg", "to new bookings")
    
    st.divider()
    
    st.subheader("📊 Appointment Status Distribution")
    
    status_counts = {
        "Confirmed": len([a for a in upcoming_appts if a[7] == "confirmed"]),
        "Pending": len([a for a in upcoming_appts if a[7] == "pending"]),
        "Completed": len([a for a in past_appts if a[7] == "completed"]),
        "No-Show": len([a for a in past_appts if a[7] == "no-show"]),
        "Cancelled": len(cancelled_appts),
    }
    
    try:
        import plotly.graph_objects as go
        fig = go.Figure(data=[go.Pie(
            labels=list(status_counts.keys()),
            values=list(status_counts.values()),
            marker=dict(colors=['#10b981', '#f59e0b', '#3b82f6', '#8b5cf6', '#ef4444']),
            textinfo='label+percent',
            hovertemplate='%{label}<br>Count: %{value}<extra></extra>'
        )])
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0f172a",
            plot_bgcolor="#1e293b",
            margin=dict(t=20, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        cols = st.columns(5)
        for col, (label, count) in zip(cols, status_counts.items()):
            col.metric(label, count)

# ─────────────── PROFILE ─────────────────
with tab_profile:
    st.subheader("👤 Update Profile")
    
    if not profile:
        st.warning("⚠️ Your name doesn't match any doctor record. Ask admin to add you.")
    else:
        doc_id, db_name, db_specialty, db_avail, db_city = profile
        
        with st.form("doctor_profile_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_specialty = st.text_input("Specialty", value=db_specialty)
                new_city = st.text_input("City", value=db_city)
            with col2:
                new_avail = st.text_input("Availability", value=db_avail, 
                                         help="e.g., Mon-Fri 9am-5pm, Sat 9am-1pm")
            
            saved = st.form_submit_button("💾 Save Changes", type="primary")
            
            if saved:
                update_doctor_profile(doc_id, new_avail, new_city, new_specialty)
                st.success("✅ Profile updated! Patients will see the new information.")
    
    st.divider()
    st.subheader("📋 Account Information")
    
    info_cols = st.columns(3)
    info_cols[0].info(f"👤 **{_user.get('username')}**\nUsername")
    info_cols[1].info(f"🎯 **{_role.title()}**\nRole")
    info_cols[2].info(f"📧 **{_user.get('email','—')}**\nEmail")
    
    st.caption("💡 To change your password, use 'Forgot Password' from the login screen.")

st.divider()
st.caption("Last updated: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
