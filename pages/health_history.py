"""
health_history.py — Patient Health History & Booking Timeline
Accessible via the Streamlit multi-page sidebar as "Health History"
"""
import streamlit as st

# ── Auth guard ────────────────────────────────────────────────────────────────
if not st.session_state.get("authenticated", False):
    st.warning("Please log in first.")
    st.page_link("pages/chat.py", label="🔒 Go to Login")
    st.stop()

import sys
sys.path.insert(0, '.')
from auth import show_user_sidebar_widget
from database import get_user_bookings, get_past_bookings, get_upcoming_bookings, find_medicines_for_symptoms, cancel_booking, reschedule_booking
import datetime

_user = st.session_state.get("current_user", {})
_user_id = str(_user.get("id", ""))
_user_name = _user.get("full_name", "User")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    show_user_sidebar_widget()
    st.divider()
    st.page_link("pages/chat.py", label="💬 Back to Chat")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.stApp { background-color: #131314; }
.card {
    background: #1e2130;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 10px;
    border-left: 4px solid #0096c7;
}
.card-cancelled { border-left-color: #ef4444 !important; }
.card-past      { border-left-color: #64748b !important; }
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}
.badge-confirmed  { background:#0e7490;  color:#fff; }
.badge-cancelled  { background:#7f1d1d;  color:#fca5a5; }
.badge-completed  { background:#14532d;  color:#86efac; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("📋 Health History")
st.caption(f"All appointments and health records for **{_user_name}**")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_upcoming, tab_past, tab_all = st.tabs(["🗓 Upcoming", "🕐 Past Visits", "📁 All Records"])

# ────────────────────────────── UPCOMING ─────────────────────────────────────
with tab_upcoming:
    upcoming = get_upcoming_bookings(_user_id)
    if not upcoming:
        st.info("No upcoming appointments. Book one from the chat!")
    else:
        st.markdown(f"**{len(upcoming)} upcoming appointment(s)**")
        for row in upcoming:
            booking_id, doc_name, specialty, city, appt_date, appt_time, status = row
            badge_cls = f"badge-{status}" if status in ("confirmed", "cancelled") else "badge-confirmed"
            st.markdown(f"""
<div class="card {'card-cancelled' if status == 'cancelled' else ''}">
  <b style="color:#e2e8f0;font-size:1rem;">🏥 {doc_name}</b>
  <span class="badge {badge_cls}" style="float:right">{status.capitalize()}</span><br>
  <span style="color:#94a3b8;font-size:0.85rem;">{specialty} · {city}</span><br>
  <span style="color:#cbd5e1;font-size:0.88rem;">📅 {appt_date} &nbsp; 🕐 {appt_time}</span>
</div>""", unsafe_allow_html=True)

            if status != "cancelled":
                col_cancel, col_reschedule, _ = st.columns([1, 1.4, 3])
                if col_cancel.button("Cancel", key=f"uh_cancel_{booking_id}"):
                    cancel_booking(booking_id)
                    st.toast("Appointment cancelled.")
                    st.rerun()
                with col_reschedule:
                    with st.popover("Reschedule"):
                        new_date = st.date_input("New date", min_value=datetime.date.today(),
                                                 key=f"nd_{booking_id}")
                        new_time = st.time_input("New time", key=f"nt_{booking_id}")
                        if st.button("Confirm reschedule", key=f"rs_{booking_id}"):
                            reschedule_booking(booking_id,
                                               new_date.strftime("%Y-%m-%d"),
                                               new_time.strftime("%H:%M"))
                            st.toast("Appointment rescheduled! ✅")
                            st.rerun()

# ────────────────────────────── PAST VISITS ──────────────────────────────────
with tab_past:
    past = get_past_bookings(_user_id)
    if not past:
        st.info("No past appointments yet.")
    else:
        st.markdown(f"**{len(past)} past visit(s)**")
        for row in past:
            booking_id, doc_name, specialty, city, appt_date, appt_time, status, created_at = row
            badge_cls = "badge-cancelled" if status == "cancelled" else "badge-completed"
            st.markdown(f"""
<div class="card card-past">
  <b style="color:#e2e8f0;font-size:1rem;">🏥 {doc_name}</b>
  <span class="badge {badge_cls}" style="float:right">{status.capitalize()}</span><br>
  <span style="color:#94a3b8;font-size:0.85rem;">{specialty} · {city}</span><br>
  <span style="color:#cbd5e1;font-size:0.88rem;">📅 {appt_date} &nbsp; 🕐 {appt_time}</span>
</div>""", unsafe_allow_html=True)

# ────────────────────────────── ALL RECORDS ──────────────────────────────────
with tab_all:
    all_books = get_user_bookings(_user_id)
    if not all_books:
        st.info("No records found.")
    else:
        # Summary stats
        total = len(all_books)
        confirmed_count = sum(1 for r in all_books if r[6] == "confirmed")
        cancelled_count = sum(1 for r in all_books if r[6] == "cancelled")

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Visits", total)
        m2.metric("Confirmed", confirmed_count)
        m3.metric("Cancelled", cancelled_count)

        st.divider()

        # Specialist frequency chart
        from collections import Counter
        spec_counts = Counter(r[2] for r in all_books)
        if spec_counts:
            st.subheader("Specialists Visited")
            try:
                import plotly.express as px
                import pandas as pd
                df = pd.DataFrame(spec_counts.items(), columns=["Specialist", "Visits"])
                df = df.sort_values("Visits", ascending=False)
                fig = px.bar(df, x="Specialist", y="Visits",
                             color="Visits",
                             color_continuous_scale="Blues",
                             template="plotly_dark")
                fig.update_layout(
                    paper_bgcolor="#131314", plot_bgcolor="#1e2130",
                    showlegend=False, margin=dict(t=20, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                for spec, cnt in spec_counts.most_common():
                    st.markdown(f"- **{spec}**: {cnt} visit(s)")

        st.divider()
        st.subheader("Full Timeline")
        for row in all_books:
            booking_id, doc_name, specialty, city, appt_date, appt_time, status, created_at = row
            badge_cls = ("badge-cancelled" if status == "cancelled"
                         else "badge-completed" if appt_date < datetime.date.today().strftime("%Y-%m-%d")
                         else "badge-confirmed")
            st.markdown(f"""
<div class="card {'card-cancelled' if status == 'cancelled' else ''}">
  <b style="color:#e2e8f0;font-size:1rem;">🏥 {doc_name}</b>
  <span class="badge {badge_cls}" style="float:right">{status.capitalize()}</span><br>
  <span style="color:#94a3b8;font-size:0.85rem;">{specialty} · {city}</span><br>
  <span style="color:#cbd5e1;font-size:0.88rem;">📅 {appt_date} &nbsp; 🕐 {appt_time}</span><br>
  <span style="color:#475569;font-size:0.75rem;">Booked on {created_at}</span>
</div>""", unsafe_allow_html=True)
