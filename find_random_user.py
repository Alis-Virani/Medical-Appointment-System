import sqlite3

conn = sqlite3.connect("hospital.db")
cur = conn.cursor()

# Find random user
cur.execute("SELECT id, username, full_name, role FROM users WHERE username='random'")
user = cur.fetchone()

if user:
    print(f"\nUser 'random':")
    print(f"  ID: {user[0]}")
    print(f"  Username: {user[1]}")
    print(f"  Full Name: {user[2]}")
    print(f"  Role: {user[3]}")
    
    # Check if they have any bookings
    cur.execute(f"SELECT COUNT(*) FROM bookings WHERE doctor_name LIKE '%{user[2]}%'")
    count = cur.fetchone()[0]
    print(f"  Bookings as doctor: {count}")
else:
    print("User 'random' not found")
    cur.execute("SELECT username, full_name FROM users LIMIT 5")
    print("\nAvailable users:")
    for row in cur.fetchall():
        print(f"  {row[0]} ({row[1]})")

conn.close()
