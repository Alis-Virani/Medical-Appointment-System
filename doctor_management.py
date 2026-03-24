"""
Dynamic Doctor Management System
=================================
CRUD operations for doctors with Neo4j + SQLite hybrid approach
- Fast search: SQLite for quick queries
- Intelligence: Neo4j for relationship reasoning
"""

from datetime import datetime
import sqlite3
import json
from typing import List, Dict, Optional
from knowledge_graph import get_knowledge_graph

DB_NAME = "hospital.db"

# ============================================================================
# ENHANCED DATABASE SCHEMA
# ============================================================================

def init_doctor_management_db():
    """Initialize enhanced doctor management schema"""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    
    # Enhanced doctors table with more details
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctors_v2 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        specialty TEXT NOT NULL,
        city TEXT NOT NULL,
        availability TEXT,
        rating REAL DEFAULT 4.5,
        fees INTEGER DEFAULT 500,
        contact TEXT,
        clinic_address TEXT,
        qualifications TEXT,
        years_experience INTEGER,
        tags TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Appointments booking table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_id TEXT NOT NULL,
        patient_name TEXT,
        patient_phone TEXT,
        appointment_date DATE,
        appointment_time TIME,
        status TEXT DEFAULT 'scheduled',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(doctor_id) REFERENCES doctors_v2(doctor_id)
    )
    """)
    
    # Doctor reviews/ratings
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctor_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_id TEXT NOT NULL,
        rating REAL,
        review TEXT,
        reviewer_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(doctor_id) REFERENCES doctors_v2(doctor_id)
    )
    """)
    
    conn.commit()
    conn.close()


# ============================================================================
# DOCTOR CRUD OPERATIONS
# ============================================================================

def add_doctor(name: str, specialty: str, city: str, availability: str = "",
               rating: float = 4.5, fees: int = 500, contact: str = "",
               clinic_address: str = "", qualifications: str = "",
               years_experience: int = 0, tags: str = "") -> str:
    """
    Add a new doctor to the system
    Returns: doctor_id
    """
    doctor_id = f"DOC_{int(datetime.now().timestamp() * 1000)}"
    
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT INTO doctors_v2 
    (doctor_id, name, specialty, city, availability, rating, fees, 
     contact, clinic_address, qualifications, years_experience, tags)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (doctor_id, name, specialty, city, availability, rating, fees,
          contact, clinic_address, qualifications, years_experience, tags))
    
    conn.commit()
    conn.close()
    
    # Also add to Neo4j
    kg = get_knowledge_graph()
    kg.add_doctor(doctor_id, name, specialty, city, rating, availability)
    
    return doctor_id


def get_doctor(doctor_id: str) -> Optional[Dict]:
    """Retrieve doctor details"""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM doctors_v2 WHERE doctor_id = ?", (doctor_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    columns = [desc[0] for desc in cursor.description]
    return dict(zip(columns, row))


def update_doctor(doctor_id: str, **kwargs) -> bool:
    """
    Update doctor information
    Example: update_doctor("DOC_123", rating=4.8, availability="Mon-Fri 10am-5pm")
    """
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    
    # Build update query
    set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
    kwargs["updated_at"] = datetime.now()
    set_clause += ", updated_at = ?"
    
    values = list(kwargs.values()) + [doctor_id]
    
    cursor.execute(f"UPDATE doctors_v2 SET {set_clause} WHERE doctor_id = ?", values)
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    
    # Also update in Neo4j
    kg = get_knowledge_graph()
    kg.update_doctor(doctor_id, **{k: v for k, v in kwargs.items() if k != "updated_at"})
    
    return success


def delete_doctor(doctor_id: str) -> bool:
    """Soft delete: mark doctor as inactive"""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    
    cursor.execute("UPDATE doctors_v2 SET is_active = 0 WHERE doctor_id = ?", (doctor_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    
    # Also remove from Neo4j
    kg = get_knowledge_graph()
    kg.remove_doctor(doctor_id)
    
    return success


def list_doctors(specialty: str = None, city: str = None, active_only: bool = True) -> List[Dict]:
    """
    List doctors with optional filters
    """
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    
    query = "SELECT * FROM doctors_v2 WHERE 1=1"
    params = []
    
    if active_only:
        query += " AND is_active = 1"
    
    if specialty:
        query += " AND specialty LIKE ?"
        params.append(f"%{specialty}%")
    
    if city:
        query += " AND city LIKE ?"
        params.append(f"%{city}%")
    
    query += " ORDER BY rating DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    
    return [dict(zip(columns, row)) for row in rows]


# ============================================================================
# APPOINTMENT MANAGEMENT
# ============================================================================

def book_appointment(doctor_id: str, patient_name: str, patient_phone: str,
                    appointment_date, appointment_time: str, notes: str = "") -> int:
    """
    Book an appointment
    Returns: appointment_id
    """
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT INTO appointments 
    (doctor_id, patient_name, patient_phone, appointment_date, appointment_time, notes)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (doctor_id, patient_name, patient_phone, appointment_date, appointment_time, notes))
    
    appointment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return appointment_id


def get_appointments(doctor_id: str, date_from = None) -> List[Dict]:
    """Get appointments for a doctor"""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    
    query = "SELECT * FROM appointments WHERE doctor_id = ? AND status = 'scheduled'"
    params = [doctor_id]
    
    if date_from:
        query += " AND appointment_date >= ?"
        params.append(date_from)
    
    query += " ORDER BY appointment_date, appointment_time"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    
    return [dict(zip(columns, row)) for row in rows]


def cancel_appointment(appointment_id: int) -> bool:
    """Cancel an appointment"""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    
    cursor.execute("UPDATE appointments SET status = 'cancelled' WHERE id = ?", (appointment_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    
    return success


# ============================================================================
# DOCTOR REVIEWS & RATINGS
# ============================================================================

def add_review(doctor_id: str, rating: float, review: str = "", reviewer_name: str = "Anonymous"):
    """Add a review for a doctor"""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    
    cursor.execute("""
    INSERT INTO doctor_reviews (doctor_id, rating, review, reviewer_name)
    VALUES (?, ?, ?, ?)
    """, (doctor_id, rating, review, reviewer_name))
    
    conn.commit()
    
    # Update doctor's average rating
    cursor.execute("""
    SELECT AVG(rating) FROM doctor_reviews WHERE doctor_id = ?
    """, (doctor_id,))
    avg_rating = cursor.fetchone()[0]
    conn.close()
    
    if avg_rating:
        update_doctor(doctor_id, rating=round(avg_rating, 1))
    
    return True


def get_reviews(doctor_id: str, limit: int = 5) -> List[Dict]:
    """Get reviews for a doctor"""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT * FROM doctor_reviews 
    WHERE doctor_id = ?
    ORDER BY created_at DESC
    LIMIT ?
    """, (doctor_id, limit))
    
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    
    return [dict(zip(columns, row)) for row in rows]


# ============================================================================
# MIGRATION: Convert old format to new format
# ============================================================================

def migrate_legacy_doctors():
    """Convert old doctors table to new format"""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    
    # Check if old table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='doctors'")
    if not cursor.fetchone():
        conn.close()
        return

    # Skip migration if new table already has data
    cursor.execute("SELECT COUNT(*) FROM doctors_v2")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    # Get all doctors from old table
    cursor.execute("SELECT name, specialty, availability, city FROM doctors")
    old_doctors = cursor.fetchall()
    conn.close()  # Close BEFORE calling add_doctor (which opens its own connection)

    # Insert into new table
    for name, specialty, availability, city in old_doctors:
        add_doctor(name, specialty, city, availability)

    print(f"✅ Migrated {len(old_doctors)} doctors to new schema")


# ============================================================================
# INITIALIZATION
# ============================================================================

def init_database():
    """Initialize all database tables"""
    from database import init_db
    init_db()  # Initialize old schema for compatibility
    init_doctor_management_db()  # Initialize new schema
    migrate_legacy_doctors()  # Migrate existing data


if __name__ == "__main__":
    init_database()
    
    # Example usage
    print("\n📝 Adding sample doctors...")
    doc1 = add_doctor("Dr. Mehta", "Cardiologist", "Ahmedabad", "Mon-Fri 11am-5pm", 4.8, 800, "+91-9876543210")
    doc2 = add_doctor("Dr. Shah", "Dermatologist", "Surat", "Mon-Sat 10am-2pm", 4.6, 600)
    
    print(f"✅ Added: {doc1}, {doc2}")
    
    print("\n📊 Listing doctors in Ahmedabad:")
    doctors = list_doctors(city="Ahmedabad")
    for doc in doctors:
        print(f"  • {doc['name']} ({doc['specialty']}) - {doc['rating']}⭐")
    
    print("\n⭐ Adding review:")
    add_review(doc1, 5.0, "Excellent doctor, very professional!", "Patient A")
    
    doctor = get_doctor(doc1)
    print(f"  Updated rating: {doctor['rating']}⭐")
