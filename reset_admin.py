import sqlite3
import hashlib

new_password = hashlib.sha256(
    "admin123".encode()
).hexdigest()

conn = sqlite3.connect(
    "database/app.db"
)

cursor = conn.cursor()

cursor.execute(
    """
    UPDATE users
    SET password_hash = ?
    WHERE username = 'admin'
    """,
    (new_password,)
)

conn.commit()

print("Admin password reset")

conn.close()