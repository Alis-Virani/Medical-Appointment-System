"""
doctor_schedule.py — Doctor: Manage availability, working hours, blocked dates
Doctor-exclusive page.
"""
import streamlit as st
import sqlite3, datetime
import sys
sys.path.insert(0, '.')
from database import DB_NAME
from auth import show_user_sidebar_widget

_user     = st.session_state.get("current_user", {})
_doc_name = _user.get("full_name", "Doctor")
_doc_id   = _user.get("id")

# ── DB helpers ────────────────────────────────────────────────────────────────
def _ensure_tables():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS doctor_blocked_dates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id   INTEGER NOT NULL,
            blocked_date TEXT NOT NULL,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS doctor_working_hours (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id   INTEGER NOT NULL UNIQUE,
            monday TEXT, tuesday TEXT, wednesday TEXT,
            thursday TEXT, friday TEXT, saturday TEXT, sunday TEXT,
            slot_minutes INTEGER DEFAULT 30,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

_ensure_tables()

def get_working_hours(doctor_id):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur  = conn.cursor()
    cur.execute("SELECT * FROM doctor_working_hours WHERE doctor_id = ?", (doctor_id,))
    row = cur.fetchone()
    conn.close()
    return row

def save_working_hours(doctor_id, hours: dict, slot_minutes: int):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("""
        INSERT INTO doctor_working_hours
            (doctor_id, monday, tuesday, wednesday, thursday, friday, saturday, sunday, slot_minutes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(doctor_id) DO UPDATE SET
            monday=excluded.monday, tuesday=excluded.tuesday,
            wednesday=excluded.wednesday, thursday=excluded.thursday,
            friday=excluded.friday, saturday=excluded.saturday,
            sunday=excluded.sunday, slot_minutes=excluded.slot_minutes,
            updated_at=CURRENT_TIMESTAMP
    """, (doctor_id,
          hours.get("Monday",""), hours.get("Tuesday",""), hours.get("Wednesday",""),
          hours.get("Thursday",""), hours.get("Friday",""), hours.get("Saturday",""),
          hours.get("Sunday",""), slot_minutes))
    conn.commit()
    conn.close()

def get_blocked_dates(doctor_id):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur  = conn.cursor()
    cur.execute("""
        SELECT id, blocked_date, reason FROM doctor_blocked_dates
        WHERE doctor_id = ? AND blocked_date >= date('now')
        ORDER BY blocked_date ASC
    """, (doctor_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def add_blocked_date(doctor_id, date_str, reason):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    # avoid duplicates
    existing = conn.execute(
        "SELECT id FROM doctor_blocked_dates WHERE doctor_id=? AND blocked_date=?",
        (doctor_id, date_str)
    ).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO doctor_blocked_dates (doctor_id, blocked_date, reason) VALUES (?, ?, ?)",
            (doctor_id, date_str, reason)
        )
        conn.commit()
    conn.close()

def remove_blocked_date(row_id):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("DELETE FROM doctor_blocked_dates WHERE id = ?", (row_id,))
    conn.commit()
    conn.close()

def get_upcoming_appointments(doc_name):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur  = conn.cursor()
    today = datetime.date.today().strftime("%Y-%m-%d")
    cur.execute("""
        SELECT b.id, u.full_name, b.appointment_date, b.appointment_time, b.status
        FROM bookings b
        LEFT JOIN users u ON u.id = b.user_id
        WHERE b.doctor_name LIKE ? AND b.appointment_date >= ? AND b.status != 'cancelled'
        ORDER BY b.appointment_date ASC, b.appointment_time ASC
    """, (f"%{doc_name}%", today))
    rows = cur.fetchall()
    conn.close()
    return rows

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.stApp { background-color: #131314; }
.slot  { display:inline-block; background:#1e293b; border:1px solid #334155;
         border-radius:8px; padding:4px 12px; margin:3px;
         font-size:0.82rem; color:#94a3b8; }
.slot-busy { background:#450a0a; border-color:#991b1b; color:#fca5a5; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    show_user_sidebar_widget()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("📅 My Schedule")
st.caption(f"Manage working hours and availability · Dr. {_doc_name}")
st.divider()

tab_calendar, tab_hours, tab_block = st.tabs(
    ["📆 Appointment Calendar", "⏰ Working Hours", "🚫 Block Dates"]
)

# ─────────────────────── CALENDAR ────────────────────────────────────────────
with tab_calendar:
    appts = get_upcoming_appointments(_doc_name)
    blocked = get_blocked_dates(_doc_id)
    blocked_dates = {r[1] for r in blocked}

    if not appts:
        st.info("No upcoming appointments scheduled.")
    else:
        # Group by date
        from collections import defaultdict
        by_date = defaultdict(list)
        for appt in appts:
            by_date[appt[2]].append(appt)

        st.markdown(f"**{len(appts)} upcoming appointment(s)**")
        for date_str in sorted(by_date.keys()):
            is_blocked = date_str in blocked_dates
            date_obj   = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            day_label  = date_obj.strftime("%A, %B %d")
            border_col = "#ef4444" if is_blocked else "#0096c7"
            blocked_tag = " 🚫 BLOCKED" if is_blocked else ""

            st.markdown(f"""
<div style="background:#1e2130;border-radius:10px;padding:12px 16px;
            margin-bottom:10px;border-left:4px solid {border_col};">
  <b style="color:#e2e8f0;">{day_label}{blocked_tag}</b>
</div>""", unsafe_allow_html=True)

            if is_blocked:
                reason = next((r[2] for r in blocked if r[1] == date_str), "")
                st.warning(f"This date is blocked. Reason: {reason or 'Not specified'}"
                           " — Patients cannot book on this day.")
            else:
                for appt in by_date[date_str]:
                    appt_id, p_name, appt_date, appt_time, status = appt
                    st.markdown(
                        f"&nbsp;&nbsp;🕐 `{appt_time}` &nbsp; 👤 **{p_name or 'Unknown'}**",
                        unsafe_allow_html=True
                    )

    # Stats summary
    if appts:
        st.divider()
        today_str   = datetime.date.today().strftime("%Y-%m-%d")
        today_count = sum(1 for a in appts if a[2] == today_str)
        week_end    = (datetime.date.today() + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        week_count  = sum(1 for a in appts if today_str <= a[2] <= week_end)
        c1, c2, c3 = st.columns(3)
        c1.metric("Today",         today_count)
        c2.metric("This Week",     week_count)
        c3.metric("Total Upcoming", len(appts))

# ─────────────────────── WORKING HOURS ───────────────────────────────────────
with tab_hours:
    st.subheader("Set Weekly Working Hours")
    st.caption("Set your start/end times for each day. Leave blank to mark as day off.")

    existing = get_working_hours(_doc_id)
    days     = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # Parse existing
    defaults = {}
    if existing:
        col_map = dict(zip(days, existing[2:9]))
        defaults = col_map
        default_slot = existing[9] if len(existing) > 9 else 30
    else:
        defaults = {d: "09:00 - 17:00" if d not in ("Saturday", "Sunday") else "" for d in days}
        default_slot = 30

    with st.form("working_hours_form"):
        st.markdown("**Working hours per day** (format: `09:00 - 17:00` or leave blank for day off)")
        hours_input = {}
        col_a, col_b = st.columns(2)
        for i, day in enumerate(days):
            col = col_a if i % 2 == 0 else col_b
            hours_input[day] = col.text_input(
                day, value=defaults.get(day, ""), placeholder="09:00 - 17:00"
            )
        slot_minutes = st.select_slider(
            "Appointment slot duration",
            options=[15, 20, 30, 45, 60],
            value=default_slot,
            help="How long each appointment slot is"
        )
        saved = st.form_submit_button("💾 Save Working Hours", type="primary",
                                      use_container_width=True)
        if saved:
            save_working_hours(_doc_id, hours_input, slot_minutes)
            st.success("✅ Working hours updated!")

    # Show slot preview
    if existing or True:
        st.divider()
        st.subheader("Today's Slot Preview")
        today_day  = datetime.date.today().strftime("%A")
        today_hrs  = hours_input.get(today_day, "") if "hours_input" in dir() else defaults.get(today_day, "")
        booked_times = {a[3] for a in get_upcoming_appointments(_doc_name)
                        if a[2] == datetime.date.today().strftime("%Y-%m-%d")}

        if today_hrs and " - " in today_hrs:
            try:
                start_s, end_s = [x.strip() for x in today_hrs.split(" - ")]
                s = datetime.datetime.strptime(start_s, "%H:%M")
                e = datetime.datetime.strptime(end_s,   "%H:%M")
                slot_dur = datetime.timedelta(minutes=slot_minutes)
                slots_html = ""
                cur_slot = s
                while cur_slot + slot_dur <= e:
                    slot_str  = cur_slot.strftime("%H:%M")
                    is_booked = slot_str in booked_times
                    cls       = "slot-busy" if is_booked else "slot"
                    label     = slot_str + (" 🔴" if is_booked else "")
                    slots_html += f'<span class="{cls}">{label}</span>'
                    cur_slot  += slot_dur
                st.markdown(slots_html + """ <br><small style='color:#475569;'>
                    🔴 Booked &nbsp; ⬜ Available</small>""", unsafe_allow_html=True)
            except ValueError:
                st.caption(f"Working today: {today_hrs}")
        else:
            st.caption(f"Today ({today_day}) is a day off.")

# ─────────────────────── BLOCK DATES ─────────────────────────────────────────
with tab_block:
    st.subheader("Block Dates (Unavailable)")
    st.caption("Block dates for holidays, conferences, or personal leave. "
               "Patients will not be able to book on these days.")

    with st.form("block_date_form"):
        col_date, col_reason = st.columns([1, 2])
        block_date   = col_date.date_input("Date to block",
                                            min_value=datetime.date.today())
        block_reason = col_reason.text_input("Reason (optional)",
                                              placeholder="e.g. Conference, Holiday, Personal")
        block_btn = st.form_submit_button("🚫 Block This Date", use_container_width=True)
        if block_btn:
            add_blocked_date(_doc_id, str(block_date), block_reason)
            st.success(f"✅ {block_date.strftime('%B %d, %Y')} blocked.")

    # Show blocked dates
    st.divider()
    st.subheader("Currently Blocked Dates")
    blocked = get_blocked_dates(_doc_id)
    if not blocked:
        st.caption("No upcoming dates blocked.")
    else:
        for row in blocked:
            row_id, date_str, reason = row
            date_obj   = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            c1, c2, c3 = st.columns([1.5, 2, 0.8])
            c1.markdown(f"🚫 **{date_obj.strftime('%b %d, %Y')}**")
            c2.caption(reason or "No reason given")
            if c3.button("Remove", key=f"unblock_{row_id}", use_container_width=True):
                remove_blocked_date(row_id)
                st.toast(f"{date_str} unblocked.")
                st.rerun()
