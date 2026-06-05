import sqlite3

conn = sqlite3.connect("database/app.db")

cursor = conn.cursor()

cursor.execute("""

SELECT *

FROM equipment_tracking

""")

for row in cursor.fetchall():

    print(row)

conn.close()