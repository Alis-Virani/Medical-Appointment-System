"""
demo_data.py — Generate realistic test data for doctor dashboard demo
Run once: python demo_data.py
This creates 20+ sample appointments for demo doctors
"""
import sqlite3
from datetime import datetime, timedelta
import random

DB_NAME = "hospital.db"

def populate_demo_data():
    """Create sample appointments for faculty demo"""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    
    # Ensure we have at least one demo doctor
    demo_doctor = "Dr. Rajesh Patel"
    cur.execute("""
        SELECT id FROM doctors_v2 
        WHERE name=? AND is_active=1
        LIMIT 1
    """, (demo_doctor,))
    
    if not cur.fetchone():
        print(f"❌ Demo doctor '{demo_doctor}' not found. Using existing doctor...")
        cur.execute("SELECT id, name FROM doctors_v2 WHERE is_active=1 LIMIT 1")
        result = cur.fetchone()
        if result:
            demo_doctor = result[1]
        else:
            print("❌ No active doctors found. Add doctors first!")
            conn.close()
            return
    
    # Sample patient names
    patient_names = [
        "Amit Sharma", "Priya Singh", "Vikram Kumar", "Rohini Desai",
        "Arjun Nair", "Neha Iyer", "Sandeep Patel", "Anjali Reddy",
        "Kunal Verma", "Deepika Gupta", "Harish Menon", "Pooja Chopra",
        "Aditya Rao", "Sneha Bhat", "Rahul Joshi", "Maya Krishnan",
        "Nikhil Saxena", "Divya Agarwal", "Sanjay Singh", "Kavya Das"
    ]
    
    # Chief complaints (symptoms/reasons)
    complaints = [
        "Fever and body ache",
        "Persistent cough",
        "Headache and dizziness",
        "Abdominal pain",
        "Allergic reaction",
        "Routine checkup",
        "Blood pressure monitoring",
        "Diabetes screening",
        "Cold and congestion",
        "Throat infection",
        "Skin rash",
        "Joint pain",
        "Fatigue and weakness",
        "Insomnia",
        "Anxiety consultation",
    ]
    
    # Generate appointments
    appointments = []
    today = datetime.now().date()
    
    # Past appointments (last 30 days)
    for i in range(12):
        appt_date = today - timedelta(days=random.randint(1, 30))
        appt_time = f"{random.randint(9, 17)}:{random.choice(['00', '30'])}"
        
        appointments.append({
            "user_id": f"patient_{i+1}",
            "doctor_name": demo_doctor,
            "specialty": "General Physician",
            "city": "Ahmedabad",
            "appointment_date": appt_date.strftime("%Y-%m-%d"),
            "appointment_time": appt_time,
            "status": random.choice(["completed", "completed", "no-show"]),
            "notes": random.choice(complaints),
            "created_at": (appt_date - timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d 10:30"),
        })
    
    # Upcoming appointments (next 14 days)
    for i in range(8):
        appt_date = today + timedelta(days=random.randint(1, 14))
        appt_time = f"{random.randint(9, 17)}:{random.choice(['00', '30'])}"
        
        appointments.append({
            "user_id": f"patient_{100+i+1}",
            "doctor_name": demo_doctor,
            "specialty": "General Physician",
            "city": "Ahmedabad",
            "appointment_date": appt_date.strftime("%Y-%m-%d"),
            "appointment_time": appt_time,
            "status": random.choice(["pending", "pending", "confirmed"]),
            "notes": random.choice(complaints),
            "created_at": (today - timedelta(days=random.randint(0, 3))).strftime("%Y-%m-%d 10:30"),
        })
    
    # Insert into database
    inserted = 0
    for appt in appointments:
        try:
            cur.execute("""
                INSERT INTO bookings 
                (user_id, doctor_name, specialty, city, appointment_date, 
                 appointment_time, status, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                appt["user_id"],
                appt["doctor_name"],
                appt["specialty"],
                appt["city"],
                appt["appointment_date"],
                appt["appointment_time"],
                appt["status"],
                appt["notes"],
                appt["created_at"]
            ))
            inserted += 1
        except sqlite3.IntegrityError:
            # Duplicate, skip
            pass
    
    conn.commit()
    conn.close()
    
    print(f"✅ Added {inserted} demo appointments for {demo_doctor}")
    print(f"   • Past appointments: 12")
    print(f"   • Upcoming appointments: 8")
    print(f"\n📌 To use this demo:")
    print(f"   1. Login as 'doctor' (if role=doctor exists)")
    print(f"   2. Visit Doctor Dashboard")
    print(f"   3. See populated appointments ready for demo!")

if __name__ == "__main__":
    populate_demo_data()
