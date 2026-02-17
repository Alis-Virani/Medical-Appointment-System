import sqlite3

DB_NAME = "hospital.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    
    conn.close()

# --- SEARCH TOOL (Smart Filter) ---
def find_doctors_in_db(specialty, city=None):
    conn = sqlite3.connect(DB_NAME)
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

# --- SESSION MANAGERS ---
def create_session(title="New Chat"):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT INTO sessions (title) VALUES (?)", (title,))
    session_id = cur.lastrowid
    conn.commit()
    conn.close()
    return session_id

def get_all_sessions():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM sessions ORDER BY id DESC")
    data = cur.fetchall()
    conn.close()
    return data

def delete_session(session_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
    cur.execute("DELETE FROM sessions WHERE id=?", (session_id,))
    conn.commit()
    conn.close()

def save_message(session_id, role, content):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)", (session_id, role, content))
    conn.commit()
    conn.close()

def load_messages(session_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT role, content FROM messages WHERE session_id=? ORDER BY id ASC", (session_id,))
    data = cur.fetchall()
    conn.close()
    return [{"role": row[0], "content": row[1]} for row in data]

if __name__ == "__main__":
    init_db()
    print("✅ Gujarat Database Updated!")