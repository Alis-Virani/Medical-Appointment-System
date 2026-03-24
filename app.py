"""
app.py — MediCare AI · Navigation Shell
Handles auth gate and assembles role-specific page navigation.
All actual page content lives in pages/.
"""
import streamlit as st
from dotenv import load_dotenv
from database import init_db
from doctor_management import init_database
from auth import show_auth_page

load_dotenv()
init_db()
init_database()

st.set_page_config(page_title="MediCare AI", page_icon="🩺", layout="wide")

# ── ENHANCED CSS STYLING ──────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ===== MAIN CONTAINER ===== */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #1a1f35 100%);
        color: #e2e8f0;
    }
    
    /* ===== SIDEBAR ===== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
        border-right: 1px solid #334155;
    }
    
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #60a5fa;
        font-weight: bold;
    }
    
    /* ===== BUTTONS ===== */
    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%) !important;
        border: 1px solid #60a5fa !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        padding: 12px 24px !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%) !important;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.4) !important;
        transform: translateY(-2px) !important;
    }
    
    /* ===== TEXT INPUT ===== */
    .stTextInput > div > div > input {
        background-color: rgba(30, 41, 59, 0.6) !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
        padding: 12px !important;
        font-size: 14px !important;
    }
    
    .stTextInput > div > div > input:focus {
        border: 2px solid #60a5fa !important;
        box-shadow: 0 0 10px rgba(96, 165, 250, 0.3) !important;
    }
    
    /* ===== ALERTS & MESSAGES ===== */
    [data-testid="stAlert"] {
        border-radius: 8px !important;
        border: 1px solid rgba(144, 144, 144, 0.2) !important;
        padding: 16px !important;
    }
    
    [data-testid="stWarning"] {
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(217, 119, 6, 0.1) 100%) !important;
        border-left: 4px solid #f59e0b !important;
    }
    
    [data-testid="stError"] {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(185, 28, 28, 0.1) 100%) !important;
        border-left: 4px solid #ef4444 !important;
    }
    
    [data-testid="stSuccess"] {
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(21, 128, 61, 0.1) 100%) !important;
        border-left: 4px solid #22c55e !important;
    }
    
    [data-testid="stInfo"] {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(30, 64, 175, 0.1) 100%) !important;
        border-left: 4px solid #3b82f6 !important;
    }
    
    /* ===== HEADERS & TEXT ===== */
    h1, h2, h3, h4, h5, h6 {
        color: #f0f9ff !important;
    }
    
    h1 {
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #60a5fa 0%, #fbbf24 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    h2 {
        color: #60a5fa !important;
        font-weight: 700 !important;
        margin-top: 20px !important;
    }
    
    /* ===== DIVIDER ===== */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #334155, transparent);
        margin: 20px 0 !important;
    }
    
    /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(30, 41, 59, 0.5);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #3b82f6 0%, #1e40af 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #60a5fa 0%, #3b82f6 100%);
    }
</style>
""", unsafe_allow_html=True)
if not st.session_state.get("authenticated", False):
    show_auth_page()
    st.stop()

# ── Role-based navigation ─────────────────────────────────────────────────────────
_role = st.session_state.get("current_user", {}).get("role", "patient")

if _role == "admin":
    pages = {
        "⚙️ Admin": [
            st.Page("pages/admin_doctors.py", title="Doctor Management", icon="👨‍⚕️"),
        ]
    }
elif _role == "doctor":
    pages = {
        "🩺 Clinic": [
            st.Page("pages/chat.py",             title="AI Assistant",icon="💬"),
            st.Page("pages/doctor_dashboard.py", title="Dashboard",icon="📊"),
            st.Page("pages/patient_notes.py",    title="Patient Notes",icon="📝"),
            st.Page("pages/doctor_schedule.py",  title="My Schedule",icon="📅"),
        ]
    }
else:
    pages = {
        "🏥 Patient": [
            st.Page("pages/chat.py",           title="AI Chat",        icon="💬"),
            st.Page("pages/health_history.py", title="Health History", icon="📋"),
        ]
    }

pg = st.navigation(pages)
pg.run()
