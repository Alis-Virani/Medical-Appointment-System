"""
patient_notes.py — Doctor: Write & view consultation notes for patients
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

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.stApp { background-color: #131314; }
.note-card {
    background: #1e2130; border-radius: 12px;
    padding: 16px 20px; margin-bottom: 12px;
    border-left: 4px solid #0096c7;
}
</style>
""", unsafe_allow_html=True)

# ── DB helpers ────────────────────────────────────────────────────────────────
def _ensure_notes_table():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS consultation_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id   INTEGER,
            doctor_name TEXT,
            patient_id  INTEGER,
            patient_name TEXT,
            booking_id  INTEGER,
            diagnosis   TEXT,
            prescription TEXT,
            notes       TEXT,
            follow_up_date TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

_ensure_notes_table()

def save_note(doctor_id, doctor_name, patient_id, patient_name,
              booking_id, diagnosis, prescription, notes, follow_up):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("""
        INSERT INTO consultation_notes
        (doctor_id, doctor_name, patient_id, patient_name, booking_id,
         diagnosis, prescription, notes, follow_up_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (doctor_id, doctor_name, patient_id, patient_name, booking_id,
          diagnosis, prescription, notes, follow_up))
    conn.commit()
    conn.close()

def get_notes_for_doctor(doctor_id):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur  = conn.cursor()
    cur.execute("""
        SELECT id, patient_name, diagnosis, prescription, notes,
               follow_up_date, created_at
        FROM consultation_notes WHERE doctor_id = ?
        ORDER BY created_at DESC
    """, (doctor_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_notes_for_patient_by_doctor(patient_id, doctor_id):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur  = conn.cursor()
    cur.execute("""
        SELECT id, diagnosis, prescription, notes, follow_up_date, created_at
        FROM consultation_notes
        WHERE patient_id = ? AND doctor_id = ?
        ORDER BY created_at DESC
    """, (patient_id, doctor_id))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_doctor_patients(doctor_name):
    """Get unique patients who booked with this doctor."""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur  = conn.cursor()
    cur.execute("""
        SELECT DISTINCT b.user_id, u.full_name, u.email,
               count(b.id) as visits
        FROM bookings b
        LEFT JOIN users u ON u.id = b.user_id
        WHERE b.doctor_name LIKE ?
        GROUP BY b.user_id
        ORDER BY visits DESC
    """, (f"%{doctor_name}%",))
    rows = cur.fetchall()
    conn.close()
    return rows

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    show_user_sidebar_widget()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("📝 Patient Notes")
st.caption(f"Write and manage consultation notes · Dr. {_doc_name}")
st.divider()

tab_write, tab_history, tab_search = st.tabs(
    ["✏️ Write Note", "📁 All Notes", "🔍 By Patient"]
)

# ─────────────────────── WRITE NOTE ─────────────────────────────────────────
with tab_write:
    patients = get_doctor_patients(_doc_name)

    if not patients:
        st.info("No patients have booked with you yet. Once bookings come in, "
                "you can write consultation notes here.")
    else:
        patient_options = {
            f"{row[1] or 'Unknown'} (ID {row[0]}) · {row[3]} visit(s)": row
            for row in patients
        }
        selected_label   = st.selectbox("Select Patient", list(patient_options.keys()))
        selected_patient = patient_options[selected_label]
        p_id, p_name, p_email, p_visits = selected_patient

        st.markdown(f"""
<div class="note-card">
  <b style="color:#e2e8f0;">👤 {p_name or 'Unknown'}</b><br>
  <span style="color:#94a3b8;font-size:0.82rem;">Email: {p_email or '—'} &nbsp;·&nbsp; Total visits: {p_visits}</span>
</div>""", unsafe_allow_html=True)

        # Show previous notes for this patient
        prev_notes = get_notes_for_patient_by_doctor(p_id, _doc_id)
        if prev_notes:
            with st.expander(f"📋 {len(prev_notes)} previous note(s) for this patient"):
                for note in prev_notes:
                    nid, diag, rx, txt, fu, ts = note
                    st.markdown(f"""
<div class="note-card" style="border-left-color:#475569;">
  <span style="color:#94a3b8;font-size:0.78rem;">{ts}</span><br>
  <b style="color:#e2e8f0;">Diagnosis:</b> <span style="color:#cbd5e1;">{diag or '—'}</span><br>
  <b style="color:#e2e8f0;">Prescription:</b> <span style="color:#cbd5e1;">{rx or '—'}</span><br>
  <b style="color:#e2e8f0;">Notes:</b> <span style="color:#cbd5e1;">{txt or '—'}</span><br>
  {"<b style='color:#fbbf24;'>Follow-up: " + fu + "</b>" if fu else ""}
</div>""", unsafe_allow_html=True)

        st.divider()
        st.subheader("Write New Note")
        with st.form("write_note_form"):
            diagnosis    = st.text_input("Diagnosis", placeholder="e.g. Viral fever, Hypertension")
            prescription = st.text_area("Prescription / Medications",
                                        placeholder="e.g. Paracetamol 500mg TDS × 5 days\nORS 1L/day",
                                        height=120)
            notes        = st.text_area("Consultation Notes",
                                        placeholder="Observations, test recommendations, lifestyle advice…",
                                        height=120)
            follow_up    = st.date_input("Follow-up Date (optional)",
                                         value=None,
                                         min_value=datetime.date.today())
            saved = st.form_submit_button("💾 Save Note", type="primary",
                                          use_container_width=True)
            if saved:
                fu_str = str(follow_up) if follow_up else ""
                save_note(
                    doctor_id=_doc_id, doctor_name=_doc_name,
                    patient_id=p_id, patient_name=p_name,
                    booking_id=None, diagnosis=diagnosis,
                    prescription=prescription, notes=notes,
                    follow_up=fu_str,
                )
                st.success(f"✅ Note saved for {p_name}.")
                if follow_up:
                    st.info(f"📅 Follow-up reminder set for {follow_up.strftime('%B %d, %Y')}")

# ─────────────────────── ALL NOTES ──────────────────────────────────────────
with tab_history:
    all_notes = get_notes_for_doctor(_doc_id)
    if not all_notes:
        st.info("No notes written yet.")
    else:
        st.markdown(f"**{len(all_notes)} total note(s)**")
        # Stats
        from collections import Counter
        diag_counts = Counter(n[2] for n in all_notes if n[2])
        if diag_counts:
            st.caption("**Top diagnoses:** " +
                       " · ".join(f"{d} ({c})" for d, c in diag_counts.most_common(5)))
        st.divider()
        for note in all_notes:
            nid, p_name, diag, rx, txt, fu, ts = note
            with st.expander(f"👤 {p_name or 'Unknown'} · {diag or 'No diagnosis'} · {ts[:10]}"):
                col1, col2 = st.columns(2)
                col1.markdown(f"**Diagnosis:** {diag or '—'}")
                col2.markdown(f"**Follow-up:** {fu or '—'}")
                st.markdown(f"**Prescription:**\n```\n{rx or '—'}\n```")
                st.markdown(f"**Notes:** {txt or '—'}")

# ─────────────────────── SEARCH BY PATIENT ───────────────────────────────────
with tab_search:
    search_q = st.text_input("Search patient name", placeholder="Type patient name...")
    if search_q:
        conn = sqlite3.connect(DB_NAME, timeout=10)
        cur  = conn.cursor()
        cur.execute("""
            SELECT id, patient_name, diagnosis, prescription, notes,
                   follow_up_date, created_at
            FROM consultation_notes
            WHERE doctor_id = ? AND patient_name LIKE ?
            ORDER BY created_at DESC
        """, (_doc_id, f"%{search_q}%"))
        results = cur.fetchall()
        conn.close()
        if results:
            for note in results:
                nid, p_name, diag, rx, txt, fu, ts = note
                st.markdown(f"""
<div class="note-card">
  <b style="color:#e2e8f0;">👤 {p_name}</b>
  <span style="float:right;color:#94a3b8;font-size:0.78rem;">{ts[:10]}</span><br>
  <span style="color:#cbd5e1;">🩺 {diag or '—'}</span><br>
  <span style="color:#94a3b8;font-size:0.8rem;">💊 {rx[:80] + '…' if rx and len(rx) > 80 else rx or '—'}</span>
</div>""", unsafe_allow_html=True)
        else:
            st.info(f"No notes found for '{search_q}'.")
