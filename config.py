"""
config.py - Centralized configuration and fallbacks for MediCare AI
Handles API defaults, caching, and security settings
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# API CONFIGURATION & FALLBACKS
# ─────────────────────────────────────────────────────────────────────────────

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# API Availability Status
API_STATUS = {
    "GROQ": bool(GROQ_API_KEY),
    "NEO4J": bool(os.getenv("NEO4J_URI")),
    "CHROMADB": True,  # Local, always available
    "SQLITE": True,  # Always available
    "SENDGRID": bool(os.getenv("SENDGRID_API_KEY")),
    "SARVAM": bool(os.getenv("SARVAM_API_KEY")),
}

# ─────────────────────────────────────────────────────────────────────────────
# DEMO RESPONSES (For when APIs unavailable)
# ─────────────────────────────────────────────────────────────────────────────

DEMO_RESPONSES = {
    "diagnosis": """
    🩺 **Possible Condition:** Common Cold / Viral Infection
    
    📊 **Confidence: 65%** (Limited confidence due to API constraints)
    
    📌 **Explanation:**
    - Based on general symptom pattern
    - This is a demo response (external API unavailable)
    - **Please consult a real doctor for accurate diagnosis**
    
    💊 **Recommended Action:**
    - Rest and hydration
    - Over-the-counter antihistamines if needed
    - Monitor temperature
    
    🚨 **When to See Doctor:**
    - Fever > 39°C for >3 days
    - Severe difficulty breathing
    - Chest pain
    
    ⚠️ **DEMO MODE**: AI reasoning is limited. Always consult a healthcare provider.
    """,
    
    "booking": "Doctor booking is currently in demo mode. In production, you'll be able to book through our database.",
    
    "notification": "Email notification queued. In production, you'll receive a confirmation email.",
}

# ─────────────────────────────────────────────────────────────────────────────
# SESSION & SECURITY SETTINGS
# ─────────────────────────────────────────────────────────────────────────────

SESSION_TIMEOUT_HOURS = 24  # Auto-logout after 24 hours
SESSION_REFRESH_MINUTES = 5  # Refresh timestamp every 5 minutes

# Password policy
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRES_UPPERCASE = True
PASSWORD_REQUIRES_NUMBER = True
PASSWORD_REQUIRES_SPECIAL = False  # Optional

# Rate limiting (future enhancement)
RATE_LIMIT_REQUESTS_PER_MINUTE = 30
RATE_LIMIT_BOOKING_PER_HOUR = 5

# ─────────────────────────────────────────────────────────────────────────────
# PERFORMANCE & CACHING
# ─────────────────────────────────────────────────────────────────────────────

# LLM instance caching (Streamlit @st.cache_resource)
LLM_CACHE_TTL_SECONDS = 3600  # Cache for 1 hour

# Database query caching
DB_CACHE_TTL_SECONDS = 300  # Cache for 5 minutes

# Vector store caching
VECTOR_CACHE_TTL_SECONDS = 600  # Cache for 10 minutes

# ─────────────────────────────────────────────────────────────────────────────
# LOGGING & MONITORING
# ─────────────────────────────────────────────────────────────────────────────

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = "logs/medical_assistant.log"
ENABLE_API_LOGGING = True
ENABLE_ERROR_LOGGING = True

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

SQLITE_DB = "hospital.db"
CHROMADB_PATH = "./chroma_db"
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")

# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTION: Check if API available with fallback
# ─────────────────────────────────────────────────────────────────────────────

def get_api_status():
    """Returns dictionary of which APIs are currently available"""
    return API_STATUS

def use_demo_mode():
    """Returns True if any critical API is down"""
    critical_apis = ["GROQ", "SQLITE"]
    return not all(API_STATUS.get(api, False) for api in critical_apis)
