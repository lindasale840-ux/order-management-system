import sqlite3

conn = sqlite3.connect(
    "database/app.db"
)

cursor = conn.cursor()

cursor.execute(
    """
    SELECT
        username,
        role
    FROM users
    """
)

print(
    cursor.fetchall()
)