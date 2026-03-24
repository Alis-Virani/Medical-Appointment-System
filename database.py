import sqlite3
from datetime import datetime, timedelta

DB_NAME = "hospital.db"

def create_connection():
    """Create and return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row  # Enable column-based access
    return conn

def init_db():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    
    # 1. Doctors Table (Now with CITY column)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        specialty TEXT,
        availability TEXT,
        city TEXT
    )
    """)
    
    # 2. Sessions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        user_id INTEGER DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2b. Users Table (Authentication)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        full_name TEXT,
        email TEXT,
        phone TEXT,
        role TEXT DEFAULT 'patient',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    )
    """)

    # 3. Messages Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        role TEXT,
        content TEXT,
        FOREIGN KEY(session_id) REFERENCES sessions(id)
    )
    """)
    
    # 4. Payments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id TEXT,
        amount INTEGER,
        currency TEXT DEFAULT 'INR',
        razorpay_order_id TEXT,
        razorpay_payment_id TEXT,
        razorpay_signature TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 5. Notifications Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        type TEXT,
        recipient TEXT,
        subject TEXT,
        message TEXT,
        status TEXT DEFAULT 'pending',
        sent_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 6. Bookings Table (Appointment History)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        doctor_id INTEGER,
        doctor_name TEXT,
        specialty TEXT,
        city TEXT,
        appointment_date TEXT,
        appointment_time TEXT,
        status TEXT DEFAULT 'confirmed',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 7. Medicines Table — verified OTC/common drug list
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS medicines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        generic_name TEXT NOT NULL,
        brand_names TEXT,
        category TEXT,
        symptoms TEXT,          -- comma-separated symptom keywords
        prescription_required INTEGER DEFAULT 0,
        dosage_note TEXT,
        warning TEXT
    )
    """)

    # Auth Tokens Table — for persistent login across refreshes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS auth_tokens (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL
    )
    """)

    # Patient Memory Table — stores per-user symptom/condition history
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS patient_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        symptom TEXT,
        condition TEXT,
        specialist TEXT,
        session_id INTEGER,
        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 8. Seed medicines (once)
    cursor.execute("SELECT count(*) FROM medicines")
    if cursor.fetchone()[0] == 0:
        medicines = [
            # (generic_name, brand_names, category, symptoms, rx_required, dosage_note, warning)
            ("Paracetamol", "Crocin, Calpol, Dolo 650", "Analgesic/Antipyretic",
             "fever,headache,body pain,mild pain,toothache",
             0, "500-1000 mg every 6-8 hrs, max 4 g/day", "Avoid if liver disease"),
            ("Ibuprofen", "Brufen, Combiflam", "NSAID",
             "pain,inflammation,fever,muscle ache,joint pain,back pain",
             0, "400 mg every 8 hrs with food", "Avoid on empty stomach; avoid if kidney/peptic ulcer history"),
            ("Cetirizine", "Zyrtec, Alerid", "Antihistamine",
             "allergy,runny nose,sneezing,itching,hives,cold,watery eyes",
             0, "10 mg once daily at night", "May cause drowsiness"),
            ("Loratadine", "Claritin, Lorfast", "Antihistamine",
             "allergy,runny nose,sneezing,itching,cold",
             0, "10 mg once daily", "Non-drowsy antihistamine"),
            ("Omeprazole", "Omez, Prilosec", "Proton Pump Inhibitor",
             "acidity,heartburn,GERD,acid reflux,stomach pain,ulcer",
             0, "20 mg once daily 30 min before breakfast", "Not for long-term use without medical advice"),
            ("Pantoprazole", "Pantop, Protonix", "Proton Pump Inhibitor",
             "acidity,heartburn,GERD,ulcer,stomach pain",
             0, "40 mg once daily before breakfast", "Better for night-time acidity"),
            ("Antacid (Magnesium Hydroxide)", "Eno, Gelusil, Digene", "Antacid",
             "acidity,heartburn,indigestion,bloating,gas",
             0, "As needed after meals or when symptomatic", "Short-term use only"),
            ("ORS", "Electral, Pedialyte", "Oral Rehydration",
             "dehydration,diarrhea,vomiting,weakness,loose motions",
             0, "Dissolve 1 sachet in 1 L water; sip throughout the day", "Essential during diarrhea/vomiting"),
            ("Dextromethorphan", "Benadryl DM, Corex-D", "Cough Suppressant",
             "dry cough,throat irritation,irritant cough",
             0, "10-20 mg every 4-6 hrs", "Do NOT use for productive (wet) cough"),
            ("Guaifenesin", "Mucinex, Grilinctus", "Expectorant",
             "wet cough,chest congestion,mucus,productive cough",
             0, "200-400 mg every 4 hrs; drink plenty of water", "Helps loosen chest mucus"),
            ("Loperamide", "Imodium, Lopamide", "Antidiarrheal",
             "diarrhea,loose stools,loose motions",
             0, "2 mg initially then 1 mg after each loose stool; max 8 mg/day", "Not for bloody or fever-associated diarrhea"),
            ("Clotrimazole", "Canesten, Candid-B", "Antifungal",
             "fungal infection,ringworm,athlete foot,skin fungus,itchy skin,candida",
             0, "Apply thin layer twice daily for 2-4 weeks", "Topical only; keep area dry"),
            ("Betadine (Povidone-iodine)", "Betadine", "Antiseptic",
             "wound,cut,scrape,minor skin infection,abrasion",
             0, "Apply to clean wound; cover with bandage", "External use only"),
            ("Vitamin C", "Limcee, Celin 500", "Supplement",
             "cold,low immunity,fatigue,weakness,scurvy",
             0, "500-1000 mg daily", "High doses may cause loose stools"),
            ("Vitamin D3", "Calcirol, D-Rise 60K", "Supplement",
             "bone pain,weakness,fatigue,vitamin D deficiency,rickets",
             0, "1000-2000 IU daily (or 60,000 IU weekly under supervision)", "Check 25-OH-D levels before high-dose therapy"),
            ("Iron Supplement", "Haemup, Ferrous Sulphate", "Supplement",
             "anaemia,weakness,fatigue,pale skin,breathlessness,iron deficiency",
             0, "Take with Vitamin C for better absorption", "May cause dark stools and constipation"),
            ("Diclofenac Gel", "Voltaren Gel, Voveran", "Topical NSAID",
             "muscle pain,joint pain,back pain,sprain,sports injury,swelling",
             0, "Apply 3-4 times daily to affected area", "External use only; avoid broken skin"),
            ("Saline Nasal Spray", "Nasoclear, Simply Saline", "Nasal Decongestant",
             "nasal congestion,stuffy nose,sinusitis,cold,blocked nose",
             0, "2 sprays per nostril 3-4 times daily", "Safe for all ages including infants"),
            ("Folic Acid", "Folvite, Folifer", "Supplement",
             "anaemia,fatigue,neural tube defect prevention,pregnancy",
             0, "5 mg daily (or 400 mcg for prevention)", "Essential during first trimester"),
            ("Calcium + Vitamin D3", "Shelcal, Calcimax", "Supplement",
             "bone pain,muscle cramps,osteoporosis,calcium deficiency",
             0, "500 mg calcium + 250 IU D3 twice daily with meals", "Excess calcium may cause kidney stones"),
            ("Metformin", "Glycomet, Glucophage", "Antidiabetic",
             "diabetes,high blood sugar,type 2 diabetes",
             1, "500-1000 mg twice daily with meals", "Prescription required; monitor kidney function"),
            ("Amlodipine", "Amlong, Norvasc", "Antihypertensive",
             "high blood pressure,hypertension",
             1, "5-10 mg once daily", "Prescription required; do not stop abruptly"),
            ("Azithromycin", "Azithral, Zithromax", "Antibiotic",
             "throat infection,respiratory infection,strep throat,ear infection",
             1, "500 mg once daily for 3-5 days", "Prescription required; complete full course"),
            ("Amoxicillin", "Amoxil, Mox", "Antibiotic",
             "ear infection,tonsillitis,urinary tract infection,sinus infection",
             1, "500 mg three times daily for 5-7 days", "Prescription required; check for penicillin allergy"),
            ("Betahistine", "Vertin, Serc", "Vestibular Agent",
             "vertigo,dizziness,tinnitus,Meniere disease,inner ear",
             0, "8-16 mg three times daily", "For inner ear related dizziness; consult doctor first"),
        ]
        cursor.executemany(
            "INSERT INTO medicines (generic_name, brand_names, category, symptoms, prescription_required, dosage_note, warning) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            medicines
        )
        conn.commit()

    # 4. DATA ENTRY: Major Cities of Gujarat
    cursor.execute("SELECT count(*) FROM doctors")
    if cursor.fetchone()[0] == 0:
        doctors = [
            # --- AHMEDABAD ---
            ("Dr. Mehta", "Cardiologist", "Mon-Fri 11am-5pm", "Ahmedabad"),
            ("Dr. Shah", "Dermatologist", "Mon-Sat 10am-2pm", "Ahmedabad"),
            ("Dr. Trivedi", "Pediatrician", "Daily 9am-6pm", "Ahmedabad"),
            ("Dr. Patel", "Orthopedic", "Mon-Fri 4pm-8pm", "Ahmedabad"),
            
            # --- SURAT ---
            ("Dr. Desai", "Cardiologist", "Tue-Sat 10am-4pm", "Surat"),
            ("Dr. Jariwala", "Dermatologist", "Mon-Fri 5pm-9pm", "Surat"),
            ("Dr. Choksi", "General Physician", "Mon-Sat 9am-9pm", "Surat"),
            
            # --- VADODARA ---
            ("Dr. Amin", "Neurologist", "Mon-Thu 11am-3pm", "Vadodara"),
            ("Dr. Gaekwad", "Orthopedic", "Mon-Sat 10am-1pm", "Vadodara"),
            ("Dr. Bhatt", "Pediatrician", "Daily 10am-7pm", "Vadodara"),
            
            # --- RAJKOT ---
            ("Dr. Virani", "Cardiologist", "Mon-Sat 9am-1pm", "Rajkot"),
            ("Dr. Kathiria", "Dermatologist", "Mon-Fri 4pm-8pm", "Rajkot"),
            ("Dr. Lodha", "General Physician", "Daily 8am-8pm", "Rajkot"),

            # --- JAMNAGAR ---
            ("Dr. Sharma", "Cardiologist", "Mon-Wed 10am-2pm", "Jamnagar"),
            ("Dr. Verma", "Orthopedic", "Mon-Sat 9am-12pm", "Jamnagar"),
            ("Dr. Jadeja", "General Physician", "Daily 10am-8pm", "Jamnagar"),

            # --- BHAVNAGAR ---
            ("Dr. Gohil", "Orthopedic", "Tue-Sat 11am-4pm", "Bhavnagar"),
            ("Dr. Pandya", "Dermatologist", "Mon-Fri 5pm-8pm", "Bhavnagar"),
            
            # --- MUMBAI (For external referrals) ---
            ("Dr. Kapoor", "Neurologist", "Tue-Thu 2pm-6pm", "Mumbai")
        ]
        cursor.executemany("INSERT INTO doctors (name, specialty, availability, city) VALUES (?, ?, ?, ?)", doctors)
        conn.commit()

    # Migration: add user_id to sessions if it doesn't exist yet (for existing DBs)
    try:
        cursor.execute("ALTER TABLE sessions ADD COLUMN user_id INTEGER DEFAULT NULL")
        conn.commit()
    except Exception:
        pass  # Column already exists — safe to ignore

    # Migration: add users table if it doesn't exist yet (for existing DBs)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        full_name TEXT,
        email TEXT,
        phone TEXT,
        role TEXT DEFAULT 'patient',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    )
    """)

    # Password reset tokens table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reset_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token TEXT NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        used INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    
    # ── DYNAMIC DOCTOR DATA TABLE (v2) ────────────────────────────────────────
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS doctors_v2 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doctor_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        specialty TEXT NOT NULL,
        city TEXT NOT NULL,
        years_experience INTEGER DEFAULT 0,
        contact TEXT,
        rating REAL DEFAULT 4.5,
        fees INTEGER DEFAULT 500,
        clinic_address TEXT,
        qualifications TEXT,
        availability TEXT DEFAULT 'Mon-Sat 9am-6pm',
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()

# --- SEARCH TOOL (Smart Filter) ---
def find_doctors_in_db(specialty, city=None):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    
    if city:
        # Filter by Specialty AND City
        query = "SELECT name, specialty, availability, city FROM doctors WHERE specialty LIKE ? AND city LIKE ?"
        cursor.execute(query, ('%' + specialty + '%', '%' + city + '%'))
    else:
        # If no city, just match Specialty
        query = "SELECT name, specialty, availability, city FROM doctors WHERE specialty LIKE ?"
        cursor.execute(query, ('%' + specialty + '%',))
        
    results = cursor.fetchall()
    conn.close()
    return results

# --- BOOKING MANAGEMENT ---
def save_booking(user_id, doctor_id, doctor_name, specialty, city, appointment_date, appointment_time, notes=""):
    """Save a new appointment booking"""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO bookings (user_id, doctor_id, doctor_name, specialty, city, appointment_date, appointment_time, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, doctor_id, doctor_name, specialty, city, appointment_date, appointment_time, "confirmed", notes))
    booking_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return booking_id

def get_user_bookings(user_id):
    """Get all bookings for a user, ordered by most recent"""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, doctor_name, specialty, city, appointment_date, appointment_time, status, created_at
        FROM bookings
        WHERE user_id = ?
        ORDER BY appointment_date DESC, appointment_time DESC
    """, (user_id,))
    results = cursor.fetchall()
    conn.close()
    return results

def get_last_booking(user_id):
    """Get the most recent booking for a user"""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, doctor_name, specialty, city, appointment_date, appointment_time, status, created_at
        FROM bookings
        WHERE user_id = ?
        ORDER BY appointment_date DESC, appointment_time DESC
        LIMIT 1
    """, (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def get_upcoming_bookings(user_id):
    """Get upcoming bookings for a user (future appointments)"""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, doctor_name, specialty, city, appointment_date, appointment_time, status
        FROM bookings
        WHERE user_id = ? AND appointment_date >= date('now')
        ORDER BY appointment_date ASC, appointment_time ASC
    """, (user_id,))
    results = cursor.fetchall()
    conn.close()
    return results

def get_past_bookings(user_id):
    """Get past appointments for a user"""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, doctor_name, specialty, city, appointment_date, appointment_time, status, created_at
        FROM bookings
        WHERE user_id = ? AND appointment_date < date('now')
        ORDER BY appointment_date DESC, appointment_time DESC
    """, (user_id,))
    results = cursor.fetchall()
    conn.close()
    return results

def cancel_booking(booking_id):
    """Cancel a booking"""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE bookings
        SET status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, ("cancelled", booking_id))
    conn.commit()
    conn.close()

def reschedule_booking(booking_id, new_date, new_time):
    """Reschedule a booking to a new date and time"""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE bookings
        SET appointment_date = ?, appointment_time = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (new_date, new_time, booking_id))
    conn.commit()
    conn.close()

# --- SESSION MANAGERS ---
def create_session(title="New Chat", user_id=None):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    cur.execute("INSERT INTO sessions (title, user_id) VALUES (?, ?)", (title, user_id))
    session_id = cur.lastrowid
    conn.commit()
    conn.close()
    return session_id

def update_session_title(session_id, title):
    """Rename a chat session."""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    cur.execute("UPDATE sessions SET title = ? WHERE id = ?", (title[:60], session_id))
    conn.commit()
    conn.close()

def get_all_sessions(user_id=None):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    if user_id is not None:
        cur.execute(
            "SELECT id, title FROM sessions WHERE user_id = ? ORDER BY id DESC",
            (user_id,)
        )
    else:
        cur.execute("SELECT id, title FROM sessions ORDER BY id DESC")
    data = cur.fetchall()
    conn.close()
    return data

def delete_session(session_id):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    cur.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
    cur.execute("DELETE FROM sessions WHERE id=?", (session_id,))
    conn.commit()
    conn.close()

def delete_all_sessions(user_id=None):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    if user_id is not None:
        # Only delete sessions (and their messages) belonging to this user
        cur.execute(
            "DELETE FROM messages WHERE session_id IN "
            "(SELECT id FROM sessions WHERE user_id = ?)",
            (user_id,)
        )
        cur.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    else:
        cur.execute("DELETE FROM messages")
        cur.execute("DELETE FROM sessions")
    conn.commit()
    conn.close()

def save_message(session_id, role, content):
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    cur.execute("INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)", (session_id, role, content))
    conn.commit()
    conn.close()

def load_messages(session_id):
    from langchain_core.messages import HumanMessage, AIMessage
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    cur.execute("SELECT role, content FROM messages WHERE session_id=? ORDER BY id ASC", (session_id,))
    data = cur.fetchall()
    conn.close()
    messages = []
    for role, content in data:
        if role == "user":
            messages.append(HumanMessage(content=content))
        else:
            messages.append(AIMessage(content=content))
    return messages

# ── DYNAMIC DOCTOR / LAB LOOKUP ─────────────────────────────────────────────

def find_doctor_by_name(name: str, city: str = None):
    """
    Search doctors/labs by partial name match.
    E.g. find_doctor_by_name('Modi Laboratory', 'Jamnagar')
    """
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    if city:
        cursor.execute(
            "SELECT name, specialty, availability, city FROM doctors "
            "WHERE name LIKE ? AND city LIKE ?",
            ('%' + name + '%', '%' + city + '%')
        )
    else:
        cursor.execute(
            "SELECT name, specialty, availability, city FROM doctors WHERE name LIKE ?",
            ('%' + name + '%',)
        )
    results = cursor.fetchall()
    conn.close()
    return results


def add_doctor_dynamic(name: str, specialty: str, city: str,
                       availability: str = "Mon-Sat 9am-6pm"):
    """
    Add a new doctor/lab/clinic mentioned by the user if not already in DB.
    Returns True if a new record was inserted, False if it already existed.
    """
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    # Deduplicate: skip if a record with same name+city exists
    cursor.execute(
        "SELECT id FROM doctors WHERE name LIKE ? AND city LIKE ?",
        ('%' + name + '%', '%' + city + '%')
    )
    if cursor.fetchone():
        conn.close()
        return False
    cursor.execute(
        "INSERT INTO doctors (name, specialty, availability, city) VALUES (?, ?, ?, ?)",
        (name, specialty, availability, city)
    )
    conn.commit()
    conn.close()
    return True


def search_doctors_smart(name: str = None, specialty: str = None, city: str = None):
    """
    Smart search: tries name-match first, then specialty+city, then specialty-only.
    Returns list of (name, specialty, availability, city) tuples.
    """
    # 1. Name-based search (highest priority — user named a specific doctor/lab)
    if name:
        results = find_doctor_by_name(name, city)
        if results:
            return results
    # 2. Specialty + city
    if specialty and city:
        results = find_doctors_in_db(specialty, city)
        if results:
            return results
    # 3. Specialty only (any city)
    if specialty:
        results = find_doctors_in_db(specialty, None)
        if results:
            return results
    return []


# ── MEDICINE LOOKUP ──────────────────────────────────────────────────────────

def find_medicines_for_symptoms(symptoms: list) -> list:
    """
    Return verified medicine records from DB whose symptom tags overlap
    with the given symptom list.  Each record is a dict with keys:
    generic_name, brand_names, category, dosage_note, warning, prescription_required.
    """
    if not symptoms:
        return []
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT generic_name, brand_names, category, symptoms, "
        "prescription_required, dosage_note, warning FROM medicines"
    )
    all_meds = cursor.fetchall()
    conn.close()

    symptom_lower = [s.lower() for s in symptoms]
    matched = []
    for row in all_meds:
        generic, brands, category, sym_tags, rx, dosage, warning = row
        # Check if any symptom keyword appears in this medicine's symptom tags
        tags = [t.strip().lower() for t in (sym_tags or "").split(",")]
        if any(any(tag in s or s in tag for tag in tags) for s in symptom_lower):
            matched.append({
                "generic_name": generic,
                "brand_names": brands,
                "category": category,
                "dosage_note": dosage,
                "warning": warning,
                "prescription_required": bool(rx),
            })
    return matched




# ── PATIENT MEMORY ────────────────────────────────────────────────────────────

def save_patient_memory(user_id: int, symptoms: list, condition: str = "",
                        specialist: str = "", session_id: int = None):
    """Persist a snapshot of the current turn's symptoms/condition for this user."""
    if not user_id or not symptoms:
        return
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    for sym in symptoms:
        if sym:
            cur.execute(
                "INSERT INTO patient_memory "
                "(user_id, symptom, condition, specialist, session_id) VALUES (?, ?, ?, ?, ?)",
                (user_id, sym.lower().strip(), condition, specialist, session_id)
            )
    conn.commit()
    conn.close()


def get_patient_memory_summary(user_id: int, limit: int = 30) -> str:
    """
    Return a short plain-text summary of the user's past symptoms/conditions
    to inject into the agent as long-term context.
    """
    if not user_id:
        return ""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    cur = conn.cursor()
    cur.execute("""
        SELECT symptom, condition, specialist, recorded_at
        FROM patient_memory
        WHERE user_id = ?
        ORDER BY recorded_at DESC
        LIMIT ?
    """, (user_id, limit))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return ""

    from collections import Counter
    symptoms_freq = Counter(r[0] for r in rows if r[0])
    conditions    = list(dict.fromkeys(r[1] for r in rows if r[1]))[:5]
    specialists   = list(dict.fromkeys(r[2] for r in rows if r[2]))[:5]
    last_date     = rows[0][3][:10] if rows[0][3] else "unknown"

    parts = [f"Patient health history (last {len(rows)} records, most recent: {last_date}):"]
    if symptoms_freq:
        top_symptoms = ", ".join(f"{s} (x{c})" for s, c in symptoms_freq.most_common(8))
        parts.append(f"  - Past symptoms: {top_symptoms}")
    if conditions:
        parts.append(f"  - Past conditions: {', '.join(conditions)}")
    if specialists:
        parts.append(f"  - Previously consulted: {', '.join(specialists)}")
    return "\n".join(parts)


# ── Auth Token Helpers ───────────────────────────────────────────────────────
import uuid

def create_auth_token(user_id: int, days: int = 30) -> str:
    """Create a persistent auth token for a user, valid for `days` days."""
    token     = str(uuid.uuid4())
    expires   = (datetime.utcnow() + timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    conn      = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute(
        "INSERT OR REPLACE INTO auth_tokens (token, user_id, expires_at) VALUES (?, ?, ?)",
        (token, user_id, expires),
    )
    conn.commit()
    conn.close()
    return token

def validate_auth_token(token: str) -> dict | None:
    """Return user dict if token is valid and not expired, else None."""
    conn    = sqlite3.connect(DB_NAME, timeout=10)
    cursor  = conn.cursor()
    cursor.execute(
        "SELECT user_id FROM auth_tokens WHERE token = ? AND expires_at > datetime('now')",
        (token,),
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    # Re-use existing login_user lookup via raw query
    conn2   = sqlite3.connect(DB_NAME, timeout=10)
    cursor2 = conn2.cursor()
    cursor2.execute(
        "SELECT id, username, full_name, email, phone, role FROM users WHERE id = ?",
        (row[0],),
    )
    u = cursor2.fetchone()
    conn2.close()
    if not u:
        return None
    return {"id": u[0], "username": u[1], "full_name": u[2],
            "email": u[3], "phone": u[4], "role": u[5]}

def revoke_auth_token(token: str):
    """Delete a token on logout."""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.execute("DELETE FROM auth_tokens WHERE token = ?", (token,))
    conn.commit()
    conn.close()


# ── DYNAMIC DOCTOR MANAGEMENT (doctors_v2 table) ────────────────────────────────

def get_all_doctors():
    """Get all doctors from doctors_v2 table as list of dicts."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, doctor_id, name, specialty, city, years_experience, 
               contact, rating, fees, clinic_address, qualifications, 
               availability, is_active, created_at, updated_at
        FROM doctors_v2
        WHERE is_active = 1
        ORDER BY name ASC
    """)
    columns = ['id', 'doctor_id', 'name', 'specialty', 'city', 'years_experience',
               'contact', 'rating', 'fees', 'clinic_address', 'qualifications',
               'availability', 'is_active', 'created_at', 'updated_at']
    rows = cursor.fetchall()
    conn.close()
    return [dict(zip(columns, row)) for row in rows]


def save_doctor(name: str, specialty: str, city: str, years_experience: int,
                contact: str, rating: float = 4.5, fees: int = 500,
                clinic_address: str = "", qualifications: str = "",
                availability: str = "Mon-Sat 9am-6pm"):
    """Add a new doctor to doctors_v2 table."""
    import uuid
    conn = create_connection()
    cursor = conn.cursor()
    
    doctor_id = f"DR{uuid.uuid4().hex[:8].upper()}"
    
    cursor.execute("""
        INSERT INTO doctors_v2 
        (doctor_id, name, specialty, city, years_experience, contact, 
         rating, fees, clinic_address, qualifications, availability, is_active, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (doctor_id, name, specialty, city, years_experience, contact,
          rating, fees, clinic_address, qualifications, availability, 1, 
          datetime.now().isoformat(), datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    return True


def update_doctor_info(doctor_id: int, name: str = None, specialty: str = None,
                       city: str = None, years_experience: int = None,
                       contact: str = None, rating: float = None, fees: int = None,
                       clinic_address: str = None, qualifications: str = None,
                       availability: str = None):
    """Update doctor information."""
    conn = create_connection()
    cursor = conn.cursor()
    
    updates = []
    values = []
    
    if name is not None:
        updates.append("name = ?")
        values.append(name)
    if specialty is not None:
        updates.append("specialty = ?")
        values.append(specialty)
    if city is not None:
        updates.append("city = ?")
        values.append(city)
    if years_experience is not None:
        updates.append("years_experience = ?")
        values.append(years_experience)
    if contact is not None:
        updates.append("contact = ?")
        values.append(contact)
    if rating is not None:
        updates.append("rating = ?")
        values.append(rating)
    if fees is not None:
        updates.append("fees = ?")
        values.append(fees)
    if clinic_address is not None:
        updates.append("clinic_address = ?")
        values.append(clinic_address)
    if qualifications is not None:
        updates.append("qualifications = ?")
        values.append(qualifications)
    if availability is not None:
        updates.append("availability = ?")
        values.append(availability)
    
    if not updates:
        conn.close()
        return False
    
    updates.append("updated_at = ?")
    values.append(datetime.now().isoformat())
    values.append(doctor_id)
    
    query = f"UPDATE doctors_v2 SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, values)
    conn.commit()
    conn.close()
    return True


def delete_doctor(doctor_id: int):
    """Soft delete a doctor (mark as inactive)."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE doctors_v2 
        SET is_active = 0, updated_at = ?
        WHERE id = ?
    """, (datetime.now().isoformat(), doctor_id))
    conn.commit()
    conn.close()
    return True


if __name__ == "__main__":
    init_db()
    print("✅ Gujarat Database Updated!")
