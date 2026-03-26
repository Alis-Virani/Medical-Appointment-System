"""Doctor schedule router."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, Depends
from backend.auth_utils import get_current_user, require_role
from database import DB_NAME, get_user_bookings
import sqlite3

router = APIRouter()


@router.get("/")
def get_schedule(current_user: dict = Depends(require_role("doctor"))):
    """Get doctor's appointments (bookings where doctor_name matches)."""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    # Get bookings for this doctor by matching their full name
    cur.execute("""
        SELECT b.id, b.user_id, u.full_name as patient_name, b.specialty,
               b.appointment_date, b.appointment_time, b.status, b.notes
        FROM bookings b
        LEFT JOIN users u ON b.user_id = u.id
        WHERE b.doctor_name LIKE ?
        ORDER BY b.appointment_date ASC, b.appointment_time ASC
    """, (f"%{current_user['full_name']}%",))
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "id": r[0], "patient_id": r[1], "patient_name": r[2],
            "specialty": r[3], "appointment_date": r[4],
            "appointment_time": r[5], "status": r[6], "notes": r[7]
        }
        for r in rows
    ]


@router.get("/today")
def today_appointments(current_user: dict = Depends(require_role("doctor"))):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    cur.execute("""
        SELECT b.id, u.full_name, b.appointment_time, b.status, b.notes
        FROM bookings b
        LEFT JOIN users u ON b.user_id = u.id
        WHERE b.doctor_name LIKE ? AND b.appointment_date = date('now')
        ORDER BY b.appointment_time ASC
    """, (f"%{current_user['full_name']}%",))
    rows = cur.fetchall()
    conn.close()
    return [
        {"id": r[0], "patient_name": r[1], "time": r[2], "status": r[3], "notes": r[4]}
        for r in rows
    ]


@router.delete("/past")
def clear_past_appointments(current_user: dict = Depends(require_role("doctor"))):
    """Delete past appointments for the logged-in doctor."""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    cur.execute(
        """
        DELETE FROM bookings
        WHERE doctor_name LIKE ?
          AND date(appointment_date) < date('now')
        """,
        (f"%{current_user['full_name']}%",)
    )
    deleted_count = cur.rowcount
    conn.commit()
    conn.close()
    return {"message": "Past appointments cleared", "deleted": deleted_count}
