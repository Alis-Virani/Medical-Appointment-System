"""Doctors router."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, Depends, Query
from backend.auth_utils import get_current_user
from database import find_doctors_in_db, get_all_doctors, search_doctors_smart
from typing import List, Optional

router = APIRouter()


@router.get("/")
def list_doctors(
    specialty: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    if specialty or city:
        rows = search_doctors_smart(specialty=specialty, city=city)
        return [{"name": r[0], "specialty": r[1], "availability": r[2], "city": r[3]} for r in rows]
    # Return from doctors_v2 (richer data)
    doctors = get_all_doctors()
    return doctors


@router.get("/search")
def search(
    q: str = Query(...),
    city: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    rows = search_doctors_smart(name=q, city=city)
    if not rows:
        rows = search_doctors_smart(specialty=q, city=city)
    return [{"name": r[0], "specialty": r[1], "availability": r[2], "city": r[3]} for r in rows]
