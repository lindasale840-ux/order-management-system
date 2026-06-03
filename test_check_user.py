import sqlite3

conn = sqlite3.connect(
    "database/app.db"
)

cursor = conn.cursor()

cursor.execute(
    "PRAGMA table_info(users)"
)

for row in cursor.fetchall():
    print(row)

conn.close()