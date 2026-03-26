"""Appointments router."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, Depends, HTTPException
from backend.models import BookingCreate, BookingResponse
from backend.auth_utils import get_current_user
from database import (
    save_booking, get_user_bookings, get_upcoming_bookings,
    get_past_bookings, cancel_booking, reschedule_booking
)
from typing import List

router = APIRouter()


def _row_to_booking(row) -> dict:
    return {
        "id": row[0],
        "doctor_name": row[1],
        "specialty": row[2],
        "city": row[3],
        "appointment_date": row[4],
        "appointment_time": row[5],
        "status": row[6],
        "created_at": str(row[7]) if len(row) > 7 else None,
    }


@router.get("/", response_model=List[BookingResponse])
def list_appointments(current_user: dict = Depends(get_current_user)):
    rows = get_user_bookings(current_user["id"])
    return [_row_to_booking(r) for r in rows]


@router.get("/upcoming", response_model=List[BookingResponse])
def upcoming_appointments(current_user: dict = Depends(get_current_user)):
    rows = get_upcoming_bookings(current_user["id"])
    return [_row_to_booking(r) for r in rows]


@router.get("/past", response_model=List[BookingResponse])
def past_appointments(current_user: dict = Depends(get_current_user)):
    rows = get_past_bookings(current_user["id"])
    return [_row_to_booking(r) for r in rows]


@router.post("/", response_model=dict)
def book_appointment(req: BookingCreate, current_user: dict = Depends(get_current_user)):
    booking_id = save_booking(
        user_id=current_user["id"],
        doctor_id=req.doctor_id,
        doctor_name=req.doctor_name,
        specialty=req.specialty,
        city=req.city,
        appointment_date=req.appointment_date,
        appointment_time=req.appointment_time,
        notes=req.notes,
    )
    return {"id": booking_id, "message": "Appointment booked successfully"}


@router.put("/{booking_id}/cancel")
def cancel_appointment(booking_id: int, current_user: dict = Depends(get_current_user)):
    cancel_booking(booking_id)
    return {"message": "Appointment cancelled"}


@router.put("/{booking_id}/reschedule")
def reschedule(booking_id: int, new_date: str, new_time: str,
               current_user: dict = Depends(get_current_user)):
    reschedule_booking(booking_id, new_date, new_time)
    return {"message": "Appointment rescheduled"}
