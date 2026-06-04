import sqlite3

conn = sqlite3.connect(
    "database/app.db"
)

cursor = conn.cursor()

cursor.execute("""

SELECT
id,
username,
action,
order_number,
created_at

FROM logs

ORDER BY id DESC

LIMIT 20

""")

for row in cursor.fetchall():
    print(row)

conn.close()