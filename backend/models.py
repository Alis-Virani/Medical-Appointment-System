"""Pydantic models for request/response bodies."""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str
    email: str = ""
    phone: str = ""
    role: str = "patient"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class UserProfile(BaseModel):
    id: int
    username: str
    full_name: str
    email: str
    phone: str
    role: str


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[int] = None

class ChatResponse(BaseModel):
    response: str
    session_id: int
    is_emergency: bool = False
    is_clinical_report: bool = False


# ── Appointments ──────────────────────────────────────────────────────────────

class BookingCreate(BaseModel):
    doctor_id: Optional[int] = None
    doctor_name: str
    specialty: str
    city: str
    appointment_date: str
    appointment_time: str
    notes: str = ""

class BookingResponse(BaseModel):
    id: int
    doctor_name: str
    specialty: str
    city: str
    appointment_date: str
    appointment_time: str
    status: str
    created_at: Optional[str] = None


# ── Doctors ───────────────────────────────────────────────────────────────────

class DoctorResponse(BaseModel):
    id: int
    name: str
    specialty: str
    availability: str
    city: str

class DoctorV2Response(BaseModel):
    id: int
    doctor_id: str
    name: str
    specialty: str
    city: str
    years_experience: int
    contact: str
    rating: float
    fees: int
    clinic_address: str
    qualifications: str
    availability: str

class DoctorCreate(BaseModel):
    name: str
    specialty: str
    city: str
    years_experience: int = 0
    contact: str = ""
    rating: float = 4.5
    fees: int = 500
    clinic_address: str = ""
    qualifications: str = ""
    availability: str = "Mon-Sat 9am-6pm"


# ── Patient Notes ─────────────────────────────────────────────────────────────

class NoteCreate(BaseModel):
    patient_id: int
    content: str
    diagnosis: str = ""
    prescription: str = ""

class NoteResponse(BaseModel):
    id: int
    patient_id: int
    patient_name: str
    content: str
    diagnosis: str
    prescription: str
    created_at: str


# ── Health History ────────────────────────────────────────────────────────────

class HealthMemoryResponse(BaseModel):
    symptom: str
    condition: str
    specialist: str
    recorded_at: str


# ── Sessions ──────────────────────────────────────────────────────────────────

class SessionResponse(BaseModel):
    id: int
    title: str
