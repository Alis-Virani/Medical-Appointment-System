"""Patient notes router (doctor-only for writing, patient can read own)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, Depends, HTTPException
from backend.auth_utils import get_current_user, require_role
from database import DB_NAME
import sqlite3
from datetime import datetime

router = APIRouter()

def _init_notes_table():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS patient_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER NOT NULL,
            patient_id INTEGER NOT NULL,
            patient_name TEXT,
            content TEXT,
            diagnosis TEXT DEFAULT '',
            prescription TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

_init_notes_table()


@router.get("/")
def list_notes(current_user: dict = Depends(get_current_user)):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    if current_user["role"] == "doctor":
        cur.execute("""
            SELECT id, patient_id, patient_name, content, diagnosis, prescription, created_at
            FROM patient_notes WHERE doctor_id = ? ORDER BY created_at DESC
        """, (current_user["id"],))
    else:
        cur.execute("""
            SELECT id, patient_id, patient_name, content, diagnosis, prescription, created_at
            FROM patient_notes WHERE patient_id = ? ORDER BY created_at DESC
        """, (current_user["id"],))
    rows = cur.fetchall()
    conn.close()
    return [
        {"id": r[0], "patient_id": r[1], "patient_name": r[2],
         "content": r[3], "diagnosis": r[4], "prescription": r[5], "created_at": r[6]}
        for r in rows
    ]


@router.post("/")
def create_note(
    patient_id: int,
    patient_name: str,
    content: str,
    diagnosis: str = "",
    prescription: str = "",
    current_user: dict = Depends(require_role("doctor"))
):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO patient_notes (doctor_id, patient_id, patient_name, content, diagnosis, prescription)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (current_user["id"], patient_id, patient_name, content, diagnosis, prescription))
    conn.commit()
    note_id = cur.lastrowid
    conn.close()
    return {"id": note_id, "message": "Note saved"}


@router.put("/{note_id}")
def update_note(
    note_id: int,
    content: str,
    diagnosis: str = "",
    prescription: str = "",
    current_user: dict = Depends(require_role("doctor"))
):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("""
        UPDATE patient_notes SET content=?, diagnosis=?, prescription=?, updated_at=?
        WHERE id=? AND doctor_id=?
    """, (content, diagnosis, prescription, datetime.now().isoformat(), note_id, current_user["id"]))
    conn.commit()
    conn.close()
    return {"message": "Note updated"}
