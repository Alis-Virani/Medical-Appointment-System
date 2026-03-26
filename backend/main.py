"""
MediCare AI — FastAPI Backend
Run: uvicorn backend.main:app --reload --port 8000  (from e:\Project)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from doctor_management import init_database

from backend.routers import auth, chat, appointments, doctors, health, notes, schedule, admin

app = FastAPI(title="MediCare AI API", version="2.0.0")

# CORS — allow React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup: init DB
@app.on_event("startup")
def startup():
    init_db()
    init_database()

# Routers
app.include_router(auth.router,         prefix="/api/auth",         tags=["Auth"])
app.include_router(chat.router,         prefix="/api/chat",         tags=["Chat"])
app.include_router(appointments.router, prefix="/api/appointments", tags=["Appointments"])
app.include_router(doctors.router,      prefix="/api/doctors",      tags=["Doctors"])
app.include_router(health.router,       prefix="/api/health",       tags=["Health"])
app.include_router(notes.router,        prefix="/api/notes",        tags=["Notes"])
app.include_router(schedule.router,     prefix="/api/schedule",     tags=["Schedule"])
app.include_router(admin.router,        prefix="/api/admin",        tags=["Admin"])

@app.get("/api/ping")
def ping():
    return {"status": "ok", "service": "MediCare AI"}
