"""
setup_doctor_pages_demo.py — Populate Patient Notes and Schedule with demo data
"""
import sqlite3
from datetime import datetime, timedelta

DB_NAME = "hospital.db"

def setup_demo_data():
    """Setup demo for Patient Notes and Doctor Schedule"""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    
    print("🎬 Setting up demo data for Patient Notes and Schedule...\n")
    
    doctor_id = 8  # Alis virani doctor ID
    doctor_name = "Alis virani"
    
    # 1. Setup working hours
    print("📋 Step 1: Setting up working hours...")
    try:
        cur.execute("""
            INSERT INTO doctor_working_hours 
            (doctor_id, monday, tuesday, wednesday, thursday, friday, saturday, sunday, slot_minutes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(doctor_id) DO UPDATE SET
                monday=excluded.monday, tuesday=excluded.tuesday,
                wednesday=excluded.wednesday, thursday=excluded.thursday,
                friday=excluded.friday, saturday=excluded.saturday,
                sunday=excluded.sunday, slot_minutes=excluded.slot_minutes
        """, (
            doctor_id,
            "10:00 AM - 1:00 PM, 3:00 PM - 6:00 PM",   # Monday
            "10:00 AM - 1:00 PM, 3:00 PM - 6:00 PM",   # Tuesday
            "10:00 AM - 1:00 PM, 3:00 PM - 6:00 PM",   # Wednesday
            "10:00 AM - 1:00 PM, 3:00 PM - 6:00 PM",   # Thursday
            "10:00 AM - 1:00 PM, 3:00 PM - 6:00 PM",   # Friday
            "10:00 AM - 1:00 PM",                       # Saturday
            "",                                          # Sunday (off)
            30  # 30-minute slots
        ))
        conn.commit()
        print("   ✅ Working hours configured")
    except Exception as e:
        print(f"   ⚠️  {e}")
    
    # 2. Add blocked dates
    print("\n📋 Step 2: Adding blocked dates (holidays/leave)...")
    today = datetime.now().date()
    blocked_dates = [
        (today + timedelta(days=8), "Vacation"),
        (today + timedelta(days=9), "Vacation"),
        (today + timedelta(days=25), "Medical Conference"),
    ]
    
    for date_str, reason in blocked_dates:
        try:
            cur.execute("""
                INSERT INTO doctor_blocked_dates (doctor_id, blocked_date, reason)
                VALUES (?, ?, ?)
            """, (doctor_id, date_str.strftime("%Y-%m-%d"), reason))
        except sqlite3.IntegrityError:
            pass
    
    conn.commit()
    print(f"   ✅ Added {len(blocked_dates)} blocked dates")
    
    # 3. Add consultation notes for demo patients
    print("\n📋 Step 3: Adding consultation notes...")
    
    # Sample consultations
    consultations = [
        {
            "patient_id": 1,
            "patient_name": "Rahul Sharma",
            "diagnosis": "Hypertension (Stage 1)",
            "prescription": "Amlodipine 5mg once daily, Low sodium diet, Regular exercise",
            "notes": "Patient presents with elevated BP readings over past 2 weeks. Family history of hypertension. BMI slightly elevated. Advised lifestyle modifications and medication.",
            "follow_up": (today + timedelta(days=14)).strftime("%Y-%m-%d"),
            "date": (today - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "patient_id": 2,
            "patient_name": "Priya Verma",
            "diagnosis": "Viral fever with cough",
            "prescription": "Paracetamol 500mg thrice daily, Cough syrup - 10ml twice daily, Rest and hydration",
            "notes": "Temperature 101.5°F, mild cough, throat irritation. Pulse and respiration normal. Advised complete bed rest for 3 days.",
            "follow_up": (today + timedelta(days=3)).strftime("%Y-%m-%d"),
            "date": (today - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "patient_id": 3,
            "patient_name": "Amit Patel",
            "diagnosis": "Type 2 Diabetes Mellitus",
            "prescription": "Metformin 500mg twice daily, Restricted sugar intake, Morning walks 30 min",
            "notes": "Fasting glucose 156 mg/dL. HbA1c pending. Discussed dietary changes and exercise routine. Referred to diabetologist.",
            "follow_up": (today + timedelta(days=21)).strftime("%Y-%m-%d"),
            "date": (today - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "patient_id": 4,
            "patient_name": "Neha Singh",
            "diagnosis": "Migraine with aura",
            "prescription": "Sumatriptan 50mg as needed, Avoid triggers, 8 hours sleep recommended",
            "notes": "Patient reports 2-3 migraine episodes per month. Identified triggers: stress, caffeine. Lifestyle modifications advised.",
            "follow_up": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "date": (today - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "patient_id": 5,
            "patient_name": "Vikram Desai",
            "diagnosis": "Acute pharyngitis",
            "prescription": "Amoxicillin 500mg thrice daily for 5 days, Salt water gargles, Lozenges",
            "notes": "Sore throat, fever 100.2°F, swollen tonsils. No pus. Likely viral. Symptomatic treatment prescribed.",
            "follow_up": (today + timedelta(days=5)).strftime("%Y-%m-%d"),
            "date": (today - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        },
    ]
    
    added = 0
    for consult in consultations:
        try:
            cur.execute("""
                INSERT INTO consultation_notes
                (doctor_id, doctor_name, patient_id, patient_name, booking_id,
                 diagnosis, prescription, notes, follow_up_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doctor_id,
                doctor_name,
                consult["patient_id"],
                consult["patient_name"],
                consult["patient_id"],  # booking_id
                consult["diagnosis"],
                consult["prescription"],
                consult["notes"],
                consult["follow_up"],
                consult["date"]
            ))
            added += 1
        except Exception as e:
            print(f"   ⚠️  Failed to add note for {consult['patient_name']}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"   ✅ Added {added} consultation notes\n")
    
    # Display summary
    print("=" * 70)
    print("🎉 DOCTOR PAGES DEMO DATA READY!\n")
    print("📋 PATIENT NOTES:")
    print("   ✓ 5 consultation notes with diagnosis, prescription, follow-up dates")
    print("   ✓ Professional medical notations")
    print("   ✓ Can view history per patient\n")
    print("📅 MY SCHEDULE:")
    print("   ✓ Working hours configured (Mon-Sat, off on Sunday)")
    print("   ✓ 30-minute appointment slots")
    print("   ✓ 3 blocked dates (vacation, conference)\n")
    print("🎬 DEMO WALKTHROUGH:")
    print("   1. Go to 'Patient Notes' tab")
    print("   2. Click 'Write Note' → Show consultation history")
    print("   3. Click 'All Notes' → Show all 5 notes")
    print("   4. Click 'By Patient' → Search specific patient notes")
    print("   5. Go to 'My Schedule' tab")
    print("   6. Show working hours for each day")
    print("   7. Show blocked dates (leave/vacation)")
    print("   8. Explain: 'Doctor can manage schedule and patient records'")
    print("=" * 70)

if __name__ == "__main__":
    setup_demo_data()
