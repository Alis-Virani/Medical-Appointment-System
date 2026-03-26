"""Admin router: doctor management."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, Depends, HTTPException
from backend.auth_utils import require_role
from backend.models import DoctorCreate
from database import get_all_doctors, save_doctor, DB_NAME
import sqlite3

router = APIRouter()


@router.get("/doctors")
def admin_list_doctors(current_user: dict = Depends(require_role("admin"))):
    return get_all_doctors()


@router.post("/doctors")
def admin_add_doctor(req: DoctorCreate, current_user: dict = Depends(require_role("admin"))):
    save_doctor(
        name=req.name, specialty=req.specialty, city=req.city,
        years_experience=req.years_experience, contact=req.contact,
        rating=req.rating, fees=req.fees,
        clinic_address=req.clinic_address, qualifications=req.qualifications,
        availability=req.availability,
    )
    return {"message": f"Doctor {req.name} added successfully"}


@router.delete("/doctors/{doctor_id}")
def admin_remove_doctor(doctor_id: int, current_user: dict = Depends(require_role("admin"))):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("UPDATE doctors_v2 SET is_active=0 WHERE id=?", (doctor_id,))
    conn.commit()
    conn.close()
    return {"message": "Doctor removed"}


@router.get("/users")
def admin_list_users(current_user: dict = Depends(require_role("admin"))):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    cur.execute("SELECT id, username, full_name, email, role, created_at FROM users ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return [
        {"id": r[0], "username": r[1], "full_name": r[2],
         "email": r[3], "role": r[4], "created_at": r[5]}
        for r in rows
    ]


@router.get("/stats")
def admin_stats(current_user: dict = Depends(require_role("admin"))):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE role='patient'")
    patients = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE role='doctor'")
    doctors = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM bookings")
    bookings = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM bookings WHERE status='confirmed'")
    confirmed = cur.fetchone()[0]
    conn.close()
    return {
        "total_patients": patients,
        "total_doctors": doctors,
        "total_bookings": bookings,
        "confirmed_bookings": confirmed,
    }
