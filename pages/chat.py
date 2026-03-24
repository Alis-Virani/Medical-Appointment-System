"""
chat.py — Main AI Chat page
Moved from app.py so navigation shell (app.py) can control routing per role.
"""
import streamlit as st
import os
import sys
import datetime
from dotenv import load_dotenv

# Add parent directory to path so we can import sibling modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from database import (
    create_session, get_all_sessions, delete_session, delete_all_sessions,
    load_messages, save_message, update_session_title, get_upcoming_bookings,
    cancel_booking, find_doctors_in_db, save_patient_memory,
    get_patient_memory_summary, find_medicines_for_symptoms, save_booking,
)
from agent import get_agent_llm, basic_chat_llm
from lang_graph_agent import get_graph_app
from auth import show_user_sidebar_widget
try:
    from voice_service import transcribe_audio_bytes_via_sarvam, synthesize_speech_via_sarvam
except ImportError:
    transcribe_audio_bytes_via_sarvam = None
    synthesize_speech_via_sarvam = None

load_dotenv()

# ── Cache heavy resources ─────────────────────────────────────────────────────
@st.cache_resource
def _get_cached_graph():
    """Cache the graph app to avoid rebuilding on every rerun"""
    return get_graph_app()

@st.cache_resource
def _get_cached_llm():
    """Cache the LLM instance"""
    return get_agent_llm()

_user     = st.session_state.get("current_user", {})
_user_id  = _user.get("id")
_user_name = _user.get("full_name", "User")

# ── CSS ───────────────────────────────────────────────────────────────────────
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
    
    /* ===== CHAT INPUT ===== */
    .stChatInputContainer {
        border-radius: 16px !important;
        border: 2px solid #334155 !important;
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
        padding: 12px !important;
    }
    
    .stChatInputContainer input {
        background-color: transparent !important;
        color: #e2e8f0 !important;
        font-size: 15px !important;
        border: none !important;
    }
    
    /* ===== CHAT MESSAGES ===== */
    .stChatMessage {
        border-radius: 12px !important;
        padding: 16px !important;
        margin: 8px 0 !important;
        backdrop-filter: blur(10px);
        background-color: rgba(30, 41, 59, 0.4) !important;
        border: 1px solid rgba(51, 65, 85, 0.5) !important;
    }
    
    /* USER MESSAGE */
    [data-testid="chatAvatarIcon-user"] ~ div {
        background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%) !important;
        border-left: 4px solid #60a5fa !important;
    }
    
    /* ASSISTANT MESSAGE */
    [data-testid="chatAvatarIcon-assistant"] ~ div {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
        border-left: 4px solid #fbbf24 !important;
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
    
    /* ===== EXPANDER ===== */
    div[data-testid="stExpander"] {
        background: rgba(30, 41, 59, 0.5) !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        margin: 8px 0 !important;
    }
    
    div[data-testid="stExpander"] div[role="button"] {
        background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%) !important;
        border-radius: 6px !important;
        padding: 12px !important;
    }
    
    div[data-testid="stExpander"] div[role="button"] p {
        font-size: 1.1rem !important;
        font-weight: bold !important;
        color: #60a5fa !important;
        margin: 0 !important;
    }
    
    div[data-testid="stExpander"] div[role="button"]:hover {
        background: linear-gradient(90deg, #334155 0%, #1e293b 100%) !important;
    }
    
    /* ===== FORM ELEMENTS ===== */
    .stForm {
        background: rgba(30, 41, 59, 0.4) !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        padding: 24px !important;
    }
    
    .stSelectbox {
        padding: 8px !important;
    }
    
    .stSelectbox > div {
        background: rgba(30, 41, 59, 0.6) !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
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
    
    /* ===== SPECIAL ===== */
    .stMetric {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(30, 64, 175, 0.1) 100%) !important;
        border-radius: 8px !important;
        border: 1px solid #334155 !important;
        padding: 16px !important;
    }
    
    section[data-testid="stSidebar"] div[data-testid="column"] {
        display: flex;
        align-items: center;
    }
</style>
""", unsafe_allow_html=True)

# ── State defaults ────────────────────────────────────────────────────────────
for _k, _v in {
    "waiting_for_city": False, "waiting_for_details": False,
    "pending_specialty": None, "pending_city": None,
    "doctor_data": None, "current_symptom": None,
    "file_context_sent": False, "file_uploader_key": 0,
}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ── Session logic ─────────────────────────────────────────────────────────────
query_params   = st.query_params
url_session_id = query_params.get("session_id")


def _sarvam_lang_code(app_lang: str) -> str:
    """Map app language code to Sarvam language code."""
    _lang = (app_lang or "en").lower()
    if _lang.startswith("hi"):
        return "hi-IN"
    if _lang.startswith("gu"):
        return "gu-IN"
    return "en-IN"


_SARVAM_VOICE_ENABLED = bool(os.getenv("SARVAM_API_KEY", "").strip())


if "active_session_id" not in st.session_state:
    if url_session_id:
        try:
            st.session_state["active_session_id"] = int(url_session_id)
        except Exception:
            new_id = create_session("New Chat", user_id=_user_id)
            st.session_state["active_session_id"] = new_id
            st.query_params["session_id"] = str(new_id)
    else:
        new_id = create_session("New Chat", user_id=_user_id)
        st.session_state["active_session_id"] = new_id
        st.query_params["session_id"] = str(new_id)

curr_id = st.session_state["active_session_id"]

# ── Delete modal ──────────────────────────────────────────────────────────────
@st.dialog("Delete chat?")
def show_delete_modal(session_id):
    st.write("This will delete prompts, responses and feedback.")
    c1, c2 = st.columns(2)
    if c1.button("Cancel", use_container_width=True): st.rerun()
    if c2.button("Delete", type="primary", use_container_width=True):
        delete_session(session_id)
        if st.session_state["active_session_id"] == session_id:
            st.session_state["active_session_id"] = None
            st.query_params.clear()
        st.rerun()

_CLEAR_KEYS = [
    "messages", "current_symptoms", "current_city", "current_severity",
    "current_specialist", "suggested_doctors", "booking_requested",
    "ask_for_city", "file_context", "file_context_sent", "analyzed_filename",
    "file_uploader_key", "waiting_for_city", "waiting_for_details",
    "pending_specialty", "pending_city", "doctor_data", "current_symptom",
    "voice_input", "last_audio_hash",
    "last_tts_audio", "last_tts_mime", "last_tts_text", "tts_autoplay_once",
]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Records")
    show_user_sidebar_widget()
    st.divider()

    if st.button("+ New Chat", use_container_width=True):
        new_id = create_session("New Chat", user_id=_user_id)
        st.session_state["active_session_id"] = new_id
        for _k in _CLEAR_KEYS:
            st.session_state.pop(_k, None)
        st.query_params["session_id"] = str(new_id)
        st.rerun()

    st.divider()
    st.subheader("Voice Command")
    if st.session_state.get("voice_status"):
        st.caption(st.session_state.get("voice_status"))
    if not _SARVAM_VOICE_ENABLED:
        st.info("ℹ️ Add `SARVAM_API_KEY` to `.env` to enable voice input.")
    from audio_recorder_streamlit import audio_recorder as _audio_recorder
    _audio_bytes = _audio_recorder(
        text="", icon_size="2x",
        neutral_color="#ffffff", recording_color="#ff4b4b",
        key="voice_recorder"
    )
    if _audio_bytes and len(_audio_bytes) > 500:
        import hashlib as _hashlib
        _audio_hash = _hashlib.md5(_audio_bytes).hexdigest()
        if st.session_state.get("last_audio_hash") != _audio_hash:
            with st.spinner("Transcribing voice..."):
                try:
                    import io as _io
                    import wave as _wave
                    import audioop as _audioop
                    import av as _av

                    # Always normalize audio to mono 16k PCM WAV for best STT compatibility.
                    _wav_buf = None
                    _raw_pcm = b""
                    try:
                        _container = _av.open(_io.BytesIO(_audio_bytes))
                        _resampler = _av.AudioResampler(format='s16', layout='mono', rate=16000)
                        _chunks = []
                        for _frame in _container.decode(audio=0):
                            for _rf in _resampler.resample(_frame):
                                _chunks.append(bytes(_rf.planes[0]))
                        for _rf in _resampler.resample(None):
                            _chunks.append(bytes(_rf.planes[0]))
                        _raw_pcm = b''.join(_chunks)
                    except Exception:
                        # Fallback: parse as WAV and convert via stdlib audioop.
                        _test = _io.BytesIO(_audio_bytes)
                        with _wave.open(_test, 'rb') as _wt:
                            _nch = _wt.getnchannels()
                            _sw = _wt.getsampwidth()
                            _fr = _wt.getframerate()
                            _frames = _wt.readframes(_wt.getnframes())
                        if _nch == 2:
                            _frames = _audioop.tomono(_frames, _sw, 0.5, 0.5)
                        if _sw != 2:
                            _frames = _audioop.lin2lin(_frames, _sw, 2)
                            _sw = 2
                        if _fr != 16000:
                            _frames, _ = _audioop.ratecv(_frames, 2, 1, _fr, 16000, None)
                        _raw_pcm = _frames

                    if not _raw_pcm:
                        st.session_state["last_audio_hash"] = _audio_hash
                        st.session_state["voice_status"] = "No audio captured. Please try again."
                        st.warning("No audio captured — try again.")
                        raise ValueError("No audio captured — try again.")

                    # Low amplitude usually means mic input/earbuds issue.
                    _peak = _audioop.max(_raw_pcm, 2)
                    if _peak < 60:
                        st.session_state["voice_status"] = (
                            f"Low mic level detected (peak={_peak}). Trying transcription anyway."
                        )

                    _wav_buf = _io.BytesIO()
                    with _wave.open(_wav_buf, 'wb') as _wf:
                        _wf.setnchannels(1)
                        _wf.setsampwidth(2)
                        _wf.setframerate(16000)
                        _wf.writeframes(_raw_pcm)
                    _wav_buf.seek(0)

                    _transcript = transcribe_audio_bytes_via_sarvam(
                        _wav_buf.getvalue(),
                        language_code=_sarvam_lang_code(st.session_state.get("user_lang", "en")),
                    )
                    if _transcript:
                        st.session_state["last_audio_hash"] = _audio_hash
                        st.session_state["voice_input"] = _transcript
                        st.session_state["voice_status"] = f"Heard: {_transcript[:80]}"
                        st.toast(f"🎤 \"{_transcript}\"")
                        st.rerun()

                except ValueError as _e:
                    st.session_state["last_audio_hash"] = _audio_hash
                    st.session_state["voice_status"] = f"STT: {_e}"
                    st.warning(f"⚠️ {_e}")
                except Exception as _e:
                    st.session_state["voice_status"] = f"Voice error: {_e}"
                    st.error(f"Voice error: {_e}")
                    with st.expander("🔍 Debug info"):
                        if "_peak" in locals():
                            st.write(f"Audio peak level: {_peak}")
                        import traceback as _tb
                        st.code(_tb.format_exc())

    # ── TTS toggle ─────────────────────────────
    st.divider()
    _tts_on = st.toggle("🔊 Speak AI Responses",
                        value=st.session_state.get("tts_enabled", False),
                        key="tts_toggle")
    st.session_state["tts_enabled"] = _tts_on
    if not _SARVAM_VOICE_ENABLED:
        st.caption("ℹ️ Add `SARVAM_API_KEY` to `.env` to enable voice.")
    if _tts_on:
        st.caption("AI responses will be read aloud automatically.")

    st.divider()
    st.subheader("Upload Report")
    uploaded_file = st.file_uploader(
        "Upload PDF/Image", type=["pdf", "png", "jpg", "jpeg"],
        key=f"uploader_{st.session_state.file_uploader_key}"
    )
    if uploaded_file:
        already_analyzed = st.session_state.get("analyzed_filename") == uploaded_file.name
        if not already_analyzed:
            with st.spinner("Analyzing document..."):
                try:
                    from report_analyzer import analyze_medical_report
                    import io as _io
                    file_bytes = uploaded_file.read()
                    file_obj = _io.BytesIO(file_bytes)
                    file_obj.name = uploaded_file.name
                    file_obj.type = uploaded_file.type
                    analysis_result = analyze_medical_report(file_obj)
                    if "⚠️" in analysis_result or "❌" in analysis_result:
                        st.toast("⚠️ Report analysis completed with warnings.")
                    else:
                        st.toast("✅ Report analyzed successfully!")
                    if analysis_result:
                        st.session_state.file_context = analysis_result
                        st.session_state.file_context_sent = False
                        st.session_state.analyzed_filename = uploaded_file.name
                        import threading
                        def _store_in_chroma(text, fname, uid, sid):
                            try:
                                from vector_store import get_vector_store
                                _vs = get_vector_store(collection_name="patient_reports")
                                _vs.add_report(text=text, filename=fname,
                                               user_id=str(uid), session_id=str(sid))
                            except Exception:
                                pass
                        threading.Thread(
                            target=_store_in_chroma,
                            args=(analysis_result, uploaded_file.name, _user_id, curr_id),
                            daemon=True,
                        ).start()
                        st.success("Report analyzed! Ask questions about it.")
                        with st.expander("View Extracted Text"):
                            st.text(analysis_result[:500] + "...")
                    else:
                        st.warning("Could not extract text from the report.")
                except Exception as e:
                    st.error(f"Error processing file: {e}")
        else:
            with st.expander("View Extracted Text"):
                st.text(st.session_state.get("file_context", "")[:500] + "...")

    if st.session_state.get("file_context"):
        if st.button("Clear Report", use_container_width=True):
            st.session_state.file_context = None
            st.session_state.file_context_sent = False
            st.session_state.analyzed_filename = None
            st.session_state.file_uploader_key += 1
            st.rerun()

    st.divider()
    st.caption("Recent Chats")
    sessions = get_all_sessions(user_id=_user_id)
    if sessions:
        if not st.session_state.get("confirm_clear_all", False):
            if st.button("Clear All Chats", key="clear_all_chats", use_container_width=True):
                st.session_state["confirm_clear_all"] = True
                st.rerun()
        else:
            st.warning("Delete all chats? This cannot be undone.")
            y_col, n_col = st.columns(2)
            if y_col.button("Yes, delete", key="confirm_yes", type="primary", use_container_width=True):
                delete_all_sessions(user_id=_user_id)
                for _k in ["messages", "active_session_id", "current_symptoms",
                            "current_city", "suggested_doctors", "file_context",
                            "confirm_clear_all", "analyzed_filename"]:
                    st.session_state.pop(_k, None)
                st.toast("All chats cleared!")
                st.rerun()
            if n_col.button("Cancel", key="confirm_no", use_container_width=True):
                st.session_state["confirm_clear_all"] = False
                st.rerun()

        for session_id, title in sessions:
            c1, c2 = st.columns([0.8, 0.2])
            if c1.button(f"{title}", key=f"s_{session_id}", use_container_width=True):
                st.session_state["active_session_id"] = session_id
                for _k in _CLEAR_KEYS:
                    st.session_state.pop(_k, None)
                st.query_params["session_id"] = str(session_id)
                st.rerun()
            if c2.button("x", key=f"d_{session_id}", help="Delete Chat",
                         use_container_width=True):
                show_delete_modal(session_id)
    else:
        st.caption("No chats yet.")

# ── Main Chat Area ────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = load_messages(curr_id)

def _display_content(raw: str) -> str:
    if "[USER QUESTION]" in raw:
        return raw.split("[USER QUESTION]")[-1].strip()
    if "[MEDICAL REPORT CONTEXT]" in raw:
        return ""
    return raw

for msg in st.session_state.messages:
    if isinstance(msg, (HumanMessage, AIMessage, SystemMessage)):
        role    = "user" if isinstance(msg, HumanMessage) else "assistant"
        content = _display_content(msg.content) if isinstance(msg, HumanMessage) else msg.content
    else:
        role    = msg.get("role", "user")
        raw     = msg.get("content", "")
        content = _display_content(raw) if role == "user" else raw
    if content:
        with st.chat_message(role):
            st.markdown(content)

# Persist latest TTS player across reruns so playback controls don't disappear.
_tts_bytes = st.session_state.get("last_tts_audio")
if _tts_bytes:
    _tts_mime = st.session_state.get("last_tts_mime", "audio/mp3")
    _tts_text = st.session_state.get("last_tts_text", "")
    with st.chat_message("assistant"):
        st.caption("Listen to latest response")
        st.audio(
            _tts_bytes,
            format=_tts_mime,
            autoplay=bool(st.session_state.get("tts_autoplay_once", False)),
        )
        if _tts_text:
            st.caption(_tts_text[:120] + ("..." if len(_tts_text) > 120 else ""))
    st.session_state["tts_autoplay_once"] = False

_voice_pending = st.session_state.pop("voice_input", None)
user_input = st.chat_input("Type your symptoms or questions...") or _voice_pending

if user_input:
    from translator import detect_language, translate_to_english, translate_from_english
    previous_lang = st.session_state.get("user_lang", "en")
    user_lang     = detect_language(user_input, fallback_lang=previous_lang)
    st.session_state["user_lang"] = user_lang

    english_input = user_input
    if user_lang != "en":
        t_res         = translate_to_english(user_input)
        english_input = t_res["translated"]
        if english_input != user_input:
            st.toast(f"🌐 Translating from {user_lang}...")

    st.chat_message("user").markdown(user_input)

    file_context      = st.session_state.get("file_context", "")
    file_context_sent = st.session_state.get("file_context_sent", False)
    if file_context and not file_context_sent:
        agent_input = f"[MEDICAL REPORT CONTEXT]\n{file_context}\n\n[USER QUESTION]\n{english_input}"
        st.session_state.file_context_sent = True
    else:
        agent_input = english_input

    st.session_state.messages.append(HumanMessage(content=agent_input))
    save_message(curr_id, "user", english_input)

    try:
        with st.spinner("Thinking..."):
            graph_app   = _get_cached_graph()
            _memory_ctx = get_patient_memory_summary(_user_id) if _user_id else ""
            initial_state = {
                "messages":        st.session_state.messages,
                "user_id":         str(curr_id),
                "user_role":       _user.get("role", "patient"),  # Pass user role to agent
                "symptoms":        st.session_state.get("current_symptoms", []),
                "city":            st.session_state.get("current_city"),
                "severity":        st.session_state.get("current_severity", "low"),
                "specialist":      st.session_state.get("current_specialist", ""),
                "doctors":         st.session_state.get("suggested_doctors", []),
                "diagnosis":       "",
                "is_emergency":    False,
                "safe_to_proceed": True,
                "needs_more_info": False,
                "memory_context":  _memory_ctx,
                "input_type":      "medical",
                "ask_for_city":    st.session_state.get("ask_for_city", False),
                "booking_requested": st.session_state.get("booking_requested", False),
            }
            final_state        = graph_app.invoke(initial_state)
            agent_response_en  = final_state["messages"][-1].content
            agent_response_display = agent_response_en
            if user_lang != "en":
                agent_response_display = translate_from_english(agent_response_en, user_lang)

            st.session_state.current_symptoms  = final_state.get("symptoms", [])
            st.session_state.current_city      = final_state.get("city")
            st.session_state.current_severity  = final_state.get("severity", "low")
            st.session_state.current_specialist = final_state.get("specialist")
            st.session_state.suggested_doctors  = final_state.get("doctors", [])
            st.session_state.ask_for_city       = final_state.get("ask_for_city", False)
            st.session_state.booking_requested  = final_state.get("booking_requested", False)

            if _user_id and final_state.get("symptoms"):
                save_patient_memory(
                    user_id=_user_id,
                    symptoms=final_state.get("symptoms", []),
                    condition=final_state.get("diagnosis", ""),
                    specialist=final_state.get("specialist", ""),
                    session_id=curr_id,
                )

            st.chat_message("assistant").markdown(agent_response_display)

            # ── TTS: read response aloud if toggle is on ───────────────
            if st.session_state.get("tts_enabled", False):
                try:
                    # Strip markdown symbols for cleaner speech
                    import re as _re
                    _clean = _re.sub(r"[*_`#>\[\]]", "", agent_response_display)[:800]
                    _tts_audio, _tts_mime = synthesize_speech_via_sarvam(
                        _clean,
                        language_code=_sarvam_lang_code(st.session_state.get("user_lang", "en")),
                    )
                    st.session_state["last_tts_audio"] = _tts_audio
                    st.session_state["last_tts_mime"] = _tts_mime
                    st.session_state["last_tts_text"] = _clean
                    st.session_state["tts_autoplay_once"] = True
                except Exception as _te:
                    pass  # silently skip if TTS fails
            st.session_state.messages.append(AIMessage(content=agent_response_en))
            save_message(curr_id, "assistant", agent_response_en)

            sessions_now  = get_all_sessions()
            current_title = next((t for sid, t in sessions_now if sid == curr_id), "New Chat")
            if current_title == "New Chat":
                update_session_title(curr_id, user_input.strip()[:50])

            st.rerun()
    except Exception as e:
        st.error(f"Error: {e}")

# ── Sidebar: Booking + Appointments + Medicines ───────────────────────────────
with st.sidebar:
    st.divider()
    # Only allow patients to book appointments (not doctors!)
    if (_user.get("role") != "doctor" and 
        (st.session_state.get("suggested_doctors") or st.session_state.get("booking_requested"))):
        st.subheader("Book Appointment")
        with st.form("booking_form"):
            doctors = st.session_state.get("suggested_doctors", [])
            if not doctors:
                spec  = st.session_state.get("current_specialist") or "General Physician"
                city  = st.session_state.get("current_city")
                rows  = find_doctors_in_db(spec, city) or find_doctors_in_db(spec, None) \
                        or find_doctors_in_db("General Physician", city) \
                        or find_doctors_in_db("General Physician", None)
                if rows:
                    doctors = [{"doctor_name": r[0], "specialist": r[1],
                                "availability": r[2], "city": r[3], "consultation_fee": 500}
                               for r in rows]
            if doctors:
                doctor_options = [
                    f"{d['doctor_name']} — {d['specialist']} ({d.get('city','')}) | {d.get('availability','')}"
                    for d in doctors
                ]
            else:
                st.warning("No doctors found.")
                doctor_options = ["General Physician (Assign Next Available)"]

            selected_doc = st.selectbox("Select Doctor", doctor_options)
            consultation_fee = 500
            if doctors and selected_doc != "General Physician (Assign Next Available)":
                consultation_fee = doctors[doctor_options.index(selected_doc)].get("consultation_fee", 500)

            st.info(f"Consultation Fee: ₹{consultation_fee}")
            name  = st.text_input("Patient Name", placeholder="Enter your full name")
            phone = st.text_input("Phone Number", placeholder="+91XXXXXXXXXX")
            email = st.text_input("Email Address *", placeholder="your@email.com", help="Required to receive appointment confirmation")
            today = datetime.date.today()
            date  = st.date_input("Preferred Date", min_value=today, value=today)
            # Business-hours time slots only (9 AM – 8 PM, 30-min steps)
            _slots = [
                datetime.time(h, m).strftime("%I:%M %p")
                for h in range(9, 20) for m in (0, 30)
            ]
            time_str = st.selectbox("Preferred Time", _slots, index=2)  # default 10:00 AM
            submit_button = st.form_submit_button("Proceed to Payment", use_container_width=True)

            if submit_button:
                if not name or not phone or not email:
                    st.error("Please fill in all required fields (Name, Phone, and Email)!")
                elif "@" not in email or "." not in email:
                    st.error("Please enter a valid email address!")
                else:
                    doc_display = selected_doc.split(" — ")[0] if " — " in selected_doc else selected_doc
                    st.session_state.pending_booking = {
                        "doctor": doc_display, "name": name, "phone": phone,
                        "email": email, "date": date, "time": time_str,
                        "consultation_fee": consultation_fee,
                        "specialist": doctors[doctor_options.index(selected_doc)].get("specialist", "") if doctors and selected_doc != "General Physician (Assign Next Available)" else "",
                        "city": doctors[doctor_options.index(selected_doc)].get("city", "") if doctors and selected_doc != "General Physician (Assign Next Available)" else "",
                    }
                    st.success("Proceeding to payment...")
                    st.balloons()

    # Show message to doctors that they cannot book appointments
    elif (_user.get("role") == "doctor" and 
          (st.session_state.get("suggested_doctors") or st.session_state.get("booking_requested"))):
        st.warning("⚠️ **Doctors cannot book appointments**\n\nYou are logged in as a doctor. "
                   "Only patients can book appointments. Please use your Doctor Dashboard to manage your schedule and view appointments.")

    if "pending_booking" in st.session_state and st.session_state.pending_booking:
        booking = st.session_state.pending_booking
        st.sidebar.markdown("---")
        st.sidebar.subheader("Payment")
        try:
            from payment_service import create_booking_payment, create_mock_payment_order, rupees_to_paise
            from notification_service import send_booking_confirmation
            booking_id    = f"{curr_id}_{len(st.session_state.messages)}"
            payment_order = create_booking_payment(
                doctor_name=booking["doctor"], patient_name=booking["name"],
                consultation_fee=booking["consultation_fee"], booking_id=booking_id
            ) or create_mock_payment_order(
                amount=rupees_to_paise(booking["consultation_fee"]),
                receipt_id=f"booking_{booking_id}"
            )
            amount_display = payment_order.get("amount_display", f"₹{booking['consultation_fee']}")
            st.sidebar.info(f"**Amount:** {amount_display}")

            payment_status = None
            if payment_order.get("mock"):
                if st.sidebar.button("✅ Confirm Payment (Test Mode)", use_container_width=True):
                    payment_status = "success"
                    payment_id = "pay_mock_" + booking_id
            else:
                st.sidebar.warning("Razorpay integration: Add API keys to .env")
                if st.sidebar.button("Pay with Razorpay (Demo)", use_container_width=True):
                    payment_status = "success"
                    payment_id = "pay_demo_" + booking_id

            if payment_status == "success":
                # 💾 Persist booking to database so My Appointments shows it
                save_booking(
                    user_id         = str(_user_id),
                    doctor_id       = 0,
                    doctor_name     = booking["doctor"],
                    specialty       = booking.get("specialist", ""),
                    city            = booking.get("city", ""),
                    appointment_date= booking["date"].strftime("%Y-%m-%d"),
                    appointment_time= booking["time"],  # already a formatted string
                )
                notification_results = send_booking_confirmation({
                    "patient_name":  booking["name"],
                    "patient_phone": booking["phone"],
                    "patient_email": booking.get("email"),
                    "doctor_name":   booking["doctor"],
                    "date":          booking["date"].strftime("%B %d, %Y"),
                    "time":          booking["time"],
                    "booking_id":    booking_id,
                })
                receipt = (
                    f"📋 **Appointment Confirmation**\n\n✅ Booked & Paid!\n\n"
                    f"**Doctor:** {booking['doctor']}\n"
                    f"**Date:** {booking['date'].strftime('%B %d, %Y')}  "
                    f"**Time:** {booking['time']}\n"
                    f"**Patient:** {booking['name']} · {booking['phone']}\n"
                    f"**Fee:** ₹{booking['consultation_fee']}  **Payment ID:** {payment_id}\n\n"
                    f"📧 **Confirmation email sent to:** {booking.get('email', 'N/A')}\n"
                    f"SMS: {'✅' if notification_results.get('sms') else '📧 Email sent'}  "
                    f"Email: {'✅ Sent successfully!' if notification_results.get('email') else '⚠️ Check spam folder'}\n\n"
                    f"*Ref: #{booking_id}*"
                )
                st.session_state.messages.append(AIMessage(content=receipt))
                save_message(curr_id, "assistant", receipt)
                st.session_state.pending_booking = None
                st.sidebar.success("✅ Payment successful!")
                st.rerun()
        except Exception as e:
            st.sidebar.error(f"Payment service error: {e}")
    else:
        if not (st.session_state.get("suggested_doctors") or st.session_state.get("booking_requested")):
            st.info("Start a chat to find doctors.")

    st.divider()
    with st.expander("📋 My Appointments"):
        upcoming = get_upcoming_bookings(str(_user_id) if _user_id else str(curr_id))
        if upcoming:
            for appt in upcoming:
                booking_id, doc_name, specialty, city, appt_date, appt_time, status = appt
                st.markdown(f"**{doc_name}** ({specialty})")
                st.caption(f"📅 {appt_date} {appt_time} · {city} · `{status}`")
                if status != "cancelled":
                    if st.button("Cancel", key=f"cancel_{booking_id}", use_container_width=True):
                        cancel_booking(booking_id)
                        st.toast("Appointment cancelled.")
                        st.rerun()
                st.markdown("---")
        else:
            st.caption("No upcoming appointments.")

    _symptoms_now = st.session_state.get("current_symptoms", [])
    if _symptoms_now:
        st.divider()
        with st.expander("💊 Medicine Suggestions", expanded=False):
            _meds = find_medicines_for_symptoms(_symptoms_now)
            if _meds:
                st.caption("⚠️ *Always consult a doctor before taking medication.*")
                for m in _meds[:6]:
                    rx_badge = "🔴 Rx Required" if m["prescription_required"] else "🟢 OTC"
                    st.markdown(f"""
<div style="background:#1e2130;border-radius:10px;padding:12px 14px;margin-bottom:8px;
            border-left:3px solid {'#ef4444' if m['prescription_required'] else '#22c55e'};">
<b style="color:#f0f0f0;">{m['generic_name']}</b>
<span style="float:right;font-size:0.72rem;color:#94a3b8;">{rx_badge}</span><br>
<span style="color:#94a3b8;font-size:0.78rem;">{m['brand_names']}</span><br>
<span style="color:#cbd5e1;font-size:0.8rem;">📋 {m['dosage_note']}</span><br>
{"<span style='color:#fbbf24;font-size:0.75rem;'>⚠️ " + m['warning'] + "</span>" if m.get('warning') else ""}
</div>""", unsafe_allow_html=True)
            else:
                st.caption("No specific OTC medicines found. Please consult a doctor.")

    with st.expander("🛠️ Debug State"):
        st.write("Severity:", st.session_state.get("current_severity"))
        st.write("City:", st.session_state.get("current_city"))
        st.write("Symptoms:", st.session_state.get("current_symptoms"))
        st.write("Ask City:", st.session_state.get("ask_for_city"))
        st.write("Booking:", st.session_state.get("booking_requested"))