"""Chat router: send message to AI agent, manage sessions."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, Depends, HTTPException
from backend.models import ChatMessage, ChatResponse, SessionResponse
from backend.auth_utils import get_current_user
from database import (
    create_session, save_message, get_all_sessions,
    delete_session, delete_all_sessions, get_patient_memory_summary
)
from typing import List

router = APIRouter()


def _run_agent(user_message: str, session_id: int, user: dict,
               history: list = None) -> dict:
    """Call the LangGraph agent using get_graph_app().invoke() — same as pages/chat.py."""
    try:
        from lang_graph_agent import get_graph_app
        from langchain_core.messages import HumanMessage, AIMessage

        # Rebuild message history from DB for multi-turn context
        msgs = []
        if history:
            for row in history:
                if row["role"] == "user":
                    msgs.append(HumanMessage(content=row["content"]))
                else:
                    msgs.append(AIMessage(content=row["content"]))
        # Append the new user message
        msgs.append(HumanMessage(content=user_message))

        memory_ctx = ""
        try:
            memory_ctx = get_patient_memory_summary(user.get("id")) or ""
        except Exception:
            pass

        initial_state = {
            "messages":          msgs,
            "user_id":           str(session_id),
            "user_role":         user.get("role", "patient"),
            "symptoms":          [],
            "city":              None,
            "severity":          "low",
            "specialist":        "",
            "doctors":           [],
            "diagnosis":         "",
            "is_emergency":      False,
            "safe_to_proceed":   True,
            "needs_more_info":   False,
            "memory_context":    memory_ctx,
            "input_type":        "medical",
            "ask_for_city":      False,
            "booking_requested": False,
            "emergency_category": "",
            "medical_info_request": False,
        }

        graph_app   = get_graph_app()
        final_state = graph_app.invoke(initial_state)

        ai_text      = final_state["messages"][-1].content
        is_emergency = final_state.get("is_emergency", False)
        # Clinical report banner if flagged by guardrails
        emergency_cat = final_state.get("emergency_category", "")
        is_clinical   = (emergency_cat == "INFORMATIONAL_REPORT")

        return {
            "response":          ai_text,
            "is_emergency":      is_emergency,
            "is_clinical_report": is_clinical,
        }
    except Exception as e:
        return {
            "response":          f"I'm sorry, I encountered an error: {str(e)}",
            "is_emergency":      False,
            "is_clinical_report": False,
        }


@router.get("/sessions", response_model=List[SessionResponse])
def get_sessions(current_user: dict = Depends(get_current_user)):
    sessions = get_all_sessions(user_id=current_user["id"])
    return [{"id": s[0], "title": s[1]} for s in sessions]


@router.post("/sessions")
def new_session(current_user: dict = Depends(get_current_user)):
    sid = create_session(title="New Chat", user_id=current_user["id"])
    return {"id": sid, "title": "New Chat"}


@router.delete("/sessions/{session_id}")
def remove_session(session_id: int, current_user: dict = Depends(get_current_user)):
    delete_session(session_id)
    return {"message": "Session deleted"}


@router.delete("/sessions")
def clear_all_sessions(current_user: dict = Depends(get_current_user)):
    delete_all_sessions(user_id=current_user["id"])
    return {"message": "All sessions cleared"}


@router.post("/message", response_model=ChatResponse)
def send_message(req: ChatMessage, current_user: dict = Depends(get_current_user)):
    # Create a new session if none provided
    session_id = req.session_id
    if not session_id:
        session_id = create_session(
            title=req.message[:40] + ("..." if len(req.message) > 40 else ""),
            user_id=current_user["id"]
        )

    # Save user message first
    save_message(session_id, "user", req.message)

    # Fetch history for multi-turn context (last 10 messages)
    import sqlite3
    from database import DB_NAME
    conn = sqlite3.connect(DB_NAME, timeout=10)
    rows = conn.execute(
        "SELECT role, content FROM messages WHERE session_id=? ORDER BY id ASC LIMIT 10",
        (session_id,)
    ).fetchall()
    conn.close()
    history = [{"role": r[0], "content": r[1]} for r in rows]

    # Run agent
    result = _run_agent(req.message, session_id, current_user, history=history)
    ai_response = result.get("response", "I'm sorry, I could not process that.")
    is_emergency = result.get("is_emergency", False)
    is_clinical = result.get("is_clinical_report", False)

    # Save AI response
    save_message(session_id, "assistant", ai_response)

    return ChatResponse(
        response=ai_response,
        session_id=session_id,
        is_emergency=is_emergency,
        is_clinical_report=is_clinical,
    )


@router.get("/history/{session_id}")
def get_history(session_id: int, current_user: dict = Depends(get_current_user)):
    import sqlite3
    from database import DB_NAME
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    cur.execute(
        "SELECT role, content FROM messages WHERE session_id=? ORDER BY id ASC",
        (session_id,)
    )
    rows = cur.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in rows]
