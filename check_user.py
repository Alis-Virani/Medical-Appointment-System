import sqlite3

conn = sqlite3.connect("hospital.db")
cur = conn.cursor()
cur.execute("SELECT id, full_name, role FROM users ORDER BY id DESC LIMIT 10")
print("\nRecent users in database:")
for row in cur.fetchall():
    print(f"ID: {row[0]}, Name: {row[1]}, Role: {row[2]}")
conn.close()
